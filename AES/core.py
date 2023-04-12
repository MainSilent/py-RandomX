from .const import *
from .impl import *

debug = True

def hashAes1Rx4(state, size):
    ptr = 0
    result = b''

    state0 = AES_HASH_1R_STATE0
    state1 = AES_HASH_1R_STATE1
    state2 = AES_HASH_1R_STATE2
    state3 = AES_HASH_1R_STATE3

    while ptr < (size // 16):
        in0 = state[ptr*16: (ptr+1)*16]
        in1 = state[(ptr+1)*16: (ptr+2)*16]
        in2 = state[(ptr+2)*16: (ptr+3)*16]
        in3 = state[(ptr+3)*16: (ptr+4)*16]

        in0 = [int.from_bytes(in0[0:4], "little"), int.from_bytes(in0[4:8], "little"), int.from_bytes(in0[8:12], "little"), int.from_bytes(in0[12:16], "little")]
        in1 = [int.from_bytes(in1[0:4], "little"), int.from_bytes(in1[4:8], "little"), int.from_bytes(in1[8:12], "little"), int.from_bytes(in1[12:16], "little")]
        in2 = [int.from_bytes(in2[0:4], "little"), int.from_bytes(in2[4:8], "little"), int.from_bytes(in2[8:12], "little"), int.from_bytes(in2[12:16], "little")]
        in3 = [int.from_bytes(in3[0:4], "little"), int.from_bytes(in3[4:8], "little"), int.from_bytes(in3[8:12], "little"), int.from_bytes(in3[12:16], "little")]

        in0.reverse()
        in1.reverse()
        in2.reverse()
        in3.reverse()

        state0 = aesenc(state0, in0)
        state1 = aesdec(state1, in1)
        state2 = aesenc(state2, in2)
        state3 = aesdec(state3, in3)

        ptr += 4

    xkey0 = AES_HASH_1R_XKEY0
    xkey1 = AES_HASH_1R_XKEY1

    state0 = aesenc(state0, xkey0)
    state1 = aesdec(state1, xkey0)
    state2 = aesenc(state2, xkey0)
    state3 = aesdec(state3, xkey0)

    state0 = aesenc(state0, xkey1)
    state1 = aesdec(state1, xkey1)
    state2 = aesenc(state2, xkey1)
    state3 = aesdec(state3, xkey1)

    _state = [state0, state1, state2, state3]

    for s in _state:
        result += s

    return result


def fillAes1Rx4(state, size):
    # result = b''
    # new_hash = b''

    # with open('./scratchpad_state.bin', 'rb') as f:
    #     new_hash = f.read()

    # with open('./scratchpad_result.bin', 'rb') as f:
    #     result = f.read()

    # return [new_hash, result]

    ptr = 0
    result = b''

    state0 = state[0:16]
    state1 = state[16:32]
    state2 = state[32:48]
    state3 = state[48:64]

    key0 = AES_GEN_1R_KEY0
    key1 = AES_GEN_1R_KEY1
    key2 = AES_GEN_1R_KEY2
    key3 = AES_GEN_1R_KEY3

    while ptr < size:
        state0 = aesdec(state0, key0)
        state1 = aesenc(state1, key1)
        state2 = aesdec(state2, key2)
        state3 = aesenc(state3, key3)

        _state = [state0, state1, state2, state3]
    
        for s in _state:
            result += s

        ptr += 64

        if debug:
            print(f'fillAes1Rx4 {ptr}/{size}')

    # Calc new tempHash
    new_hash = b''
    _state = [state0, state1, state2, state3]
    for s in _state:
        new_hash += s

    return [new_hash, result]


def fillAes4Rx4(state, size):
    ptr = 0
    result = b''

    key0 = AES_GEN_4R_KEY0
    key1 = AES_GEN_4R_KEY1
    key2 = AES_GEN_4R_KEY2
    key3 = AES_GEN_4R_KEY3
    key4 = AES_GEN_4R_KEY4
    key5 = AES_GEN_4R_KEY5
    key6 = AES_GEN_4R_KEY6
    key7 = AES_GEN_4R_KEY7

    state0 = state[0:16]
    state1 = state[16:32]
    state2 = state[32:48]
    state3 = state[48:64]

    while ptr < size:
        state0 = aesdec(state0, key0)
        state1 = aesenc(state1, key0)
        state2 = aesdec(state2, key4)
        state3 = aesenc(state3, key4)

        state0 = aesdec(state0, key1)
        state1 = aesenc(state1, key1)
        state2 = aesdec(state2, key5)
        state3 = aesenc(state3, key5)

        state0 = aesdec(state0, key2)
        state1 = aesenc(state1, key2)
        state2 = aesdec(state2, key6)
        state3 = aesenc(state3, key6)

        state0 = aesdec(state0, key3)
        state1 = aesenc(state1, key3)
        state2 = aesdec(state2, key7)
        state3 = aesenc(state3, key7)

        _state = [state0, state1, state2, state3]
    
        for s in _state:
            result += s

        ptr += 64

    return result