import lief
from .decoder import decode_lea, RAX


def find_idausr_offset(ida_path):
    ida = lief.parse(ida_path)

    imagebase = ida.optional_header.imagebase
    string = None

    for sect in ida.sections:
        if sect.name == '.text':
            text = sect
            code = str(bytearray(text.content))

        value = sect.search('IDAUSR')
        if value != 0xffffffffffffffff:
            string = sect.virtual_address + imagebase + value

    def search(code, addr, offset, size, target):
        end = offset + size
        if visited[offset]:
            return
        while offset <= end:
            offset = code.find('\x48\x8d', offset)

            if visited[offset]:
                break

            visited[offset] = True
            insn = decode_lea(addr + offset, memoryview(code)[offset:offset+15])
            if insn and target(insn):
                print 'Found:',
                print hex(insn.target),
                print insn
                return insn
            offset += 1

    def like_yara(delim, target, start=0, end=None):
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

    func = like_yara('\x84\xc0', lambda insn: insn.target == string)[1]
    ret = like_yara('\xc3', lambda insn: insn.reg == RAX, func, func + 0x10000)[0]

    offset = ret.target - imagebase
    print 'offset:', hex(offset)
    return offset
