"""
Package-related classes and methods are in pkg.package module. All constructing arguments are accessible via property.
"""

import glob
import json
import os
import random
import shutil
import sys
import threading
import traceback
import urllib2
import zipfile
from StringIO import StringIO

import ida_loader
from semantic_version import Version, Spec

from . import internal_api
from .config import g
from .downloader import _download
from .env import ea as current_ea, os as current_os
from .logger import getLogger
from .util import putenv, execute_in_main_thread, rename
from .virtualenv_utils import FixInterpreter

ALL_EA = (32, 64)
__all__ = ["LocalPackage", "InstallablePackage"]

log = getLogger(__name__)


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


def _unique_items(items):
    seen = set()
    res = [(item, seen.add(item))[0] for item in items if item not in seen]
    return res


def _idausr_add_unix(orig, new):
    if orig is None:
        orig = os.path.join(os.getenv('HOME'), '.idapro')
    return ':'.join(_unique_items(orig.split(':') + [new]))


def _idausr_add_win(orig, new):
    if orig is None:
        orig = os.path.join(os.getenv('APPDATA'), 'Hex-Rays', 'IDA Pro')
    return ';'.join(_unique_items(orig.split(';') + [new]))


def _idausr_add(orig, new):
    if current_os == 'win':
        return _idausr_add_win(orig, new)
    else:
        return _idausr_add_unix(orig, new)


def _idausr_remove(orig, target):
    if current_os == 'win':
        sep = ';'
    else:
        sep = ':'

    orig = orig.split(sep)
    index = orig.index(target)

    assert index != -1

    orig.remove(target)
    return sep.join(orig)


class LocalPackage(object):
    def __init__(self, id, path, version):
        self.id = str(id)
        self.version = str(version)

        self.path = os.path.normpath(path)

    def remove(self):
        """
        Removes a package.
        """
        idausr = os.environ.get('IDAUSR', '')
        if self.path in idausr:
            new = _idausr_remove(idausr, self.path)
            putenv('IDAUSR', new)

            internal_api.invalidate_idausr()

        with FixInterpreter():
            for script in self.metadata().get('uninstallers', []):
                script = os.path.join(self.path, script)
                try:
                    execfile(script, {__file__: script})
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

    def install(self, remove_on_fail=False):
        """
        Run python scripts specified by :code:`installers` field in `info.json`.

        :returns: None
        """
        orig_cwd = os.getcwd()
        try:
            os.chdir(self.path)
            info = self.metadata()
            scripts = info.get('installers', [])
            if not isinstance(scripts, list):
                raise Exception(
                    '%r Corrupted package: installers key is not list')
            with FixInterpreter():
                for script in scripts:
                    log.info('Executing installer path %r...', script)
                    script = os.path.join(self.path, script)
                    execfile(script, {
                        __file__: script
                    })
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
        if not force and self.path in os.environ.get('IDAUSR', ''):
            # Already loaded, just update sys.path for python imports
            sys.path.append(self.path)
            return

        env = str(_idausr_add(os.getenv('IDAUSR'), self.path))
        # XXX: find a more efficient way to ensure dependencies
        errors = []
        for dependency in self.metadata().get('dependencies', {}).keys():
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
            assert isinstance(threading.current_thread(),
                              threading._MainThread)
            # Load plugins immediately
            # processors / loaders will be loaded on demand
            sys.path.append(self.path)

            # Update IDAUSR variable
            internal_api.invalidate_idausr()
            putenv('IDAUSR', env)

            # Immediately load compatible plugins
            self._find_loadable_modules('plugins', ida_loader.load_plugin)

            # Find loadable processor modules, and if exists, invalidate cached process list (proccache).
            invalidates = []
            self._find_loadable_modules('procs', invalidates.append)

            if invalidates:
                internal_api.invalidate_proccache()

        execute_in_main_thread(handler)

    def populate_env(self):
        """
        A passive version of load; it only populates IDAUSR variable.
        It's called at :code:`idapythonrc.py`.
        """
        errors = []
        for dependency in self.metadata().get('dependencies', {}).keys():
            dep = LocalPackage.by_name(dependency)
            if not dep:
                errors.append('Dependency not found: %r' % dependency)
                continue
            dep.populate_env()

        if errors:
            for error in errors:
                log.error(error)
            return

        putenv('IDAUSR', str(_idausr_add(os.getenv("IDAUSR"), self.path)))
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

    def _find_loadable_modules(self, path, callback):
        # Load modules in external languages (.py, .idc, ...)
        for suffix in ['.' + x.fileext for x in internal_api.get_extlangs()]:
            expr = os.path.join(self.path, path, '*' + suffix)
            for path in glob.glob(expr):
                callback(str(path))

        # Load native modules
        for suffix in (_get_native_suffix(),):
            expr = os.path.join(self.path, path, '*' + suffix)
            for path in glob.glob(expr):
                is64 = path[:-len(suffix)][-2:] == '64'

                if is64 == (current_ea == 64):
                    callback(str(path))

    def metadata(self):
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
        InstallablePackage.install_from_repo(
            self.repo, self.id, allow_upgrade=upgrade)

    @staticmethod
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
            downloading = None if (
                prev and release['version'] == prev.version) else release['version']
        else:
            downloading = None

        if downloading:
            log.info('Collecting %s...', name)
            data = _download(repo.url + '/download?spec=' +
                             urllib2.quote(name) + '==' + urllib2.quote(downloading)).read()
            io = StringIO(data)
            f = zipfile.ZipFile(io, 'r')

            info = json.load(f.open('info.json'))
            install_path = os.path.join(g['path']['packages'], info["_id"])

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
            f.extractall(install_path)

            # Initiate LocalPackage object
            pkg = LocalPackage(info['_id'], install_path, info['version'])
        else:
            pkg = prev

            log.info("Requirement already satisfied: %s%s",
                     name, '' if version_spec == '*' else version_spec)

        restart_required = pkg.metadata().get('restart_required', False)
        _visited[name] = (pkg.version, restart_required)

        # First, install dependencies
        # TODO: add version check
        for dep_name, dep_version_spec in pkg.metadata().get('dependencies', {}).items():
            InstallablePackage.install_from_repo(
                repo, dep_name, dep_version_spec, allow_upgrade, _visited)

        if downloading:
            pkg.install()

        if not restart_required:
            pkg.load()

        if top_level:
            log.info("Successfully installed %s", ' '.join('%s-%s' %
                                                           (key, value[0]) for key, value in _visited.items()))

            delayed = [(key, value)
                       for key, value in _visited.items() if value[1]]
            if delayed:
                log.info(
                    "Plugins in the following packages will be loaded after restarting IDA.")
                log.info("  %s", " ".join('%s-%s' %
                                          (key, value[0]) for key, value in delayed))

        return pkg

    def __repr__(self):
        return '<InstallablePackage id=%r version=%r repo=%r>' % \
               (self.id, self.version, self.repo)
