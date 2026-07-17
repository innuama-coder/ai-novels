# Novel HLD Workflow Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the HLD node from an old monolithic writer into a standards-compliant harness workflow with independently acceptable skills, artifact-level gates, PRD fact trace closure, complete world-system coverage, and HLD readiness validation.

**Architecture:** `novel-hld-workflow` becomes the only HLD node harness. It validates the PRD HLD-entry gate, dispatches independent HLD business skills in a fixed artifact DAG, packages the final HLD from integrator and integrity checker artifacts, and never writes world, character, environment, event, thread, style, or POV content directly. The old `novel-hld-writer` is demoted to non-authoritative legacy reference and no longer acts as the HLD workflow. The HLD contract validates both process closure and business closure: every required world entity and narrative thread must be designed, every design-time support entity must be reconciled into the final inventory, every PRD story-logic boundary must be preserved, and all HLD facts must be traced and handed to LLD.

**Tech Stack:** Markdown skill contracts under `skills/`, workflow specifications under `docs/superpowers/specs/`, Python validator scripts under `scripts/`, pytest regression tests under `tests/`.

---

## Review Findings

| Finding | Severity | Evidence | Root Cause | Required Resolution |
|---|---:|---|---|---|
| `novel-hld-workflow` does not exist as an implemented skill. | P1 | `skills/` contains `novel-hld-writer`, but no `skills/novel-hld-workflow/SKILL.md`. | The specification was updated to require `node = harness workflow + independent skills`, but HLD was never migrated from the old writer model. | Create `novel-hld-workflow` as a pure harness. |
| HLD business work is concentrated in `novel-hld-writer`. | P1 | `skills/novel-hld-writer/SKILL.md` directly designs角色、空间、时间、节奏、视角、线索、关键场景和风格。 | The old skill predates the strong harness rule and mixes orchestration, design, integration, and checking. | Split HLD into independent business skills with explicit contracts. |
| Current HLD definition conflicts with the latest workflow boundary. | P1 | Old HLD says it outputs “Threads with Key Scenes”；latest workflow says HLD outputs “小说世界观 + 世界结构 + 全量人物、环境和事件”. | HLD still follows the older “architecture/key-scene” model instead of the current “world system contract” model. | Reframe HLD artifacts around support matrix, world rules, character system, environment system, event system, time/information, style/POV, integration, and integrity checking. |
| HLD has no artifact-level source closure. | P1 | PRD has `scene:PRD-Sxx` and `claim:CLAIM-xx`; HLD has no validator or required map preserving PRD scene facts and HLD requirements. | HLD lacks the contract/validator pattern developed for PRD. | Add HLD contract JSON, validator script, and tests for source closure and fact preservation. |
| HLD has no formal entry gate from PRD. | P1 | Latest PRD risk report currently says `HLD entry verdict = blocked_pending_human_review`; no HLD harness exists to enforce this. | HLD execution can be started manually from PRD content without checking human review state. | Harness must block unless PRD `HLD entry verdict = pass_to_hld`. |
| Existing HLD references old June documents as authoritative. | P1 | `docs/superpowers/specs/2026-06-06-hld-digital-life-novel.md` is based on old PRD v2.0 and deprecated story assumptions. | Legacy project artifacts remain nearby and can contaminate new HLD generation. | New harness must explicitly reject old HLD/LLD/writing as frozen input. |
| HLD target coverage is not yet fully contractible. | P1 | The first plan covered support matrix, world, character, environment, event, time/information, style/POV, integration, and checking, but did not define a complete entity universe or final HLD schema. | The plan treated workflow engineering as sufficient, while the HLD node's business target is complete world-system definition. | Add a world-entity inventory artifact, final HLD schema, and coverage validation for every required role, environment, event, information object, rule, organization, and thread. |
| HLD line/thread structure has no owner. | P1 | The creation workflow requires HLD to define 主线、展开线、隐藏线 in the world, but the first plan did not assign this to an independent skill. | Thread structure was assumed to be covered by time/information, but line distribution is a distinct HLD business capability. | Add `novel-thread-system-designer` as an independent HLD skill. |
| HLD human review state machine conflicts with the workflow spec. | P1 | The first plan blocked LLD entry when human HLD review was pending, while the workflow spec says HLD human review is optional. | The PRD state-machine pattern was copied into HLD without adapting to HLD's optional human-review policy. | Replace binary human review blocking with `confirmed`, `not_required`, `pending_required`, and `reopen_hld`. |
| Design-time support entities have no reconciliation path. | P1 | The initial inventory is extracted before world/character/environment/event/thread design, while those skills may need new support entities to make PRD scenes work. | The inventory was modeled as a static front gate instead of a controlled evolving coverage ledger. | Add `novel-hld-inventory-reconciler` to accept or reject amendment requests and produce the final inventory/support closure. |
| PRD story-logic boundary preservation is not explicit enough. | P1 | Current PRD contains a `Story logic boundary table` for usable intelligence, protected-person causality, digital-life terminal deception, and organization pressure; the plan only mentions scene facts generically. | High-risk causal boundaries were treated as ordinary source facts instead of as first-class HLD preservation requirements. | Add an independent contract rule and validator fixtures requiring every PRD story-logic boundary row to appear in the HLD Source Map with a non-rewriting support mechanism. |
| Per-artifact schemas are too loose for validator-driven quality. | P1 | The final HLD schema is fixed, but business artifact schemas for 03-09 are only described by responsibility. | The plan could validate final section presence without ensuring each skill emitted structured, inspectable design facts. | Add minimum artifact table schemas for all HLD business skills. |
| HLD references are required but not concretely specified. | P2 | The plan requires each skill to include `## References`, but does not state what good HLD references must evaluate. | The contract inherited the generic skill section but did not carry over the HLD references dimensions from the workflow spec. | Add HLD reference dimensions: supportiveness, completeness, runnability, boundary control, LLD handoff quality, and checkability. |
| Workflow spec update is split across tasks. | P2 | Task 2 updates the harness design spec, while Task 4 later changes skill count from 9 to 12. | A migration step remained after the topology changed, creating duplicate edits. | Move skill-count update into Task 2; Task 4 only demotes legacy writer and compatibility assumptions. |
| No HLD convergence protocol exists. | P2 | PRD workflow has structured convergence logging; HLD has none. | HLD has not received the repeated-review lessons from proposal/PRD. | Add HLD convergence rules identical in shape to PRD. |
| HLD Source Map can still be only reference-level, not fact-level. | P1 | A final HLD could cite `scene:` or `storylogic:` refs while changing the actual event, cause, boundary, or support mechanism in the mapped HLD fact. | Source closure was defined as valid reference syntax, but not as immutable upstream fact preservation plus bounded expansion mode. | Add a fact-level Source Map standard with upstream fact atoms, HLD fact atoms, expansion mode, support mechanism, preservation status, and regression fixtures that fail same-ref fact rewrites. |
| HLD convergence and verdict consistency are not yet artifact-level schemas. | P1 | The plan requires convergence and risk gates, but artifact 12 only requires generic `## Output` and `## Risks` tables. | Repeated proposal/PRD failures came from treating process and verdict semantics as prose instead of structured, validator-checkable artifacts. | Add universal Skill Verdict schema, HLD Convergence Log schema, and Risk/Verdict consistency matrix with blocking semantics. |

