# Validation and Release

Run:

```powershell
uv run --offline --with-requirements harnesses/novel-conception-autonomous/requirements.txt `
  python harnesses/novel-conception-autonomous/validators/validate_harness.py
```

The validator checks both the production and terminal APIs, exact workflow
graph, persisted-orchestration files, adapter contract, evaluation corpus and
the ten exact stage owners. It parses every owner runtime, verifies each public
API and proves the production `ACTION_CONTRACT` equals `dependency-spec.json`.
Exit code is 0 only when `ValidationReport.ok` is true.

Build reproducible, product-versioned archives:

```powershell
uv run --offline --with-requirements harnesses/novel-conception-autonomous/requirements.txt `
  python harnesses/novel-conception-autonomous/tools/build_release.py
```

The builder creates repo-shaped self-contained bundles containing the root
scheduler skill, all ten independent owner skills, the presentation-fidelity
gate skill, the nested harness, the V2
workflow and all public schemas. It generates `dependency-lock.json` over every
required skill/spec file, validates source and staging, writes deterministic
ZIP files, extracts and revalidates them, rejects legacy D1 skills, and writes a
relative-path checksum manifest. Archive names and the release manifest carry
the product version from `manifest.yaml`; product version `1.0.0` is distinct
from internal schema versions. Absolute paths are forbidden in the manifest.
