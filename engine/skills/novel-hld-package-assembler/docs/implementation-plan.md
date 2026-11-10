# Implementation plan

1. Define closed artifact schemas and public contract.
2. Implement standard-library-only canonical JSON, hashing, safe path and schema admission.
3. Reuse common Harness profile/manifest/completion validators.
4. Implement lossless copy, authority/source-control projection and stable-ID index.
5. Implement closed HDD aggregation and LWR→LWK bijection.
6. Implement explicit-reference traceability and deterministic Markdown views.
7. Seal manifest/completion/result without hash cycles or staging-path leaks.
8. Independently regenerate and byte-compare.
9. Exercise positive, negative, boundary, envelope-tamper and owner-routing regression.
10. Publish acceptance evidence only after all gates pass.