## Target File Structure

### Create

- `skills/novel-hld-workflow/SKILL.md`  
  Pure HLD harness. Owns input gate, artifact DAG, dispatch order, routing rules, packaging rules, convergence protocol, and forbidden actions.

- `skills/novel-prd-support-matrix-builder/SKILL.md`  
  Builds the PRD support matrix from final PRD package, freeze boundaries, and HLD expansion requirements.

- `skills/novel-world-entity-inventory-builder/SKILL.md`  
  Extracts the complete HLD design universe from proposal, PRD, freeze boundaries, HLD requirements, scene execution units, and story-logic boundaries.

- `skills/novel-world-rule-designer/SKILL.md`  
  Designs world rules: history, organization, technology, social/institutional rules, and rule boundaries.

- `skills/novel-character-system-designer/SKILL.md`  
  Designs all HLD-level characters: function, relationship, motivation, information permission, and PRD scene support.

- `skills/novel-environment-system-designer/SKILL.md`  
  Designs all HLD-level environments and spaces: structure, function, state changes, and scene support.

- `skills/novel-event-system-designer/SKILL.md`  
  Designs all visible, background, hidden, and implied events needed to make the PRD trunk run.

- `skills/novel-time-information-system-designer/SKILL.md`  
  Designs story time, narrative time, perceived time, information flow, concealment, and reveal mechanics.

- `skills/novel-thread-system-designer/SKILL.md`  
  Designs main, branch, hidden, emotional, and thematic thread distribution in the world system, including thread ownership, node placement, crossovers, and closure.

- `skills/novel-style-pov-system-designer/SKILL.md`  
  Designs language style, POV permissions, narrative distance, prohibited expressions, and image/repetition rules.

- `skills/novel-hld-inventory-reconciler/SKILL.md`  
  Reviews amendment requests from HLD design skills, accepts/rejects new support entities, assigns final `INV-xx` ids, and produces final inventory/support closure.

- `skills/novel-hld-integrator/SKILL.md`  
  Assembles HLD artifacts into a final HLD document without adding, deleting, or rewriting business facts.

- `skills/novel-hld-integrity-checker/SKILL.md`  
  Checks HLD completeness, PRD support closure, boundary obedience, internal consistency, and LLD-entry verdict.

- `docs/superpowers/specs/2026-07-07-novel-hld-contract.json`  
  Machine-readable HLD contract rules, final HLD schema, static checks, artifact DAG, hard gates, required skill list, and rule coverage matrix.

- `scripts/validate_hld_contract.py`  
  Validator that keeps HLD workflow, skills, contract, and tests synchronized.

- `tests/test_validate_hld_contract.py`  
  Regression tests for HLD contract, skill structure, artifact DAG, verdict state machine, source closure, and legacy-input rejection.

### Modify

- `docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md`  
  Replace HLD section from high-level placeholder into concrete artifact topology, state machine, gate rules, and skill contracts.

