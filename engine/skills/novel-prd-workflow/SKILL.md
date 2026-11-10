---
name: novel-prd-workflow
description: Use when an accepted novel proposal must become a PRD trunk-scene document for a specified part before HLD work begins.
---

# novel-prd-workflow

## Role

This is the PRD node harness. It orchestrates independent PRD skills and packages their outputs into a PRD document. It must not design trunk scenes itself.

## Hard Boundary

The accepted proposal is the highest constraint for PRD. The harness must verify the upstream proposal PRD entry verdict before dispatching business skills. If the proposal Risk Report does not say `PRD entry verdict` = `pass_to_prd`, stop and return the proposal to human confirmation or proposal repair.

PRD expands only the specified part. It may define trunk scenes, role/environment/event facts needed for those scenes, conflict/value shifts, information changes, freeze boundaries, HLD expansion requirements, and upstream required HLD entities. It must not rewrite the proposal's core concept, reader promise, terminal agency, focal POV rule, or irreversible outcome.

## Harness Flow

| Step | Harness Action | Business Owner |
|---|---|---|
| 1 | Validate proposal source path, proposal version, and proposal PRD entry verdict | harness |
| 2 | Select the specified part scope from proposal-approved candidates | `novel-part-scope-selector` |
| 3 | Define the selected part's story function and acceptance boundary | `novel-part-goal-definer` |
| 4 | Design the linear trunk scene list | `novel-trunk-scene-designer` |
| 5 | Add conflict and value-shift rows to each trunk scene | `novel-scene-conflict-value-designer` |
| 6 | Add reader/character information-flow changes | `novel-scene-information-flow-designer` |
| 7 | Write PRD freeze boundaries | `novel-prd-freeze-boundary-writer` |
| 8 | Write HLD expansion requirements and upstream required HLD entities | `novel-hld-expansion-requirement-writer` |
| 9 | Assemble the PRD document from artifacts 01-07 | `novel-prd-integrator` |
| 10 | Check causality, boundary control, risk severity, and HLD entry verdict | `novel-prd-causality-checker` |
| 11 | Package `final-prd-package` from integrator and checker outputs | harness |

## Dispatch Order

1. `novel-part-scope-selector`
2. `novel-part-goal-definer`
3. `novel-trunk-scene-designer`
4. `novel-scene-conflict-value-designer`
5. `novel-scene-information-flow-designer`
6. `novel-prd-freeze-boundary-writer`
7. `novel-hld-expansion-requirement-writer`
8. `novel-prd-integrator`
9. `novel-prd-causality-checker`

Artifacts 04 and 05 may only run after the trunk scene list exists. Artifact 08 may depend on artifacts 01-07 only. Artifact 09 may depend on artifacts 01-08. `final-prd-package` depends exactly on artifacts 08 and 09.

Formal PRD runs must declare `upstream_proposal_risk_report`, `final_prd_package`, and all skill artifact paths. The upstream proposal Risk Report must pass the PRD entry gate before any PRD artifact is accepted.

Every PRD skill artifact from artifacts 01-09 must include a structured `## Skill Verdict` table. The harness may route only by this table, the PRD Integration Verdict, and the causality checker output; it must not infer pass/fail from prose.

## Routing Gate

The harness may package a PRD only by checking the presence and routing status of independent skill outputs. It must not independently judge trunk-scene causality, conflict quality, value-shift quality, information-flow quality, freeze sufficiency, or HLD readiness.

Reject packaging or route a rerun only when an independent output says so:

- Upstream proposal PRD entry verdict is missing or not `pass_to_prd`.
- Scope selector cannot prove the specified part is proposal-authorized and independently reviewable.
- Trunk scene designer reports missing causal coverage or proposal conflict.
- Trunk scene designer or causality checker reports that post-death memory reading lacks a prior causal setup for failed critical-intelligence handoff, transmission, or reporting.
- Trunk scene designer or causality checker reports missing `Scene execution table` coverage or fewer than two execution units for any trunk scene.
- Trunk scene designer or causality checker reports missing `Story logic boundary table` coverage for usable-intelligence versus complete-cause split, protected-person causality, or digital-life terminal deception.
- Trunk scene designer or causality checker reports missing plausibility anchors for major-event action window, protected-person relationship weight, digital-life terminal execution conditions, or organization pressure limits.
- Conflict/value or information-flow artifacts report missing rows for any trunk scene.
- Freeze boundary or HLD expansion/entity handoff artifacts report hidden assumptions.
- Integrator reports missing source, trace drift, unauthorized scene rewrite, or source contradiction.
- Causality checker reports unresolved P0/P1, non-pass agent quality, or blocked HLD entry.

