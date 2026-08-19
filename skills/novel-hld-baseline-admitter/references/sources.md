# Research sources

Accessed: 2026-08-06. The list favors standards bodies and official project documentation. These sources inform admission mechanics only; none authorizes HB0 to interpret story meaning.

1. **JSON Schema Draft 2020-12** — https://json-schema.org/draft/2020-12 — Freeze a schema dialect and validate instances and schemas against versioned contracts.
2. **JSON Schema Validation: A Vocabulary for Structural Validation of JSON** — https://json-schema.org/draft/2020-12/json-schema-validation — Use assertions for required values, closed objects, arrays and exact enums; do not confuse annotations with enforced validation.
3. **JSON Schema Core: A Media Type for Describing JSON Documents** — https://json-schema.org/draft/2020-12/json-schema-core.html — Treat schema identity, references and validator output as explicit protocol elements.
4. **RFC 8785: JSON Canonicalization Scheme (JCS)** — https://www.rfc-editor.org/rfc/rfc8785.html — Hash invariant JSON representations rather than formatting-dependent serializations.
5. **FIPS 180-4: Secure Hash Standard** — https://csrc.nist.gov/pubs/fips/180-4/upd1/final — Use SHA-256 digests to detect changed artifacts.
6. **RFC 6901: JavaScript Object Notation (JSON) Pointer** — https://www.rfc-editor.org/rfc/rfc6901.html — Resolve locators token-by-token and terminate on invalid escapes, missing members or invalid array indices.
7. **SLSA v1.1 Provenance** — https://slsa.dev/spec/v1.1/provenance — Verify artifact identity against expected builder/input provenance before consumption.
8. **SLSA v1.0 Terminology: Verification model** — https://slsa.dev/spec/v1.0/terminology — Separate producer claims from consumer verification against preconfigured expectations.
9. **in-toto Getting Started** — https://in-toto.io/docs/getting-started/ — Bind ordered steps, authorized actors, materials and products into a verifiable chain.
10. **in-toto Stable Specification v1.0** — https://in-toto.io/docs/specs/ — Use versioned layout/link metadata rather than informal provenance notes.
11. **Reproducible Builds: SOURCE_DATE_EPOCH** — https://reproducible-builds.org/docs/source-date-epoch/ — Replace current clock reads with a caller-fixed timestamp for reproducible outputs.
12. **Reproducible Builds: Timestamps** — https://reproducible-builds.org/docs/timestamps/ — Avoid embedding build time where source identity and explicit environment data are more precise.
13. **Python pathlib documentation** — https://docs.python.org/3/library/pathlib.html — Resolve paths before containment checks and reject paths outside the declared root.
14. **OWASP Path Traversal** — https://owasp.org/www-community/attacks/Path_Traversal — Accept known-good paths and prevent user-controlled traversal beyond the root.
15. **Open Container Initiative Descriptor Specification** — https://specs.opencontainers.org/image-spec/descriptor/ — Verify bytes against descriptor digests before consuming content.
16. **Git data model** — https://git-scm.com/docs/gitdatamodel.html — Model immutable content with content-derived object identities and append-only references.
17. **Semantic Versioning 2.0.0** — https://semver.org/ — Treat released versions as immutable and express compatibility through an explicit public contract.
18. **NIST Secure Software Development Framework** — https://csrc.nist.gov/projects/ssdf — Preserve integrity/provenance evidence and verify reused components against requirements.