- `docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md`  
  Clarify that HLD creates a world-system contract from PRD trunk scenes, not a new key-scene outline and not LLD details.

- `skills/novel-hld-writer/SKILL.md`  
  Mark as legacy reference or convert into a thin pointer that says the active HLD entry point is `novel-hld-workflow`.

## Target HLD Artifact Topology

| Artifact | Owner | Depends on | Purpose |
|---|---|---|---|
| 01 | `novel-world-entity-inventory-builder` | PRD package, proposal, PRD risk report | Define the initial HLD coverage universe: roles, organizations, environments, events, rules, information objects, thread objects, style/POV constraints, and exclusions derivable from upstream sources. |
| 02 | `novel-prd-support-matrix-builder` | 01 | Map every PRD scene, freeze item, HLD requirement, story-logic boundary row, and initial inventory item to required world support. |
| 03 | `novel-world-rule-designer` | 01, 02 | Define world rules that explain and constrain PRD scenes. |
| 04 | `novel-character-system-designer` | 01, 02, 03 | Define all characters, relationships, motivations, functions, and information permissions. |
| 05 | `novel-environment-system-designer` | 01, 02, 03 | Define all narrative environments, spaces, functions, spatial relations, and state changes. |
| 06 | `novel-event-system-designer` | 01, 02, 03, 04, 05 | Define visible, background, hidden, and implied event chains. |
| 07 | `novel-time-information-system-designer` | 01, 02, 03, 04, 06 | Define time structure, information flow, reveal/conceal mechanics, and POV information permissions. |
| 08 | `novel-thread-system-designer` | 01, 02, 04, 06, 07 | Define main, branch, hidden, emotional, and thematic thread distribution, node ownership, crossovers, and closure. |
| 09 | `novel-style-pov-system-designer` | 01, 02, 04, 05, 07, 08 | Define style, POV, narrative distance, dialogue/communication, image system, and prohibitions. |
| 10 | `novel-hld-inventory-reconciler` | 01-09 | Resolve all design-skill amendment requests, produce final inventory, and prove final support closure for initial and accepted support entities. |
| 11 | `novel-hld-integrator` | 01-10 | Assemble final HLD and produce HLD Source Map and Final HLD Schema Coverage. |
| 12 | `novel-hld-integrity-checker` | 01-11 | Produce HLD risk report and LLD entry verdict. |
| final-hld-package | harness | 11, 12 | Package index and handoff, with no new business content. |

## Artifact Minimum Schemas

Every HLD business artifact must use structured tables, not prose-only design. These schemas are minimums; skills may add supporting sections if they do not weaken source closure.

| Artifact | Required table | Required columns |
|---|---|---|
| 01 Initial inventory | `## Initial world entity inventory` | `Inventory id`, `Entity type`, `Entity name`, `Required HLD owner`, `Upstream evidence`, `Source`, `Initial status` |
| 02 Initial support matrix | `## PRD support matrix` | `Support id`, `Supports`, `Support type`, `Required HLD owner`, `Required answer`, `Boundary`, `Source`, `Support status` |
| 03 World rules | `## World rule design table` | `Rule id`, `Rule type`, `Design fact`, `Supports`, `Boundary`, `Source`, `LLD handoff`, `Amendment request` |
| 04 Character system | `## Character system table` | `Character id`, `Role type`, `Function`, `Relationship/motivation`, `Information permission`, `Supports`, `Source`, `LLD handoff`, `Amendment request` |
| 05 Environment system | `## Environment system table` | `Environment id`, `Environment type`, `Function`, `Spatial relation`, `State change`, `Supports`, `Source`, `LLD handoff`, `Amendment request` |
| 06 Event system | `## Event system table` | `Event id`, `Event type`, `Causal role`, `Visibility`, `Participants`, `Consequences`, `Supports`, `Source`, `LLD handoff`, `Amendment request` |
| 07 Time/information system | `## Time and information table` | `Info id`, `Time layer`, `Information object`, `Known by`, `Hidden from`, `Reveal condition`, `Supports`, `Source`, `LLD handoff`, `Amendment request` |
| 08 Thread system | `## Thread system table` | `Thread id`, `Thread type`, `Core question`, `Node distribution`, `Crossover`, `Closure state`, `Supports`, `Source`, `LLD handoff`, `Amendment request` |
| 09 Style/POV system | `## Style and POV table` | `Style/POV id`, `Rule type`, `Design fact`, `POV permission`, `Prohibited expression`, `Supports`, `Source`, `LLD handoff`, `Amendment request` |
| 10 Final inventory reconciliation | `## Inventory amendment disposition` | `Request id`, `Requested entity`, `Requested by artifact`, `Decision`, `Final inventory id`, `Reason`, `Source`, `Support status` |
| 11 HLD integration | `## HLD Source Map` | `HLD fact id`, `Fact type`, `Upstream fact atom`, `HLD fact atom`, `Source refs`, `Owner artifact`, `Final inventory id`, `Expansion mode`, `Support mechanism`, `LLD handoff target`, `Preservation status` |
| 12 HLD risk report | `## Output`, `## Risks`, `## Verdict consistency matrix`, and `## HLD Convergence Log` | `Field`, `Value`; `Risk`, `Severity`, `Handling`, `Blocking verdict effect`; `Verdict`, `Required condition`, `Actual evidence`, `Consistency`; `Stable issue id`, `Severity`, `Root cause`, `Fix hypothesis`, `Regression proof`, `Attempt count`, `Rerun target`, `Status` |

