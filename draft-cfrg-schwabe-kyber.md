---
title: Kyber Post-Quantum KEM
abbrev: kyber
category: info

docname: draft-cfrg-schwabe-kyber-latest
date:
stand_alone: yes
v: 3 # TODO
# area: AREA # TODO
workgroup: None
keyword:
 - kyber
 - kem
 - post-quantum
venue:
  group: CFRG
  type: Working Group
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
  KyberV302:
    target: https://pq-crystals.org/kyber/data/kyber-specification-round3-20210804.pdf
    title: CRYSTALS-Kyber, Algorithm Specification And Supporting Documentation (version 3.02)
    author:
      -
        ins: R. Avanzi
      -
        ins: J. Bos
      -
        ins: L. Ducas
      -
        ins: E. Kiltz
      -
        ins: T. Lepoint
      -
        ins: V. Lyubashevsky
      -
        ins: J. Schanck
      -
        ins: P. Schwabe
      -
        ins: G. Seiler
      -
        ins: D. Stehle # TODO unicode in references
    date: 2021
    format:
      PDF: https://pq-crystals.org/kyber/data/kyber-specification-round3-20210804.pdf
--- abstract

This memo specifies Kyber, an IND-CCA2 secure Key Encapsulation Method.

--- middle

# Introduction

Kyber is NIST's pick for a post-quantum key agreement.

TODO #7

## Warning on stability

**NOTE** This draft is not stable and does not (yet) match the final
NIST standard expected in 2024. Currently it matches Kyber as submitted
to round 3 of the NIST PQC process. {{KyberV302}}

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

- _A_ a uniformly sampled  k by k matrix over R _and_
- _t = A s + e_, where `e` is a suitably small masking vector.

Distinguishing between such A s + e and a uniformly sampled t is the
MLWE problem.

To save space in the public key, A is recomputed deterministically from
a seed *rho*.

A ciphertext for a message m under this public key is a pair (c\_1, c\_2)
computed roughly as follows:

    c_1 = Compress(A^T r + e_1, d_u)
    c_2 = Compress(t^T r + e_2 + Decompress(m, 1), d_v)

where

- e\_1, e\_2 and r are small blinds;
- Compress(-, d) removes some information, leaving d bits per coefficient
  and Decompress is such that Compress after Decompress does nothing and
- d\_u, d\_v are scheme parameters.

TODO add a quick rationale.

To decrypt the ciphertext, one computes

    m = Compress(Decompress(c_2, d_v) - s^T Decompress(c_1, d_u), 1).

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

    a_0 + a_1 x + a_2 x^2 + ... + a_255 x^255.

With polynomial coefficients, vector and matrix indices, we will start
counting at zero.

## Operations

### Addition and multiplication

Addition of elements is componentwise. Thus

    (a_0, ..., a_255) +  (b_0, ..., b_255) = (a_0 + b_0, ..., a_255 + b_255)

where addition in each component is computed modulo q.

Multiplication is that of polynomials (convolution) with the additional rule
that x^256=-1. To wit

    (a_0, ..., a_255) \* (b_0, ..., b_255)
        = (a_0 * b_0 - a_255 * b_1 - ... - a_1 * b_255,
           a_0 * b_1 + a_1 * b_0 - a_255 * b_2 - ... - a_2 * b_255,

                ...

           a_0 * b_255 + ... + a_255 * b_0)

We will not use this schoolbook multiplication to compute the product.
Instead we will use the more efficient, number theoretic transform (NTT),
see TODO.

### Size of polynomials

For a polynomial a = (a\_0, ..., a\_255) in R, we write:

    || a || = max_i || a_i ||

Thus a polynomial is considered large if one of its components is large.

### Background on the Number Theoretic Transform (NTT)

