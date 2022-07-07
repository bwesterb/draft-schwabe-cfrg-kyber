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

# The field Z\_q

Kyber is defined over Z\_q, the integers modulo q = 13\*2^8+1 = 3329.

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

Kyber is defined over a polynomial ring R = Z\_q[x]/(x^n+1)
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

# Security Considerations

TODO Security


# IANA Considerations

This document has no IANA actions.


--- back

# Acknowledgments
{:numbered="false"}

TODO acknowledge.
