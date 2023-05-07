# Requires the CryptoDome and pytest, install with:
#
#   pip install pycryptodome pytest
#
# To execute tests, run
#
#   pytest

from kyber import *

import pytest

import binascii
import hashlib

import Crypto
from Crypto.Cipher import AES
from Crypto.Hash import SHAKE128

#
# Assertions used in the draft.
#

def test_zeta():
    assert pow(zeta, 128, q) == q-1

def test_smod_round():
    assert smod(3325) == -4
    assert smod(-3320) == 9

    assert Round(.4) == 0
    assert Round(.5) == 1
    assert Round(-.5) == 0
    assert Round(-.6) == -1

def test_brv():
    assert brv(91) == 109
    assert brv(1) == 64

def test_ntt():
    assert Poly([1,1] + [0]*254).NTT() == Poly([1]*256)

    range256NTT = Poly((
        2429, 2845, 425, 795, 1865, 1356, 624, 31, 2483, 2197, 2725,
        2668, 2707, 517, 1488, 2194, 1971, 803, 922, 231, 2319, 613,
        1075, 606, 306, 3143, 1380, 2718, 1155, 531, 818, 1586, 2874,
        155, 304, 1442, 2619, 1712, 2169, 2159, 1479, 2634, 2864, 2014,
        1679, 3200, 102, 1923, 1603, 558, 681, 316, 517, 931, 1732,
        1999, 2024, 1094, 2276, 2159, 2187, 1973, 2637, 2158, 2373,
        198, 2986, 247, 1482, 449, 1157, 1290, 1057, 2220, 1124, 1019,
        400, 2206, 1225, 2233, 1376, 2880, 2664, 614, 1960, 1974, 2934,
        2679, 2860, 2217, 2897, 3234, 1905, 36, 2306, 2145, 219, 581,
        3000, 1378, 2392, 2835, 1685, 1091, 1054, 2150, 543, 3192, 2518,
        3246, 2277, 570, 239, 2522, 838, 1990, 126, 2637, 126, 818,
        3232, 1075, 940, 742, 2617, 630, 650, 2776, 2606, 482, 2208,
        868, 1949, 2149, 3066, 1896, 2996, 2306, 63, 883, 2463, 1313,
        1951, 2999, 97, 1806, 2830, 2104, 1771, 2453, 370, 2605, 871,
        1467, 2426, 1985, 2363, 658, 1015, 655, 501, 664, 1249, 3120,
        106, 3100, 1274, 1919, 1890, 2147, 1961, 1949, 1738, 461, 2772,
        1270, 3095, 2089, 1051, 2576, 1628, 1735, 3195, 2034, 655, 524,
        3195, 901, 2007, 1419, 157, 2334, 2344, 2825, 634, 850, 2523,
        2642, 672, 1604, 216, 3280, 1317, 905, 1165, 1532, 3059, 777,
        242, 1752, 2052, 533, 1006, 1858, 2336, 1183, 1656, 1668, 2037,
        2946, 2184, 1048, 104, 2825, 877, 111, 1363, 1989, 1995, 659,
        12, 506, 1551, 2022, 3212, 1591, 1637, 2330, 1625, 2795, 774,
        70, 1002, 3194, 928, 987, 2717, 3005, 2883, 149, 2594, 3105,
        2502, 2134, 2717, 2303,
    ))

    assert Poly(range(256)).NTT().InvNTT() == Poly(range(256))
    assert Poly(range(256)).NTT() == Poly(range(256)).RefNTT()
    assert range256NTT.InvNTT() == Poly(range(256))
    assert Poly(range(256)).NTT() == range256NTT

def test_word_to_bits():
    assert WordsToBits([12,45], 8) == [0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0]

