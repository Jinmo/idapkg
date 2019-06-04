import struct

# Register constants
RAX = 0
RDI = 7


class Instruction(object):
    def __init__(self, reg, target, address):
        self.reg = reg
        self.target = target
        self.address = address

    def __str__(self):
        return 'lea %s, 0x%x' % (self.reg, self.target)


def decode_lea(address, bytes):
    rm = ord(bytes[2])
    # PC/RIP-relative addressing
    if rm & 0x7 == 0b101 and (rm >> 6) == 0:
        return Instruction(
            reg=(rm >> 3) & 7,
            target=address + 7 + struct.unpack("<L", bytes[3:7])[0],
            address=address
        )
