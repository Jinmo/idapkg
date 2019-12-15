from __future__ import print_function

from .decoder import decode_lea, RAX
from .kaitai.microsoft_pe import MicrosoftPe


def find_idausr_offset(ida_path):
    ida = MicrosoftPe.from_file(ida_path)
    string = None

    imagebase = ida.pe.optional_hdr.windows.image_base_64

    for sect in ida.pe.sections:
        if sect.name == '.text':
            text = sect
            code = text.body

        value = sect.body.find(b'IDAUSR')
        if value != -1:
            string = sect.virtual_address + imagebase + value

    def search(code, addr, offset, size, target):
        end = offset + size
        if visited[offset]:
            return
        while offset <= end:
            offset = code.find(b'\x48\x8d', offset)

            if visited[offset]:
                break

            visited[offset] = True
            insn = decode_lea(addr + offset, memoryview(code)[offset:offset + 15])
            if insn and target(insn):
                print('Found:', hex(insn.target), insn)
                return insn
            offset += 1

    def like_yara(code, delim, target, start=0, end=None):
        global visited
        visited = [None] * len(code)
        cur = code.find(delim, start)
        if end is None:
            end = len(code)
        while cur != -1 and cur < end:
            for i in range(30):
                res = search(code, text.virtual_address +
                             imagebase, cur - i, i, target)
                if res:
                    return res, cur - i
            cur = code.find(delim, cur + 1)

    func = like_yara(code, b'\x84\xc0', lambda insn: insn.target == string)[1]
    ret = like_yara(code, b'\xc3', lambda insn: insn.reg == RAX, func, func + 0x10000)[0]

    offset = ret.target - imagebase
    print('offset:', hex(offset))
    return offset
