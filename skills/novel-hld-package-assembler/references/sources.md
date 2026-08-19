# Primary research sources

Research was reviewed on 2026-08-06. The implementation uses the methods below; no source is treated as story authority.

| # | Primary source | Method extracted | HP1 absorption |
|---|---|---|---|
| 1 | [RFC 8785: JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785) | Stable property ordering and deterministic JSON representation | Sorted, compact, UTF-8 JSON with rejected non-finite numbers |
| 2 | [RFC 6901: JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901) | Unambiguous location within JSON | Escaped locators in cross-index entries |
| 3 | [NIST FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final) | SHA-256 digest definition | All file/value bindings use lowercase SHA-256 |
| 4 | [SLSA v1.2 Provenance](https://slsa.dev/spec/v1.2/provenance) | Bind outputs to inputs and builder identity | Assembly execution records implementation/input/output hashes |
| 5 | [SLSA v1.2 Verifying Artifacts](https://slsa.dev/spec/v1.2/verifying-artifacts) | Verify artifact identity before trusting provenance | Upstream refs, manifests and completion refs are all reverified |
| 6 | [in-toto Specification](https://in-toto.io/in-toto-spec/) | Layout, link metadata and supply-chain step binding | Fixed upstream topology and package-external result envelope |
| 7 | [Reproducible Builds: SOURCE_DATE_EPOCH](https://reproducible-builds.org/docs/source-date-epoch/) | Eliminate ambient clock variation | Output timestamp comes only from the sealed work-order |
| 8 | [Reproducible Builds: Archives](https://reproducible-builds.org/docs/archives/) | Stable ordering and normalized archive membership | Fixed package profile and sorted traversal |
| 9 | [Reproducible Builds: Timestamps](https://reproducible-builds.org/docs/timestamps/) | Avoid filesystem modification-time influence | No mtime enters content or hash decisions |
| 10 | [OCI Image Spec: Descriptor](https://specs.opencontainers.org/image-spec/descriptor/) | Media objects are bound by digest, size and identity | Role/path/digest references and manifest closure |
| 11 | [W3C PROV-DM](https://www.w3.org/TR/prov-dm/) | Entity/activity/agent provenance model | Source owner, producing stage and assembly activity stay distinct |
| 12 | [W3C PROV-O](https://www.w3.org/TR/prov-o/) | Machine-readable provenance relations | Cross-index and trace records preserve derivation links |
| 13 | [JSON Schema 2020-12 Core](https://json-schema.org/draft/2020-12/json-schema-core) | Vocabulary, references and instance evaluation | Contract schemas use bounded Draft 2020-12 constructs |
| 14 | [JSON Schema 2020-12 Validation](https://json-schema.org/draft/2020-12/json-schema-validation) | Required/type/enum/uniqueness assertions | Closed object contracts and structural hard gates |
| 15 | [OpenAPI 3.1.1 Specification](https://spec.openapis.org/oas/v3.1.1.html) | Contract-first interfaces and JSON Schema alignment | Explicit input/output lifecycle and failure outcomes |

## Source sufficiency

The set covers canonicalization, hashing, provenance, supply-chain verification, reproducibility, locators and contract validation. These are the disciplines needed by a non-semantic assembler. Narrative design methods are intentionally excluded because HP1 must not author narrative meaning.
