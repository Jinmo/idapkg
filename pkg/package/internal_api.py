import ctypes
import os
from ..env import ea as current_ea, os as current_os, version as current_ver, version_info


def ida_lib():
    ea_name = 'ida64' if current_ea == 64 else 'ida'
    if current_os == 'win':
        functype = ctypes.WINFUNCTYPE
        lib = getattr(ctypes.windll, ea_name)
    else:
        functype = ctypes.CFUNCTYPE
        lib = getattr(ctypes.cdll, 'lib' + ea_name)
    return functype, lib


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
        k = ctypes.windll.kernel32
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


__possible_to_invalidate = True


def invalidate_idadir():
    global __possible_to_invalidate

    if not __possible_to_invalidate:
        return False

    IDADIR_OFFSETS = {
        (7, 0, 171130): {"win": [0x5e9dc8, 0x5f20d8]}
    }

    # Now this is tricky part
    _, lib = ida_lib()
    base = lib._handle

    try:
        offset = IDADIR_OFFSETS[version_info][current_os][current_ea == 64]
    except KeyError:
        logging.info(
            "Loading processors/loaders are not supported in this platform.")
        __possible_to_invalidate = False
        return False

    # qvector<qstring> *ptr(getenv("IDAUSR").split(";" or ":"))
    # ptr.len = ptr.cap = 0
    ptr = ctypes.cast(base + offset, ctypes.POINTER(ctypes.c_size_t))
    # Memory leak here, but not too much.
    ptr[1] = ptr[2] = 0
    return True