TODO (#8) This section gives background not necessary for the implementation.
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

    a |-> (   a_0 + zeta^64 a_128,   a_1 + zeta^64 a_129,
             ...
            a_126 + zeta^64 a_254, a_127 + zeta^64 a_255,
              a_0 - zeta^64 a_128,   a_1 - zeta^64 a_129,
             ...
            a_126 - zeta^64 a_254, a_127 - zeta^64 a_255)

We can see this as 128 applications of the linear map CT\_64, where

    CT_i: (a, b) |-> (a + zeta^i b, a - zeta^i b)   modulo q

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

    GS_i: (a, b) |-> ( (a+b)/2, zeta^-i (a-b)/2 )    modulo q

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
    (NTT)_{ij} = [
                 [ 0                                  otherwise

Its inverse is called the InvNTT.

It can be computed more efficiently as described in section TODO.

Examples:

    NTT(1, 1, 0, ..., 0)   = (1, 1, ..., 1, 1)
    NTT(1, 2, 3, ..., 255) = (2429, 2845, 425, 1865, ..., 2502, 2134, 2717, 2303)

## Multiplication in NTT domain

For elements a, b in R, we write a o b for multiplication in the NTT domain.
That is: a * b = InvNTT(NTT(a) o NTT(b)). Concretely:

                [ a_i b_i + zeta^{2 brv(i >> 1) + 1} a_{i+1} b_{i+1}   if i even
    (a o b)_i = [
                [ a_{i+1} b_i + a_i b_{i+1}                            otherwise

### Dot product and matrix multiplication

We will also use "o" to denote the dot product and matrix multiplication
in the NTT. Concretely:

1. For two length k vector v and w, we write

        v o w = v_0 o w_0 + ... + v_{k-1} o w_{k-1}

2. For a k by k matrix A and a length k vector v, we have

        (A o v)_i = A_i o v,

   where A\_i denotes the (i+1)th row of the matrix A as we start
   counting at zero.

# Symmetric cryptographic primitives

Kyber makes use of cryptographic primitives PRF, XOF, KDF, H and G, where

    XOF(seed) = SHAKE-128(seed)
    PRF(seed, counter) = SHAKE-256(seed || counter)
    KDF(msg) = SHAKE-256(msg)[:32]
    H(msg) = SHA3-256(msg)
    G(msg) = (SHA3-512(msg)[:32], SHA3-512(msg)[32:])

TODO Elaborate on types and usage
TODO Stick to one?

# Operations on vectors

Recall that Compress(x, d) maps a field element x into {0, ..., 2^d-1}.
In Kyber always d <= 11 and so we can interpret Compress(x, d) as a field
element again.

In this way, we can extend Compress(-, d) to polynomials by applying
to each coefficient separately and in turn to vectors by applying
to each polynomial. That is, for a vector v and polynomial p:

    Compress(p, d)_i = Compress(p_i, d)
    Compress(v, d)_i = Compress(v_i, d)

We define Decompress(-, d) for vectors and polynomials in the same way.

# Serialization

TODO #20

## OctetsToBits
For any list of octets a\_0, ..., a\_{s-1}, we define OctetsToBits(a), which
is a list of bits of length 8s, defined by

    OctetsToBits(a)_i = ((a_(i>>3)) >> (i umod 8)) umod 2.

Example:

    OctetsToBits(12,34) = (0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0)

## Encode and Decode
For an integer 0 < w <= 12, we define Decode(a, w), which converts
any  list a of w\*l/8 octets into a list of length l with
values in {0, ..., 2^w-1} as follows.

    Decode(a, w)_i = b_{wi} + b_{wi+1} 2 + b_{wi+2} 2^2 + ... + b_{wi+w-1} 2^{w-1},

where b = OctetsToBits(a).

Encode(-, w) is the unique inverse of Decode(-, w)

### Polynomials
A polynomial p is encoded by passing its coefficients to Encode:

    EncodePoly(p, w) = Encode(p_0, p_1, ..., p_{n-1})

DecodePoly(-, w) is the unique inverse of EncodePoly(-, w).

### Vectors
A vector v of length k over R is encoded by concatenating the coefficients
in the obvious way:

    EncodeVec(v, w) = Encode((v_0)_0, ..., (v_0)_{n-1},
                             (v_1)_{0}, ..., (v_1)_{n-1},
                                    ..., (v_{k-1})_{n-1})

DecodeVec(-, w) is the unique inverse of EncodeVec(-, w).

## Sampling of polynomials

### Uniformly
The polynomials in the matrix A are sampled uniformly and deterministically
from an octet stream (XOF) using rejection sampling as follows.

Three octets b\_0, b\_1, b\_2 are read from the stream at a time. These are
interpreted as two 12-bit unsigned integers d\_1, d\_2 via

    d_1 + d_2 2^12 = b_0 + b_1 2^8 + b_2 2^16

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

#### sampleMatrix
Now, the *k* by *k* matrix *A* over *R* is derived deterministically
from a 32-octet seed *rho* using sampleUniform as follows.

    sampleMatrix(rho)_{ij} = sampleUniform(XOF(rho || octet(j) || octet(i))

That is, to derive the polynomial at the *i*th row and *j*th column,
sampleUniform is called with the 34-octet seed created by first appending
the octet *j* and then the octet *i* to *rho*. Recall that we start counting
rows and columns from zero.

As the NTT is a bijection, it does not matter whether we interpret
the polynomials of the sampled matrix in the NTT domain or not.
For efficiency, we do interpret the sampled matrix in the NTT domain.

### From a binomial distribution
Noise is sampled from a centered binomial distribution Binomial(2eta, 1/2) - eta
deterministically  as follows.

An octet array a of length 2\*eta is converted to a polynomial CBD(a, eta)

    CBD(a, eta)_i = b_{2i eta} + b_{2i eta + 1} + ... + b_{2i eta + eta-1}
                  - b_{2i eta + eta} + ... + b_{2i eta + 2eta - 1},

where b = OctetsToBits(a).

Examples:

    CBD((0, 1, 2, ..., 127), 2) = (0, 0, 1, 0, 1, 0, ..., 3328, 1, 0, 1)
    CBD((0, 1, 2, ..., 191), 3) = (0, 1, 3328, 0, 2, ..., 3328, 3327, 3328, 1)

#### sampleNoise
A *k* component small vector *v* is derived from a seed 32-octet seed *sigma*,
an offset *offset* and size *eta* as follows:

    sampleNoise(sigma, eta, offset)_i = CBD(PRF(sigma, i+offset), eta)

Recall that we start counting vector indices at zero.

# Kyber.CPAPKE

We are ready to define the IND-CPA secure Public-Key Encryption scheme that
underlies Kyber.

TODO warning about using Kyber.CPAPKE directly (#21)

## Parameters
We have already been introduced to the following parameters:

*q*
: Order of field underlying *R*.

*n*
: Length of polynomials in *R*.

*zeta*
: Primitive root of unity in GF(q), used for NTT in R.

*XOF*, *H*, *G*, *PRF*, *KDF*
: Various symmetric primitives.

*k*
: Main security parameter: the number of rows and columns in the matrix *A*.

Additionally, Kyber takes the following parameters

*eta1*, *eta2*
: Size of small coefficients used in the private key and noise vectors.

*d\_u*, *d\_v*
: How many bits to retain per coefficient of the *u* and *v* components
of the ciphertext.

TODO reference to table with values.

## Key generation
Kyber.CPAPKE.KeyGen(seed) takes a 32 octet **seed** and deterministically
produces a keypair as follows.

1. Set (rho, sigma) = G(seed).
2. Derive
    1. AHat = sampleMatrix(rho).
    2. s = sampleNoise(sigma, eta1, 0)
    3. e = sampleNoise(sigma, eta1, k)
3. Compute
    1. sHat = NTT(s)
    2. tHat = AHat o sHat + NTT(e)
4. Return
    1. publicKey = EncodeVec(tHat, 12) \|\| rho
    2. privateKey = EncodeVec(sHat, 12)

Note that in essence we're simply computing t = A s + e.

## Encryption
Kyber.CPAPKE.Enc(msg, publicKey, seed) takes a 32-octet seed,
and deterministically encrypts the 32-octet msg for the Kyber.CPAPKE public
key publicKey as follows.

1. Split publicKey into
    1. n/8\*12-octet tHatPacked
    2. 32-octet rho
2. Parse tHat = DecodeVec(tHat, 12)
3. Derive
    1. AHat = sampleMatrix(rho)
    2. r = sampleNoise(seed, eta1, 0)
    3. e\_1 = sampleNoise(seed, eta2, k)
    4. e\_2 = sampleNoise(seed, eta2, 2k)\_0
4. Compute
    1. rHat = NTT(r)
    2. u = InvNTT(AHat^T o rHat) + e\_1
    3. v = InvNTT(tHat o rHat) + e\_2 + Decompress(Decode(msg, 1), 1)
    4. c\_1 = EncodeVec(Compress(u, d\_u), d\_u)
    5. c\_2 = EncodePoly(Compress(v, d\_v), d\_v)
5. Return
    1. cipherText = c\_1 \|\| c\_2

## Decryption
Kyber.CPAPKE.Dec(cipherText, privateKey) takes a Kyber.CPAPKE private key
privateKey and decrypts a cipher text cipherText as follows.

1. Split cipherText into
    1. d\_u\*k\*n/8-octet c\_1
    2. d\_v\*n/8-octet c\_2
2. Parse
    1. u = Decompress(DecodeVec(c\_1, d\_u), d\_u)
    2. v = Decompress(DecodePoly(c\_2, d\_v), d\_v)
    3. sHat = DecodeVec(privateKey, 12)
3. Compute
    1. m = v - InvNTT(sHat o NTT(u))
4. Return
    1. plainText = EncodePoly(Compress(m))

# Kyber

Now we are ready to define Kyber itself.

## Key generation

A Kyber keypair is derived deterministically from a 64-octet seed as follows.

1. Split seed into
    1. A 32-octet z
    2. A 32-octet cpaSeed
2. Compute
    1. (cpaPublicKey, cpaPrivateKey) = Kyber.CPAPKE.KeyGen(cpaSeed)
    2. h = H(cpaPublicKey)
3. Return
    1. publicKey = cpaPublicKey
    2. privateKey = cpaPrivateKey \|\| cpaPublicKey \|\| h \|\| z

## Encapsulation

Kyber encapsulation takes a public key and a 32-octet seed and deterministically
generates a shared secret and ciphertext for the public key as follows.

1. Compute
    1. m = H(seed)
    2. (Kbar, cpaSeed) = G(m \|\| H(pk))
    3. cpaCipherText = Kyber.CPAPKE.Enc(m, publicKey, cpaSeed)
2. Return
    1. cipherText = cpaCipherText
    2. sharedSecret = KDF(KBar \|\| H(cpaCipherText))

## Decapsulation
Kyber decapsulation takes a private key and a cipher text and
returns a shared secret as follows.

1. Split privateKey into
    1. A 12\*k\*n/8-octet cpaPrivateKey
    2. A 12\*k\*n/8+32-octet cpaPublicKey
    3. A 32-octet h
    4. A 32-octet z
2. Compute
    1. m2 = Kyber.CPAPKE.Dec(cipherText, cpaPrivateKey)
    2. (KBar2, cpaSeed2) = G(m2 \|\| h)
    3. cipherText2 = Kyber.CPAPKE.Enc(m2, cpaPublicKey, cpaSeed2)
    4. K1 = KDF(KBar2 \|\| H(cipherText))
    5. K2 = KDF(z \|\| H(cipherText))
3. In constant-time, set K = K1 if cipherText == cipherText2 else set K = K2.
4. Return
    1. sharedSecret = K

## Common to all parameter sets

|Name  | Value | Description                        |
|-----:|:-----:|:-----------------------------------|
|q     | 3329  | Order of base field                |
|n     | 256   | Degree of polynomials              |
|zeta  | 17    | nth root of unity in base field    |


|Primitive| Instantiation        |
|--------:|:---------------------|
|XOF      | SHAKE-128            |
|H        | SHA3-256             |
|G        | SHA3-512             |
|PRF(s,b) | SHAKE-256(s \|\| b)  |
|KDF      | SHAKE-256            |

## Parameter sets

| Name       |Description                                                                                        |
|-----------:|:--------------------------------------------------------------------------------------------------|
| k          |Dimension of module                                                                                |
| eta1, eta2 |Size of "small" coefficients used in the private key and noise vectors.                           |
| d\_u       |How many bits to retain per coefficient of `u`, the private-key independent part of the ciphertext |
| d\_v       |How many bits to retain per coefficient of `v`, the private-key dependent part of the ciphertext.  |

|Parameter set | k |eta1|eta2|d\_u|d\_v|sec|
|-------------:|:-:|:--:|:--:|:--:|:--:|:-:|
|Kyber512      | 2 |  3 | 2  |10  |4   |I  |
|Kyber768      | 3 |  2 | 2  |10  |4   |III|
|Kyber1024     | 4 |  2 | 2  |11  |5   |V  |

# Machine-readable implementation

TODO insert kyber.py automatically (#14)

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
        # TODO #5 proper streaming SHAKE128
        return io.BytesIO(hashlib.shake_128(seed + bytes([j, i])).digest(length=1344))

    def PRF(seed, nonce):
        # TODO #5 proper streaming SHAKE256
        assert len(seed) == 32
        return io.BytesIO(hashlib.shake_256(seed + bytes([nonce])
            ).digest(length=2000))

    def G(seed):
        h = hashlib.sha3_512(seed).digest()
        return h[:32], h[32:]

    def H(msg): return hashlib.sha3_256(msg).digest()
    def KDF(msg): return hashlib.shake_256(msg).digest(length=32)

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

    def sampleNoise(sigma, eta, offset, k):
        return Vec(CBD(PRF(sigma, i+offset).read(64*eta), eta) for i in range(k))

    def CPAPKE_KeyGen(seed, params):
        assert len(seed) == 32
        rho, sigma = G(seed)
        A = sampleMatrix(rho, params.k)
        s = sampleNoise(sigma, params.eta1, 0, params.k)
        e = sampleNoise(sigma, params.eta1, params.k, params.k)
        sHat = s.NTT()
        eHat = e.NTT()
        tHat = A.MulNTT(sHat) + eHat
        pk = EncodeVec(tHat, 12) + rho
        sk = EncodeVec(sHat, 12)
        return (pk, sk)

    def CPAPKE_Enc(pk, msg, seed, params):
        assert len(msg) == 32
        tHat = DecodeVec(pk[:-32], params.k, 12)
        rho = pk[-32:]
        A = sampleMatrix(rho, params.k)
        r = sampleNoise(seed, params.eta1, 0, params.k)
        e1 = sampleNoise(seed, eta2, params.k, params.k)
        e2 = sampleNoise(seed, eta2, 2*params.k, 1).ps[0]
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

# Security Considerations

TODO Security (#18)


# IANA Considerations

TODO (#17)


--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge. (#16)
