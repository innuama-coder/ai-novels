---
name: novel-hld-workflow
description: Use when an accepted PRD package must become a novel HLD world-system contract before LLD work begins.
---

# novel-hld-workflow

## Role

This is the HLD node pure harness. It validates inputs, dispatches independent HLD skills, routes Skill Verdicts, records convergence, and packages accepted outputs. It must not write HLD business facts.

## Input Gate

Read the final PRD package, upstream proposal package, upstream source inventory, PRD artifacts 05 and 08, and PRD risk report. Start artifact 01 only when `HLD entry verdict = pass_to_hld`, `python3 scripts/validate_prd_contract.py` authenticates the registered PRD run and manifest, the upstream source inventory contains `## Upstream required HLD entities` with `Source fact field`, and the `## HLD information boundary table` in artifact 05, artifact 08, and the final PRD package is present and text-identical.

If PRD gate is blocked, emit only manifest and gate report. No artifacts 01-12.

| PRD state | Harness action |
|---|---|
| `HLD entry verdict = blocked_pending_human_review` | Create blocked manifest and gate report; wait for human PRD review. |
| `HLD entry verdict = blocked_revision_required` | Create blocked manifest and PRD reopen request. |
| `HLD entry verdict = pass_to_hld` with an authenticated registered PRD package and a complete `## Upstream required HLD entities` table, including `Source fact field` | Dispatch artifact 01 and follow the Dispatch DAG. |
| `HLD entry verdict = pass_to_hld` but PRD manifest authentication, the entity table, its `Source fact field`, or any authenticated information-boundary copy is missing or divergent | Create blocked manifest and PRD reopen request for missing or divergent PRD handoff contract. |

## Dispatch DAG

| Artifact | Owner skill | Depends on |
|---|---|---|
| 01 | `novel-world-entity-inventory-builder` | input gate |
| 02 | `novel-prd-support-matrix-builder` | 01 |
| 03 | `novel-world-rule-designer` | 02 |
| 04 | `novel-character-system-designer` | 03 |
| 05 | `novel-environment-system-designer` | 03 |
| 06 | `novel-event-system-designer` | 04, 05 |
| 07 | `novel-time-information-system-designer` | 06 |
| 08 | `novel-thread-system-designer` | 07 |
| 09 | `novel-style-pov-system-designer` | 08 |
| 10 | `novel-hld-inventory-reconciler` | 09 |
| 11 | `novel-hld-integrator` | 10 |
| 12 | `novel-hld-integrity-checker` | 11 |
| `final-hld-package` | harness package shell | 11, 12 |

Artifact 11 must not depend on artifact 12. Artifact 12 checks artifact 11. The final package depends exactly on artifact 11 and artifact 12.

## Harness Boundary

Allowed:

- Validate input paths, upstream verdicts, artifact presence, schemas, and Skill Verdict tables.
- Dispatch skills in DAG order.
- Record convergence rows from skill/checker output.
- Package artifact 11 and artifact 12 without changing their contents.
- Route reopen requests to PRD, proposal, or the owning HLD skill.

Forbidden:

- The harness must not write HLD business facts.
- Do not fill artifact table cells.
- Do not define world rules, characters, environments, events, time/information logic, threads, style, POV, or LLD handoff details.
- Do not repair malformed business output during packaging.
- Do not use legacy HLD/LLD/writing artifacts as authority.

## Routing Rules

Route only from structured `## Skill Verdict`, artifact 11 `## HLD Source Map` and `## LLD handoff index`, artifact 12 risk/verdict sections, `Artifact rubric coverage`, upstream source inventory coverage, and `scripts/validate_hld_contract.py`.

Before packaging, run `validate_upstream_source_coverage` with the final PRD package and proposal package as upstream source inventory. The upstream source inventory must include `## Upstream required HLD entities` with a valid `Source fact field`; missing or legacy mandatory entity handoff blocks HLD and reopens PRD. Artifact 01 and artifact 02 must each cover every required `scene:`, `freeze:`, `hldreq:`, `claim:`, and `storylogic:` source ref extracted from upstream. Artifact 01 must cover every upstream required HLD entity at fact/entity level. When validating an artifact directory with `scripts/validate_hld_contract.py`, pass the artifact directory first plus `05-information-flow.md`, `08-prd-integrator.md`, `final-prd-package.md`, and proposal source files; artifact-dir validation must reject runs without the three authenticated PRD boundary sources.

Artifact 01 `Secondary HLD owners` are dispatch obligations. Artifact 02 must create at least one inventory-bound support row for every non-`none` secondary owner, with the exact artifact 01 provisional `Inventory id` in `Inventory obligations` and the exact same source refs, before downstream design can pass.

