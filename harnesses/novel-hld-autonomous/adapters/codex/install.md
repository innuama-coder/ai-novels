# Codex adapter installation

Use the repository source tree, or unpack the Codex archive into an empty controlled directory and treat the archive's single top-level folder as the workspace root. It contains `harnesses/novel-hld-autonomous/` and the exact 14 `skills/novel-hld-*` owners at repository-relative paths. Run `python harnesses/novel-hld-autonomous/tools/post_install_validate.py` before the first job; success must report 17 registry tokens, 14 skills, the operation contract and the explicit qualification status.

Invoke the portable Python modules with Python 3.11+. Schema validation is supplied by `runtime/schema_catalog.py` and requires only the Python standard library; do not install or silently substitute an ambient JSON Schema package. Start every job with `adapters/codex/operation.md`; do not copy adapter text into a standalone prompt and omit the schemas, shared runtime, validators, or registered skill directories.

An `implementation-candidate` may be installed for qualification, but not represented as semantically qualified. To promote it, materialize the evidence package described in `docs/agentic-qualification-contract.md`, then run `python harnesses/novel-hld-autonomous/tools/validate_agentic_acceptance.py <evidence-root>/agentic-acceptance.json`. Only a zero exit status permits changing both manifests and release acceptance to `release-candidate`.
