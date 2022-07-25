# WARNING This is a specification of Kyber; not a production ready
# implementation. It is slow and does not run in constant time.

import io
import hashlib
import functools
import collections

from math import floor

q = 3329
nBits = 8
zeta = 17
eta2 = 2

n = 2**nBits
inv2 = (q+1)//2 # inverse of 2

params = collections.namedtuple('params', ('k', 'du', 'dv', 'eta1'))

params512  = params(k = 2, du = 10, dv = 4, eta1 = 3)
params768  = params(k = 3, du = 10, dv = 4, eta1 = 2)
params1024 = params(k = 4, du = 11, dv = 5, eta1 = 2)

def smod(x):
    r = x % q
    if r > (q-1)//2:
        r -= q
    return r

# Rounds to nearest integer with ties going up
def Round(x):
    return int(floor(x + 0.5))

def Compress(x, d):
    return Round((2**d / q) * x) % (2**d)

def Decompress(y, d):
    assert 0 <= y and y <= 2**d
    return Round((q / 2**d) * y)

def BitsToWords(bs, w):
    assert len(bs) % w == 0
    return [sum(bs[i+j] * 2**j for j in range(w))
            for i in range(0, len(bs), w)]

def WordsToBits(bs, w):
    return sum([[(b >> i) % 2 for i in range(w)] for b in bs], [])

def Encode(a, w):
    return bytes(BitsToWords(WordsToBits(a, w), 8))

def Decode(a, w):
    return BitsToWords(WordsToBits(a, 8), w)

def brv(x):
    """ Reverses a 7-bit number """
    return int(''.join(reversed(bin(x)[2:].zfill(nBits-1))), 2)

