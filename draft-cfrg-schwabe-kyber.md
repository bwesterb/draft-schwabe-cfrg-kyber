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

Note that the powers of zeta that appear, from the third line down,
are in binary:

    010000 110000
    001000 101000 011000 111000
    000100 100100 010100 110100 001100 101100 011100 111100
                ...

That is: brv(2), brv(3), brv(4), ..., where brv(x) denotes the 7-bit
bitreversal of x.

These polynomials x^2 +- zeta^i are irreducible and coprime, hence by
the Chinese Remainder Theorem for commutative rings, we know

    R = GF(q)[x]/(x^256+1) -> GF(q)[x]/(x^2-zeta) x ... x GF(q)[x]/(x^2+zeta^127)

given by a |-> ( a mod x^2 - zeta, ..., a mod x^2 + zeta^127 ) is an isomorphism.
This is the Number Theoretic Transform. Multiplication on the right is
much easier: it's almost componentwise. Thus to compute a multiplication
in R efficiently, one can first use this isomorphism, the NTT, to go
to the rigth; compute the multiplication there and move back with the
inverse NTT.

The NTT can be computed efficiently by performing each binary split
of the polynomial separately as follows:

    a |-> ( a mod x^128 - zeta^64, a mod x^128 + zeta^64),
      |-> ( a mod x^64 - zeta^32, a mod x^64 + zeta^32,
            a mod x^64 - zeta^96, a mod x^64 + zeta^96)

        et cetera

If we concatenate the resulting coefficients, expanding the definitions,
for the first step we get:

    a |-> ( a\_0 + zeta^64 a\_128, a\_1 + zeta^64 a\_129,
             ...
            a\_126 + zeta^64 a\_254, a\_127 + zeta^64 a\_255,
            a\_0 - zeta^64 a\_128, a\_1 - zeta^64 a\_129,
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

This CT\_i is known as a Cooley-Tukey butterfly. Its inverse is given
by the Gentleman-Sande butterfly:

    GS\_i: (a, b) |-> ( (a+b)/2, zeta^i(a-b)/2 )    modulo q

The inverse NTT can be computed by replacing CS\_i by GS\_i and flipping
the diagram horizontally.

# NTT and InvNTT

Define zeta=17. 


# Parameters

## Common to all parameter sets

    Name    Value   Reference
    -----------------------------------
    q       3329    See section TODO
    zeta    17      See section TODO


# Security Considerations

TODO Security


# IANA Considerations

This document has no IANA actions.


--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
