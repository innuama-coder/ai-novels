# Independent research sources

Accessed 2026-08-06. Each absorption point is implemented in methodology or SOP.

1. [NIST FIPS 180-4 Secure Hash Standard](https://csrc.nist.gov/pubs/fips/180-4/upd1/final) — message digests detect changes; applied to byte-level artifact binding.
2. [NIST SP 800-218 SSDF](https://csrc.nist.gov/pubs/sp/800/218/final) — protect release integrity, publish verification information, and retain provenance; applied to final package evidence.
3. [NIST SSDF project](https://csrc.nist.gov/projects/ssdf) — track requirements/design decisions and collect provenance for release components; applied to complete chain binding.
4. [NIST Security Considerations for Code Signing](https://csrc.nist.gov/News/2018/Security-Considerations-for-Code-Signing) — distinguish integrity from source authentication; applied to the hash-versus-authority boundary.
5. [NIST SP 1800-34, Validating Device Integrity](https://csrc.nist.gov/pubs/sp/1800/34/final) — verify stored reference information and fail on tampering; applied to recomputation rather than trusting declarations.
6. [NIST SP 800-128 Configuration Management](https://csrc.nist.gov/pubs/sp/800/128/upd1/final) — preserve approved baselines and controlled change; applied to current-revision and stale-evidence rejection.
7. [RFC 8785 JSON Canonicalization Scheme](https://www.ietf.org/rfc/rfc8785.html) — invariant JSON representation enables repeatable hashing; applied to deterministic serialization.
8. [SLSA Provenance v1.2](https://slsa.dev/spec/v1.2/provenance) — bind artifact subjects and materials with digests; applied to input/output reference sets.
9. [SLSA Specification v1.2](https://slsa.dev/spec/v1.2/) — verification summaries and provenance are consumer-verifiable release evidence; applied to final validation.
10. [in-toto Specification](https://github.com/in-toto/docs/blob/master/in-toto-spec.md) — bit-for-bit artifact equivalence, authorized steps, order, and material/product links; applied to fixed topology and profiles.
11. [in-toto Attestation Framework](https://github.com/in-toto/attestation) — authenticated metadata captures artifact-production claims for consumers; applied to bounded completion evidence.
12. [NASA Systems Engineering Handbook Appendix](https://www.nasa.gov/reference/system-engineering-handbook-appendix/) — verification matrices bind requirements to source and method; applied to chain and handoff checks.
13. [U.S. GAO 2024 Government Auditing Standards](https://www.gao.gov/yellowbook) — objective evidence, documentation, independence and quality management; applied to durable final validation.
14. [NIST Secure Hash Algorithm Validation](https://csrc.nist.gov/Projects/Cryptographic-Algorithm-Validation-Program/Secure-Hashing) — test known algorithms and do not confuse local tests with formal certification; applied to precise SHA-256 claims.
