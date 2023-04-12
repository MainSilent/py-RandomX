from struct import pack
from blake import BLAKE2b
from program import Program
from AES import hashAes1Rx4, fillAes1Rx4, fillAes4Rx4
from common import *


class RegisterFile:
    r = [0] * RegistersCount
    f = [{"lo":0, "hi":0}, {"lo":0, "hi":0}, {"lo":0, "hi":0}, {"lo":0, "hi":0}]
    e = [{"lo":0, "hi":0}, {"lo":0, "hi":0}, {"lo":0, "hi":0}, {"lo":0, "hi":0}]
    a = [{"lo":0, "hi":0}, {"lo":0, "hi":0}, {"lo":0, "hi":0}, {"lo":0, "hi":0}]


class VM(Program):
    DATASET = None
    program = None
    scratchpad = None
    reg = RegisterFile


    def init_dataset(self):
        print("load dataset")
        with open('create_dataset/build/dataset.bin', 'r') as f:
            self.DATASET = f.read().split('~')
        print("loading dataset done")


    def getEntropy(self, i):
        a = toBigEndian(self.entropy[i*8: (i+1)*8])
        res = int.from_bytes(a, 'big')
        return res


    def scratchpadRead(self, addr, offset):
        data = self.scratchpad[addr: addr+offset]
        return int.from_bytes(data, "little")


    def initScratchpad(self, seed):
        pad = fillAes1Rx4(seed, ScratchpadSize)
        self.scratchpad = bytearray(pad[1])

        return pad[0]


    def initialize(self):
        self.reg.a[0]['lo'] = getSmallPositiveFloatBits(self.getEntropy(0))
        self.reg.a[0]['hi'] = getSmallPositiveFloatBits(self.getEntropy(1))
        self.reg.a[1]['lo'] = getSmallPositiveFloatBits(self.getEntropy(2))
        self.reg.a[1]['hi'] = getSmallPositiveFloatBits(self.getEntropy(3))
        self.reg.a[2]['lo'] = getSmallPositiveFloatBits(self.getEntropy(4))
        self.reg.a[2]['hi'] = getSmallPositiveFloatBits(self.getEntropy(5))
        self.reg.a[3]['lo'] = getSmallPositiveFloatBits(self.getEntropy(6))
        self.reg.a[3]['hi'] = getSmallPositiveFloatBits(self.getEntropy(7))

        self.ma = self.getEntropy(8) & CacheLineAlignMask
        self.mx = self.getEntropy(10)
        self.mx = int(hex(self.mx)[10:18], 16)

        addressRegisters = self.getEntropy(12)
        self.readReg0 = 0 + (addressRegisters & 1)
        addressRegisters >>= 1
        self.readReg1 = 2 + (addressRegisters & 1)
        addressRegisters >>= 1
        self.readReg2 = 4 + (addressRegisters & 1)
        addressRegisters >>= 1
        self.readReg3 = 6 + (addressRegisters & 1)

        self.datasetOffset = (self.getEntropy(13) % (DatasetExtraItems + 1)) * CacheLineSize

        self.eMask[0] = getFloatMask(self.getEntropy(14))
        self.eMask[1] = getFloatMask(self.getEntropy(15))

        self.reg.r =  [0] * RegistersCount


    def run(self, seed):
        self.program = fillAes4Rx4(seed, 128 + 8 * RANDOMX_PROGRAM_SIZE)
        self.entropy = self.program[:128]
        self.program = self.program[128:]

        self.initialize()

        for i in range(RegistersCount):
            self.registerUsage[i] = -1

        self.compileProgram()

        spAddr0 = self.mx
        spAddr1 = self.ma

        for _ in range(RANDOMX_PROGRAM_ITERATIONS):
            spMix = self.reg.r[self.readReg0] ^ self.reg.r[self.readReg1]
            spAddr0 ^= spMix
            spAddr0 &= ScratchpadL3Mask64
            spAddr1 ^= spMix >> 32
            spAddr1 &= ScratchpadL3Mask64
			
            for i in range(RegistersCount):
                addr = spAddr0 + 8 * i
                self.reg.r[i] ^= self.scratchpadRead(addr, offset=8)

            for i in range(RegisterCountFlt):
                addr = spAddr1 + 8 * i
                p = unpack("ii", pack("II", self.scratchpadRead(addr, offset=4), self.scratchpadRead(addr+4, offset=4)))
                self.reg.f[i]['lo'] = p[0]
                self.reg.f[i]['hi'] = p[1]

            for i in range(RegisterCountFlt):
                addr = spAddr1 + 8 * (RegisterCountFlt + i)
                p = list(unpack("ii", pack("II", self.scratchpadRead(addr, offset=4), self.scratchpadRead(addr+4, offset=4))))
                p = maskRegisterExponentMantissa(self.eMask, p)
                self.reg.e[i]['lo'] = p[0]
                self.reg.e[i]['hi'] = p[1]

            self.execute()

            self.mx ^= self.reg.r[self.readReg2] ^ self.reg.r[self.readReg3]
            self.mx &= CacheLineAlignMask
            self.datasetRead(self.datasetOffset + self.ma, self.reg.r)
            self.mx, self.ma = self.ma, self.mx

            for i in range(RegistersCount):
                addr = spAddr1 + 8 * i
                self.scratchpad[addr: addr+8] = self.reg.r[i].to_bytes(8, "little")

            for i in range(RegisterCountFlt):
                f_lo = unpack("Q", pack("d", self.reg.f[i]['lo']))[0]
                f_hi = unpack("Q", pack("d", self.reg.f[i]['hi']))[0]

                e_lo = unpack("Q", pack("d", self.reg.e[i]['lo']))[0]
                e_hi = unpack("Q", pack("d", self.reg.e[i]['hi']))[0]

                f_lo ^= e_lo
                f_hi ^= e_hi

                self.reg.f[i]['lo'] = unpack("d", pack("Q", f_lo))[0]
                self.reg.f[i]['hi'] = unpack("d", pack("Q", f_hi))[0]

            for i in range(RegisterCountFlt):
                addr = spAddr0 + 16 * i
                self.scratchpad[addr: addr+16] = pack("dd", self.reg.f[i]['lo'], self.reg.f[i]['hi'])

            spAddr0 = 0
            spAddr1 = 0


    def getRegisterFile(self):
        _reg = self.reg

        return pack(
            "<8Q24d",
            _reg.r[0], _reg.r[1], _reg.r[2], _reg.r[3],
            _reg.r[4], _reg.r[5], _reg.r[6], _reg.r[7],

            _reg.f[0]["lo"], _reg.f[0]["hi"], _reg.f[1]["lo"], _reg.f[1]["hi"],
            _reg.f[2]["lo"], _reg.f[2]["hi"], _reg.f[3]["lo"], _reg.f[3]["hi"],

            _reg.e[0]["lo"], _reg.e[0]["hi"], _reg.e[1]["lo"], _reg.e[1]["hi"],
            _reg.e[2]["lo"], _reg.e[2]["hi"], _reg.e[3]["lo"], _reg.e[3]["hi"],

            _reg.a[0]["lo"], _reg.a[0]["hi"], _reg.a[1]["lo"], _reg.a[1]["hi"],
            _reg.a[2]["lo"], _reg.a[2]["hi"], _reg.a[3]["lo"], _reg.a[3]["hi"]
        )


    def finalResult(self):
        regByte = bytearray(self.getRegisterFile())
        scratchpadHash = hashAes1Rx4(bytes(self.scratchpad), ScratchpadSize)

        regByte[-64:] = scratchpadHash

        regHash = BLAKE2b(regByte, digest_size=32).digest()

        return bytes(regHash)


    def hash(self, msg):
        tempHash = BLAKE2b(msg).digest()

        tempHash = self.initScratchpad(tempHash)

        for _ in range(RANDOMX_PROGRAM_COUNT):
            self.run(tempHash)
            tempHash = BLAKE2b(self.getRegisterFile()).digest()

        self.run(tempHash)
        return self.finalResult()