def test_sampling():
    p = sampleUniform(io.BytesIO(hashlib.shake_128(b'').digest(length=1344)))
    assert p.cs[:4] == (3199, 697, 2212, 2302)
    assert p.cs[-3:] == (255, 846, 1)

    p = CBD(range(64*2), 2)
    assert p.cs[:6] == (0, 0, 1, 0, 1, 0)
    assert p.cs[-4:] == (3328, 1, 0, 1)

    p = CBD(range(64*3), 3)
    assert p.cs[:5] == (0, 1, 3328, 0, 2)
    assert p.cs[-4:] == (3328, 3327, 3328, 1)

    noise3Test = Poly(x%q for x in [
        0, 0, 1, -1, 0, 2, 0, -1, -1, 3, 0, 1, -2, -2, 0, 1, -2,
        1, 0, -2, 3, 0, 0, 0, 1, 3, 1, 1, 2, 1, -1, -1, -1, 0, 1,
        0, 1, 0, 2, 0, 1, -2, 0, -1, -1, -2, 1, -1, -1, 2, -1, 1,
        1, 2, -3, -1, -1, 0, 0, 0, 0, 1, -1, -2, -2, 0, -2, 0, 0,
        0, 1, 0, -1, -1, 1, -2, 2, 0, 0, 2, -2, 0, 1, 0, 1, 1, 1,
        0, 1, -2, -1, -2, -1, 1, 0, 0, 0, 0, 0, 1, 0, -1, -1, 0,
        -1, 1, 0, 1, 0, -1, -1, 0, -2, 2, 0, -2, 1, -1, 0, 1, -1,
        -1, 2, 1, 0, 0, -2, -1, 2, 0, 0, 0, -1, -1, 3, 1, 0, 1, 0,
        1, 0, 2, 1, 0, 0, 1, 0, 1, 0, 0, -1, -1, -1, 0, 1, 3, 1,
        0, 1, 0, 1, -1, -1, -1, -1, 0, 0, -2, -1, -1, 2, 0, 1, 0,
        1, 0, 2, -2, 0, 1, 1, -3, -1, -2, -1, 0, 1, 0, 1, -2, 2,
        2, 1, 1, 0, -1, 0, -1, -1, 1, 0, -1, 2, 1, -1, 1, 2, -2,
        1, 2, 0, 1, 2, 1, 0, 0, 2, 1, 2, 1, 0, 2, 1, 0, 0, -1, -1,
        1, -1, 0, 1, -1, 2, 2, 0, 0, -1, 1, 1, 1, 1, 0, 0, -2, 0,
        -1, 1, 2, 0, 0, 1, 1, -1, 1, 0, 1
    ])
    assert noise3Test == CBD(PRF1(bytes(range(32)), 37).read(3*64), 3)
    noise2Test = Poly(x%q for x in [
        1, 0, 1, -1, -1, -2, -1, -1, 2, 0, -1, 0, 0, -1,
        1, 1, -1, 1, 0, 2, -2, 0, 1, 2, 0, 0, -1, 1, 0, -1,
        1, -1, 1, 2, 1, 1, 0, -1, 1, -1, -2, -1, 1, -1, -1,
        -1, 2, -1, -1, 0, 0, 1, 1, -1, 1, 1, 1, 1, -1, -2,
        0, 1, 0, 0, 2, 1, -1, 2, 0, 0, 1, 1, 0, -1, 0, 0,
        -1, -1, 2, 0, 1, -1, 2, -1, -1, -1, -1, 0, -2, 0,
        2, 1, 0, 0, 0, -1, 0, 0, 0, -1, -1, 0, -1, -1, 0,
        -1, 0, 0, -2, 1, 1, 0, 1, 0, 1, 0, 1, 1, -1, 2, 0,
        1, -1, 1, 2, 0, 0, 0, 0, -1, -1, -1, 0, 1, 0, -1,
        2, 0, 0, 1, 1, 1, 0, 1, -1, 1, 2, 1, 0, 2, -1, 1,
        -1, -2, -1, -2, -1, 1, 0, -2, -2, -1, 1, 0, 0, 0,
        0, 1, 0, 0, 0, 2, 2, 0, 1, 0, -1, -1, 0, 2, 0, 0,
        -2, 1, 0, 2, 1, -1, -2, 0, 0, -1, 1, 1, 0, 0, 2,
        0, 1, 1, -2, 1, -2, 1, 1, 0, 2, 0, -1, 0, -1, 0,
        1, 2, 0, 1, 0, -2, 1, -2, -2, 1, -1, 0, -1, 1, 1,
        0, 0, 0, 1, 0, -1, 1, 1, 0, 0, 0, 0, 1, 0, 1, -1,
        0, 1, -1, -1, 2, 0, 0, 1, -1, 0, 1, -1, 0,
    ])
    assert noise2Test == CBD(PRF1(bytes(range(32)), 37).read(2*64), 2)

#
# NIST Known Answer Test (KAT) test vectors
#

