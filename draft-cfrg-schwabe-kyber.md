---
title: "Kyber Post-Quantum KEM"
abbrev: "kyber"
category: info # TODO

docname: draft-cfrg-schwabe-kyber-latest
submissiontype: IETF
number:
date:
consensus: true # TODO
v: 3 # TODO
# area: AREA # TODO
# workgroup: WG Working Group
keyword:
 - kyber
 - kem
 - post-quantum
venue:
#  group: CFRG
#  type: Working Group
#  mail: WG@example.com  # TODO
#  arch: https://example.com/WG # TODO
  github: "bwesterb/draft-schwabe-cfrg-kyber"
  latest: "https://bwesterb.github.io/draft-schwabe-cfrg-kyber/draft-cfrg-schwabe-kyber.html"

author:
 -
    fullname: Peter Schwabe
    organization: MPI-SPI & Radboud University
    email: peter@cryptojedi.org
 -
    fullname: Bas Westerbaan
    organization: Cloudflare
    email: bas@cloudflare.com

normative:

informative:


--- abstract

This memo specifies Kyber, an IND-CCA2 secure Key Encapsulation Method.


--- middle

# Introduction

Kyber is NIST's pick for a post-quantum key agreement.

TODO

## Warning on stability

**NOTE** This draft is not stable and does not (yet) match the final
NIST standard expected in 2024. Currently it matches Kyber as submitted
to round 3 of the NIST PQC process.

# Conventions and Definitions

{::boilerplate bcp14-tagged}

# Overview

Kyber is an IND-CCA2 secure KEM. It is constructed by applying a
Fujisaki--Okamato style transformation on Kyber.CPAPKE, which is
the underlying IND-CPA secure Public Key Encryption scheme.
We cannot use Kyber.CPAPKE directly, as its ciphertexts are malleable.

                       F.O. transform
    Kyber.CPAPKE   ---------------------->   Kyber
       IND-CPA                              IND-CCA2

Kyber.CPAPKE is a lattice-based scheme. More precisely, its security
is based on the learning-with-errors problem in module lattices (MLWE).
The underlying polynomial ring R (defined in TODO) is chosen such that
multiplication is very fast using the number theoretic transform
(NTT, see TODO).

A Kyber.CPAPKE private key is a vector *s* over R of length k which is
_small_ in a particular way. Here `k` is a security parameter akin to the
size of a prime modulus. For Kyber512, which targets AES-128's security level,
the value of k is 2.

The public key consists of two values:

    - *A* a uniformly sampled  k by k matrix over R _and_
    - *t* = A s + e, where `e` is a suitably small masking vector.

Distinguishing between such A s + e and a uniformly sampled t is the
MLWE problem.

To save space in the public key, A is recomputed deterministically from
a seed *rho*.

A ciphertext for a message m under this public key is a pair (c\_1, c\_2)
computed roughly as follows:

    c\_1 = Compress(A^T r + e\_1, d\_u)
    c\_2 = Compress(t^T r + e\_2 + Decompress(m, 1), d\_v)

where

    - e\_1, e\_2 and r are small blinds;
    - Compress(-, d) removes some information, leaving d bits per coefficient
      and Decompress is such that Compress after Decompress does nothing and
    - d\_u, d\_v are scheme parameters.

TODO add a quick rationale.

To decrypt the ciphertext, one computes

    m = Compress(Decompress(c\_2, d\_v) - s^T Decompress(c\_1, d\_u), 1).

To define all these operations precisely, we first define the field
of coefficients for our polynomial ring; what it means to be small;
and how to compress. Then we define the polynomial ring R; its operations
and in particular the NTT. We continue with the different methods of
sampling and (de)serialization. Then, we define first Kyber.CPAPKE
and finally Kyber proper.

# The field GF(q)

Kyber is defined over GF(q) = Z/qZ, the integers modulo q = 13\*2^8+1 = 3329.

## Size

To define the size of a field element, we need a signed modulo. For any odd m,
we write

    a smod m

for the unique integer b with (m-1)/2 < b <= (m-1)/2 and b = a modulo m.

To avoid confusion, for the more familiar modulo we write umod; that is

    a umod m

is the unique integer b with 0 <= b < m and b = a modulo m.

Now we can define the norm of a field element:

    || a || = abs(a smod q)

Examples:

     3325 smod q = -4        ||  3325 || = 4
    -3320 smod q =  9        || -3320 || = 9

## Compression

In several parts of the algorithm, we will need a method to compress
fied elements down into d bits. To do this, we use the following method.

For any positive integer d, integer x and integer 0 <= y < 2^d, we define

      Compress(x, d) = Round( (2^d / q) x ) umod 2^d
    Decompress(y, d) = Round( (q / 2^d) y )

