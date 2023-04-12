from common import *
from math import sqrt
import ctypes
libc = ctypes.CDLL('libm.so.6')


class RoundMode:
    Nearest = 0x0000
    Down = 0x0400
    Up = 0x0800
    Zero = 0x0c00


class Instruction:
    registerUsage = [0] * RegistersCount


    def __init__(self):
        libc.fesetround(RoundMode.Nearest)


    def IADD_RS(self, dst, src, shift, imm):
        val = (self.reg.r[src] << shift) + imm
        self.reg.r[dst] += val
        self.reg.r[dst] %= EightByte


    def IADD_M(self, dst, src, imm, memMask, isImm):
        if not isImm:
            src = self.reg.r[src]
        addr = getScratchpadAddress(src, imm, memMask)
        self.reg.r[dst] += self.scratchpadRead(addr, offset=8)
        self.reg.r[dst] %= EightByte


    def ISUB_R(self, dst, src, isImm):
        if not isImm:
            src = self.reg.r[src]
        self.reg.r[dst] -= src
        self.reg.r[dst] %= EightByte


    def ISUB_M(self, dst, src, imm, memMask, isImm):
        if not isImm:
            src = self.reg.r[src]
        addr = getScratchpadAddress(src, imm, memMask)
        self.reg.r[dst] -= self.scratchpadRead(addr, offset=8)
        self.reg.r[dst] %= EightByte


    def IMUL_R(self, dst, src, isImm):
        if not isImm:
            src = self.reg.r[src]
        self.reg.r[dst] *= src
        self.reg.r[dst] %= EightByte


    def IMUL_M(self, dst, src, imm, memMask, isImm):
        if not isImm:
            src = self.reg.r[src]
        addr = getScratchpadAddress(src, imm, memMask)
        self.reg.r[dst] *= self.scratchpadRead(addr, offset=8)
        self.reg.r[dst] %= EightByte


    def IMULH_R(self, dst, src):
        self.reg.r[dst] = mulh(self.reg.r[dst], self.reg.r[src])


    def IMULH_M(self, dst, src, imm, memMask, isImm):
        if not isImm:
            src = self.reg.r[src]
        addr = getScratchpadAddress(src, imm, memMask)
        self.reg.r[dst] = mulh(self.reg.r[dst], self.scratchpadRead(addr, offset=8))


    def ISMULH_R(self, dst, src):
        self.reg.r[dst] = smulh(self.reg.r[dst], self.reg.r[src])


    def ISMULH_M(self, dst, src, imm, memMask, isImm):
        if not isImm:
            src = self.reg.r[src]
        addr = getScratchpadAddress(src, imm, memMask)
        self.reg.r[dst] = smulh(self.reg.r[dst], self.scratchpadRead(addr, offset=8))


    def INEG_R(self, dst):
        self.reg.r[dst] = (~self.reg.r[dst] + 1) % EightByte


    def IXOR_R(self, dst, src, isImm):
        if not isImm:
            src = self.reg.r[src]
        self.reg.r[dst] ^= src


    def IXOR_M(self, dst, src, imm, memMask, isImm):
        if not isImm:
            src = self.reg.r[src]
        addr = getScratchpadAddress(src, imm, memMask)
        self.reg.r[dst] ^= self.scratchpadRead(addr, offset=8)


    def IROR_R(self, dst, src, isImm):
        self.reg.r[dst] = rotr(
            self.reg.r[dst],
            (src if isImm else self.reg.r[src]) & 63
        ) % EightByte


    def IROL_R(self, dst, src, isImm):
        self.reg.r[dst] = rotl(
            self.reg.r[dst],
            (src if isImm else self.reg.r[src]) & 63
        ) % EightByte


    def ISWAP_R(self, dst, src):
        self.reg.r[dst], self.reg.r[src] = self.reg.r[src], self.reg.r[dst]


    def FSWAP_R(self, dst, _reg):
        if _reg == 'f':
            reg = self.reg.f
        if _reg == 'e':
            reg = self.reg.e

        reg[dst]['lo'], reg[dst]['hi'] = reg[dst]['hi'], reg[dst]['lo']


    def FADD_R(self, dst, src):
        self.reg.f[dst]['lo'] += self.reg.a[src]['lo']
        self.reg.f[dst]['hi'] += self.reg.a[src]['hi']


    def FADD_M(self, dst, src, imm, memMask):
        addr = getScratchpadAddress(self.reg.r[src], imm, memMask)
        p = list(unpack("ii", pack("II", self.scratchpadRead(addr, offset=4), self.scratchpadRead(addr+4, offset=4))))
        self.reg.f[dst]['lo'] += p[0]
        self.reg.f[dst]['hi'] += p[1]


    def FSUB_R(self, dst, src):
        self.reg.f[dst]['lo'] -= self.reg.a[src]['lo']
        self.reg.f[dst]['hi'] -= self.reg.a[src]['hi']


    def FSUB_M(self, dst, src, imm, memMask):
        addr = getScratchpadAddress(self.reg.r[src], imm, memMask)
        p = list(unpack("ii", pack("II", self.scratchpadRead(addr, offset=4), self.scratchpadRead(addr+4, offset=4))))
        self.reg.f[dst]['lo'] -= p[0]
        self.reg.f[dst]['hi'] -= p[1]


    def FSCAL_R(self, dst):
        vec_scale(self.reg.f[dst])


    def FMUL_R(self, dst, src):
        self.reg.e[dst]['lo'] *= self.reg.a[src]['lo']
        self.reg.e[dst]['hi'] *= self.reg.a[src]['hi']


    def FDIV_M(self, dst, src, imm, memMask):
        addr = getScratchpadAddress(self.reg.r[src], imm, memMask)
        p = list(unpack("ii", pack("II", self.scratchpadRead(addr, offset=4), self.scratchpadRead(addr+4, offset=4))))
        p = maskRegisterExponentMantissa(self.eMask, p)
        self.reg.e[dst]['lo'] /= p[0]
        self.reg.e[dst]['hi'] /= p[1]


    def FSQRT_R(self, dst):
        self.reg.e[dst]['lo'] = sqrt(self.reg.e[dst]['lo'])
        self.reg.e[dst]['hi'] = sqrt(self.reg.e[dst]['hi'])


    def CBRANCH(self, dst, imm, memMask, target):
        self.reg.r[dst] += imm
        if (self.reg.r[dst] & memMask) == 0:
            self.pc = target


    def CFROUND(self, src, imm):
        mod = rotr(self.reg.r[src], imm) % 4
        if mod == 0:
            libc.fesetround(RoundMode.Nearest)
        if mod == 1:
            libc.fesetround(RoundMode.Down)
        if mod == 2:
            libc.fesetround(RoundMode.Up)
        if mod == 3:
            libc.fesetround(RoundMode.Zero)


    def ISTORE(self, dst, src, imm, memMask):
        dst = self.reg.r[dst]
        addr = getScratchpadAddress(dst, imm, memMask)
        self.scratchpad[addr: addr+8] = self.reg.r[src].to_bytes(8, 'little')


    def NOP():
        return