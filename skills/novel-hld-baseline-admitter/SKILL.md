---
name: novel-hld-baseline-admitter
description: Revalidate one formal novel-development-baseline-preparer ready package and deterministically admit it as the immutable HB0 control plane for a new novel-hld-autonomous run. Use only when the HLD harness issues a sealed HB0 work-order. Reject stale, unlisted, unsafe, incompatible, malformed, or non-ready baselines; do not summarize the novel, decide HDD dispositions, design HLD, repair conception, or write run state.
---

# Novel HLD Baseline Admitter

## Mission

Prove that the exact formal development baseline is still current, then losslessly wrap its controls and source locators for HLD. This is a deterministic script skill, not a story-design skill.

## Read before execution

Read completely:

1. [references/input-output-contract.md](references/input-output-contract.md)
2. [references/sop.md](references/sop.md)

Read [references/methodology.md](references/methodology.md) when changing admission logic. Read [references/sources.md](references/sources.md) when auditing the research basis.

## Execute

From the repository root, run:

```powershell
python skills/novel-hld-baseline-admitter/scripts/run_hb0.py <sealed-workspace>/work-order.json
```

Then independently revalidate:

```powershell
python skills/novel-hld-baseline-admitter/scripts/validate_hb0.py <sealed-workspace>/work-order.json
```

Exit codes:

- `0`: ready package and package-external result are reproducible and valid;
- `2`: input/source admission is blocked and durable blocked evidence is valid;
- `1`: runtime/configuration failure; no semantic readiness verdict may be inferred.

## Hard input rule

Accept only the work-order path. Before reading semantic inputs, verify exact skill, stage, mode, implementation hash, pre-state, input gate, empty upstream list, empty unresolved projection, event/timestamp binding, output directory and every allowlisted path/hash. Read no file outside the allowlist.

## Ready output

The content package contains exactly:

- `hld-control-baseline.json`
- `hld-source-index.json`
- `hb0-execution.json`
- `validation.json`
- `package-manifest.json`
- `stage-completion.json`

The same sealed workspace contains one `stage-result.json` outside the content package. HB0 never writes run state; the parent creates revision 001 only after consuming this result.

## Blocked output

The result package contains exactly `gate-data.json`, `blocked-report.json`, `validation.json`, and `result-manifest.json`. The workspace contains one package-external blocked `stage-result.json`. No candidate, control baseline, source index or completion may coexist.

## Forbidden behavior

- Do not summarize or interpret story content.
- Do not create `HDD-` or decide whether an unresolved source matters.
- Do not use inventory counts as semantic object counts.
- Do not repair baseline, conception, locators, schemas or hashes.
- Do not broaden the fixed source-access matrix.
- Do not write a successor state, return owner or next route.
- Do not use local time in deterministic output.

## Done rule

Report only `ready`, `blocked`, or runtime failure; include the workspace, result hash, validation command and bounded parent action. A structurally valid package that cannot be reproduced from the same sealed inputs is not deliverable.
