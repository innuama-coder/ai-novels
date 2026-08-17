# H1-A V2 plan and assembly contract

## Authority and files

H1-A reads only the current, validator-ready P1 package and the current H1
workspace. The sole plan artifact is `review-plan.json`; legacy
`h1-review-plan.json`, R1, and D1 are forbidden.

## Plan

Plan entry requires the exact `initialized` workspace bound to the current P1
completion and an explicit `work_title` launch argument. The runtime stores it
as `work_identity` with `metadata_kind=project_display_metadata`, the exact
input-gate artifact reference, and the only legal report title
`《{work_title}》构思人审报告`. `work_title` is the plain work name; an
already quoted title, package label, or report label is rejected rather than
wrapped again. This metadata is not a conception fact.
It must not be inferred from a path, filename, synopsis, or run id.

A controlled Agent must submit, in one task/thread context:

1. `review-task-analysis`
2. `information-architecture`
3. `visual-and-fragment-plan`
4. `ten-minute-budget-test`
5. `final-review-plan`

The final plan contains exactly three boards in world, storylines, characters
order, followed by fragment evidence and an unselected decision. The ten-minute
default path is explicitly the complete **decision-control surface**, not a
claim that every P1 object is fully restated there. A bounded decision-control
registry covers world, storylines, characters and fragment evidence. Every
control is default visible and total default-path reading remains at most 600
seconds.

Every P1 source anchor is retained separately in an exact expandable drill-down
index. A reduction ledger maps each anchor to one or more decision controls and
states whether it supports, refines, constrains or excepts the control. Critical
anchors must be both default-visible and drill-down accessible; structural and
supporting anchors may be drill-down-only. Missing anchors, forged locator/hash
values, unused decision controls and critical-only-drill-down mappings are hard
failures. Source binding proves provenance; it does not by itself prove semantic
equivalence, so the Agent must provide an explicit rationale and must-not-imply
boundary for each reduction.

The Agent-owned `assembly_projection` is presented in
`visual-and-fragment-plan` and copied unchanged into the final plan. It maps
every report field to module ids in the matching section. Control-array mappings
partition all modules in that section; scalar
and constraint mappings may reuse same-section modules. The assembler copies
the mapped module fields and never infers a report category.

The same phase must provide exactly one attributed graph for each role:

| semantic role | section | visual kind | additional minimum |
| --- | --- | --- | --- |
| `control_logic_chain` | storylines | flow | at least 2 nodes and 1 edge |
| `world_environment_map` | world | map | 1 node; edges optional |
| `storyline_architecture` | storylines | flow | 1 node; edges optional |
| `major_event_timeline` | storylines | timeline | non-empty unique lanes; every node binds a lane and temporal label |
| `character_relationship_network` | characters | network | 1 node; edges optional |

Every graph carries stable group/node/edge/text-equivalent IDs, array-order
matching continuous `order`, human-facing label/summary/kind, nullable
group/lane/tier/temporal metadata, explicit edge endpoints/direction/relation,
and per-element P1 source anchors. Non-null group references and edge endpoints
must close inside the same visual. Text-equivalent entries must partition all
groups, nodes, and edges exactly once and bind the exact union of their source
anchors. The visual-level anchors must equal the graph-wide union. Runtime
checks these structural facts and hashes only; semantic selection belongs to
the controlled Agent.

The same phase presents `decision_prompts` and `presentation_bindings`.
Bindings exactly cover every module, visual, brief, and prompt in presentation
order. Each binds the complete element hash and the ordered frozen P1
anchor/value hashes, plus an explicit `must_not_imply` challenge result.
Runtime recomputes these values; it never creates content or chooses anchors.

Every fragment brief explicitly carries `zh-Hans-review-v1`,
`restrained-concrete-scene-v1`、`character-grounded-scene-v1`、third-person limited POV, information limits,
allowed perception channels, a complete before/goal/pressure/obstacle/choice/
consequence/after scene contract, the process-only interiority policy, and the
fragment-local non-authoritative surface-detail policy. These Agent-owned
controls are included in the brief content/value bindings but are hidden from
the default author reading measurement.

All default-visible modules, same-section visuals, fragment slots, and decision
prompts form one ordered visible registry. The author reviews exactly four
content dimensions in order: world, storylines, characters, and fragments.
The fifth path step is only the trailing decision operation and is not a fifth
content dimension. These five path steps cover
the registry exactly and only within their matching kinds. Source coverage
may cite only a path-visible element that actually binds the stated anchor.
Budget items are exactly the five PATH ids in path order with identical
per-step seconds; ghosts, omissions, duplicates, and drift are rejected.

Reading uses the non-configurable `review-reading-baseline-v1`: 400 CJK
characters/minute plus 200 Latin words/minute, summed for mixed text. Every
default-visible graph string is charged once at its actual field occurrence:
title, purpose, group/node label-summary-kind and non-null lane/tier/time,
edge relation-summary-kind-direction and non-null lane/tier/time, and every
text-equivalent string. This explicit field list prevents recursive double
counting and prevents hiding prose inside graph payloads. Each visual adds
10 seconds and each decision prompt adds 15 seconds. Fragment
visible brief text is counted and `target_words_max` is conservatively charged
at the Latin rate. Every path estimate must meet its recomputed minimum and the
five-step total must remain at most 600 seconds.

Plan publication precedes the harness transition from `initialized` to
`planned`. A publish failure must not advance workspace state.

## Assembly

Assembly entry requires the same session's formal H1-B `planned` workspace,
the resulting `fragments_ready` workspace, current plan manifest, and fragment
package. H1-A dynamically invokes the formal H1-B package validator and
continues only on `ready`; it passes the same sealed `plan_input_gate` and
active return request, and H1-B must re-run this skill's full formal plan
validator before accepting the package. It does not duplicate H1-B domain
validation.
The ready workspace must directly hash-chain from the supplied planned state.
H1-A copies fragment text and P1 control values without rewriting either. It
emits JSON and Markdown only; HTML and author decisions remain outside. The
assembled report copies `review_path` and all five visuals in plan order,
recursively replacing only `source_anchor_ids` with their deterministic
`source_ids`. Its title comes only from sealed `work_identity`. The formal
validator recomputes the entire report and rejects omission, reordering,
rewriting, source drift, or title drift.

`fragment-package.json` carries complete fragment records using the report
fragment schema. Their order, ids, titles, review purposes, and P1 source ids
must exactly project the current briefs; text is copied byte-for-byte at the
string level. Assembly execution evidence has the unique file name
`assembly-execution.json` and binds the H1-B planned workspace.

Assembly publication and read-only revalidation precede the harness transition
from `fragments_ready` to `assembled`. Coordinator rejection leaves a valid,
non-current orphan package.

The JSON report retains machine ids, hashes, source bindings and ledgers for
deterministic replay. Markdown and HTML project only author-facing titles and
copy: machine ids remain in invisible `data-*` bindings, fixed navigation and
field labels are natural Chinese, and fragment review-purpose/contract text is
not inserted into the sample prose. Assembly validation rejects visible
machine tokens, fixed English audit labels, nested book-title wrappers and
audit-style wording before publication. H1-C repeats the same visible-text
check over parsed body text while ignoring attributes, styles and escaped
inactive markup.