class NistDRBG:
    """ NIST's DRBG used to generate NIST's Known Answer Tests (KATs),
        see PQCgenKAT.c. """
    def __init__(self, seed):
        self.key = b'\0'*32
        self.v = 0
        assert len(seed) == 48
        self._update(seed)
    def _update(self, seed):
        b = AES.new(self.key, AES.MODE_ECB)
        buf = b''
        for i in range(3):
            self.v += 1
            buf += b.encrypt(self.v.to_bytes(16, 'big'))
        if seed is not None:
            buf = bytes([x ^ y for x, y in zip(seed, buf)])
        self.key = buf[:32]
        self.v = int.from_bytes(buf[32:], 'big')
    def read(self, length):
        b = AES.new(self.key, AES.MODE_ECB)
        ret = b''
        while len(ret) < length:
            self.v += 1
            block = b.encrypt(self.v.to_bytes(16, 'big'))
            ret += block
        self._update(None)
        return ret[:length]

@pytest.mark.parametrize("name,params,want", [
            (b"Kyber512", params512, "1717803847308c66415874aa7f84a9c7854bb55b632043895b6448f569341dd5"),
            (b"Kyber768", params768, "cbee30e334ec7d346dcf94c4fbdf803bf82c0ce591bba336f48ba8ae527e8a9f"),
            (b"Kyber1024", params1024, "35c1dca71b07c657e2c41c49b4797ec29ecd8a15559103068bcccc5ddeb2fe55"),
        ])
def test_nist_kat(name, params, want):
    seed = bytes(range(48))
    g = NistDRBG(seed)
    f = hashlib.sha256()
    f.update(b"# %s\n\n" % name)
    for i in range(100):
        seed = g.read(48)
        f.update(b"count = %d\n" % i)
        f.update(b"seed = %s\n" % binascii.hexlify(seed).upper())
        g2 = NistDRBG(seed)

        kseed = g2.read(32) +  g2.read(32)
        eseed = g2.read(32)

        pk, sk = KeyGen(kseed, params)
        ct, ss = Enc(pk, eseed, params)
        ss2 = Dec(sk, ct, params)
        assert ss == ss2
        f.update(b"pk = %s\n" % binascii.hexlify(pk).upper())
        f.update(b"sk = %s\n" % binascii.hexlify(sk).upper())
        f.update(b"ct = %s\n" % binascii.hexlify(ct).upper())
        f.update(b"ss = %s\n\n" % binascii.hexlify(ss).upper())

    assert f.hexdigest() == want

def test_sizes():
    for params, sss, pks, cts, sks in (
            (params512, 32, 800, 768, 1632),
            (params768, 32, 1184, 1088, 2400),
            (params1024, 32, 1568, 1568, 3168),
        ):

        pk, sk = KeyGen(b'\0'*64, params)
        assert len(pk) == pks
        assert len(sk) == sks
        ct, ss = Enc(pk, b'\0'*32, params)
        assert len(ct) == cts
        assert len(ss) == sss

def test_compress():
    for d in [1, 3, 4, 10, 11]:
        mask = (1 << d) - 1
        for x in range(q):
            assert (20642679 * ((x << d) + q//2)) >> 36 & mask == Compress(x, d)

# Check against test/test_vectors{512,768,1024} from the reference
# implementation, truncated to 10 cases.
@pytest.mark.parametrize("params,want", [
            (params512,  "9006eb8020e3dc802df1fe60f26d0b51009fad373b9dcbece595c82b941ebf9a"),
            (params768,  "9f210734f803ba8bcc95ab0ce774e14f53978593d9a2000c6d69f59e5d740b1b"),
            (params1024, "6118511cb40f262e8e176fd7cbfa1ee487664568563b9b45191e643a09c8e965"),
        ])
def test_vectors(params, want):
    h = SHAKE128.new()
    f = hashlib.sha256()
    for i in range(10):
        pk, sk = KeyGen(h.read(64), params)
        f.update(b'Public Key: ' + binascii.hexlify(pk) + b'\n')
        f.update(b'Secret Key: ' + binascii.hexlify(sk) + b'\n')
        ct, ss = Enc(pk, h.read(32), params)
        f.update(b'Ciphertext: ' + binascii.hexlify(ct) + b'\n')
        f.update(b'Shared Secret B: ' + binascii.hexlify(ss) + b'\n')
        ss2 = Dec(sk, ct, params)
        f.update(b'Shared Secret A: ' + binascii.hexlify(ss2) + b'\n')
        ct2 = h.read(len(ct))
        ss3 = Dec(sk, ct2, params)
        f.update(b'Pseudorandom shared Secret A: ' + binascii.hexlify(ss3) + b'\n')
    assert f.hexdigest() == want