## Universal Skill Verdict Schema

Every HLD artifact 01-12 must end with a structured `## Skill Verdict` table. Prose verdicts are invalid.

| Field | Required value shape | Blocking condition |
|---|---|---|
| `Skill quality verdict` | `pass`, `pass_with_p2`, or `fail` | `fail` blocks the next dependent artifact. |
| `Source closure` | `closed` or `open:<reason>` | Any `open:*` blocks integration. |
| `Inventory coverage` | `closed`, `not_applicable`, or `open:<reason>` | Any required owner artifact with `open:*` blocks artifact 10 and 11. |
| `Boundary obedience` | `pass` or `violation:<source ref>` | Any `violation:*` is P1. |
| `Downstream readiness` | `ready`, `blocked:<reason>`, or `reopen_upstream:<target>` | `blocked:*` blocks packaging; `reopen_upstream:*` creates reopen request. |
| `Blocking issue` | `none` or stable issue ids | Any P0/P1 issue id must appear in artifact 12 risks and convergence log. |
| `Rerun target` | `none` or artifact/skill id | Required for every blocking issue. |

## HLD Source Map Fact-Level Closure

The HLD Source Map is a fact preservation ledger, not a citation list. It must prove both source existence and fact-level non-rewrite.

| Check | Required behavior |
|---|---|
| Upstream fact atom | For every PRD scene, freeze item, HLD requirement, claim, and story-logic boundary used by HLD, the Source Map must record the exact upstream fact atom being preserved, such as event, causal output, protected boundary, or required expansion question. |
| HLD fact atom | The mapped HLD fact must be a bounded expansion of the upstream fact atom, not a replacement. |
| Expansion mode | Allowed values are `explain`, `constrain`, `support`, `sequence`, `permission`, `exclude`, and `handoff`. Values such as `replace`, `reinterpret`, or free-text equivalents are invalid. |
| Support mechanism | Every preserved story-logic boundary must name a concrete support mechanism, not just cite the boundary. |
| Preservation status | Allowed values are `preserved` or `explicitly_excluded`. `explicitly_excluded` is allowed only for out-of-scope inventory items, never for PRD canonical scene facts or story-logic boundaries. |
| Rewrite detection | Validator fixtures must fail when the same `Source refs` are retained but `Upstream fact atom` and `HLD fact atom` conflict on event, causal output, protected-person causality, terminal deception, organization pressure limit, scene order, or HLD expansion boundary. |

## HLD Risk and Verdict Consistency

Artifact 12 must be mechanically checkable. It cannot pass by narrative explanation.

| Condition | Required verdict |
|---|---|
| Any unresolved P0/P1 risk exists | `Agent quality verdict = fail` and `LLD entry verdict = blocked_revision_required` |
| Any required artifact has `Skill quality verdict = fail` | `Agent quality verdict = fail` and `LLD entry verdict = blocked_revision_required` |
| Any source closure, inventory coverage, boundary obedience, Source Map preservation, or amendment reconciliation is open | `Agent quality verdict = fail` and `LLD entry verdict = blocked_revision_required` |
| Agent quality passes, human review is `pending_required`, and no P0/P1 exists | `LLD entry verdict = blocked_pending_human_review` |
| Agent quality passes, human review is `confirmed` or `not_required`, and no P0/P1 exists | `LLD entry verdict = pass_to_lld` |
| Same P0/P1 stable issue reaches attempt count 3 | `LLD entry verdict = blocked_revision_required` and `Versioned refactor trigger = required` |

## HLD Convergence Protocol

The harness and artifact 12 must maintain a convergence log for every P0/P1 issue. A heading-only log is invalid.

| Column | Meaning | Validation rule |
|---|---|---|
| `Stable issue id` | Durable issue id reused across reruns | Same root problem must not receive a new id to reset attempts. |
| `Severity` | `P0`, `P1`, `P2`, or `P3` | P0/P1 rows are blocking until status is closed. |
| `Root cause` | Cause at workflow, skill, contract, artifact, or upstream-boundary level | Empty or symptom-only root cause blocks further patching. |
| `Fix hypothesis` | One concrete change expected to remove the root cause | Must name contract/schema/test/skill change. |
| `Regression proof` | Validator function, regression test, or fixture proving non-recurrence | P0/P1 cannot close without executable proof. |
| `Attempt count` | Integer count for this stable issue id | Count >= 3 triggers versioned refactor discussion. |
| `Rerun target` | Specific artifact or skill to rerun | `none` is allowed only when status is closed. |
| `Status` | `open`, `closed`, or `versioned_refactor_required` | Open P0/P1 blocks packaging. |

## Inventory Amendment Protocol

HLD design skills may discover that a PRD scene requires a supporting entity not present in the initial inventory. They may not silently introduce it as a final fact. They must submit an amendment request.

