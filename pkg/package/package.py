import json
import os
import re
import sys
import glob
import ctypes
import zipfile
import urllib2
import PyQt5.QtCore
import PyQt5.QtWidgets
from StringIO import StringIO

from ..config import g
from ..downloader import download
from ..logger import logger

ALL_EA = (32, 64)
OS_MAP = {'win32': 'win', 'darwin': 'mac', 'linux2': 'linux'}

current_ea = -1
current_os = 'unknown'
current_ver = '0.0'


class Worker(PyQt5.QtCore.QObject):
    work = PyQt5.QtCore.pyqtSignal()

def execute_in_main_thread(func):
    signal_source = Worker()
    signal_source.moveToThread(PyQt5.QtWidgets.qApp.thread())
    signal_source.work.connect(func)
    signal_source.work.emit()


def get_extlangs():
    ea_name = 'ida64' if current_ea == 64 else 'ida'
    if current_os == 'win':
        functype = ctypes.WINFUNCTYPE
        lib = getattr(ctypes.windll, ea_name)
    else:
        functype = ctypes.CFUNCTYPE
        lib = getattr(ctypes.cdll, 'lib' + ea_name)

    class extlang_t(ctypes.Structure):
        _fields_ = [
        ('size', ctypes.c_size_t),
        ('flags', ctypes.c_uint),
        ('refcnt', ctypes.c_int),
        ('name', ctypes.c_char_p),
        ('fileext', ctypes.c_char_p),
        ('highlighter', ctypes.c_void_p)
        ]

    functype = functype(ctypes.c_size_t, (ctypes.c_void_p), ctypes.POINTER(extlang_t))

    class extlang_visitor_t(ctypes.Structure):
        _fields_ = [
            ('vtable', ctypes.POINTER(functype))
        ]

    res = []

    @functype
    def visitor(self, extlang):
        extlang = extlang[0]
        k=ctypes.windll.kernel32
        new_extlang = extlang_t(
            extlang.size,
            extlang.flags,
            extlang.refcnt,
            str(extlang.name),
            str(extlang.fileext),
            None # not supported
            )
        res.append(new_extlang)
        return 0
    
    vtable = (functype * 1)()
    vtable[0] = visitor

    visitor = extlang_visitor_t()
    visitor.vtable = vtable

    lib.for_all_extlangs(ctypes.pointer(visitor), False)
    return res

def get_native_suffix():
    if current_os == 'win':
        suffix = '.dll'
    elif current_os == 'linux':
        suffix = '.so'
    elif current_os == 'mac':
        suffix = '.dylib'
    return suffix

def idausr_join_unix(orig, new):
    if orig == None:
        orig = os.path.join(os.getenv('HOME'), '.idapro')
    return ':'.join([orig, new])

def idausr_join_win(orig, new):
    if orig == None:
        orig = os.path.join(os.getenv('APPDATA'), 'Hex-Rays', 'IDA Pro')
    return ';'.join([orig, new])

def idausr_join(orig, new):
    if current_os == 'win':
        return idausr_join_win(orig, new)
    else:
        return idausr_join_unix(orig, new)

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
        return '<%s name=%r path=%r version=%r>' % (self.__class__.__name__, self.name, self.path, self.version)


def check_version(cur_version_str, expr):
    spec = Spec(expr)
    return spec.match(Version.coerce(cur_version_str))


def check_os(os_str, expr):
    if isinstance(expr, basestring):
        expr = [expr]

    if len(expr) == 1 and '*' in expr:
        return True
    else:
        assert all(item in ('win', 'mac', 'linux', "!win", "!mac", "!linux")
                   for item in expr), '"os" specifiers must be one of os or !os; os: %r' % OS_MAP.values()
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

    def install(self):
        raise NotImplementedError

    def remove(self):
        with open(os.path.join(self.path, '.removed'), 'wb'):
            pass

    def fetch(self, url):
        return open(url, 'rb').read()

    def load(self):
        import ida_loader
        env = idausr_join(os.getenv('IDAUSR'), self.path)
        os.putenv('IDAUSR', env)
        os.environ['IDAUSR'] = env

        def handler():
            # Load plugins immediately (processors / loaders will be loaded on demand)
            for suffix in ['.' + x.fileext for x in get_extlangs()]:
                for path in glob.glob(os.path.join(self.path, 'plugins', '*' + suffix)):
                    ida_loader.load_plugin(str(path))

            for suffix in (get_native_suffix(), ):
                for path in glob.glob(os.path.join(self.path, 'plugins', '*' + suffix)):
                    if path[:-len(suffix)][-2:] == '64':
                        is64 = True
                    else:
                        is64 = False
                    if is64 == (current_ea == 64):
                        print path
                        ida_loader.load_plugin(str(path))

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
        data = download(self.base + '/download?spec=' + urllib2.quote(self.path)).read()
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
        pkg.load()

        return pkg


def __load_version_from_ida():
    global current_ea, current_os, current_ver
    if idc.__EA64__:
        current_ea = 64
    else:
        current_ea = 32

    current_os = OS_MAP[sys.platform]
    current_ver = idaapi.get_kernel_version()

    current_ver = re.sub(r'^(\d.)0(\d.*)', r'\1\2', current_ver)


try:
    import idc
    import idaapi

    __load_version_from_ida()

except ImportError:
    assert __name__ == '__main__'

if __name__ == '__main__':
    def set_version(os, ver, ea):
        global current_os, current_ver, current_ea
        current_os, current_ver, current_ea = os, ver, ea


    set_version('win', '7.0.0', 32)

    assert select_entry([{
        'ea': [32],
        'path': 'win32',
        'version': '>= 7.0, <=7.2',
    }]) == 'win32'
