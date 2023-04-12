from .const import *


def xor(a, b):
    c = [0, 0, 0, 0]

    c[0] = a[0] ^ b[0]
    c[1] = a[1] ^ b[1]
    c[2] = a[2] ^ b[2]
    c[3] = a[3] ^ b[3]

    return c


def aesenc(_in, key):
    s3 = int.from_bytes(_in[0:4], "little")
    s2 = int.from_bytes(_in[4:8], "little")
    s1 = int.from_bytes(_in[8:12], "little")
    s0 = int.from_bytes(_in[12:16], "little")

    out = (
        lutEnc0[s0 & 0xff] ^ lutEnc1[(s3 >> 8) & 0xff] ^ lutEnc2[(s2 >> 16) & 0xff] ^ lutEnc3[s1 >> 24],
        lutEnc0[s1 & 0xff] ^ lutEnc1[(s0 >> 8) & 0xff] ^ lutEnc2[(s3 >> 16) & 0xff] ^ lutEnc3[s2 >> 24],
        lutEnc0[s2 & 0xff] ^ lutEnc1[(s1 >> 8) & 0xff] ^ lutEnc2[(s0 >> 16) & 0xff] ^ lutEnc3[s3 >> 24],
        lutEnc0[s3 & 0xff] ^ lutEnc1[(s2 >> 8) & 0xff] ^ lutEnc2[(s1 >> 16) & 0xff] ^ lutEnc3[s0 >> 24]
    )

    out = xor(out, key)

    result = b''
    result += (out[3]).to_bytes(4, "little")
    result += (out[2]).to_bytes(4, "little")
    result += (out[1]).to_bytes(4, "little")
    result += (out[0]).to_bytes(4, "little")

    return result


def aesdec(_in, key):
    s3 = int.from_bytes(_in[0:4], "little")
    s2 = int.from_bytes(_in[4:8], "little")
    s1 = int.from_bytes(_in[8:12], "little")
    s0 = int.from_bytes(_in[12:16], "little")

    out = (
        lutDec0[s0 & 0xff] ^ lutDec1[(s1 >> 8) & 0xff] ^ lutDec2[(s2 >> 16) & 0xff] ^ lutDec3[s3 >> 24],
        lutDec0[s1 & 0xff] ^ lutDec1[(s2 >> 8) & 0xff] ^ lutDec2[(s3 >> 16) & 0xff] ^ lutDec3[s0 >> 24],
        lutDec0[s2 & 0xff] ^ lutDec1[(s3 >> 8) & 0xff] ^ lutDec2[(s0 >> 16) & 0xff] ^ lutDec3[s1 >> 24],
        lutDec0[s3 & 0xff] ^ lutDec1[(s0 >> 8) & 0xff] ^ lutDec2[(s1 >> 16) & 0xff] ^ lutDec3[s2 >> 24]
    )

    out = xor(out, key)

    result = b''
    result += (out[3]).to_bytes(4, "little")
    result += (out[2]).to_bytes(4, "little")
    result += (out[1]).to_bytes(4, "little")
    result += (out[0]).to_bytes(4, "little")

    return result