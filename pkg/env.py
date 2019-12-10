# pylint: disable=invalid-name
"""
:os: operating system. 'win' | 'mac' | 'linux'
:ea: current ea. 32 | 64
:version: Decimal object for IDA Pro's version (ex. :code:`Decimal(6.95)`)
:version_info:
    namedtuple with version details
    (ex. :code:`VersionPair(major=7, minor=0, micro=171130)`)

"""

import collections
import os as _os
import sys
from decimal import Decimal

OS_MAP = {'win32': 'win', 'darwin': 'mac', 'linux2': 'linux'}

idc, idaapi = None, None

# Will be set from IDA Pro
ea = -1
os = 'unknown'
version = Decimal('0.0')


def __load_version_from_ida():
    if idc.__EA64__:
        _ea = 64
    else:
        _ea = 32

    _os = OS_MAP[sys.platform]
    return _ea, _os


class version_info_cls(collections.namedtuple('VersionPair', 'major minor micro')):
    def str(self):
        return '%s.%s.%s' % (self.major, self.minor, self.micro)


version_info = version_info_cls(0, 0, 0)


def __load_ida_native_version():
    sysdir = _os.path.dirname(idaapi.idadir(idaapi.CFG_SUBDIR))
    exe_name = 'ida' if ea == 32 else 'ida64'
    if os == 'win':
        path = _os.path.join(sysdir, exe_name + '.exe')
        with open(path, 'rb') as f:
            data = f.read()
            needle = b'F\0i\0l\0e\0V\0e\0r\0s\0i\0o\0n\0\0\0\0\0'
            offset = data.rfind(needle) + len(needle)
            offset2 = data.find(b'\0\0', offset) + 1
            version_str = data[offset:offset2].decode('utf16')

            version_str = version_str[:version_str.rfind(
                '.')] + version_str[version_str.rfind('.') + 1:]
    elif os == 'mac':
        path = _os.path.join(sysdir, exe_name)
        with open(path, 'rb') as f:
            data = f.read()
            needle = b'<key>CFBundleShortVersionString</key>'
            offset = data.rfind(needle)
            offset = data.find(b'<string>', offset) + 8
            offset2 = data.find(b'</string', offset)
            version_str = data[offset:offset2].decode('utf8')

    result = version_info_cls._make(int(_) for _ in version_str.split('.'))
    return result


try:
    import idc
    import idaapi

    ea, os = __load_version_from_ida()

    version_info = __load_ida_native_version()
    version = Decimal('%d.%d' % (version_info.major, version_info.minor))

except ImportError:
    pass

__all__ = ['os', 'ea', 'version', 'version_info']