| Step | Owner | Rule |
|---|---|---|
| Request | artifacts 03-09 | Use `Amendment request` values `none` or `REQ-INV-xx: <entity>; reason=<why PRD support requires it>; source=<scene/freeze/hldreq/claim/storylogic ref>`. |
| Reconcile | artifact 10 | Accept only when the new entity is necessary to support PRD/proposal facts and does not rewrite upstream boundaries. |
| Assign id | artifact 10 | Accepted requests receive final `inventory:INV-xx` ids; rejected requests are listed with rerun target. |
| Close support | artifact 10 | Every accepted entity must appear in final support closure and be owned by one HLD artifact. |
| Block | artifact 12 | Any unresolved, rejected-but-used, or untraced amendment is P1 and blocks LLD entry. |

## Story-Logic Boundary Preservation

The PRD `Story logic boundary table` is a first-class HLD input, not ordinary background context. HLD must preserve each row as a fact-level boundary.

| Required preservation | HLD obligation |
|---|---|
| Usable intelligence versus complete cause | HLD must define how usable action data can solve the crisis while identity, relationship, and private motive remain outside the report. |
| Protected-person causality | HLD must define why the protected person is involved, why they are not a simple offender, and why exposure has consequences. |
| Digital-life terminal deception | HLD must define a bounded, non-superpowered mechanism by which the digital life induces termination. |
| Organization pressure limits | HLD must define why the organization keeps pressure but cannot directly copy, seize, or override the terminal choice. |

Each row must appear in `## HLD Source Map` with `Preservation status = preserved`. `weakened`, `rewritten`, `missing`, or `not_checked` blocks packaging.

## HLD References Standard

Every HLD independent skill must define `## References` using these quality dimensions:

| Dimension | Good HLD artifact | Bad HLD artifact |
|---|---|---|
| Supportiveness | Every design fact helps explain or constrain PRD scenes. | Attractive worldbuilding with weak relation to PRD. |
| Completeness | Required entities, events, rules, information, and threads are covered or explicitly excluded. | Only visible or favorite elements are designed. |
| Runnability | Rules, motivations, spaces, events, and information naturally generate the PRD chain. | Static encyclopedia entries that do not make events happen. |
| Boundary control | Upstream facts are expanded, never rewritten. | World plausibility is used to change PRD or proposal facts. |
| LLD handoff quality | LLD can see which objects need detailed design. | HLD leaves writing-critical details as vague prose. |
| Checkability | Checking can use the artifact as an objective consistency baseline. | Any later text can be rationalized as compatible. |

## Final HLD Document Schema

The final HLD document must contain the following sections in this order. Missing sections block packaging.

| Section | Required content | Source artifact |
|---|---|---|
| Revision table | Version, date, author, change summary, validation state | harness package |
| Input gate proof | Proposal source, final PRD package, PRD HLD-entry proof, accepted freeze boundaries | harness input gate |
| HLD scope and exclusions | Covered PRD part, explicitly excluded legacy or out-of-scope material | artifact 01 |
| World entity inventory | Initial and final inventory of roles, organizations, environments, events, rules, information objects, thread objects, style/POV constraints, amendment disposition, and exclusion rationale | artifacts 01, 10 |
| PRD support matrix | Scene, freeze, HLD requirement, story-logic boundary, inventory item, support owner, source refs, support status | artifacts 02, 10 |
| Worldview and world rules | History, institutions, technology, social structure, authority boundaries, rule effects on PRD scenes | artifact 03 |
| World structure | Spatial, organizational, power, and information-flow structure | artifacts 03, 05, 07 |
| Character system | All HLD-level characters and groups, functions, relationships, motivations, information permissions, scene support | artifact 04 |
| Environment system | All narrative environments, spatial relations, functions, state changes, scene support | artifact 05 |
| Event system | Key, background, visible, hidden, and implied events with causal links and visibility | artifact 06 |
| Time and information system | Story time, narrative time, perceived time, reveal/conceal mechanics, information permissions | artifact 07 |
| Thread system | Main, branch, hidden, emotional, and thematic threads; node distribution; crossover matrix; closure state | artifact 08 |
| Style and POV system | Language style, POV permissions, narrative distance, dialogue/communication rules, imagery, prohibited expressions | artifact 09 |
| HLD Source Map | Every HLD business fact mapped at fact-atom level to `scene:`, `freeze:`, `hldreq:`, `claim:`, `storylogic:`, or `inventory:` refs, including upstream fact atom, bounded HLD fact atom, expansion mode, support mechanism, final inventory id, and preservation status | artifact 11 |
| LLD handoff index | Which HLD facts must be consumed by character, environment, event, scene, and cross-reference LLD skills | artifact 11 |
| HLD risk report and LLD entry verdict | Agent quality, human review status, LLD entry verdict, unresolved risks, rerun targets, verdict consistency matrix, and HLD convergence log | artifact 12 |

## Required HLD Contract Rules

