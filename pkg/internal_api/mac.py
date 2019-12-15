from __future__ import print_function

from .decoder import decode_lea, RDI
from .kaitai.mach_o import MachO


def find_idausr_offset(ida_path):
    ida = MachO.from_file(ida_path)
    string = None

    segments = (cmd.body for cmd in ida.load_commands if cmd.type == cmd.type.segment_64)
    sections = (section for segment in segments for section in segment.sections)

    for sect in sections:
        if sect.sect_name.lower() == '__text':
            text = sect
            code = text.data

        value = sect.data.find(b'IDAUSR')
        if value != -1:
            string = sect.addr + value

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
                res = search(code, text.addr, cur - i, i, target)
                if res:
                    return res, cur - i
            cur = code.find(delim, cur + 1)

    func = like_yara(code, b'\x48\x8d\x3d', lambda insn: insn.target == string)
    ret = like_yara(code, b'\xe8', lambda insn: insn.reg == RDI and insn.address != func[0].address, func[1],
                    func[1] + 0x10000)[0]

    offset = ret.target
    print('offset:', hex(offset))
    return offset