Reject packaging whenever any artifact 01-09 has `Skill quality verdict` other than `pass`, `Source closure` other than `pass`, `Boundary obedience` other than `pass`, or `Downstream readiness` other than `pass`.

## Convergence Protocol

Every retry caused by a P0/P1 finding must be recorded before rerun. The harness records routing facts only; it must not decide the business fix.

| Field | Requirement |
|---|---|
| Stable issue id | Keep the same id across review/fix/review cycles for the same defect |
| Root cause | Quote the independent checker's root-cause statement or mark missing root cause as a rerun blocker |
| Fix hypothesis | Name the skill output expected to change and why that skill owns the fix |
| Regression proof | Name the validator, artifact row, or independent report that must fail before the fix and pass after the fix |
| Attempt count | Increment for the same Stable issue id whenever a rerun does not remove the P0/P1 |
| Versioned refactor trigger | If the same P0/P1 remains after three attempts, stop targeted reruns and propose a new workflow/skill-contract version |

Every unresolved P0/P1 row in the PRD risk report must have a matching convergence-log row whose root cause, fix hypothesis, or regression proof names that blocking risk. A P0/P1 risk without convergence coverage blocks packaging.

Any non-pass PRD core risk check with status `fail` or `not_checked` is itself blocking: the causality checker must surface it as an unresolved P0/P1 risk, and the harness must require matching convergence-log coverage before rerun or packaging.

## Forbidden

- Do not design trunk scenes, conflicts, value shifts, information flow, freeze boundaries, or HLD requirements directly.
- Do not start from old PRD/HLD/LLD/writing artifacts as frozen input.
- Do not rewrite proposal facts to make a part easier to design.
- Do not write HLD world bible, LLD scene blueprint, dialogue, prose, or chapter draft.

## Output Package

The packaged PRD must include:

| Section | Source |
|---|---|
| Proposal source and PRD entry proof | harness input gate |
| Specified part scope | `novel-part-scope-selector` |
| Part goal and acceptance boundary | `novel-part-goal-definer` |
| Linear trunk scene table | `novel-trunk-scene-designer` |
| Conflict and value-shift table | `novel-scene-conflict-value-designer` |
| Information-flow table | `novel-scene-information-flow-designer` |
| PRD freeze boundaries | `novel-prd-freeze-boundary-writer` |
| HLD expansion requirements | `novel-hld-expansion-requirement-writer` |
| Upstream required HLD entities | `novel-hld-expansion-requirement-writer` |
| PRD Integration Verdict | `novel-prd-integrator` |
| PRD risk report and HLD entry verdict | `novel-prd-causality-checker` |

Artifact-level validation must verify the complete package, not only the trunk scene table: scope, goal, trunk scenes, conflict/value, information flow, freeze boundaries, HLD requirements, integration, risk report, and `final-prd-package` all remain required in a formal run.

Artifact 03 is the canonical trunk-scene fact source. In a formal run, each trunk scene row must include `Scene content`, `Previous dependency`, `Next pressure`, and `Indispensability proof` so HLD receives concrete scene-level content and a causal contract rather than a proposal-level plot label.

If a formal PRD part contains post-death memory reading, artifact 03 must include a prior pre-extraction causal setup scene explaining how critical intelligence failed normal handoff, transmission, or reporting because of the accident/death context. A PRD that begins directly at life support or brainwave analysis without this setup has a trunk-causality gap and cannot be packaged.

Artifact 03 must also include `## Scene execution table`. Every canonical trunk scene must have at least two execution units with scene objective, on-page action, conflict turn, exit state, and proposal trace. This table is still PRD-level design, not prose: it defines the visible action path that HLD/LLD/writing must expand without inventing missing scene mechanics.

When artifact 03 contains story logic that resolves a crisis with usable intelligence while withholding complete cause, protects a person tied to the event, or lets a digital life deceive the researcher into terminal action, artifact 03 must include `## Story logic boundary table`. The table must freeze the PRD-level causal answers and leave only bounded HLD expansion room. A package that leaves these answers as vague HLD-owned details is not ready for HLD.

