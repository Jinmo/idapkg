import lief
import capstone


def find_idausr_offset(ida_path):
    ida = lief.parse(ida_path)

    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    csDetails = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    csDetails.detail = True

    imagebase = ida.optional_header.imagebase

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
            if visited[offset]:
                break

            loop = False
            for insn in (cs.disasm(code[offset:offset + 15], addr + offset)):
                if visited[offset]:
                    break
                visited[offset] = True
                if insn.bytes[0] == 0x48 and insn.mnemonic == 'lea':
                    details = next(csDetails.disasm(str(bytearray(insn.bytes)), insn.address))
                    ops = details.operands
                    if ops[1].mem.base == capstone.x86_const.X86_REG_RIP:
                        if target(details):
                            print 'Found:',
                            print hex(details.address),
                            print details.mnemonic, details.op_str
                            return details
                offset = insn.address + insn.size - addr
                loop = True

            if not loop:
                visited[offset] = True
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

    func = like_yara('\x84\xc0', lambda insn: insn.address +
                                              insn.size + insn.operands[1].mem.disp == string)[1]
    ret = like_yara('\xc3', lambda insn: insn.operands[0].reg ==
                                         capstone.x86_const.X86_REG_RAX, func, func + 0x10000)[0]

    # lea rax, [rip + offset]
    offset = ret.address + ret.size + ret.operands[1].mem.disp
    offset -= imagebase
    print 'offset:', hex(offset)
    return offset
