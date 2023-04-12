from struct import pack, unpack


EightByte = 18446744073709551616
RANDOMX_PROGRAM_SIZE = 256
mantissaSize = 52
exponentBias = 1023
mantissaMask = 4503599627370495
exponentMask = 2047
RANDOMX_JUMP_BITS = 8
RANDOMX_JUMP_OFFSET = 8
RANDOMX_DATASET_BASE_SIZE  = 2147483648
RANDOMX_DATASET_EXTRA_SIZE = 33554368
RANDOMX_DATASET_ITEM_SIZE = 64
RANDOMX_SCRATCHPAD_L3 = 2097152
RANDOMX_SCRATCHPAD_L2 = 262144
RANDOMX_SCRATCHPAD_L1 = 16384
RANDOMX_PROGRAM_COUNT = 7
RANDOMX_PROGRAM_SIZE = 256
RANDOMX_PROGRAM_ITERATIONS = 2048
ScratchpadSize = RANDOMX_SCRATCHPAD_L3
CacheLineSize = RANDOMX_DATASET_ITEM_SIZE
CacheLineAlignMask = (RANDOMX_DATASET_BASE_SIZE - 1) & ~(CacheLineSize - 1)
DatasetExtraItems = RANDOMX_DATASET_EXTRA_SIZE // RANDOMX_DATASET_ITEM_SIZE
RegistersCount = 8
RegisterCountFlt = 4

ScratchpadL1 = RANDOMX_SCRATCHPAD_L1 // 8
ScratchpadL2 = RANDOMX_SCRATCHPAD_L2 // 8
ScratchpadL3 = RANDOMX_SCRATCHPAD_L3 // 8
ScratchpadL1Mask = (ScratchpadL1 - 1) * 8
ScratchpadL2Mask = (ScratchpadL2 - 1) * 8
ScratchpadL1Mask16 = (ScratchpadL1 // 2 - 1) * 16
ScratchpadL2Mask16 = (ScratchpadL2 // 2 - 1) * 16
ScratchpadL3Mask = (ScratchpadL3 - 1) * 8
ScratchpadL3Mask64 = (ScratchpadL3 // 8 - 1) * 64
RegistersCount = 8
RegisterCountFlt = RegistersCount // 2
RegisterNeedsDisplacement = 5
RegisterNeedsSib = 4
StoreL3Condition = 14
dynamicExponentBits = 4
ConditionOffset = RANDOMX_JUMP_OFFSET
ConditionMask = 255
dynamicMantissaMask = (1 << (mantissaSize + dynamicExponentBits)) - 1


def getStaticExponent(entropy):
    exponent = 0x300
    exponent |= (entropy >> (60)) << 4
    exponent <<= 52
    return exponent


def getFloatMask(entropy):
    mask22bit = 4194303
    return (entropy & mask22bit) | getStaticExponent(entropy)


def getSmallPositiveFloatBits(entropy):
    exponent = entropy >> 59
    mantissa = entropy & mantissaMask
    exponent += exponentBias
    exponent &= exponentMask
    exponent <<= mantissaSize
    res = exponent | mantissa
    return unpack("d", pack("Q", res))[0]


def maskRegisterExponentMantissa(eMask, x):
    x[0] = unpack("Q", pack("d", x[0]))[0]
    x[1] = unpack("Q", pack("d", x[1]))[0]

    xexponentMask = eMask
    x[0] &= dynamicMantissaMask
    x[1] &= dynamicMantissaMask
    x[0] |= xexponentMask[0]
    x[1] |= xexponentMask[1]

    x[0] = unpack("d", pack("Q", x[0]))[0]
    x[1] = unpack("d", pack("Q", x[1]))[0]

    return x


def getModMem(mod):
    return mod % 4


def getModShift(mod):
    return (mod >> 2) % 4


def getModCond(mod):
    return mod >> 4


def reciprocal(divisor):
    p2exp63 = 1 << 63;

    quotient = p2exp63 // divisor
    remainder = p2exp63 % divisor

    bsr = 0

    bit = divisor
    while bit > 0:
        bsr += 1
        bit >>= 1

    shift = 0
    while shift < bsr:
        if (remainder >= divisor - remainder):
            quotient = quotient * 2 + 1
            remainder = remainder * 2 - divisor
        else:
            quotient = quotient * 2
            remainder = remainder * 2
        shift += 1

    return quotient


def getScratchpadAddress(src, imm, memMask):
    addr = (src + imm) & memMask
    return addr


def vec_scale(a):
    mask = 0x80F0000000000000

    a['lo'] = unpack('Q', pack('d', a['lo']))[0] ^ mask
    a['hi'] = unpack('Q', pack('d', a['hi']))[0] ^ mask

    a['lo'] = unpack('d', pack('Q', a['lo']))[0]
    a['hi'] = unpack('d', pack('Q', a['hi']))[0] 


def rotr(a, b):
    return (a >> b) | (a << (-b & 63))


def rotl(a, b):
    return (a << b) | (a >> (-b & 63))


def toBigEndian(byte):
    a = int.from_bytes(byte, "little")
    return a.to_bytes(len(byte), "big")


def LO(x):
    return x & 0xffffffff

def HI(x):
    return x >> 32


def mulh(a, b):
    ah = HI(a)
    al = LO(a)
    bh = HI(b)
    bl = LO(b)
    x00 = al * bl
    x01 = al * bh
    x10 = ah * bl
    x11 = ah * bh
    m1 = LO(x10) + LO(x01) + HI(x00)
    m2 = HI(x10) + HI(x01) + LO(x11) + HI(m1)
    m3 = HI(x11) + HI(m2)

    return (m3 << 32) + LO(m2)


def smulh(a, b):
    src = unpack("q", pack("Q", a))[0]
    dst = unpack("q", pack("Q", b))[0]
    hi = (src * dst) >> 64
    return hi % EightByte