Story logic boundary rows must include plausibility anchors: a concrete major-event action window, protected-person relationship weight, bounded terminal execution conditions, and organization pressure limits where those risks appear. These anchors stay at PRD level; they do not replace HLD mechanics, but they prevent HLD from inventing the missing causal load later.

Every PRD `Proposal trace` must use `CLAIM-xx; role=<upstream Constraint role>` and the Claim ID must resolve to the upstream proposal Risk Report's Claim Source Map coverage. Unknown claim traces, missing claim traces, or missing role markers block packaging.

Claim trace is fact-level, not ID-level: the PRD row that cites a claim must preserve the claim's Critical business claim and exact Constraint role from the upstream Claim Source Map. Reusing a valid `CLAIM-*` ID while changing the story fact, scope, causal function, or role marker is trace drift and blocks packaging.

Freeze boundary `Source` fields, HLD expansion `Source` fields, and upstream required HLD entity `Source refs` fields must use structured source references only: `scene:PRD-Sxx` for canonical PRD scene facts and `claim:CLAIM-xx` for upstream proposal claims. Free text source labels, raw `PRD-Sxx`, and raw `CLAIM-xx` do not satisfy source closure. A source that cites a non-existent scene or unknown claim blocks packaging.

Artifact 07 must include `## Upstream required HLD entities` with `Upstream fact id`, `Source fact field`, exact `Upstream fact atom`, `Required HLD entity`, `Required entity type`, and `Source refs`. Each ID must anchor its own `scene:PRD-Sxx`; `Source fact field` must name a permitted artifact 03 field; the atom must equal that field's complete value exactly; and the entity name must occur verbatim in the atom. Every artifact 05 `entity:<名称>` knowledge holder must resolve to one registered `character` or `group`. The final package must preserve this table and artifact 07's complete `HLD expansion requirement list` exactly. The table is the mandatory HLD artifact 01 entry inventory seed; missing, unstructured, unregistered, incomplete, or source-drifting rows block HLD entry.

Artifact 07 must also give every HLD expansion requirement `Information boundary refs` and `Inherited HLD obligations` fields. Each artifact 05 `PRD-INFO-xx` `HLD obligation` must be consumed by at least one requirement whose support scenes and source include the boundary anchor or reveal scene, and whose inherited-obligation field reproduces the exact obligation; unknown, duplicate within a row, unanchored, altered, or unconsumed information-boundary refs block packaging.

Artifact 03 Story logic boundary rows must declare `Required HLD entity refs`. Artifact 07 must contain `## Story logic requirement coverage`: every `PRD-LOGIC-nn` maps exactly once to one HLD requirement and reproduces the exact frozen answer. The cited requirement must support and source a scene from that logic boundary, and every declared logic-boundary entity must resolve to an artifact 07 `character` or `group` row. The final package must reproduce this coverage table exactly.

Every artifact 07 `Requirement id` must match `HLD-REQ-nn` and be unique. For each requirement, the full `Supports scene ids` set must exactly equal the row's `scene:PRD-Sxx` source-ref set; proposal claims may add evidence but cannot replace a supported scene source. A duplicate ID, unknown support, or source/support drift blocks packaging.

HLD entry verdict must follow a closed state machine. `Agent quality verdict = pass`, `Human review verdict = confirmed`, no unresolved P0/P1, and all core risk checks `pass` requires `HLD entry verdict = pass_to_hld`. `Agent quality verdict = pass` with `Human review verdict = pending` requires `blocked_pending_human_review`. Any unresolved P0/P1, non-pass core check, non-pass Agent quality verdict, or human `reopen_prd` requires `blocked_revision_required`.

Artifact 08 must include `## PRD Integration Verdict` before `## Scene Source Map`. The integration verdict must prove source completeness, scene fact preservation, no new business content, and package readiness.

The `final-prd-package` index must preserve exact source ownership: scope from artifact 01, goal from artifact 02, trunk scenes from artifact 03, conflict/value from artifact 04, information flow from artifact 05, freeze boundaries from artifact 06, the complete HLD expansion requirement list and upstream required HLD entities from artifact 07, integration and Scene Source Map from artifact 08, and risk/HLD entry verdict from artifact 09. Unknown, missing, partial, or extra package sources block packaging.
