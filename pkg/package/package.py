import os
import sys
import json
import glob
import zipfile
import urllib2
import ida_loader
from StringIO import StringIO

from ..config import g
from ..downloader import download
from ..logger import logger
from ..env import ea as current_ea, os as current_os, version as current_ver
from ..util import putenv, execute_in_main_thread

from . import internal_api

ALL_EA = (32, 64)


def get_native_suffix():
    if current_os == 'win':
        suffix = '.dll'
    elif current_os == 'linux':
        suffix = '.so'
    elif current_os == 'mac':
        suffix = '.dylib'
    return suffix


def uniq(items):
    seen = set()
    res = [(item, seen.add(item))[0] for item in items if item not in seen]
    return res


def _idausr_add_unix(orig, new):
    if orig == None:
        orig = os.path.join(os.getenv('HOME'), '.idapro')
    return ':'.join(uniq(orig.split(':') + [new]))


def _idausr_add_win(orig, new):
    if orig == None:
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
    def __init__(self, name, path, version):
        self.name = name
        self.path = path
        self.version = version

    def install(self):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError

    def fetch(self, url):
        raise NotImplementedError

    def __repr__(self):
        return '<%s name=%r path=%r version=%r>' % \
            (self.__class__.__name__, self.name, self.path, self.version)


# TODO: use some of check_* for matching dependency version
def check_version(cur_version_str, expr):
    pass


def check_os(os_str, expr):
    pass


def select_entry(entry):
    assert isinstance(entry, list), repr(entry)

    for x in entry:
        matches = {
            'ea': current_ea in x.get('ea', ALL_EA),
            'os': check_os(current_os, x.get('os', '*')),
            'version': check_version(current_ver, x.get('ida_version', '*'))
        }

        logger.debug('Matching', matches, 'against', x)
        if all(matches.values()):
            return x['path']


class LocalPackage(Package):
    def __init__(self, name, path, version):
        super(LocalPackage, self).__init__(name, path, version)

        self.path = os.path.normpath(path)

    def remove(self):
        with open(os.path.join(self.path, '.removed'), 'wb'):
            pass

        idausr = os.environ.get('IDAUSR', '')
        if self.path in idausr:
            new = idausr_remove(idausr, self.path)
            putenv('IDAUSR', new)

            internal_api.invalidate_idausr()

    def fetch(self, url):
        return open(url, 'rb').read()

    def install(self):
        orig_cwd = os.getcwd()
        try:
            os.chdir(self.path)
            info = self.info()
            t = info.get('installers', [])
            if not isinstance(t, list):
                raise Exception(
                    '%r Corrupted package: installers key is not list')
            for script in t:
                logger.info('Executing installer path %r...' % script)
                script = os.path.join(self.path, script)
                execfile(script, {
                    __file__: script
                })
            logger.info('Done!')
        except:
            # TODO: implement rollback if needed
            logger.info('Installer failed!')
            self.remove()
            raise
        finally:
            os.chdir(orig_cwd)

    def load(self):
        if self.path in os.environ.get('IDAUSR', ''):
            # Already loaded, just update sys.path for python imports
            sys.path.append(self.path)
            return

        env = str(_idausr_add(os.getenv('IDAUSR'), self.path))

        def handler():
            # Load plugins immediately
            # processors / loaders will be loaded on demand
            def find_loadable_modules(path, callback):
                for suffix in ['.' + x.fileext for x in internal_api.get_extlangs()]:
                    expr = os.path.join(self.path, path, '*' + suffix)
                    for path in glob.glob(expr):
                        callback(str(path))

                for suffix in (get_native_suffix(), ):
                    expr = os.path.join(self.path, path, '*' + suffix)
                    for path in glob.glob(expr):
                        is64 = path[:-len(suffix)][-2:] == '64'

                        if is64 == (current_ea == 64):
                            callback(str(path))

            # Immediately load compatible plugins
            find_loadable_modules('plugins', ida_loader.load_plugin)

            # Find loadable processor modules, and if exists, invalidate cached process list (proccache).
            invalidates = []
            find_loadable_modules('procs', invalidates.append)

            if invalidates:
                internal_api.invalidate_proccache()

            # Update IDAUSR variable
            internal_api.invalidate_idausr()
            putenv('IDAUSR', env)

            sys.path.append(self.path)

        execute_in_main_thread(handler)

    def info(self):
        with open(os.path.join(self.path, 'info.json'), 'rb') as f:
            return json.load(f)

    @staticmethod
    def by_name(name, prefix=None):
        if prefix is None:
            prefix = g['path']['packages']

        path = os.path.join(prefix, name)

        # filter removed package
        removed = os.path.join(path, '.removed')
        if os.path.isfile(removed):
            return None

        info_json = os.path.join(path, 'info.json')
        if not os.path.isfile(info_json):
            logger.debug('Warning: info.json is not found at %r' % path)
            return None

        with open(info_json, 'rb') as f:
            info = json.load(f)
            result = LocalPackage(name=name if 'title' not in info or not info['title'].strip() else info['title'],
                                  path=path, version=info['version'])
            return result

    @staticmethod
    def all():
        prefix = g['path']['packages']

        res = os.listdir(prefix)
        res = filter(lambda x: os.path.isdir(os.path.join(prefix, x)), res)
        res = map(lambda x: LocalPackage.by_name(x), res)
        res = filter(lambda x: x, res)
        return res


class InstallablePackage(Package):
    def __init__(self, name, path, version, repo):
        super(InstallablePackage, self).__init__(name, path, version)
        self.repo = repo

    def install(self):
        InstallablePackage.install_from_repo(self.repo, self.path)

    def remove(self):
        raise NotImplementedError

    @staticmethod
    def install_from_repo(repo, spec):
        """
        This method downloads a package satisfying spec.
        The function waits until it downloads and installs all of plugins.
        So I recommend you to run it as separate thread if possible.
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
                name = info['_id']

            install_path = os.path.join(
                g['path']['packages'],
                name
            )

            f.extractall(install_path)

            logger.info('Extracting into %r...' % install_path)
            assert os.path.isfile(os.path.join(install_path, 'info.json'))

        removed = os.path.join(install_path, '.removed')
        if os.path.isfile(removed):
            os.unlink(removed)

        # Initiate LocalPackage object
        pkg = LocalPackage(name, install_path, info['version'])

        # First, install dependencies. This is blocking job!
        # TODO: add version check, is this only for same repo?
        for dep_name, dep_spec in info.get('dependencies', {}).items():
            InstallablePackage.install_from_repo(repo, dep_name)

        pkg.install()
        pkg.load()

        return pkg


if __name__ == '__main__':
    # TODO: add tests that uses select_entry
    pass
