---
title: "Kyber Post-Quantum KEM"
abbrev: "kyber"
category: info # TODO (#6)

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

TODO #7

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

- _A_ a uniformly sampled  k by k matrix over R _and_
- _t = A s + e_, where `e` is a suitably small masking vector.

Distinguishing between such A s + e and a uniformly sampled t is the
MLWE problem.

To save space in the public key, A is recomputed deterministically from
a seed ρ.

A ciphertext for a message m under this public key is a pair (c₁, c₂)
computed roughly as follows:

-  c₁ = Compress(A^T r + e₁, d\_u)
-  c₂ = Compress(t^T r + e₂ + Decompress(m, 1), d\_v)

where

- e₁, e₂ and r are small blinds;
- Compress(-, d) removes some information, leaving d bits per coefficient
  and Decompress is such that Compress after Decompress does nothing and
- d\_u, d\_v are scheme parameters.

TODO add a quick rationale.

To decrypt the ciphertext, one computes

> m = Compress(Decompress(c₂, d\_v) - s^T Decompress(c₁, d\_u), 1).

To define all these operations precisely, we first define the field
of coefficients for our polynomial ring; what it means to be small;
and how to compress. Then we define the polynomial ring R; its operations
and in particular the NTT. We continue with the different methods of
sampling and (de)serialization. Then, we define first Kyber.CPAPKE
and finally Kyber proper.

# The field GF(q)

Kyber is defined over GF(q) = ℤ/qℤ, the integers modulo q = 13⋅2⁸+1 = 3329.

## Size

To define the size of a field element, we need a signed modulo. For any odd m,
we write

    a smod m

for the unique integer b with (m-1)/2 < b ≤ (m-1)/2 and b = a modulo m.

To avoid confusion, for the more familiar modulo we write umod; that is

    a umod m

is the unique integer b with 0 ≤ b < m and b = a modulo m.

Now we can define the norm of a field element:

    ‖a‖ = abs(a smod q)

Examples:

     3325 smod q = -4        ‖ 3325 ‖ = 4
    -3320 smod q =  9        ‖-3320 ‖ = 9

## Compression

In several parts of the algorithm, we will need a method to compress
fied elements down into d bits. To do this, we use the following method.

For any positive integer d, integer x and integer 0 ≤ y < 2^d, we define

      Compress(x, d) = Round( (2^d / q) x ) umod 2^d
    Decompress(y, d) = Round( (q / 2^d) y )

where Round(x) rounds any fraction to the nearest integer going up with ties.

Note that in TODO we define Compress and Decompress for polynomials and vectors.

