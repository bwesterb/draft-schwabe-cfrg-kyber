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

class Poly:
    def __init__(self, cs=None):
        self.cs = (0,)*n if cs is None else tuple(cs)

    def __add__(self, other):
        return Poly((a+b) % q for a,b in zip(self.cs, other.cs))

    def __str__(self):
        return f"Poly({self.cs}"

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

print(Poly(range(n)).NTT().InvNTT())
