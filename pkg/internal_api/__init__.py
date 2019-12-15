# pylint: disable=invalid-name,protected-access
import collections
import ctypes
import os
import traceback

import idaapi

from ..config import g, _save_config
from ..env import ea as current_ea, os as current_os, version_info
from ..logger import getLogger

IDADIR = idaapi.idadir('')
log = getLogger(__name__)


def _os_error():
    return Exception("unknown os: %r" % current_os)


def _ida_lib_path(ea):
    ea_name = 'ida64' if ea == 64 else 'ida'
    if current_os == 'win':
        path = os.path.join(IDADIR, ea_name + ".dll")
    elif current_os == 'mac':
        path = os.path.join(IDADIR, "lib" + ea_name + ".dylib")
    elif current_os == 'linux':
        path = os.path.join(IDADIR, "lib" + ea_name + ".so")
    else:
        raise _os_error()
    return os.path.normpath(path)


def _ida_lib():
    ea_name = 'ida64' if current_ea == 64 else 'ida'
    if current_os == 'win':
        functype = ctypes.WINFUNCTYPE
        lib = getattr(ctypes.windll, ea_name)
    elif current_os == 'mac':
        functype = ctypes.CFUNCTYPE
        lib = ctypes.CDLL(_ida_lib_path(current_ea))
    elif current_os == 'linux':
        functype = ctypes.CFUNCTYPE
        lib = getattr(ctypes.cdll, 'lib' + ea_name)
    else:
        raise _os_error()
    return functype, lib


def _get_lib_base(handle):
    if current_os == 'win':
        return handle._handle
    elif current_os == 'mac':
        class Dl_info(ctypes.Structure):
            _fields_ = [
                ('dli_fname', ctypes.c_char_p),
                ('dli_fbase', ctypes.c_void_p),
                ('dli_sname', ctypes.c_char_p),
                ('dli_saddr', ctypes.c_void_p)
            ]

        libc = ctypes.CDLL('/usr/lib/libSystem.B.dylib')
        info = Dl_info()
        if not libc.dladdr(ctypes.cast(handle.find_plugin, ctypes.c_void_p), ctypes.byref(info)):
            return None
        return info.dli_fbase


def get_extlangs():
    """
    Wrapper around get_extlangs() in C++ API.
    """
    functype, lib = _ida_lib()

    class _extlang_t(ctypes.Structure):
        _fields_ = [
            ('size', ctypes.c_size_t),
            ('flags', ctypes.c_uint),
            ('refcnt', ctypes.c_int),
            ('name', ctypes.c_char_p),
            ('fileext', ctypes.c_char_p),
            ('highlighter', ctypes.c_void_p)
        ]

    functype = functype(ctypes.c_size_t, (ctypes.c_void_p),
                        ctypes.POINTER(_extlang_t))

    extlang_t = collections.namedtuple(
        'extlang_t', 'size flags refcnt name fileext highlighter')

    class _extlang_visitor_t(ctypes.Structure):
        _fields_ = [
            ('vtable', ctypes.POINTER(functype))
        ]

    res = []

    @functype
    def _visitor_func(_this, extlang):
        extlang = extlang[0]
        new_extlang = extlang_t(
            extlang.size,
            extlang.flags,
            extlang.refcnt,
            extlang.name.decode('utf8'),
            extlang.fileext.decode('utf8'),
            None  # not supported
        )
        res.append(new_extlang)
        return 0

    vtable = (functype * 1)(_visitor_func)
    visitor = _extlang_visitor_t(vtable)

    lib.for_all_extlangs(ctypes.pointer(visitor), False)
    return res


def invalidate_proccache():
    _, lib = _ida_lib()
    # This returns proccache vector
    func = lib.get_idp_descs
    func.restype = ctypes.POINTER(ctypes.c_size_t)
    ptr = func()
    # Memory leak here, but not too much.
    ptr[1] = ptr[2] = 0


__possible_to_invalidate = None


def invalidate_idausr():
    global __possible_to_invalidate

    if __possible_to_invalidate is False:
        return False

    cfg = g['idausr_native_bases'][current_os][version_info.str()]
    already_found = cfg[current_ea == 64]

    _, lib = _ida_lib()
    base = _get_lib_base(lib)

    if already_found is False:
        __possible_to_invalidate = False
        return False

    if already_found:
        offset = already_found
    else:
        r"""
        Now this is tricky part...
        Analyzing the IDA executable:
            1. find "IDAUSR\0" string
            2. find code xref
            3. find return value
        """
        offset = None
        path = _ida_lib_path(current_ea)

        try:
            log.info('Loading offsets from IDA binary... (takes a while)')
            if current_os == 'win':
                from .win import find_idausr_offset
                offset = find_idausr_offset(path)
            elif current_os == 'mac':
                from .mac import find_idausr_offset
                offset = find_idausr_offset(path)
            else:
                pass
        except:
            traceback.print_exc()

        if offset is None:
            log.info(
                "Loading processors/loaders requires restarting in this platform.")
            cfg[current_ea == 64] = False
            __possible_to_invalidate = False
            return False
        else:
            log.info("Success!")
            __possible_to_invalidate = True
            cfg[current_ea == 64] = offset
            _save_config(g)

    # qvector<qstring> *ptr(getenv("IDAUSR").split(";" or ":"))
    # ptr.len = ptr.cap = 0
    ptr = ctypes.cast(base + offset, ctypes.POINTER(ctypes.c_size_t))
    # Memory leak here, but not too much.
    # TODO: we can use qvector.clear() here?
    ptr[1] = ptr[2] = 0
    return True
