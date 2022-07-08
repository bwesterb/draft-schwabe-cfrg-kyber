from math import floor

q = 3329
n = 256
zeta = 17

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