where Round(x) rounds any fraction to the nearest integer going up with ties.

Note that in TODO we define Compress and Decompress for polynomials and vectors.

These two operations have the following properties:

 * `0 <= Compress(x, d) < 2^d`
 * `0 <= Decompress(y, d) < q`
 * `Compress(Decompress(y, d), d) = y`
 * If `Decompress(Compress(x, d), d) = x'`, then `|| x' - x || <= Round(q/2^(d+1))`
 * If `x = x' modulo q`, then `Compress(x, d) = Compress(x', d)`

For implementation efficiency, these can be computed as follows.

      Compress(x, d) = Div( (x << d) + q/2), d ) & ((1 << d) - 1)
    Decompress(y, d) = (q*y + (1 << (d-1))) >> d

where Div(x, a) = Floor(x / a).

TODO Do we want to include the proof that this is correct?
TODO Do we need to define >> and <<?

# The ring R

Kyber is defined over a polynomial ring R = GF(q)[x]/(x^n+1)
where n=256 (and q=3329). Elements of R are tuples of 256 integers modulo q.
We will call them polynomials or elements interchangeably.

A tuple a = (a\_0, ..., a\_255) represents the polynomial

    a\_0 + a\_1 x + a\_2 x^2 + ... + a\_255 x^255.

## Operations

### Addition and multiplication

Addition of elements is componentwise. Thus

    (a\_0, ..., a\_255) +  (b\_0, ..., b\_255) = (a\_0 + b\_0, ..., a\_255 + b\_255)

where addition in each component is computed modulo q.

Multiplication is that of polynomials (convolution) with the additional rule
that x^256=-1. To wit

    (a\_0, ..., a\_255) \* (b\_0, ..., b\_255)
        = (a\_0 * b\_0 - a\_255 * b\_1 - ... - a\_1 * b\_255,
           a\_0 * b\_1 + a\_1 * b\_0 - a\_255 * b\_2 - ... - a\_2 * b\_255,

                ...

           a\_0 * b\_255 + ... + a\_255 * b\_0)

We will not use this schoolbook multiplication to compute the product.
Instead we will use the more efficient, number theoretic transform (NTT),
see TODO.

### Size of polynomials

For a polynomial a = (a\_0, ..., a\_255) in R, we write:

    || a || = max_i || a_i ||

Thus a polynomial is considered large if one of its components is large.

### Background on the Number Theoretic Transform (NTT)

TODO This section gives background not necessary for the implementation.
     Should we keep it?

The modulus q was chosen such that 256 divides into q-1. This means that
there are zeta with

    zeta^128 = -1  modulo  q

With such a zeta, we can almost completely split the polynomial x^256+1
used to define R over GF(q):

    x^256 + 1 = x^256 - zeta^128
              = (x^128 - zeta^64)(x^128 + zeta^64)
              = (x^128 - zeta^64)(x^128 - zeta^192)
              = (x^64 - zeta^32)(x^64 + zeta^32)
                    (x^64 - zeta^96)(x^64 + zeta^96)

                ...

              = (x^2 - zeta)(x^2 + zeta)(x^2 - zeta^65)(x^2 + zeta^65)
                        ... (x^2 - zeta^127)(x^2 + zeta^127)

Note that the powers of zeta that appear in the second, fourth, ...,
and final lines are in binary:

    0100000 1100000
    0010000 1010000 0110000 1110000
    0001000 1001000 0101000 1101000 0011000 1011000 0111000 1111000
                ...
    0000001 1000001 0100001 1100001 0010001 1010001 0110001 ... 1111111

That is: brv(2), brv(3), brv(4), ..., where brv(x) denotes the 7-bit
bitreversal of x. The final line is brv(64), brv(65), ..., brv(127).

These polynomials x^2 +- zeta^i are irreducible and coprime, hence by
the Chinese Remainder Theorem for commutative rings, we know

    R = GF(q)[x]/(x^256+1) -> GF(q)[x]/(x^2-zeta) x ... x GF(q)[x]/(x^2+zeta^127)

given by a |-> ( a mod x^2 - zeta, ..., a mod x^2 + zeta^127 ) is an isomorphism.
This is the Number Theoretic Transform (NTT). Multiplication on the right is
much easier: it's almost componentwise, see section TODO.