class Poly:
    def __init__(self, cs=None):
        self.cs = (0,)*n if cs is None else tuple(cs)
        assert len(self.cs) == n

    def __add__(self, other):
        return Poly((a+b) % q for a,b in zip(self.cs, other.cs))

    def __neg__(self):
        return Poly(q-a for a in self.cs)
    def __sub__(self, other):
        return self + -other

    def __str__(self):
        return f"Poly({self.cs}"

    def __eq__(self, other):
        return self.cs == other.cs

    def NTT(self):
        cs = list(self.cs)
        layer = n // 2
        zi = 0
        while layer >= 2:
            for offset in range(0, n-layer, 2*layer):
                zi += 1
                z = pow(zeta, brv(zi), q)

                for j in range(offset, offset+layer):
                    t = (z * cs[j + layer]) % q
                    cs[j + layer] = (cs[j] - t) % q
                    cs[j] = (cs[j] + t) % q
            layer //= 2
        return Poly(cs)

    def RefNTT(self):
        # Slower, but simpler, version of the NTT.
        cs = [0]*n
        for i in range(0, n, 2):
            for j in range(n // 2):
                z = pow(zeta, (2*brv(i//2)+1)*j, q)
                cs[i] = (cs[i] + self.cs[2*j] * z) % q
                cs[i+1] = (cs[i+1] + self.cs[2*j+1] * z) % q
        return Poly(cs)

    def InvNTT(self):
        cs = list(self.cs)
        layer = 2
        zi = n//2
        while layer < n:
            for offset in range(0, n-layer, 2*layer):
                zi -= 1
                z = pow(zeta, brv(zi), q)

                for j in range(offset, offset+layer):
                    t = (cs[j+layer] - cs[j]) % q
                    cs[j] = (inv2*(cs[j] + cs[j+layer])) % q
                    cs[j+layer] = (inv2 * z * t) % q
            layer *= 2
        return Poly(cs)

    def MulNTT(self, other):
        """ Computes self o other, the multiplication of self and other
            in the NTT domain. """
        cs = [None]*n
        for i in range(0, n, 2):
            a1 = self.cs[i]
            a2 = self.cs[i+1]
            b1 = other.cs[i]
            b2 = other.cs[i+1]
            z = pow(zeta, 2*brv(i//2)+1, q)
            cs[i] = (a1 * b1 + z * a2 * b2) % q
            cs[i+1] = (a2 * b1 + a1 * b2) % q
        return Poly(cs)

    def Compress(self, d):
        return Poly(Compress(c, d) for c in self.cs)

    def Decompress(self, d):
        return Poly(Decompress(c, d) for c in self.cs)

    def Encode(self, d):
        return Encode(self.cs, d)

def sampleUniform(stream):
    cs = []
    while True:
        b = stream.read(3)
        d1 = b[0] + 256*(b[1] % 16)
        d2 = (b[1] >> 4) + 16*b[2]
        assert d1 + 2**12 * d2 == b[0] + 2**8 * b[1] + 2**16*b[2]
        for d in [d1, d2]:
            if d >= q:
                continue
            cs.append(d)
            if len(cs) == n:
                return Poly(cs)

def CBD(a, eta):
    assert len(a) == 64*eta
    b = WordsToBits(a, 8)
    cs = []
    for i in range(n):
        cs.append((sum(b[:eta]) - sum(b[eta:2*eta])) % q)
        b = b[2*eta:]
    return Poly(cs)

def XOF(seed, j, i):
    # TODO proper streaming SHAKE128
    return io.BytesIO(hashlib.shake_128(seed + bytes([j, i])).digest(length=1344))

def PRF(seed, nonce):
    # TODO proper streaming SHAKE256
    assert len(seed) == 32
    return io.BytesIO(hashlib.shake_256(seed + bytes([nonce])
        ).digest(length=2000))

def G(seed):
    h = hashlib.sha3_512(seed).digest()
    return h[:32], h[32:]

def H(msg):
    return hashlib.sha3_256(msg).digest()

def KDF(msg):
    return hashlib.shake_128(msg).digest(length=32)

class Vec:
    def __init__(self, ps):
        self.ps = tuple(ps)

    def NTT(self):
        return Vec(p.NTT() for p in self.ps)

    def InvNTT(self):
        return Vec(p.InvNTT() for p in self.ps)

    def DotNTT(self, other):
        """ Computes the dot product <self, other> in the NTT domain. """
        return sum((a.MulNTT(b) for a, b in zip(self.ps, other.ps)), Poly())

    def __add__(self, other):
        return Vec(a+b for a,b in zip(self.ps, other.ps))

    def Compress(self, d):
        return Vec(p.Compress(d) for p in self.ps)

    def Decompress(self, d):
        return Vec(p.Decompress(d) for p in self.ps)

    def Encode(self, d):
        return Encode(sum((p.cs for p in self.ps), ()), d)

    def __eq__(self, other):
        return self.ps == other.ps

def EncodeVec(vec, w):
    return Encode(sum([p.cs for p in vec.ps], ()), w)
def DecodeVec(bs, k, w):
    cs = Decode(bs, w)
    return Vec(Poly(cs[n*i:n*(i+1)]) for i in range(k))
def DecodePoly(bs, w):
    return Poly(Decode(bs, w))

class Matrix:
    def __init__(self, cs):
        """ Samples the matrix uniformly from seed rho """
        self.cs = tuple(tuple(row) for row in cs)

    def MulNTT(self, vec):
        """ Computes matrix multiplication A*vec in the NTT domain. """
        return Vec(Vec(row).DotNTT(vec) for row in self.cs)

    def T(self):
        """ Returns transpose of matrix """
        k = len(self.cs)
        return Matrix((self.cs[j][i] for j in range(k)) for i in range(k))

def sampleMatrix(rho, k):
    return Matrix([[sampleUniform(XOF(rho, j, i))
            for j in range(k)] for i in range(k)])

def sampleNoise(sigma, k, eta, offset):
    return Vec(CBD(PRF(sigma, i+offset).read(64*eta), eta) for i in range(k))

def CPAPKE_KeyGen(seed, params):
    assert len(seed) == 32
    rho, sigma = G(seed)
    A = sampleMatrix(rho, params.k)
    s = sampleNoise(sigma, params.k, params.eta1, 0)
    e = sampleNoise(sigma, params.k, params.eta1, params.k)
    sHat = s.NTT()
    eHat = e.NTT()
    tHat = A.MulNTT(sHat) + eHat
    pk = EncodeVec(tHat, 12) + rho
    sk = EncodeVec(sHat, 12)
    return (pk, sk)

def CPAPKE_Enc(pk, msg, seed, params):
    tHat = DecodeVec(pk[:-32], params.k, 12)
    rho = pk[-32:]
    A = sampleMatrix(rho, params.k)
    r = sampleNoise(seed, params.k, params.eta1, 0)
    e1 = sampleNoise(seed, params.k, eta2, params.k)
    e2 = sampleNoise(seed, 1, eta2, 2*params.k).ps[0]
    rHat = r.NTT()
    u = A.T().MulNTT(rHat).InvNTT() + e1
    v = tHat.DotNTT(rHat).InvNTT() + e2 + Poly(Decode(msg, 1)).Decompress(1)
    c1 = u.Compress(params.du).Encode(params.du)
    c2 = v.Compress(params.dv).Encode(params.dv)
    return c1 + c2

def CPAPKE_Dec(sk, ct, params):
    split = params.du * params.k * n // 8
    c1, c2 = ct[:split], ct[split:]
    u = DecodeVec(c1, params.k, params.du).Decompress(params.du)
    v = DecodePoly(c2, params.dv).Decompress(params.dv)
    sHat = DecodeVec(sk, params.k, 12)
    return (v - sHat.DotNTT(u.NTT()).InvNTT()).Compress(1).Encode(1)

def KeyGen(seed, params):
    assert len(seed) == 64
    z = seed[32:]
    pk, sk2 = CPAPKE_KeyGen(seed[:32], params)
    h = H(pk)
    return (pk, sk2 + pk + h + z)

def Enc(pk, seed, params):
    assert len(seed) == 32

    m = H(seed)
    Kbar, r = G(m + H(pk))
    ct = CPAPKE_Enc(pk, m, r, params)
    K = KDF(Kbar + H(ct))
    return (ct, K)

def Dec(sk, ct, params):
    sk2 = sk[:12 * params.k * n//8]
    pk = sk[12 * params.k * n//8 : 24 * params.k * n//8 + 32]
    h = sk[24 * params.k * n//8 + 32 : 24 * params.k * n//8 + 64]
    z = sk[24 * params.k * n//8 + 64 : 24 * params.k * n//8 + 96]
    m2 = CPAPKE_Dec(sk, ct, params)
    Kbar2, r2 = G(m2 + h)
    ct2 = CPAPKE_Enc(pk, m2, r2, params)
    if ct == ct2: # NOTE <- in production this must be done in constant time!
        return KDF(Kbar2 + H(ct))
    return KDF(z + H(ct))

# Down below are assertions used in the draft.

assert pow(zeta, 128, q) == q-1

assert smod(3325) == -4
assert smod(-3320) == 9

assert Round(.4) == 0
assert Round(.5) == 1
assert Round(-.5) == 0
assert Round(-.6) == -1

assert brv(91) == 109
assert brv(1) == 64

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

assert WordsToBits([12,45], 8) == [0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0]

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
assert noise3Test == CBD(PRF(bytes(range(32)), 37).read(3*64), 3)
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
assert noise2Test == CBD(PRF(bytes(range(32)), 37).read(2*64), 2)

#  Check NIST test vectors
