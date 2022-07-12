---
###
# Internet-Draft Markdown Template
#
# For initial setup, you only need to edit the first block of fields.
# Only "title" needs to be changed; delete "abbrev" if your title is short.
# Any other content can be edited, but be careful not to introduce errors.
# Some fields will be set automatically during setup if they are unchanged.
#
# Don't include "-00" or "-latest" in the filename.
# Labels in the form draft-<yourname>-<workgroup>-<name>-latest are used by
# the tools to refer to the current version; see "docname" for example.
#
# This template uses kramdown-rfc: https://github.com/cabo/kramdown-rfc
# You can replace the entire file if you prefer a different format.
# Change the file extension to match the format (.xml for XML, etc...)
#
###
title: "Kyber Post-Quantum KEM"
abbrev: "kyber"
category: info

docname: draft-cfrg-schwabe-kyber
submissiontype: IETF
number:
date:
consensus: true
v: 3
area: AREA
workgroup: WG Working Group
keyword:
 - kyber
 - kem
 - post-quantum
venue:
  group: CFRG
  type: Working Group
  mail: WG@example.com  # todo
  arch: https://example.com/WG
  github: USER/REPO
  latest: https://example.com/LATEST

author:
 -
    fullname: Peter Schwabe
    organization: todo
    email: todo
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


# Conventions and Definitions

{::boilerplate bcp14-tagged}

# Overview

TODO

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

 * 0 <= Compress(x, d) < 2^d
 * 0 <= Decompress(y, d) < q
 * Compress(Decompress(y, d), d) = y
 * If Decompress(Compress(x, d), d) = x', then || x' - x || <= Round(q/2^(d+1))
 * If x = x' modulo q, then Compress(x, d) = Compress(x', d)

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

# Serialization

## OctetsToBits
For any list of octets a\_0, ..., a\_{s-1}, we define OctetsToBits(a), which
is a list of bits of length 8s, defined by

    OctetsToBits(a)\_i = ((a\_(i>>3)) >> (i umod 8)) umod 2.

## Encode\_w and Decode\_w
For an integer 0 < w <= 12, we define Decode\_w(a), which converts
a list of 32w octets into a polynomial with coefficients in {0, ..., 2^w-1}
as follows.

    Decode\_w(a)\_i = b\_{wi} + b\_{wi+1} 2 + b\_{wi+2} 2^2 + ... + b\_{wi+w-1} 2^{w-1},

where b = OctetsToBits(a).

Encode\_w is the unique inverse of Decode\_w.

# Kyber.CPAPKE

We are ready to define the IND-CPA secure Public-Key Encryption scheme that
underlies Kyber.

## Key generation





# Parameters

## Common to all parameter sets

    Name        Value
    -----------------------------------
    q           3329
    n           256
    zeta        17

    XOF         SHAKE-128
    H           SHA3-256
    G           SHA3-512    
    PRF(s,b)    SHAKE-256(s || b)
    KDF         SHAKE-256
    


# Security Considerations

TODO Security


# IANA Considerations

This document has no IANA actions.


--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
