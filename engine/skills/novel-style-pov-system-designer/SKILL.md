---
name: novel-style-pov-system-designer
description: Use when HLD artifact 09 must design style, POV, narrative distance, communication rules, image system, and prohibited expressions.
---

# novel-style-pov-system-designer

## Responsibility

Own HLD artifact 09 only: design style and POV execution rules for downstream LLD and writing.

## Inputs

- Artifacts 01-08
- Proposal POV rules, PRD information-flow facts, freeze boundaries
- Methodology reference: `engine/docs/superpowers/references/2026-07-08-hld-methodology-and-best-practices.md`

## Output Artifact

Produce `## Style and POV table` with columns:

| Style/POV id | Rule type | Access policy | Information refs | Thread refs | Reader disclosure mode | Language profile | Design fact | POV permission | Prohibited expression | Supports | Source | LLD handoff | Amendment request |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Artifact Metadata

Every output must include:

| Field | Value |
|---|---|
| Artifact id | `09` |
| Owner skill | `novel-style-pov-system-designer` |
| Run id | HLD run id |
| Upstream package | final PRD package |
| Input artifacts | artifacts 01-08 |
| Output path | artifact path assigned by harness |
| Version | artifact version |

## HLD Fact Trace

Every style/POV fact must include:

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|

Style/POV facts must preserve PRD information boundaries and convert them into downstream expression permissions.

Every `Style/POV id` in the main table must have a matching `Fact trace id`.

## SOP

1. Consume every ready artifact 02 support row assigned to this artifact, then translate proposal and PRD POV limits into concrete permissions.
2. Define all eight rule types: POV, narrative distance, information access, digital-life interiority, dialogue, image system, prohibited expression, and language style.
3. Bind every rule to resolved `info:HLD-07-nn` and `thread:HLD-08-nn` refs, select its fixed access policy and Reader disclosure mode, and use the referenced artifact 07 conceal/reveal state to prevent advance disclosure.
4. Define `Design fact` as `rule=<...>; scope=<info:HLD-07-nn or thread:HLD-08-nn>; effect=<...>`, `POV permission` as `focalizer=<artifact 04 entity name>; permitted=<...>; evidence=<info:HLD-07-nn>`, and `Prohibited expression` as `forbidden=<...>; target=<info:HLD-07-nn or thread:HLD-08-nn>; trigger=<Reader disclosure mode>`. Every reference must be one of the same row's resolved `Information refs` or `Thread refs`. The action fields must express the rule-type behavior: focalization, distance, reveal gate, mediated agency, dialogue qualification, image evidence, identity separation, or register control.
5. For the language-style rule, define `Language profile` as `register=mode:<...>, limit:<...>; syntax=sentence:<...>, variation:<...>; diction=prefer:<...>, avoid:<...>; rhythm=pace:<...>, shift:<...>`.
6. Define LLD handoff instructions that help scene designers write without leaking hidden facts.

## Boundary

Do not write prose samples, dialogue, scene text, or full literary style guide. Do not alter event or information facts to fit a preferred style.

## Rules

- Every style/POV rule must prevent or enable a concrete downstream writing behavior.
- Artifact 09 must consume every ready artifact 02 support row assigned to this artifact through `Supports`; block instead of leaving assigned support unused.
- Rule type must be one of POV, narrative distance, information access, digital-life interiority, dialogue, image system, prohibited expression, or language style.
- Every listed rule type is required at least once. `Access policy` is fixed by Rule type: POV=`limited_focalization`, narrative distance=`controlled_distance`, information access=`reveal_gated`, digital-life interiority=`no_direct_interior`, dialogue=`mediated_dialogue`, image system=`bounded_image_system`, prohibited expression=`hard_prohibition`, language style=`controlled_register`.
- `Information refs` must resolve to artifact 07 as `info:HLD-07-nn`; `Thread refs` must resolve to artifact 08 as `thread:HLD-08-nn`. Neither field may be empty.
- Reader disclosure mode is fixed by Rule type: information access=`reveal_at_information_gate`; all other rule types=`external_inference`. Reader-hidden information may only be handled through those two constrained modes.
- `Design fact`, `POV permission`, and `Prohibited expression` must use the required three-part execution structure; no free-form sentence is accepted.
- `rule`, `permitted`, and `forbidden` must contain behavior specific to their Rule type; generic wording such as "适当", "优美", "自然", "恰当", "good", or "appropriate" is rejected.
- `scope` and `target` must resolve to the row's `Information refs` or `Thread refs`; `evidence` must resolve to the row's `Information refs`; `trigger` must equal the row's Reader disclosure mode.
- A focalizer must resolve to an artifact 04 entity name and may use a concise Chinese name; do not pad a name or other atomic field merely to satisfy a length threshold.
- Only the language-style rule may carry `Language profile`, and it must define `mode`/`limit`, `sentence`/`variation`, `prefer`/`avoid`, and `pace`/`shift`; every other row uses `none`.
- Prohibited expression must name a real failure mode through `forbidden`, `target`, and `trigger`.
- The digital-life interiority rule must use `no_direct_interior`; unrestricted digital-life interiority is blocked.

## References

Good POV rules cover every required execution dimension, use type-specific behavior in the controlled execution and language-profile structures, apply type-specific access and reader-disclosure policies, and bind permissions to exact information and thread boundaries. Bad POV rules use a free-form or vague adjective such as "冷峻", "优美", or "适当", omit a required language directive, or permit facts outside the referenced reveal boundary.

## Traceability

Every row cites source refs and relevant information/thread support.

Provisional inventory refs from artifact 01 may be used before reconciliation. `artifact 10 finalizes inventory`; do not require final `inventory:INV-xx` ids in artifact 09.

## Acceptance

Pass only when style and POV rules are operational, bounded, aligned with information conceal/reveal mechanics, and every ready artifact 02 support row assigned to this artifact is consumed.

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | `pass`, `pass_with_p2`, or `fail` |
| Source closure | `closed` or `open:<reason>` |
| Inventory coverage | `closed`, `not_applicable`, or `open:<reason>` |
| Boundary obedience | `pass` or `violation:<source ref>` |
| Downstream readiness | `ready`, `blocked:<reason>`, or `reopen_upstream:<target>` |
| Blocking issue | `none` or stable issue ids |
| Rerun target | `none` or artifact/skill id |