These two operations have the following properties:

 * 0 ≤ Compress(x, d) < 2^d
 * 0 ≤ Decompress(y, d) < q
 * Compress(Decompress(y, d), d) = y
 * If Decompress(Compress(x, d), d) = x', then ‖ x' - x ‖ ≤ Round(q/2^(d+1)`
 * If x = x' modulo q, then Compress(x, d) = Compress(x', d)

For implementation efficiency, these can be computed as follows.

      Compress(x, d) = Div( (x ≪ d) + q/2), d ) & ((1 ≪ d) - 1)
    Decompress(y, d) = (q⋅y + (1 ≪ (d-1))) ≫ d

where Div(x, a) = Floor(x / a).

TODO Do we want to include the proof that this is correct?
TODO Do we need to define ≫ and ≪?

# The ring R

Kyber is defined over a polynomial ring R = GF(q)\[x\]/(xⁿ+1)
where n=256 (and q=3329). Elements of R are tuples of 256 integers modulo q.
We will call them polynomials or elements interchangeably.

A tuple a = (a₀, …, a₂₅₅) represents the polynomial

    a₀ + a₁ x + a₂ x² + … + a₂₅₅ x²⁵⁵

## Operations

### Addition and multiplication

Addition of elements is componentwise. Thus

    (a₀, …, a₂₅₅) +  (b₀, …, b₂₅₅) = (a₀ + b₀, …, a₂₅₅ + b₂₅₅)

where addition in each component is computed modulo q.

Multiplication is that of polynomials (convolution) with the additional rule
that x²⁵⁶=-1. To wit

    (a₀, …, a₂₅₅) ⋅ (b₀, …, b₂₅₅)
        = (a₀ ⋅ b₀ - a₂₅₅ ⋅ b₁ - … - a₁ ⋅ b₂₅₅,
           a₀ ⋅ b₁ + a₁ ⋅ b₀ - a₂₅₅ ⋅ b₂ - … - a₂ ⋅ b₂₅₅,

                …

           a₀ ⋅ b₂₅₅ + … + a₂₅₅ ⋅ b₀)

We will not use this schoolbook multiplication to compute the product.
Instead we will use the more efficient, number theoretic transform (NTT),
see TODO.

### Size of polynomials

For a polynomial a = (a₀, …, a₂₅₅) in R, we write:

    ‖a‖ = maxᵢ ‖aᵢ‖

Thus a polynomial is considered large if one of its components is large.

### Background on the Number Theoretic Transform (NTT)

TODO (#8) This section gives background not necessary for the implementation.
     Should we keep it?

The modulus q was chosen such that 256 divides into q-1. This means that
there are ζ with

    ζ¹²⁸ = -1  modulo  q

With such a ζ, we can almost completely split the polynomial x²⁵⁶+1
used to define R over GF(q):

    x²⁵⁶ + 1 = x²⁵⁶ - ζ¹²⁸
             = (x¹²⁸ - ζ⁶⁴)(x¹²⁸ + ζ⁶⁴)
             = (x¹²⁸ - ζ⁶⁴)(x¹²⁸ - ζ¹⁹²)
             = (x⁶⁴ - ζ³²)(x⁶⁴ + ζ³²)(x⁶⁴ - ζ⁹⁶)(x⁶⁴ + ζ⁹⁶)

                …

             = (x² - ζ)(x² + ζ)(x² - ζ⁶⁵)(x² + ζ⁶⁵) ⋯ (x² - ζ¹²⁷)(x² + ζ¹²⁷)

Note that the powers of ζ that appear in the second, fourth, …, and final
lines are in binary:

    0100000 1100000
    0010000 1010000 0110000 1110000
    0001000 1001000 0101000 1101000 0011000 1011000 0111000 1111000
                …
    0000001 1000001 0100001 1100001 0010001 1010001 0110001 … 1111111

That is: brv(2), brv(3), brv(4), …, where brv(x) denotes the 7-bit
bitreversal of x. The final line is brv(64), brv(65), …, brv(127).

These polynomials x² ± ζⁱ are irreducible and coprime, hence by
the Chinese Remainder Theorem for commutative rings, we know

    R = GF(q)[x]/(x²⁵⁶+1) -> GF(q)[x]/(x²-ζ) x … x GF(q)[x]/(x²+ζ¹²⁷)

given by a ↦ ( a mod x² - ζ, …, a mod x² + ζ¹²⁷ ) is an isomorphism.
This is the Number Theoretic Transform (NTT). Multiplication on the right is
much easier: it's almost componentwise, see section TODO.

A propos, the the constant factors that appear in the moduli in order
can be computed efficiently as follows (all modulo q):

    -ζ    = -ζ^brv(64)  = -ζ^{1 + 2 brv(0)}
     ζ    =  ζ^brv(64)  = -ζ^{1 + 2 brv(1)}
    -ζ⁶⁵  = -ζ^brv(65)  = -ζ^{1 + 2 brv(2)}
     ζ⁶⁵  =  ζ^brv(65)  = -ζ^{1 + 2 brv(3)}
    -ζ³³  = -ζ^brv(66)  = -ζ^{1 + 2 brv(4)}
     ζ³³  =  ζ^brv(66)  = -ζ^{1 + 2 brv(5)}

                 …§

    -ζ¹²⁷ = -ζ^brv(127) = -ζ^{1 + 2 brv(126)}
     ζ¹²⁷ =  ζ^brv(127) = -ζ^{1 + 2 brv(127)}

To compute a multiplication in R efficiently, one can first use the
NTT, to go to the rigth; compute the multiplication there and move
back with the inverse NTT.

The NTT can be computed efficiently by performing each binary split
of the polynomial separately as follows:

    a ↦ ( a mod x¹²⁸ - ζ⁶⁴, a mod x¹²⁸ + ζ⁶⁴ ),
      ↦ ( a mod  x⁶⁴ - ζ³², a mod  x⁶⁴ + ζ³²,
          a mod  x⁶⁴ - ζ⁹⁶, a mod  x⁶⁴ + ζ⁹⁶ ),

        et cetera

If we concatenate the resulting coefficients, expanding the definitions,
for the first step we get:

    a |-> (   a₀ + ζ⁶⁴ a₁₂₈,   a₁ + ζ⁶⁴ a₁₂₉,
                …
            a₁₂₆ + ζ⁶⁴ a₂₅₄, a₁₂₇ + ζ⁶⁴ a₂₅₅,
              a₀ - ζ⁶⁴ a₁₂₈,   a₁ - ζ⁶⁴ a₁₂₉,
                …
            a₁₂₆ - ζ⁶⁴ a₂₅₄, a₁₂₇ - ζ⁶⁴ a₂₅₅ )

We can see this as 128 applications of the linear map CT₆₄, where

    CTᵢ: (a, b) |-> (a + ζⁱ b, a - ζⁱ b)   modulo q

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
row groups respectively. The appropriate power of ζ in the first
level is brv(1)=64. The second level has brv(2) and brv(3) as powers
of ζ for the top and bottom row group respectively, and so on.

The CTᵢ is known as a Cooley-Tukey butterfly. Its inverse is given
by the Gentleman-Sande butterfly:

    GSᵢ: (a, b) |-> ( (a+b)/2, ζ^-i (a-b)/2 )    modulo q

The inverse NTT can be computed by replacing CSᵢ by GSᵢ and flipping
the diagram horizontally.

#### Optimization notes
The modular divisions by two in the InvNTT can be collected into a
single modular division by 128.

ζ^-i can be computed as -ζ^(128-i), which allows one to use the same
precomputed table of powers of ζ for both the NTT and InvNTT.

TODO Montgomery, Barrett and https://eprint.iacr.org/2020/1377.pdf
TODO perhaps move this elsewhere?

# NTT and InvNTT

As primitive 256th root of unity we use ζ=17.

As before, brv(i) denotes the 7-bit bitreversal of i, so brv(1)=64
and brv(91)=109.

The NTT is a linear bijection R -> R given by the matrix:

                  [ ζ^{ (2 brv(i ≫ 1) + 1) j }     if i=j modulo 2
    (NTT)\_{ij} = [
                  [ 0                               otherwise

Its inverse is called the InvNTT.

It can be computed more efficiently as described in section TODO.

Examples:

    NTT(1, 1, 0, …, 0)   = (1, 1, …, 1, 1)
    NTT(1, 2, 3, …, 255) = (2429, 2845, 425, 1865, …, 2502, 2134, 2717, 2303)

## Multiplication in NTT domain

For elements a, b in R, we write a o b for multiplication in the NTT domain.
That is: a ⋅ b = InvNTT(NTT(a) o NTT(b)). Concretely:

              [ aᵢ bᵢ + ζ^{2 brv(i ≫ 1) + 1} aᵢ₊₁ bᵢ₊₁   if i even
    (a o b)ᵢ= [
              [ aᵢ₊₁ bᵢ + aᵢ bᵢ₊₁                         otherwise

# Symmetric cryptographic primitives
Kyber makes use of cryptographic primitives PRF, XOF, KDF, H and G, where

    XOF(seed) = SHAKE-128(seed)
    PRF(seed, counter) = SHAKE-256(seed ‖ counter)
    KDF(msg) = SHAKE-256(msg)[:32]
    H(msg) = SHA3-256(msg)
    G(msg) = (SHA3-512(msg)[:32], SHA3-512(msg)[32:])

TODO Elaborate on types and usage
TODO Stick to one?

# Serialization

TODO #20

## OctetsToBits
For any list of octets a₀, …, aₛ₋₁, we define OctetsToBits(a), which
is a list of bits of length 8s, defined by

    OctetsToBits(a)ᵢ = ((a\_(i≫3)) ≫ (i umod 8)) umod 2.

Example:

    OctetsToBits(12,34) = (0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0)

## Encode and Decode
For an integer 0 < w ≤ 12, we define Decode(a, w), which converts
a list a of 32w octets into a polynomial with coefficients in {0, …, 2^w-1}
as follows.

    Decode(a, w)ᵢ = b\_{wi} + b\_{wi+1} 2 + b\_{wi+2} 2² + … + b\_{wi+w-1} 2^{w-1},

where b = OctetsToBits(a).

Encode(-, w) is the unique inverse of Decode(-, w)

## Sampling of polynomials

### Uniformly
The polynomials in the matrix A are sampled uniformly and deterministically
from an octet stream (XOF) using rejection sampling as follows.

Three octets b₀, b₁, b₂ are read from the stream at a time. These are
interpreted as two 12-bit unsigned integers d₁, d₂ via

    d₁ + d₂ 2¹² = b₀ + b₁ 2⁸ + b₂ 2¹⁶

This creates a stream of 12-bit `d`s. Of these, the elements ≥ q are
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

    sampleUniform(SHAKE-128('')) = (3199, 697, 2212, 2302, …, 255, 846, 1)

### From a binomial distribution
Noise is sampled from a centered binomial distribution Binomial(2η, 1/2) - η
deterministically  as follows.

An octet array a of length 2η is converted to a polynomial CBD(a, η)

    CBD(a, η)ᵢ = b\_{2i η} + b\_{2i η + 1} + … + b\_{2i η + η-1}
                  - b\_{2i η + η} + … + b\_{2i η + 2η - 1},

where b = OctetsToBits(a).

Examples:

    CBD((0, 1, 2, …, 127), 2) = (0, 0, 1, 0, 1, 0, …, 3328, 1, 0, 1)
    CBD((0, 1, 2, …, 191), 3) = (0, 1, 3328, 0, 2, …, 3328, 3327, 3328, 1)


# Kyber.CPAPKE

We are ready to define the IND-CPA secure Public-Key Encryption scheme that
underlies Kyber.

## Key generation



# Parameters

## Common to all parameter sets

|Name  | Value | Description                        |
|-----:|:-----:|:-----------------------------------|
|q     | 3329  | Order of base field                |
|n     | 256   | Degree of polynomials              |
|ζ     | 17    | nth root of unity in base field    |


|Primitive| Instantiation        |
|--------:|:---------------------|
|XOF      | SHAKE-128            |
|H        | SHA3-256             |
|G        | SHA3-512             |
|PRF(s,b) | SHAKE-256(s ‖ b)  |
|KDF      | SHAKE-256            |

## Parameter sets

| Name       |Description                                                                                        |
|-----------:|:--------------------------------------------------------------------------------------------------|
| k          |Dimension of module                                                                                |
| η₁, η₂     |Size of "small" coefficients used in the private key  and noise vectors.                           |
| d\_u       |How many bits to retain per coefficient of `u`, the private-key independent part of the ciphertext |
| d\_v       |How many bits to retain per coefficient of `v`, the private-key dependent part of the ciphertext.  |

|Parameter set | k | η₁ | η₂ |d\_u|d\_v|sec|
|-------------:|:-:|:--:|:--:|:--:|:--:|:-:|
|Kyber512      | 2 |  3 | 2  |10  |4   | Ⅰ |
|Kyber768      | 3 |  2 | 2  |10  |4   | Ⅲ |
|Kyber1024     | 4 |  2 | 2  |11  |5   | Ⅴ |

# Machine-readable implementation

TODO insert kyber.py automatically (#14)

# Security Considerations

TODO Security (#18)


# IANA Considerations

TODO (#17)


--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge. (#16)
