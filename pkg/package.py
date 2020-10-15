"""
Package-related classes and methods are in pkg.package module. All constructing arguments are accessible via property.
"""

import ctypes
import glob
import json
import os
import random
import runpy
import shutil
import sys
import traceback
import zipfile

import ida_kernwin
import ida_loader
import ida_diskio

from .config import g
from .env import ea as current_ea, os as current_os
from .internal_api import invalidate_proccache, get_extlangs, idausr_remove, idausr_add
from .logger import getLogger
from .vendor.semantic_version import Version, Spec
from .virtualenv_utils import FixInterpreter

__all__ = ["LocalPackage", "InstallablePackage"]

log = getLogger(__name__)


def rename(old, new):
    if sys.platform == 'win32':
        if not ctypes.windll.kernel32.MoveFileExA(str(old), str(new), 0):
            raise WindowsError(ctypes.windll.kernel32.GetLastError())
    else:
        return os.rename(old, new)


def _get_native_suffix():
    if current_os == 'win':
        suffix = '.dll'
    elif current_os == 'linux':
        suffix = '.so'
    elif current_os == 'mac':
        suffix = '.dylib'
    else:
        raise Exception("unknown os: %r" % current_os)
    return suffix


class LocalPackage(object):
    def __init__(self, id, path, version):
        self.id = str(id)
        self.version = str(version)

        self.path = os.path.normpath(path)

    def remove(self):
        """
        Removes a package.
        """
        idausr_remove(self.path)

        with FixInterpreter():
            for script in self.info().get('uninstallers', []):
                script = os.path.join(self.path, script)
                try:
                    runpy.run_path(script)
                except Exception:
                    # XXX: How can I rollback this?
                    traceback.print_exc()
                    log.warn(
                        "Uninstallation script %r exited with exception!", script)

        if not LocalPackage._remove_package_dir(self.path):
            log.error(
                "Package directory is in use and will be removed after restart.")

            # If not modified, the only case this fails is, custom ld.so or windows.
            # Latter case is common.
            new_path = self.path.rstrip('/\\') + '-removed'
            if os.path.exists(new_path):
                new_path += '-%x' % random.getrandbits(64)
            rename(self.path, new_path)
            # XXX: is it good to mutate this object?
            self.path = new_path

        log.info("Done!")

    def install(self, remove_on_fail=False):
        """
        Run python scripts specified by :code:`installers` field in `info.json`.

        :returns: None
        """
        orig_cwd = os.getcwd()
        try:
            os.chdir(self.path)
            info = self.info()
            scripts = info.get('installers', [])
            if not isinstance(scripts, list):
                raise Exception(
                    '%r: Corrupted package: installers key is not list' % self.id)
            with FixInterpreter():
                for script in scripts:
                    log.info('Executing installer path %r...', script)
                    script = os.path.join(self.path, script)
                    runpy.run_path(script)
        except Exception:
            log.info('Installer failed!')
            if remove_on_fail:
                self.remove()
            raise
        finally:
            os.chdir(orig_cwd)

    def load(self, force=False):
        """
        Actually does :code:`ida_loaders.load_plugin(paths)`, and updates IDAUSR variable.
        """
        if not force and self.path in ida_diskio.get_ida_subdirs(''):
            # Already loaded, just update sys.path for python imports
            if self.path not in sys.path:
                sys.path.append(self.path)
            return

        # XXX: find a more efficient way to ensure dependencies
        errors = []
        for dependency in self.info().get('dependencies', {}).keys():
            dep = LocalPackage.by_name(dependency)
            if not dep:
                errors.append('Dependency not found: %r' % dependency)
                continue
            dep.load()

        if errors:
            for error in errors:
                log.error(error)
            return

        def handler():
            # Load plugins immediately
            # processors / loaders will be loaded on demand
            if self.path not in sys.path:
                sys.path.append(self.path)

            # Update IDAUSR variable
            idausr_add(self.path)

            # Immediately load compatible plugins
            self._find_loadable_modules('plugins', ida_loader.load_plugin)

            # Find loadable processor modules, and if exists, invalidate cached process list (proccache).
            invalidates = []
            self._find_loadable_modules('procs', invalidates.append)

            if invalidates:
                invalidate_proccache()

        # Run in main thread
        ida_kernwin.execute_sync(handler, ida_kernwin.MFF_FAST)

    def populate_env(self):
        """
        A passive version of load; it only populates IDAUSR variable.
        It's called at :code:`idapythonrc.py`.
        """
        errors = []
        for dependency in self.info().get('dependencies', {}).keys():
            dep = LocalPackage.by_name(dependency)
            if not dep:
                errors.append('Dependency not found: %r' % dependency)
                continue
            dep.populate_env()

        if errors:
            for error in errors:
                log.error(error)
            return

        idausr_add(self.path)

        if self.path not in sys.path:
            sys.path.append(self.path)

    def plugins(self):
        return self._collect_modules('plugins')

    def loaders(self):
        return self._collect_modules('loaders')

    def procs(self):
        return self._collect_modules('procs')

    def _collect_modules(self, category):
        result = []
        self._find_loadable_modules(category, result.append)
        return result

    def _find_loadable_modules(self, subdir, callback):
        # Load modules in external languages (.py, .idc, ...)
        for suffix in ['.' + x.fileext for x in get_extlangs()]:
            expr = os.path.join(self.path, subdir, '*' + suffix)
            for path in glob.glob(expr):
                callback(str(path))

        # Load native modules
        for suffix in (_get_native_suffix(),):
            expr = os.path.join(self.path, subdir, '*' + suffix)
            for path in glob.glob(expr):
                is64 = path[:-len(suffix)][-2:] == '64'

                if is64 == (current_ea == 64):
                    callback(str(path))

    def info(self):
        """
        Loads :code:`info.json` and returns a parsed JSON object.

        :rtype: dict
        """
        with open(os.path.join(self.path, 'info.json'), 'rb') as _file:
            return json.load(_file)

    @staticmethod
    def by_name(name, prefix=None):
        """
        Returns a package with specified `name`.

        :rtype: LocalPackage
        """
        if prefix is None:
            prefix = g['path']['packages']

        path = os.path.join(prefix, name)

        # check if the folder exists
        if not os.path.isdir(path):
            return None

        # filter removed package
        removed = os.path.join(path, '.removed')
        if os.path.isfile(removed):
            LocalPackage._remove_package_dir(path)
            return None

        info_json = os.path.join(path, 'info.json')
        if not os.path.isfile(info_json):
            log.warn('Warning: info.json is not found at %r', path)
            return None

        with open(info_json, 'rb') as _file:
            try:
                info = json.load(_file)
            except Exception:
                traceback.print_exc()
                log.warn('Warning: info.json is not valid at %r', path)
                return None

        result = LocalPackage(
            id=info['_id'], path=path, version=info['version'])
        return result

    @staticmethod
    def all(disabled=False):
        """
        List all packages installed at :code:`g['path']['packages']`.

        :rtype: list(LocalPackage)
        """
        prefix = g['path']['packages']

        res = os.listdir(prefix)
        res = (x for x in res if os.path.isdir(os.path.join(prefix, x)))
        res = (LocalPackage.by_name(x) for x in res)
        res = (x for x in res if x)
        res = [x for x in res if (x.id in g['ignored_packages']) == disabled]
        return res

    @staticmethod
    def _remove_package_dir(path):
        errors = []

        def onerror(_listdir, _path, exc_info):
            log.error("%s: %s", _path, str(exc_info[1]))
            errors.append(exc_info[1])

        shutil.rmtree(path, onerror=onerror)

        if errors:
            # Mark for later removal
            open(os.path.join(path, '.removed'), 'wb').close()

        return not errors

    def __repr__(self):
        return '<LocalPackage id=%r path=%r version=%r>' % \
               (self.id, self.path, self.version)