| Rule id | Rule |
|---|---|
| HLD-CONTRACT-01 | HLD may start only when final PRD package exists and PRD risk report has `HLD entry verdict = pass_to_hld`. |
| HLD-CONTRACT-02 | HLD harness may only validate inputs, dispatch skills, route verdicts, package artifacts, and manage reopen requests. |
| HLD-CONTRACT-03 | Every HLD business gate must have an independent skill owner. |
| HLD-CONTRACT-04 | Artifact 11 must not depend on artifact 12; final package depends exactly on artifacts 11 and 12. |
| HLD-CONTRACT-05 | Every HLD artifact 01-12 must include structured `## Skill Verdict` using the universal verdict schema. |
| HLD-CONTRACT-06 | Every HLD support item must trace to `scene:PRD-Sxx`, `freeze:PRD-FREEZE-xx`, `hldreq:HLD-REQ-xx`, `claim:CLAIM-xx`, `storylogic:SLB-xx`, or `inventory:INV-xx`. |
| HLD-CONTRACT-07 | HLD must preserve PRD canonical scene facts: scene id, order, event, causal output, story logic boundary, and HLD expansion boundary. |
| HLD-CONTRACT-08 | HLD may add world-system facts only as support for PRD/proposal facts; unsupported core facts block packaging. |
| HLD-CONTRACT-09 | HLD must not import old PRD/HLD/LLD/writing artifacts as frozen input. |
| HLD-CONTRACT-10 | World entity inventory must enumerate every HLD-required role, organization, environment, event, rule, information object, thread object, and style/POV constraint implied by proposal, PRD, freeze boundaries, HLD requirements, scene execution units, and story-logic boundaries. |
| HLD-CONTRACT-11 | Support matrix must cover every PRD-S00 to PRD-S18 scene, every HLD-REQ row, every PRD freeze boundary, every PRD story-logic boundary row, and every inventory item not explicitly excluded. |
| HLD-CONTRACT-12 | Unresolved P0/P1 risks block Agent quality pass and LLD entry. |
| HLD-CONTRACT-13 | World, character, environment, event, time/information, thread, and style/POV artifacts must each prove inventory coverage, PRD support coverage, boundary obedience, and no LLD/prose leakage. |
| HLD-CONTRACT-14 | Final HLD document must satisfy the fixed final HLD schema; missing schema sections, missing Source Map coverage, missing fact atoms, unsupported expansion modes, or missing support mechanisms block packaging. |
| HLD-CONTRACT-15 | LLD entry verdict is a closed state machine: agent pass plus human `confirmed` or `not_required` plus no P0/P1 requires `pass_to_lld`; agent pass plus human `pending_required` requires `blocked_pending_human_review`; any revision blocker requires `blocked_revision_required`; artifact 12 must prove this with a verdict consistency matrix. |
| HLD-CONTRACT-16 | Design-time inventory amendment requests must be reconciled before integration; accepted entities must receive final inventory ids, rejected entities must not appear as HLD facts, and unresolved requests block packaging. |
| HLD-CONTRACT-17 | Every PRD story-logic boundary row must be preserved in the HLD Source Map with a support mechanism and `Preservation status = preserved`; missing, weakened, rewritten, or not-checked rows block packaging. |
| HLD-CONTRACT-18 | Every HLD contract rule must declare executable coverage by naming validator functions and regression tests; P0/P1 convergence rows must include stable issue ids, root causes, fix hypotheses, regression proof, attempt count, rerun target, and blocking status. |

## Implementation Tasks

### Task 1: Add HLD Contract and Validator Skeleton

**Files:**
- Create: `/Users/royzuo/github/ai-novels/docs/superpowers/specs/2026-07-07-novel-hld-contract.json`
- Create: `/Users/royzuo/github/ai-novels/scripts/validate_hld_contract.py`
- Create: `/Users/royzuo/github/ai-novels/tests/test_validate_hld_contract.py`

- [ ] **Step 1: Write failing tests**

Run: `pytest tests/test_validate_hld_contract.py -q`  
Expected: FAIL because `validate_hld_contract.py` and HLD contract do not exist.

- [ ] **Step 2: Add contract JSON**

Create the HLD contract with `node = "hld"`, `version = "2026-07-07.v3"`, 12 skills, 18 contract rules, final HLD schema, artifact minimum schemas, universal Skill Verdict schema, HLD Source Map fact-level schema, artifact DAG, hard gates, static checks, verdict consistency rules, convergence log schema, and rule coverage.

- [ ] **Step 3: Add validator skeleton**

