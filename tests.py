from blake import BLAKE2b
from AES import *
from vm import VM

# Test blake
print("Test Blake2b")
br = None
b2 = BLAKE2b(digest_size=64)
b2.update(b'RandomX AesHash1R state')
br = b2.hexdigest()

assert br == '0d2cb592de56a89f47db82ccad3a98d76e998d3398b7c7155a129ef55780e7ac1700776ad0c762ae6b507950e47ca0e80c240a638d82ad070500a1794849997e'

b2 = BLAKE2b(digest_size=32)
b2.update(b'RandomX AesHash1R xkeys')
br = b2.hexdigest()

assert br == '8983faf69f94248bbf56dc9001028906d163b2613ce0f451c64310ee9bf918ed'

b2 = BLAKE2b(digest_size=64)
b2.update(b'RandomX' * 1000)
br = b2.hexdigest()

assert br == '3c39884fa02a3cd06852f6d239e07459a62fb97540090489c1fec13eed2eaf3547ffbc5367539ae3c36fa8fd1e12fc83fee6f50704759b6a998e4942009dfb35'

b2 = BLAKE2b(digest_size=32)
b2.update(b'RandomX' * 1000)
br = b2.hexdigest()

assert br == '946877ebaa4f172a0091646d4457d20135b772dd5c2b16bec9fc8bdcd9307b0d'


# Test AES
print("Test AES")

tempAES = fillAes1Rx4(
    int("6c19536eb2de31b6c0065f7f116e86f960d8af0c57210a6584c3237b9d064dc7", 16).to_bytes(32, byteorder='big'),
    64
)[1]

assert tempAES.hex() == "fa89397dd6ca422513aeadba3f124b5540324c4ad4b6db434394307a17c833aba330406d942cc6cd1d2b92a617b1726c56e28c091f52d9d2eb2f527537f2752a"


tempAES = fillAes4Rx4(
    int("6c19536eb2de31b6c0065f7f116e86f960d8af0c57210a6584c3237b9d064dc7", 16).to_bytes(32, byteorder='big'),
    64
)

assert tempAES.hex() == "7596e422dba53fa5c112391178256860b4124e33c3c1a6285fa051a3c0a79ab4c9ae1320506ab932d5ad00e6145cd658554d4c885ce082b23031cd407103e724"


# Test Hash
vm = VM()
vm.init_dataset()

r = [0] * 8
vm.datasetRead(24, r)

assert r == [7495547411488711387, 10505140075988195060, 3174008826684355752, 2807892716207044791, 15802380311510598485, 18410110538984067793, 3933910281115102905, 9221217956855870065]

result = vm.hash(b"Lorem ipsum dolor sit amet")

# print()
# print(result.hex())
# print()

assert result.hex() == "300a0adb47603dedb42228ccb2b211104f4da45af709cd7547cd049e9489c969"

print("\nTest Successful\n")