class InstallablePackage(object):
    def __init__(self, id, name, version, description, author, repo):
        self.id = str(id)
        self.name = name
        self.version = str(version)
        self.description = description
        self.repo = repo
        self.author = author

    def install(self, upgrade=False):
        """
        Just calls :code:`InstallablePackage.install_from_repo(self.repo, self.id, upgrade)`.
        """
        install_from_repo(self.repo, self.id, allow_upgrade=upgrade)

    def __repr__(self):
        return '<InstallablePackage id=%r version=%r repo=%r>' % \
               (self.id, self.version, self.repo)


def install_from_repo(repo, name, version_spec='*', allow_upgrade=False, _visited=None):
    """
    This method downloads a package satisfying spec.

    .. note ::
        The function waits until all of dependencies are installed.
        Run it as separate thread if possible.
    """

    top_level = _visited is None
    _visited = _visited or {}

    if name in _visited:
        log.warn("Cyclic dependency found when installing %r <-> %r",
                 name, _visited)
        return

    prev = LocalPackage.by_name(name)

    _version_spec = Spec(version_spec)
    satisfies_local = prev and Version(prev.version) in _version_spec

    if allow_upgrade or not satisfies_local:
        log.debug("Fetching releases for %r from %r...", name, repo)

        releases = repo.releases(name)
        if not releases:
            error = "Release not found on remote repository: %r on %r (error: %r)" % (
                name, repo, releases['error'])
            raise Exception(error)

        releases = [release for release in releases
                    if Version(release['version']) in _version_spec]

        if not releases:
            error = "Release satisfying the condition %r %r not found on remote repository %r" % (
                name, version_spec, repo)
            raise Exception(error)
        downloading = None if (
                prev and releases[-1]['version'] == prev.version) else releases[-1]['version']
    else:
        downloading = None

    if downloading:
        log.info('Collecting %s...', name)
        data = repo.download(name, downloading)
        f = zipfile.ZipFile(data, 'r')

        # No  /: topmost files
        # One /: topmost folders
        topmost_files = [path for path in f.namelist() if path.count('/') == 0]
        # From ZipInfo.is_dir() in Python 3.x
        topmost_folders = [path for path in f.namelist() if path.endswith('/')]
        common_prefix = topmost_folders[0] if len(topmost_files) == 0 and len(topmost_folders) == 1 else ""

        info = json.load(f.open(common_prefix + 'info.json'))
        packages_path = g['path']['packages']
        install_path = os.path.join(packages_path, info["_id"])

        # this ensures os.path.exists(install_path) == False
        # TODO: should we unload a already-loaded plugin?
        if prev:
            prev.remove()
            assert not os.path.exists(install_path)

        # XXX: edge case?
        removed = os.path.join(install_path, '.removed')
        if os.path.isfile(removed):
            os.unlink(removed)

        log.info('Extracting into %r...', install_path)
        if common_prefix:
            f.extractall(packages_path)
            os.rename(os.path.join(packages_path, common_prefix), install_path)
        else:
            f.extractall(install_path)

        # Initiate LocalPackage object
        pkg = LocalPackage(info['_id'], install_path, info['version'])
    else:
        pkg = prev

        log.info("Requirement already satisfied: %s%s",
                 name, '' if version_spec == '*' else version_spec)

    restart_required = pkg.info().get('restart_required', False)
    _visited[name] = (pkg.version, restart_required)

    # First, install dependencies
    # TODO: add version check
    for dep_name, dep_version_spec in pkg.info().get('dependencies', {}).items():
        install_from_repo(repo, dep_name, dep_version_spec, allow_upgrade, _visited)

    # Then, install this package.
    if downloading:
        pkg.install()

    if not restart_required:
        pkg.load()

    if top_level:
        log.info("Successfully installed %s",
                 ' '.join('%s-%s' % (key, value[0]) for key, value in _visited.items()))

        delayed = [(key, value) for key, value in _visited.items() if value[1]]
        if delayed:
            log.info(
                "Plugins in the following packages will be loaded after restarting IDA.")
            log.info(
                "  %s", " ".join('%s-%s' % (key, value[0]) for key, value in delayed))

    return pkg