Apply HLD-CONTRACT-13 and HLD-CONTRACT-16 business-rule validation as artifact-level gates through `validate_hld_business_rules`; do not treat enum-like fields, time/reveal graphs, fact atoms, or cross-artifact references as prose-only guidance.

Artifact 02 support rows are dispatch obligations, not optional notes. Before packaging, every ready support row assigned to artifact 03-09 must be consumed by the matching owner artifact through its `Supports` column only; unconsumed support, owner-missing consumption, or any non-owner consumption blocks packaging.

Artifact 10 is the final inventory authority. Before packaging, reconstruct its subject register from artifact 01 inventory and the actual amendment declarations in artifacts 03-09. Every artifact 01 `Inventory id` must have exactly one identity- and fact-trace-matched row; an amendment may not mint an inventory id; each accepted inventory row may mint exactly one id; and a merge must name an accepted canonical subject. Artifact 11 may cite only ids resolved from those accepted rows, and must use `none` for non-inventory artifact 03, 08, and 09 facts. Artifact 11 must map every accepted artifact 03-09 fact trace exactly once, mirror each mapping in its own fact trace, and create one ready LLD handoff-index row with the same fact-level fields. Artifact 10 metadata must declare `Reconciliation mode = bootstrap|continuity`. A continuity run must pass the previous approved artifact 10 through `validate_hld_artifact_dir(..., previous_reconciliation_path=...)` and record its SHA-256; a bootstrap run must not declare a prior artifact. A previously resolved subject must not change final id.

Reject packaging when any artifact has:

- `Skill quality verdict = fail`
- `Source closure = open:<reason>`
- `Inventory coverage = open:<reason>`
- `Boundary obedience = violation:<source ref>`
- `Downstream readiness = blocked:<reason>` or `reopen_upstream:<target>`
- unresolved P0/P1 in artifact 12
- failed `Artifact rubric coverage`
- failed upstream source coverage
- failed HLD-CONTRACT-13 or HLD-CONTRACT-16 business-rule validation
- missing, duplicate, orphaned, or field-drifted artifact 11 Source Map / LLD handoff-index closure

## Artifact Contract

Each artifact 01-12 must include:

- `## Artifact Metadata`
- the required artifact table
- `## HLD Fact Trace`
- `## Skill Verdict`

All source refs must use `scene:PRD-Sxx`, `freeze:PRD-FREEZE-xx`, `hldreq:HLD-REQ-xx`, `claim:CLAIM-xx`, `storylogic:PRD-LOGIC-xx`, or `inventory:INV-xx`.

## Blocked Run Behavior

If PRD gate is blocked, write only a blocked run manifest and gate report under `duanxian/design/runs/hld/<run-id>/`. The blocked manifest records harness name, PRD package path, PRD risk report path, blocking verdict, and convergence status.

## Packaging

The harness creates `final-hld-package` as an index only. It may include artifact paths, versions, checksums, and final verdicts. It must not add, delete, merge, or rewrite HLD facts.

## Release Preflight

HLD-CONTRACT-18 requires a release preflight after packaging and before the HLD run is called release-ready. Run `python3 scripts/validate_hld_release.py` with the artifact directory, `final-hld-package`, and every authenticated PRD/proposal upstream source. This read-only gate verifies one committed Git snapshot for the HLD contract, methodology reference, harness, all 12 owner skills, validators, regression tests, actual HLD artifacts, final package index, and upstream inputs; rejects any file that differs from `HEAD`; validates the real artifact directory against the authenticated upstream package; requires a `## Release Artifact Index` containing exactly artifact 11 and artifact 12 paths plus SHA-256 values that match their files; and requires artifact 12 to resolve to `Agent quality verdict = pass`, `HLD human review state = confirmed|not_required`, and `LLD entry verdict = pass_to_lld`.

A failed release preflight means `blocked`, never `release-ready`. It must report the failed release condition without editing artifact facts, staging files, creating commits, or treating a pending human review as an approval.

## Convergence Protocol

Each unresolved P0/P1 must have:

| Field | Requirement |
|---|---|
| Stable issue id | Same id across review/fix/review cycles |
| Root cause | Specific failed contract, source, or artifact responsibility |
| Fix hypothesis | Owning artifact expected to change |
| Regression proof | Validator/test/check that must fail before fix and pass after |
| Attempt count | Incremented for repeat failures |
| Rerun target | Owning artifact or upstream reopen target |
| Status | `open`, `fixed`, `blocked`, or `versioned_refactor_required` |

If the same P0/P1 remains after three attempts, stop local patching and propose a versioned HLD workflow/skill contract refactor.