A propos, the the constant factors that appear in the moduli in order
can be computed efficiently as follows (all modulo q):

    -zeta     = -zeta^brv(64)  = -zeta^{1 + 2 brv(0)}
     zeta     =  zeta^brv(64)  = -zeta^{1 + 2 brv(1)}
    -zeta^65  = -zeta^brv(65)  = -zeta^{1 + 2 brv(2)}
     zeta^65  =  zeta^brv(65)  = -zeta^{1 + 2 brv(3)}
    -zeta^33  = -zeta^brv(66)  = -zeta^{1 + 2 brv(4)}
     zeta^33  =  zeta^brv(66)  = -zeta^{1 + 2 brv(5)}

                 ...

    -zeta^127 = -zeta^brv(127) = -zeta^{1 + 2 brv(126)}
     zeta^127 =  zeta^brv(127) = -zeta^{1 + 2 brv(127)}

To compute a multiplication in R efficiently, one can first use the
NTT, to go to the rigth; compute the multiplication there and move
back with the inverse NTT.

The NTT can be computed efficiently by performing each binary split
of the polynomial separately as follows:

    a |-> ( a mod x^128 - zeta^64, a mod x^128 + zeta^64 ),
      |-> ( a mod  x^64 - zeta^32, a mod  x^64 + zeta^32,
            a mod  x^64 - zeta^96, a mod  x^64 + zeta^96 ),

        et cetera

If we concatenate the resulting coefficients, expanding the definitions,
for the first step we get:

    a |-> (   a\_0 + zeta^64 a\_128,   a\_1 + zeta^64 a\_129,
             ...
            a\_126 + zeta^64 a\_254, a\_127 + zeta^64 a\_255,
              a\_0 - zeta^64 a\_128,   a\_1 - zeta^64 a\_129,
             ...
            a\_126 - zeta^64 a\_254, a\_127 - zeta^64 a\_255)

We can see this as 128 applications of the linear map CT\_64, where

    CT\_i: (a, b) |-> (a + zeta^i b, a - zeta^i b)   modulo q

for the appropriate i in the following order, pictured in the case of n=16:

    -x----------------x--------x---
    -|-x--------------|-x------|-x-
    -|-|-x------------|-|-x----x-|-
    -|-|-|-x----------|-|-|-x----x-
    -|-|-|-|-x--------x-|-|-|--x---
    -|-|-|-|-|-x--------x-|-|--|-x-
    -|-|-|-|-|-|-x--------x-|--x-|-
    -|-|-|-|-|-|-|-x--------x----x-
    -x-|-|-|-|-|-|-|--x--------x---
    ---x-|-|-|-|-|-|--|-x------|-x-
    -----x-|-|-|-|-|--|-|-x----x-|-
    -------x-|-|-|-|--|-|-|-x----x-
    ---------x-|-|-|--x-|-|-|--x---
    -----------x-|-|----x-|-|--|-x-
    -------------x-|------x-|--x-|-
    ---------------x--------x----x-

For n=16 there are 3 levels with 1, 2 and 4 row groups respectively.
For the full n=256, there are 7 levels with 1, 2, 4, 8, 16, 32 and 64
row groups respectively. The appropriate power of zeta in the first
level is brv(1)=64. The second level has brv(2) and brv(3) as powers
of zeta for the top and bottom row group respectively, and so on.

The CT\_i is known as a Cooley-Tukey butterfly. Its inverse is given
by the Gentleman-Sande butterfly:

    GS\_i: (a, b) |-> ( (a+b)/2, zeta^-i (a-b)/2 )    modulo q

The inverse NTT can be computed by replacing CS\_i by GS\_i and flipping
the diagram horizontally.

#### Optimization notes
The modular divisions by two in the InvNTT can be collected into a
single modular division by 128.

zeta^-i can be computed as -zeta^(128-i), which allows one to use the same
precomputed table of powers of zeta for both the NTT and InvNTT.

TODO Montgomery, Barrett and https://eprint.iacr.org/2020/1377.pdf
TODO perhaps move this elsewhere?

# NTT and InvNTT

As primitive 256th root of unity we use zeta=17.

As before, brv(i) denotes the 7-bit bitreversal of i, so brv(1)=64
and brv(91)=109.

