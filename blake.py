import binascii
import struct
from ctypes import *


WORDBITS = 64
MASKBITS = 0xffffffffffffffff
BLOCKBYTES = 128
IV = [
    0x6a09e667f3bcc908, 0xbb67ae8584caa73b,
    0x3c6ef372fe94f82b, 0xa54ff53a5f1d36f1,
    0x510e527fade682d1, 0x9b05688c2b3e6c1f,
    0x1f83d9abfb41bd6b, 0x5be0cd19137e2179
]
sigma = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
    [11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4],
    [7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8],
    [9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13],
    [2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9],
    [12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11],
    [13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10],
    [6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5],
    [10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0],
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3]
]


class BLAKE2b(object):
    def __init__(self, data=None, digest_size=64):
        class ParamFields64(LittleEndianStructure):
            _fields_ = [
                ("digest_size", c_ubyte),
                ("key_length", c_ubyte),
                ("fanout", c_ubyte),
                ("depth", c_ubyte)
            ]

        class Params64(Union):
            _fields_ = [("F", ParamFields64), ("W", c_uint64 * 8)]

        self.digest_size = digest_size

        P = Params64()
        P.F.digest_size = self.digest_size
        P.F.fanout = 1
        P.F.depth = 1

        self.h = [IV[i] ^ P.W[i] for i in range(8)]

        self.totbytes = 0
        self.t = [0]*2
        self.f = [0]*2
        self.buflen = 0
        self.buf = b''
        self.finalized = False
        self.block_size = BLOCKBYTES

        if data:
            self.update(data)

    def _compress(self, block):
        ROT1 = 32
        ROT2 = 24
        ROT3 = 16
        ROT4 = 63
        WB_ROT1 = WORDBITS - ROT1
        WB_ROT2 = WORDBITS - ROT2
        WB_ROT3 = WORDBITS - ROT3
        WB_ROT4 = WORDBITS - ROT4

        m = struct.unpack_from('<16%s' % 'Q', bytes(block))

        v = [0]*16
        v[0: 8] = self.h
        v[8:12] = IV[:4]
        v[12] = self.t[0] ^ IV[4]
        v[13] = self.t[1] ^ IV[5]
        v[14] = self.f[0] ^ IV[6]
        v[15] = self.f[1] ^ IV[7]

        def G(a, b, c, d):
            va = v[a]
            vb = v[b]
            vc = v[c]
            vd = v[d]
            va = (va + vb + msri2) & MASKBITS
            w = vd ^ va
            vd = (w >> ROT1) | (w << (WB_ROT1)) & MASKBITS
            vc = (vc + vd) & MASKBITS
            w = vb ^ vc
            vb = (w >> ROT2) | (w << (WB_ROT2)) & MASKBITS
            va = (va + vb + msri21) & MASKBITS
            w = vd ^ va
            vd = (w >> ROT3) | (w << (WB_ROT3)) & MASKBITS
            vc = (vc + vd) & MASKBITS
            w = vb ^ vc
            vb = (w >> ROT4) | (w << (WB_ROT4)) & MASKBITS
            v[a] = va
            v[b] = vb
            v[c] = vc
            v[d] = vd

        for r in range(12):
            sr = sigma[r]
            msri2 = m[sr[0]]
            msri21 = m[sr[1]]
            G(0,  4,  8, 12)
            msri2 = m[sr[2]]
            msri21 = m[sr[3]]
            G(1,  5,  9, 13)
            msri2 = m[sr[4]]
            msri21 = m[sr[5]]
            G(2,  6, 10, 14)
            msri2 = m[sr[6]]
            msri21 = m[sr[7]]
            G(3,  7, 11, 15)
            msri2 = m[sr[8]]
            msri21 = m[sr[9]]
            G(0,  5, 10, 15)
            msri2 = m[sr[10]]
            msri21 = m[sr[11]]
            G(1,  6, 11, 12)
            msri2 = m[sr[12]]
            msri21 = m[sr[13]]
            G(2,  7,  8, 13)
            msri2 = m[sr[14]]
            msri21 = m[sr[15]]
            G(3,  4,  9, 14)

        self.h = [self.h[i] ^ v[i] ^ v[i+8] for i in range(8)]

    def update(self, data):
        assert self.finalized == False

        datalen = len(data)
        dataptr = 0
        while True:
            if len(self.buf) > BLOCKBYTES:
                self._increment_counter(BLOCKBYTES)
                self._compress(self.buf[:BLOCKBYTES])
                self.buf = self.buf[BLOCKBYTES:]
            if dataptr < datalen:
                self.buf += data[dataptr:dataptr + BLOCKBYTES]
                dataptr += BLOCKBYTES
            else:
                break

    def digest(self):
        if not self.finalized and len(self.buf):
            self._increment_counter(len(self.buf))
            self.f[0] = MASKBITS
            self.buf += (chr(0).encode())*(BLOCKBYTES - len(self.buf))
            self._compress(self.buf)
            self.buf = b''
        self.digest_ = struct.pack('<8%s' % 'Q', *tuple(self.h))
        self.finalized = True
        return self.digest_[:self.digest_size]

    def hexdigest(self):
        return binascii.hexlify(self.digest()).decode()

    def _increment_counter(self, numbytes):
        self.totbytes += numbytes
        self.t[0] = self.totbytes & MASKBITS
        self.t[1] = self.totbytes >> WORDBITS