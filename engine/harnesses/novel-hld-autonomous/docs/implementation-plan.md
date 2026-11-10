# Harness implementation plan

1. Freeze topology, stage ownership, source access, package profiles and evaluation dimensions in one portable contract module.
2. Express transport objects as closed Draft 2020-12 JSON Schemas.
3. Implement canonical references, immutable state, HDD, revision, author-gate and package operations.
4. Validate project structure and concrete instances independently of stage prose.
5. Bind the Codex adapter to the portable core without duplicating business rules.
6. Build source and runtime archives only after validation, with SHA-256 release metadata.
7. Keep the manifest at `implementation-candidate` until the complete multi-stage execution suite passes.
