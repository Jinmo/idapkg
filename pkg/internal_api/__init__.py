import ctypes
import os
import traceback
import idaapi

from ..env import ea as current_ea, os as current_os, version as current_ver, version_info
from ..logger import logger
from ..config import g, save_config
from ..process import system

IDADIR = os.path.dirname(os.path.dirname(idaapi.__file__))


def ida_lib_path(ea):
    ea_name = 'ida64' if ea == 64 else 'ida'
    if current_os == 'win':
        path = os.path.join(IDADIR, ea_name + ".dll")
    if current_os == 'mac':
        path = os.path.join(IDADIR, "lib" + ea_name + ".dylib")
    if current_os == 'linux':
        path = os.path.join(IDADIR, "lib" + ea_name + ".so")
    return os.path.normpath(path)


def ida_lib():
    ea_name = 'ida64' if current_ea == 64 else 'ida'
    if current_os == 'win':
        functype = ctypes.WINFUNCTYPE
        lib = getattr(ctypes.windll, ea_name)
    elif current_os == 'mac':
        functype = ctypes.CFUNCTYPE
        lib = ctypes.CDLL(ida_lib_path(current_ea))
    else:
        functype = ctypes.CFUNCTYPE
        lib = getattr(ctypes.cdll, 'lib' + ea_name)
    return functype, lib


def get_lib_base(handle):
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
    functype, lib = ida_lib()

    class extlang_t(ctypes.Structure):
        _fields_ = [
            ('size', ctypes.c_size_t),
            ('flags', ctypes.c_uint),
            ('refcnt', ctypes.c_int),
            ('name', ctypes.c_char_p),
            ('fileext', ctypes.c_char_p),
            ('highlighter', ctypes.c_void_p)
        ]

    functype = functype(ctypes.c_size_t, (ctypes.c_void_p),
                        ctypes.POINTER(extlang_t))

    class extlang_visitor_t(ctypes.Structure):
        _fields_ = [
            ('vtable', ctypes.POINTER(functype))
        ]

    res = []

    @functype
    def visitor(self, extlang):
        extlang = extlang[0]
        new_extlang = extlang_t(
            extlang.size,
            extlang.flags,
            extlang.refcnt,
            str(extlang.name),
            str(extlang.fileext),
            None  # not supported
        )
        res.append(new_extlang)
        return 0

    vtable = (functype * 1)()
    vtable[0] = visitor

    visitor = extlang_visitor_t()
    visitor.vtable = vtable

    lib.for_all_extlangs(ctypes.pointer(visitor), False)
    return res


def invalidate_proccache():
    _, lib = ida_lib()
    # This returns proccache vector
    func = lib.get_idp_descs
    func.restype = ctypes.POINTER(ctypes.c_size_t)
    ptr = func()
    # Memory leak here, but not too much.
    ptr[1] = ptr[2] = 0


__possible_to_invalidate = None


def invalidate_idausr():
    global __possible_to_invalidate

    if __possible_to_invalidate == False:
        return False

    already_found = g['idausr_native_bases'][current_ea == 64]

    _, lib = ida_lib()
    base = get_lib_base(lib)

    if already_found:
        offset = already_found
    else:
        # Now this is tricky part
        # First, try to analyze IDA executable
        # 1. find "IDAUSR\0" string / 2. find code xref / 3. find return value
        offset = None
        path = ida_lib_path(current_ea)

        try:
            import lief
            import capstone
        except ImportError:
            logger.info('Installing dependencies for analyzing IDAUSR offsets...')
            system('pip install lief capstone')

        try:
            logger.info('Loading offsets from IDA binary... (takes a while)')
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
            pass

        if offset is None:
            logger.info(
                "Loading processors/loaders are not supported in this platform.")
            __possible_to_invalidate = False
            return False
        else:
            logger.info("Success!")
            __possible_to_invalidate = True
            g['idausr_native_bases'][current_ea == 64] = offset
            save_config(g)

    # qvector<qstring> *ptr(getenv("IDAUSR").split(";" or ":"))
    # ptr.len = ptr.cap = 0
    ptr = ctypes.cast(base + offset, ctypes.POINTER(ctypes.c_size_t))
    # Memory leak here, but not too much.
    ptr[1] = ptr[2] = 0
    return True