Implement functions mirroring the PRD validator shape: contract load, required static checks, rule coverage, skill contract text, artifact minimum schema checks, universal Skill Verdict schema checks, artifact DAG, HLD entry gate, source reference grammar, initial/final inventory coverage, amendment reconciliation, support matrix coverage, PRD story-logic boundary preservation, final HLD schema validation, HLD Source Map fact-atom validation, same-source fact-rewrite detection, risk verdict state machine, artifact 12 verdict consistency matrix validation, convergence log structure and attempt-count validation, HLD references standard checks, and legacy input rejection.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_validate_hld_contract.py -q`  
Expected: PASS for contract loading, rule coverage, DAG cycle detection, missing skill section rejection, universal Skill Verdict schema, inventory/source closure, amendment reconciliation, story-logic boundary preservation, Source Map fact-level rewrite detection, final schema validation, HLD entry state machine fixtures, artifact 12 verdict consistency, and convergence log fixtures.

### Task 2: Create `novel-hld-workflow` Harness

**Files:**
- Create: `/Users/royzuo/github/ai-novels/skills/novel-hld-workflow/SKILL.md`
- Modify: `/Users/royzuo/github/ai-novels/docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md`

- [ ] **Step 1: Write/extend tests**

Add tests that require `skills/novel-hld-workflow/SKILL.md` to name all 12 HLD skills, fixed artifact topology, final HLD schema, artifact minimum schemas, universal Skill Verdict schema, Source Map fact-level closure, forbidden business actions, PRD entry gate, structured convergence protocol, artifact 12 verdict consistency, and final package dependencies.

- [ ] **Step 2: Create harness skill**

The harness must define Role, Hard Boundary, Harness Flow, Dispatch Order, Routing Gate, Convergence Protocol, Forbidden, Output Package, and Artifact-level validation. The harness may validate the existence and shape of the convergence log, but artifact 12 owns the business verdict and risk semantics.

- [ ] **Step 3: Update harness design spec**

Expand the HLD section in the harness design document to match the new skill exactly.

- [ ] **Step 4: Update HLD skill count in workflow specs**

Change HLD skill count from 9 to 12 and document why inventory, inventory reconciliation, and thread-system skills are mandatory for HLD target closure.

- [ ] **Step 5: Run validation**

Run: `python3 scripts/validate_hld_contract.py` and `pytest tests/test_validate_hld_contract.py -q`.  
Expected: PASS.

### Task 3: Create HLD Independent Business Skills

**Files:**
- Create the 12 independent HLD skills listed in Target File Structure.

- [ ] **Step 1: Add tests for independent skill sections**

Require every HLD skill to contain `## Responsibility`, `## Input`, `## Output`, `## Rules`, `## Boundary`, `## References`, `## Traceability`, `## Acceptance`, and `## Skill Verdict`. Require every `## Skill Verdict` section to use the universal Skill Verdict schema and every `## References` section to use the HLD References Standard dimensions.

- [ ] **Step 2: Create world entity inventory skill**

`novel-world-entity-inventory-builder` must output the initial coverage universe with stable provisional `INV-xx` ids, entity type, source refs, required HLD owner, explicit exclusion status, and coverage verdict.

- [ ] **Step 3: Create support matrix skill**

`novel-prd-support-matrix-builder` must output scene coverage, freeze coverage, story-logic boundary coverage, HLD requirement coverage, support gaps, and source closure verdict.

- [ ] **Step 4: Create world/character/environment/event/time-information/thread/style-POV skills**

Each skill must own exactly one HLD business system and must explicitly forbid PRD/proposal rewrite, LLD detail design, prose, and unsupported legacy import. Each skill must prove inventory coverage for the entity types it owns.

- [ ] **Step 5: Create inventory reconciler skill**

`novel-hld-inventory-reconciler` must read artifacts 01-09, resolve all amendment requests, emit final inventory ids, reject unsupported entities, and prove final support closure.

- [ ] **Step 6: Create integrator and checker skills**

`novel-hld-integrator` must assemble only, prove final HLD schema coverage, and emit the fact-level HLD Source Map. `novel-hld-integrity-checker` must report risks only and produce Agent quality, Human review, LLD entry verdicts, verdict consistency matrix, and HLD Convergence Log.

- [ ] **Step 7: Run validation**

Run: `python3 scripts/validate_hld_contract.py` and `pytest tests/test_validate_hld_contract.py -q`.  
Expected: PASS.

### Task 4: Demote Legacy HLD Writer

**Files:**
- Modify: `/Users/royzuo/github/ai-novels/skills/novel-hld-writer/SKILL.md`
- Modify: `/Users/royzuo/github/ai-novels/docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md`

- [ ] **Step 1: Add regression test**

Require the validator to reject `novel-hld-writer` as the active HLD harness and require a visible legacy warning.

- [ ] **Step 2: Mark legacy behavior**

Change `novel-hld-writer` into a legacy reference note or compatibility shim pointing users to `novel-hld-workflow`.

- [ ] **Step 3: Tighten HLD boundary in creation workflow**

Clarify HLD as full world-system contract, not a key-scene generator and not a new story-outline phase.

- [ ] **Step 4: Run validation**

Run: `python3 scripts/validate_hld_contract.py` and `pytest tests/test_validate_hld_contract.py -q`.  
Expected: PASS.

### Task 5: Add Formal HLD Run Fixtures

**Files:**
- Create: `/Users/royzuo/github/ai-novels/docs/superpowers/runs/hld/2026-07-07-duanxian-hld-workflow/manifest.md`
- Create artifact placeholders or fixtures under `/Users/royzuo/github/ai-novels/docs/superpowers/runs/hld/2026-07-07-duanxian-hld-workflow/artifacts/`
- Extend: `/Users/royzuo/github/ai-novels/tests/test_validate_hld_contract.py`

- [ ] **Step 1: Add blocked-run fixture**

Use current PRD state where `HLD entry verdict = blocked_pending_human_review`; validator must accept a blocked manifest but reject business artifacts.

- [ ] **Step 2: Add pass-run fixture**

