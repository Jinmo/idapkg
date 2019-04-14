import json
import os
import glob
import zipfile
import urllib2
import PyQt5.QtCore
import PyQt5.QtWidgets
import ida_loader
from StringIO import StringIO

from ..config import g
from ..downloader import download
from ..logger import logger
from ..env import ea as current_ea, os as current_os, version as current_ver
from ..util import putenv

from .internal_api import get_extlangs, invalidate_proccache, invalidate_idadir

ALL_EA = (32, 64)
supported_os = ('win', 'mac', 'linux', "!win", "!mac", "!linux")


class Worker(PyQt5.QtCore.QObject):
    work = PyQt5.QtCore.pyqtSignal()


def execute_in_main_thread(func):
    signal_source = Worker()
    signal_source.moveToThread(PyQt5.QtWidgets.qApp.thread())
    signal_source.work.connect(func)
    signal_source.work.emit()


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

def idausr_join_unix(orig, new):
    if orig == None:
        orig = os.path.join(os.getenv('HOME'), '.idapro')
    return ':'.join(uniq(orig.split(':') + [new]))


def idausr_join_win(orig, new):
    if orig == None:
        orig = os.path.join(os.getenv('APPDATA'), 'Hex-Rays', 'IDA Pro')
    return ';'.join(uniq(orig.split(';') + [new]))


def idausr_join(orig, new):
    if current_os == 'win':
        return idausr_join_win(orig, new)
    else:
        return idausr_join_unix(orig, new)


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


def check_version(cur_version_str, expr):
    spec = Spec(expr)
    return spec.match(Version.coerce(cur_version_str))


def check_os(os_str, expr):
    if isinstance(expr, basestring):
        expr = [expr]

    if len(expr) == 1 and '*' in expr:
        return True
    else:
        assert all(item in supported_os for item in expr), \
            '"os" specifiers must be one of os or !os; os: %r' % OS_MAP.values()
        assert len(set(expr)) == len(expr), '"os" specifiers must be unique'

        positive = []
        negative = []
        for item in expr:
            if item.startswith('!'):
                negative.append(item[1:])
            else:
                positive.append(item)

        result = os_str in positive and os_str not in negative
        return result


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
            # Already loaded
            return

        env = str(idausr_join(os.getenv('IDAUSR'), self.path))

        def handler():
            # Load plugins immediately
            # processors / loaders will be loaded on demand
            def find_loadable_modules(path, callback):
                for suffix in ['.' + x.fileext for x in get_extlangs()]:
                    for path in glob.glob(os.path.join(self.path, path, '*' + suffix)):
                        callback(str(path))

                for suffix in (get_native_suffix(), ):
                    for path in glob.glob(os.path.join(self.path, path, '*' + suffix)):
                        if path[:-len(suffix)][-2:] == '64':
                            is64 = True
                        else:
                            is64 = False
                        if is64 == (current_ea == 64):
                            print path
                            callback(str(path))
            find_loadable_modules('plugins', ida_loader.load_plugin)
            invalidates = []
            find_loadable_modules('procs', invalidates.append)

            if invalidates:
                invalidate_proccache()

            invalidate_idadir()

            putenv('IDAUSR', env)

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
    def __init__(self, name, path, version, base):
        super(InstallablePackage, self).__init__(name, path, version)
        self.base = base

    def install(self):
        logger.info('Downloading...')
        data = download(self.base + '/download?spec=' +
                        urllib2.quote(self.path)).read()
        io = StringIO(data)

        install_path = os.path.join(
            g['path']['packages'],
            self.path
        )

        with zipfile.ZipFile(io, 'r') as f:
            with f.open('info.json') as j:
                info = json.load(j)

            logger.info('Extracting into %r...' % install_path)
            f.extractall(install_path)

        removed = os.path.join(install_path, '.removed')
        if os.path.isfile(removed):
            os.unlink(removed)

        pkg = LocalPackage(str(self.name), install_path, self.version)
        pkg.install()
        pkg.load()

        return pkg

    def remove(self):
        raise NotImplementedError

    @staticmethod
    def install_from_url(url):
        # Just reimplementation
        logger.info('Downloading...')
        data = download(url).read()
        io = StringIO(data)

        logger.info('Validating...')
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

        pkg = LocalPackage(name, install_path, info['version'])
        pkg.install()
        pkg.load()

        return pkg


if __name__ == '__main__':
    assert select_entry([{
        'ea': [32],
        'path': 'win32',
        'version': '>= 7.0, <=7.2',
    }]) == 'win32'
