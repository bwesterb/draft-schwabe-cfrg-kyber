from math import floor

q = 3329
nBits = 8
zeta = 17

n = 2**nBits
inv2 = (q+1)//2 # inverse of 2

assert pow(zeta, 128, q) == q-1

def smod(x):
    r = x % q
    if r > (q-1)//2:
        r -= q
    return r

assert smod(3325) == -4
assert smod(-3320) == 9

# Rounds to nearest integer with ties going up
def Round(x):
    return int(floor(x + 0.5))

assert Round(.4) == 0
assert Round(.5) == 1
assert Round(-.5) == 0
assert Round(-.6) == -1

def Compress(x, d):
    return Round((2**d / q) * x) % (2**d)

def Decompress(y, d):
    assert 0 <= y and y <= 2**d
    return Round((q / 2**d) * y)

def brv(x):
    """ Reverses a 7-bit number """
    return int(''.join(reversed(bin(x)[2:].zfill(nBits-1))), 2)

assert brv(91) == 109
assert brv(1) == 64

class Poly:
    def __init__(self, cs=None):
        self.cs = (0,)*n if cs is None else tuple(cs)

    def __add__(self, other):
        return Poly((a+b) % q for a,b in zip(self.cs, other.cs))

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

p2 = Poly([1]*256).NTT()
p1 = Poly([1,0,1]+[0]*253).NTT()
print(p1.MulNTT(p2).InvNTT())
