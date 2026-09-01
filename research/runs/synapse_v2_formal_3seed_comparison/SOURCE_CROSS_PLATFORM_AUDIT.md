# Synapse v2 Cross-Platform Source Audit

**Research Author and Repository Maintainer:** xuwen  
**Affiliation:** Japan Advanced Institute of Science and Technology (JAIST)

## Scope

This audit compares the `models/vmunet/vmamba.py` files used for formal E1
inference on RunPod RTX 4090 and HAKUSAN A100.

## File hashes

- HAKUSAN file SHA-256: `309f4a7a9b2d5df98305957177eab30cc4eb258b307486f8f9712ad31f2db281`
- RunPod file SHA-256: `d188ae7dd4efa16e5f52fa91ba9d6f4993b31bad343c4cc4212589256cf51617`

The raw hashes differ. A unified source diff and Python AST comparison found
that the differences are limited to author comments, ordinary whitespace, and
whitespace inside two documentation strings. No executable statement,
operator, constant used by model computation, control-flow branch, parameter
definition, or scan operation differs.

## Decision

The two source files are functionally equivalent for E1. Therefore, fixed
checkpoint accuracy metrics from the two platforms can be aggregated across
the preregistered seeds. GPU-dependent timing must still be compared only on
the same hardware.