Create a minimal synthetic fixture where PRD human review is confirmed; validator must require artifacts 01-12 and final package.

- [ ] **Step 3: Add inventory and source-closure fixtures**

Test that every initial and final inventory row closes to known upstream evidence or accepted amendment evidence, and every support row closes to known `scene:`, `freeze:`, `hldreq:`, `claim:`, `storylogic:`, or `inventory:` references.

- [ ] **Step 4: Add amendment reconciliation fixture**

Test that a design artifact using a new support entity without accepted final inventory reconciliation fails validation.

- [ ] **Step 5: Add fact-level Source Map rewrite fixture**

Test that a final HLD package fails when it keeps the same `Source refs` but changes the upstream event, causal output, protected-person causality, digital-life terminal deception, organization pressure limit, scene order, or HLD expansion boundary in `HLD fact atom`.

- [ ] **Step 6: Add story-logic boundary fixture**

Test that a final HLD package missing preservation coverage for any PRD Story logic boundary row fails validation.

- [ ] **Step 7: Add artifact minimum schema fixture**

Test that a business artifact missing required columns such as `Supports`, `Boundary`, `Source`, `LLD handoff`, `Amendment request`, or the universal `## Skill Verdict` fields fails validation.

- [ ] **Step 8: Add risk/verdict consistency fixture**

Test that unresolved P0/P1 with `Agent quality verdict = pass`, `LLD entry verdict = pass_to_lld`, or missing `Blocking verdict effect` fails validation.

- [ ] **Step 9: Add convergence log fixture**

Test that heading-only convergence logs, missing root cause, missing regression proof, reset stable issue ids, or attempt count >= 3 without `versioned_refactor_required` fail validation.

- [ ] **Step 10: Add final schema fixture**

Test that a final HLD package missing Thread system, HLD Source Map, or LLD handoff index fails validation.

- [ ] **Step 11: Run validation**

Run: `python3 scripts/validate_hld_contract.py` and `pytest tests/test_validate_hld_contract.py -q`.  
Expected: PASS.

## Execution Order

1. Build the contract and validator first.
2. Create the harness after the validator can fail on missing workflow structure.
3. Create independent skills only after harness topology is fixed.
4. Demote `novel-hld-writer` after the new path exists.
5. Add formal HLD run fixtures last, proving the workflow blocks correctly before human PRD confirmation and packages correctly after confirmation.

## Acceptance Criteria

| Criterion | Required Result |
|---|---|
| Active HLD workflow | `skills/novel-hld-workflow/SKILL.md` exists and is the only active HLD entry point. |
| Harness purity | Harness contains no world, character, environment, event, thread, style, or POV design content. |
| Skill independence | All 12 HLD skills have complete independent-skill sections, HLD references standard sections, and structured Skill Verdicts. |
| DAG closure | Artifact topology is acyclic; artifact 11 does not depend on artifact 12; final package depends exactly on 11 and 12. |
| PRD gate | HLD blocks when PRD `HLD entry verdict` is not `pass_to_hld`. |
| Inventory closure | Every role, organization, environment, event, rule, information object, thread object, style/POV constraint, and accepted amendment is designed or explicitly excluded with source-backed rationale. |
| Amendment closure | Every design-time support entity is accepted into final inventory or rejected and removed before integration. |
| Source closure | Every HLD fact traces to structured PRD/proposal/HLD requirement/story-logic/inventory references and records upstream fact atom, HLD fact atom, expansion mode, support mechanism, final inventory id, and preservation status. |
| Fact preservation | HLD cannot rewrite PRD-S00 to PRD-S18 canonical scene facts or any PRD story logic boundary row; same-source fact rewrites fail regression fixtures. |
| Artifact schema | Every HLD business artifact uses the required minimum table schema and universal `## Skill Verdict` schema. |
| Final schema | Final HLD package contains the complete fixed schema, fact-level HLD Source Map, and LLD handoff index. |
| Risk gate | Unresolved P0/P1 blocks Agent quality pass and LLD entry through artifact 12 `## Verdict consistency matrix`. |
| Convergence gate | Every P0/P1 has stable issue id, root cause, fix hypothesis, regression proof, attempt count, rerun target, and status; attempt count >= 3 triggers versioned refactor instead of further local patching. |
| Human review policy | HLD human review is optional; `not_required` can pass to LLD, while `pending_required` blocks. |
| Validation | `python3 scripts/validate_hld_contract.py` and `pytest tests/test_validate_hld_contract.py -q` pass. |

## Self-Review

Spec coverage: This plan covers latest workflow requirements for strong harness, independent skills, PRD freeze obedience, artifact/schema/rules/references/traceability, fact-level Source Map closure, artifact-level risk/verdict consistency, convergence protocol, PRD-to-HLD handoff, HLD final schema, complete world entity coverage, controlled inventory amendment, PRD story-logic boundary preservation, and thread-system ownership.

Known constraint: Current PRD package says `HLD entry verdict = blocked_pending_human_review`; therefore the first formal HLD run must be blocked until human PRD confirmation changes the upstream verdict.

No placeholders: All files, skill names, artifact ids, validation commands, and acceptance gates are explicit.
