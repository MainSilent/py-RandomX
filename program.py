from instruction import Instruction
from common import *


class OpCode:
    NOP = 0
    IADD_RS = 0x10
    IADD_M = 0x17
    ISUB_R = 0x27
    ISUB_M = 0x2e
    IMUL_R = 0x3e
    IMUL_M = 0x42
    IMULH_R = 0x46
    IMULH_M = 0x47
    ISMULH_R = 0x4b
    ISMULH_M = 0x4c
    IMUL_RCP = 0x54
    INEG_R = 0x56
    IXOR_R = 0x65
    IXOR_M = 0x6a
    IROR_R = 0x72
    IROL_R = 0x74
    ISWAP_R = 0x78
    FSWAP_R = 0x7c
    FADD_R = 0x8c
    FADD_M = 0x91
    FSUB_R = 0xa1
    FSUB_M = 0xa6
    FSCAL_R = 0xac
    FMUL_R = 0xcc
    FDIV_M = 0xd0
    FSQRT_R = 0xd6
    CBRANCH = 0xef
    CFROUND = 0xf0
    ISTORE = 0x100


class Program(Instruction):
    ma = 0
    mx = 0
    eMask = [0, 0]
    datasetOffset = 0
    entropy = [None] * 16
    programBuffer = [None] * RANDOMX_PROGRAM_SIZE
    readReg0, readReg1, readReg2, readReg3 = [0, 0, 0, 0]


    def datasetRead(self, address, r):
        itemNumber = address // CacheLineSize
        rl = self.DATASET[itemNumber].split('|')
        rl = [int(rl[i], 16) for i in range(RegistersCount)]

        for i in range(RegistersCount):
            r[i] ^= rl[i]


    def execute(self):
        self.pc = 0
        while self.pc < RANDOMX_PROGRAM_SIZE:
            self.programBuffer[self.pc]()
            self.pc += 1


    def compileProgram(self):
        for i in range(RANDOMX_PROGRAM_SIZE):
            self.programBuffer[i] = self.compileInstruction(self.program[i*8: (i+1)*8], i)


    def compileInstruction(self, instr, i):
        op = instr[0]
        dst = instr[1]
        src = instr[2]
        mod = instr[3]
        imm = unpack("<i", instr[4: 8])[0]


        if op < OpCode.IADD_RS:
            dst = dst % RegistersCount
            src = src % RegistersCount
            shift = getModShift(mod)
            if dst != RegisterNeedsDisplacement:
                imm = 0
            self.registerUsage[dst] = i

            return lambda: self.IADD_RS(dst, src, shift, imm)


        if op < OpCode.IADD_M:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src != dst:
                if getModMem(mod):
                    memMask = ScratchpadL1Mask
                else:
                    memMask = ScratchpadL2Mask
            else:
                src = 0
                isImm = True
                memMask = ScratchpadL3Mask
            self.registerUsage[dst] = i

            return lambda: self.IADD_M(dst, src, imm, memMask, isImm)


        if op < OpCode.ISUB_R:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src == dst:
                src = imm
                isImm = True
            self.registerUsage[dst] = i

            return lambda: self.ISUB_R(dst, src, isImm)


        if op < OpCode.ISUB_M:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src != dst:
                if getModMem(mod):
                    memMask = ScratchpadL1Mask
                else:
                    memMask = ScratchpadL2Mask
            else:
                src = 0
                isImm = True
                memMask = ScratchpadL3Mask
            self.registerUsage[dst] = i

            return lambda: self.ISUB_M(dst, src, imm, memMask, isImm)


        if op < OpCode.IMUL_R:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src == dst:
                src = imm
                isImm = True
            self.registerUsage[dst] = i

            return lambda: self.IMUL_R(dst, src, isImm)


        if op < OpCode.IMUL_M:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src != dst:
                if getModMem(mod):
                    memMask = ScratchpadL1Mask
                else:
                    memMask = ScratchpadL2Mask
            else:
                src = 0
                isImm = True
                memMask = ScratchpadL3Mask
            self.registerUsage[dst] = i 

            return lambda: self.IMUL_M(dst, src, imm, memMask, isImm)          


        if op < OpCode.IMULH_R:
            dst = dst % RegistersCount
            src = src % RegistersCount
            self.registerUsage[dst] = i

            return lambda: self.IMULH_R(dst, src) 


        if op < OpCode.IMULH_M:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src != dst:
                if getModMem(mod):
                    memMask = ScratchpadL1Mask
                else:
                    memMask = ScratchpadL2Mask
            else:
                src = 0
                isImm = True
                memMask = ScratchpadL3Mask
            self.registerUsage[dst] = i

            return lambda: self.IMULH_M(dst, src, imm, memMask, isImm) 


        if op < OpCode.ISMULH_R:
            dst = dst % RegistersCount
            src = src % RegistersCount
            self.registerUsage[dst] = i

            return lambda: self.ISMULH_R(dst, src) 


        if op < OpCode.ISMULH_M:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src != dst:
                if getModMem(mod):
                    memMask = ScratchpadL1Mask
                else:
                    memMask = ScratchpadL2Mask
            else:
                src = 0
                isImm = True
                memMask = ScratchpadL3Mask
            self.registerUsage[dst] = i

            return lambda: self.ISMULH_M(dst, src, imm, memMask, isImm) 


        if op < OpCode.IMUL_RCP:
            if not ((imm & (imm - 1)) == 0):
                dst = dst % RegistersCount
                imm = reciprocal((imm % EightByte) & 0x00000000FFFFFFFF)
                src = imm
                self.registerUsage[dst] = i

                return lambda: self.IMUL_R(dst, src, True) 
            else:
                return self.NOP()


        if op < OpCode.INEG_R:
            dst = dst % RegistersCount
            self.registerUsage[dst] = i

            return lambda: self.INEG_R(dst)


        if op < OpCode.IXOR_R:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src == dst:
                isImm = True
                src = imm % EightByte

            self.registerUsage[dst] = i

            return lambda: self.IXOR_R(dst, src, isImm)


        if op < OpCode.IXOR_M:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src != dst:
                if getModMem(mod):
                    memMask = ScratchpadL1Mask
                else:
                    memMask = ScratchpadL2Mask
            else:
                src = 0
                isImm = True
                memMask = ScratchpadL3Mask
            self.registerUsage[dst] = i

            return lambda: self.IXOR_M(dst, src, imm, memMask, isImm)


        if op < OpCode.IROR_R:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src == dst:
                src = imm
                isImm = True
            self.registerUsage[dst] = i

            return lambda: self.IROR_R(dst, src, isImm)


        if op < OpCode.IROL_R:
            isImm = False
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src == dst:
                src = imm
                isImm = True
            self.registerUsage[dst] = i

            return lambda: self.IROL_R(dst, src, isImm)


        if op < OpCode.ISWAP_R:
            dst = dst % RegistersCount
            src = src % RegistersCount
            if src != dst:
                self.registerUsage[dst] = i
                self.registerUsage[src] = i

                return lambda: self.ISWAP_R(dst, src)
            else:
                return self.NOP()


        if op < OpCode.FSWAP_R:
            dst = dst % RegistersCount
            if (dst < RegisterCountFlt):
                reg = 'f'
            else:
                reg = 'e'
                dst = dst - RegisterCountFlt

            return lambda: self.FSWAP_R(dst, reg)


        if op < OpCode.FADD_R:
            dst = dst % RegisterCountFlt
            src = src % RegisterCountFlt

            return lambda: self.FADD_R(dst, src)


        if op < OpCode.FADD_M:
            dst = dst % RegisterCountFlt
            src = src % RegistersCount
            if getModMem(mod):
                memMask = ScratchpadL1Mask
            else:
                memMask = ScratchpadL2Mask

            return lambda: self.FADD_M(dst, src, imm, memMask)


        if op < OpCode.FSUB_R:
            dst = dst % RegisterCountFlt
            src = src % RegisterCountFlt

            return lambda: self.FSUB_R(dst, src)         


        if op < OpCode.FSUB_M:
            dst = dst % RegisterCountFlt
            src = src % RegistersCount
            if getModMem(mod):
                memMask = ScratchpadL1Mask
            else:
                memMask = ScratchpadL2Mask

            return lambda: self.FSUB_M(dst, src, imm, memMask)


        if op < OpCode.FSCAL_R:
            dst = dst % RegisterCountFlt

            return lambda: self.FSCAL_R(dst)


        if op < OpCode.FMUL_R:
            dst = dst % RegisterCountFlt
            src = src % RegisterCountFlt

            return lambda: self.FMUL_R(dst, src)


        if op < OpCode.FDIV_M:
            dst = dst % RegisterCountFlt
            src = src % RegistersCount
            if getModMem(mod):
                memMask = ScratchpadL1Mask
            else:
                memMask = ScratchpadL2Mask

            return lambda: self.FDIV_M(dst, src, imm, memMask)


        if op < OpCode.FSQRT_R:
            dst = dst % RegisterCountFlt

            return lambda: self.FSQRT_R(dst)


        if op < OpCode.CBRANCH:
            dst = dst % RegistersCount
            target = self.registerUsage[dst]
            shift = getModCond(mod) + ConditionOffset
            imm = imm | (1 << shift)
            imm &= ~(1 << (shift - 1))
            memMask = ConditionMask << shift

            for j in range(RegistersCount):
                self.registerUsage[j] = i

            return lambda: self.CBRANCH(dst, imm, memMask, target)


        if op < OpCode.CFROUND:
            src = src % RegistersCount
            imm = imm & 63

            return lambda: self.CFROUND(src, imm)


        if op < OpCode.ISTORE:
            dst = dst % RegistersCount
            src = src % RegistersCount
            if getModCond(mod) < StoreL3Condition:
                if getModMem(mod):
                    memMask = ScratchpadL1Mask
                else:
                    memMask = ScratchpadL2Mask
            else:
                memMask = ScratchpadL3Mask

            return lambda: self.ISTORE(dst, src, imm, memMask)


    def NOP(self):
        return lambda: 0