The NTT is a linear bijection R -> R given by the matrix:

                  [ zeta^{ (2 brv(i >> 1) + 1) j }     if i=j modulo 2
    (NTT)\_{ij} = [
                  [ 0                                  otherwise

Its inverse is called the InvNTT.

It can be computed more efficiently as described in section TODO.

Examples:

    NTT(1, 1, 0, ..., 0)   = (1, 1, ..., 1, 1)
    NTT(1, 2, 3, ..., 255) = (2429, 2845, 425, 1865, ..., 2502, 2134, 2717, 2303)

## Multiplication in NTT domain

For elements a, b in R, we write a o b for multiplication in the NTT domain.
That is: a * b = InvNTT(NTT(a) o NTT(b)). Concretely:

                 [ a\_i b\_i + zeta^{2 brv(i >> 1) + 1} a\_{i+1} b\_{i+1}   if i even
    (a o b)\_i = [
                 [ a\_{i+1} b\_i + a\_i b\_{i+1}                            otherwise

# Symmetric cryptographic primitives
Kyber makes use of cryptographic primitives PRF, XOF, KDF, H and G, where

    XOF(seed) = SHAKE-128(seed)
    PRF(seed, counter) = SHAKE-256(seed || counter)
    KDF(msg) = SHAKE-256(msg)[:32]
    H(msg) = SHA3-256(msg)
    G(msg) = (SHA3-512(msg)[:32], SHA3-512(msg)[32:])

TODO Elaborate on types and usage
TODO Stick to one?

# Serialization

## OctetsToBits
For any list of octets a\_0, ..., a\_{s-1}, we define OctetsToBits(a), which
is a list of bits of length 8s, defined by

    OctetsToBits(a)\_i = ((a\_(i>>3)) >> (i umod 8)) umod 2.

Example:

    OctetsToBits(12,34) = (0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0)

## Encode and Decode
For an integer 0 < w <= 12, we define Decode(a, w), which converts
a list a of 32w octets into a polynomial with coefficients in {0, ..., 2^w-1}
as follows.

    Decode(a, w)\_i = b\_{wi} + b\_{wi+1} 2 + b\_{wi+2} 2^2 + ... + b\_{wi+w-1} 2^{w-1},

where b = OctetsToBits(a).

Encode(-, w) is the unique inverse of Decode(-, w)

## Sampling of polynomials

### Uniformly
The polynomials in the matrix A are sampled uniformly and deterministically
from an octet stream (XOF) using rejection sampling as follows.

Three octets b\_0, b\_1, b\_2 are read from the stream at a time. These are
interpreted as two 12-bit unsigned integers d\_1, d\_2 via

    d\_1 + d\_2 2^12 = b\_0 + b\_1 2^8 + b\_2 2^16

This creates a stream of 12-bit `d`s. Of these, the elements >= q are
ignored. From the resultant stream, the coefficients of the polynomial
are taken in order. In Python:

    def sampleUniform(stream):
        cs = []
        while True:
            b = stream.read(3)
            d1 = b[0] + 256*(b[1] % 16)
            d2 = (b[1] >> 4) + 16*b[2]
            for d in [d1, d2]:
                if d >= q: continue
                cs.append(d)
                if len(cs) == n: return Poly(cs)

Example:

    sampleUniform(SHAKE-128('')) = (3199, 697, 2212, 2302, ..., 255, 846, 1)

### From a binomial distribution
Noise is sampled from a centered binomial distribution Binomial(2eta, 1/2) - eta
deterministically  as follows.

An octet array a of length 2\*eta is converted to a polynomial CBD(a, eta)

    CBD(a, eta)\_i = b\_{2i eta} + b\_{2i eta + 1} + ... + b\_{2i eta + eta-1}
                  - b\_{2i eta + eta} + ... + b\_{2i eta + 2eta - 1},

where b = OctetsToBits(a).

Examples:

    CBD((0, 1, 2, ..., 127), 2) = (0, 0, 1, 0, 1, 0, ..., 3328, 1, 0, 1)
    CBD((0, 1, 2, ..., 191), 3) = (0, 1, 3328, 0, 2, ..., 3328, 3327, 3328, 1)


# Kyber.CPAPKE

We are ready to define the IND-CPA secure Public-Key Encryption scheme that
underlies Kyber.

## Key generation





# Parameters

## Common to all parameter sets

    Name    Value   Description
    -------------------------------------------------------------------------
    q       3329    Order of base field
    n       256     Degree of polynomials
    zeta    17      nth root of unity in base field

    XOF         SHAKE-128
    H           SHA3-256
    G           SHA3-512
    PRF(s,b)    SHAKE-256(s || b)
    KDF         SHAKE-256

## Parameter sets

    Name        Description
    --------------------------------------------------------------------------
    k           Dimension of module
    eta1, eta2  Size of "small" coefficients used in the private key
                and noise vectors.
    d\_u        How many bits to retain per coefficient of `u`, the
                private-key independent part of the ciphertext.
    d\_v        How many bits to retain per coefficient of `v`, the
                private-key dependent part of the ciphertext.

    Parameter set   k eta1 eta2 d\_u d\_v sec
    --------------------------------------
    Kyber512        2   3   2   10  4   I
    Kyber768        3   2   2   10  4   III
    Kyber1024       4   2   2   11  5   V

# Machine-readable implementation

TODO insert kyber.py automatically

# Security Considerations

TODO Security


# IANA Considerations

This document has no IANA actions.


--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
