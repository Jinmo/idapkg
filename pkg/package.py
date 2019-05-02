"""
Package-related classes and methods are in pkg.package module. All constructing arguments are accessible via property.
"""

import os
import sys
import json
import glob
import shutil
import zipfile
import urllib2
import traceback
import ida_loader
from StringIO import StringIO

from .config import g
from .downloader import download
from .logger import logger
from .env import ea as current_ea, os as current_os
from .util import putenv, execute_in_main_thread
from .virtualenv_utils import FixInterpreter

from . import internal_api

ALL_EA = (32, 64)
__all__ = ["LocalPackage", "InstallablePackage"]


def get_native_suffix():
    if current_os == 'win':
        suffix = '.dll'
    elif current_os == 'linux':
        suffix = '.so'
    elif current_os == 'mac':
        suffix = '.dylib'
    else:
        raise Exception("unknown os: %r" % current_os)
    return suffix


def uniq(items):
    seen = set()
    res = [(item, seen.add(item))[0] for item in items if item not in seen]
    return res


def _idausr_add_unix(orig, new):
    if orig is None:
        orig = os.path.join(os.getenv('HOME'), '.idapro')
    return ':'.join(uniq(orig.split(':') + [new]))


def _idausr_add_win(orig, new):
    if orig is None:
        orig = os.path.join(os.getenv('APPDATA'), 'Hex-Rays', 'IDA Pro')
    return ';'.join(uniq(orig.split(';') + [new]))


def _idausr_add(orig, new):
    if current_os == 'win':
        return _idausr_add_win(orig, new)
    else:
        return _idausr_add_unix(orig, new)


def idausr_remove(orig, target):
    if current_os == 'win':
        sep = ';'
    else:
        sep = ':'

    orig = orig.split(sep)
    index = orig.index(target)

    assert index != -1

    orig.remove(target)
    return sep.join(orig)


class Package(object):
    def __init__(self, id, version):
        self.id = str(id)
        self.version = str(version)

    def __repr__(self):
        raise NotImplementedError


class LocalPackage(Package):
    def __init__(self, id, path, version):
        super(LocalPackage, self).__init__(id, version)

        self.path = os.path.normpath(path)

    def remove(self):
        """
        Removes a package.
        """
        with open(os.path.join(self.path, '.removed'), 'wb'):
            pass

        idausr = os.environ.get('IDAUSR', '')
        if self.path in idausr:
            new = idausr_remove(idausr, self.path)
            putenv('IDAUSR', new)

            internal_api.invalidate_idausr()

        if not LocalPackage._remove_package_dir(self.path):
            logger.error(
                "Package directory is in use and will be removed after restart.")

        logger.info("Done!")

    @staticmethod
    def _remove_package_dir(path):
        errors = []

        def onerror(_listdir, _path, exc):
            logger.error(str(exc))
            errors.append(exc)

        shutil.rmtree(path, onerror=onerror)

        return not errors

    def install(self):
        """
        Run python scripts specified by :code:`installers` field in `info.json`.
        """
        orig_cwd = os.getcwd()
        try:
            os.chdir(self.path)
            info = self.metadata()
            t = info.get('installers', [])
            if not isinstance(t, list):
                raise Exception(
                    '%r Corrupted package: installers key is not list')
            with FixInterpreter():
                for script in t:
                    logger.info('Executing installer path %r...' % script)
                    script = os.path.join(self.path, script)
                    execfile(script, {
                        __file__: script
                    })
            logger.info('Done!')
        except:
            logger.info('Installer failed!')
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
        for dependency in self.metadata().get('dependencies', {}).keys():
            LocalPackage.by_name(dependency).load()

        def handler():
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
        # passive version of load
        for dependency in self.info().get('dependencies', {}).keys():
            LocalPackage.by_name(dependency).populate_env()

        putenv('IDAUSR', str(_idausr_add(os.getenv("IDAUSR"), self.path)))
        sys.path.append(self.path)

    def _find_loadable_modules(self, path, callback):
        for suffix in ['.' + x.fileext for x in internal_api.get_extlangs()]:
            expr = os.path.join(self.path, path, '*' + suffix)
            for path in glob.glob(expr):
                callback(str(path))

        for suffix in (get_native_suffix(),):
            expr = os.path.join(self.path, path, '*' + suffix)
            for path in glob.glob(expr):
                is64 = path[:-len(suffix)][-2:] == '64'

                if is64 == (current_ea == 64):
                    callback(str(path))

    def metadata(self):
        """
        Loads :code:`info.json` and returns a parsed JSON object.
        """
        with open(os.path.join(self.path, 'info.json'), 'rb') as f:
            return json.load(f)

    @staticmethod
    def by_name(name, prefix=None):
        """
        Returns a package with specified `name`.
        """
        if prefix is None:
            prefix = g['path']['packages']

        path = os.path.join(prefix, name)

        # filter removed package
        removed = os.path.join(path, '.removed')
        if os.path.isfile(removed):
            LocalPackage._remove_package_dir(path)
            return None

        info_json = os.path.join(path, 'info.json')
        if not os.path.isfile(info_json):
            logger.debug('Warning: info.json is not found at %r' % path)
            return None

        with open(info_json, 'rb') as f:
            info = json.load(f)
            result = LocalPackage(id=info['_id'], path=path, version=info['version'])
            return result

    @staticmethod
    def all():
        """
        List all packages installed at :code:`g['path']['packages']`.
        """
        prefix = g['path']['packages']

        res = os.listdir(prefix)
        res = filter(lambda x: os.path.isdir(os.path.join(prefix, x)), res)
        res = map(lambda x: LocalPackage.by_name(x), res)
        res = filter(lambda x: x, res)
        return res

    def __repr__(self):
        return '<LocalPackage id=%r path=%r version=%r>' % \
               (self.id, self.path, self.version)


class InstallablePackage(Package):
    def __init__(self, id, name, version, repo):
        super(InstallablePackage, self).__init__(id, version)
        self.name = name
        self.repo = repo

    def install(self):
        """
        Just calls :code:`InstallablePackage.install_from_repo(self.repo, self.id)`.
        """
        InstallablePackage.install_from_repo(self.repo, self.id)

    @staticmethod
    def install_from_repo(repo, spec):
        """
        This method downloads a package satisfying spec.

        .. note ::
            The function waits until all of dependencies are installed.
            Run it as separate thread if possible.
        """
        url = repo + '/download?spec=' + urllib2.quote(spec)
        logger.info('Downloading %s...' % spec)
        data = download(url).read()
        io = StringIO(data)

        logger.info('Validating %s...' % spec)
        info = None

        with zipfile.ZipFile(io, 'r') as f:
            with f.open('info.json') as j:
                info = json.load(j)

            install_path = os.path.join(
                g['path']['packages'],
                info["_id"]
            )

            f.extractall(install_path)

            logger.info('Extracting into %r...' % install_path)
            assert os.path.isfile(os.path.join(install_path, 'info.json'))

        removed = os.path.join(install_path, '.removed')
        if os.path.isfile(removed):
            os.unlink(removed)

        # Initiate LocalPackage object
        pkg = LocalPackage(info['_id'], install_path, info['version'])

        # First, install dependencies. This is blocking job!
        # TODO: add version check, is this only for same repo?
        for dep_name, dep_spec in info.get('dependencies', {}).items():
            InstallablePackage.install_from_repo(repo, dep_name)

        pkg.install()
        pkg.load()

        return pkg

    def __repr__(self):
        return '<InstallablePackage id=%r version=%r>' % \
               (self.id, self.version)
