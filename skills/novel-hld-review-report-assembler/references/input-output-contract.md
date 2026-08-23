# Input and output contract

## Admission

The harness supplies a sealed `HH1` work order and input gate. `exact_owner_skill` is `novel-hld-review-report-assembler`; `action=execute`; upstream stages are exactly `[HB0,HP1,HQ2]`. HP1 and HQ2 are current ready completions and HQ2 binds the same HP1 hash. The work order declares the report-schema version and output directory.

Allowed semantic inputs are exactly the ordered roles in `runtime-contract.json`: HP1 completion/manifest/validation, `novel-hld-package.json`, cross-index, traceability matrix, spec, and the six byte-copied canonical models. HH1 state and work-order/input-gate are operational bootstrap inputs. HB0 completion and HQ2 completion/manifest/validation/acceptance are gate evidence only. An accepted HP1 or HQ2 may have been sealed at an earlier coordinator revision than its HH1 consumer; currency is proved by the work order's exact artifact references and the sealed package bindings, not by requiring equal revision numbers. No other file is a content source. In particular, sample chapters and novel prose are neither input nor output of HLD review assembly.

## Canonical report

`hld-human-review-report.json` contains identity and bindings plus these non-empty sections:

1. `title_and_decision_scope`
2. `overall_narrative_architecture`
3. `world_environment_definitions`
4. `character_definitions`
5. `environment_definitions`
6. `storyline_choreography`
7. `character_arc_placement`
8. `pov_information_suspense`
9. `time_space_pacing_tension`
10. `key_scene_functions`
11. `open_items_constraints_and_lld_boundary`
12. `visual_models`
13. `source_bindings`
14. `review_budget`

All section entries are display elements. Report/control elements use `HRE-`; visual models use `HVG-`. Each has `id`, `element_kind`, `conclusion`, `source_ids`, `locators`, `visual_role`, and `review_question`. `element_id`, `HUI-`, DOM, HTML, CSS, and SVG markup are forbidden. Every `(element, source, locator)` pair appears exactly once in `source_bindings`.

The ten HLD domains are the ten sections after title and before visuals; all must be non-empty. `world_environment_definitions` contains exactly five macro cards: city/region, local people/daily life, social order/public atmosphere, technology/infrastructure, and climate/physical environment. Together they cover every sealed author-locked world source. Each card states a definition, at least two defining features, lived daily experience, story pressure/limits, and details that remain author-open. The city/region card additionally seals a connected narrative network of at least four named cities. Every city states its country, story function, scale, at least two concrete urban sections, street/architecture texture, transport/daily rhythm, seasonal expression, and key story events. The network also states at least four intercity links, each separating travel time, physical movement, information movement, and dramatic function. The local-life card provides at least one distinct ordinary-person portrait for every defined city; each portrait states its city, identity, routine, material details, crisis exposure, and knowledge boundary. The climate card seals a concrete season, story window, weather, light/air, daily effects, and plot effects across the city network. These required decisions may not be reopened as placeholders or author-open details. These cards are not replacements for `environment_definitions`: the latter remains the complete one-card-per-source projection of concrete places. `character_definitions` likewise remains one card per sealed character source. The title section is a presentation-only label: it gives the exact work title and may carry no source IDs or locators. Process state, report version, schema language, validation status, internal IDs, source locations, and workflow instructions remain machine data and must not be placed in author-visible conclusions.

The author-facing report answers only: what story this is, how it develops, how its storylines meet, what changes for the characters, how information and suspense are controlled, where pace and climaxes land, which scenes must work, and which genuinely unresolved choices require the author. `review_question` is retained for machine completeness, but only questions in `open_items_constraints_and_lld_boundary` are author-visible; all other questions are internal review prompts.

`review_budget.formula` is exactly `CJK/500 + Latin/250 + visuals*0.25`; counts are recomputed from all author-visible definition fields and ordinary display-element conclusions, visual roles, and review questions. `estimated_read_minutes` is rounded to four decimals and must be `<=18`. The allowance exists for concrete city, season, ordinary-person, character, and place definitions; it never authorizes process notes or audit prose.

Each character or concrete-place card keeps its sealed baseline definition as the first source/locator pair. When a later canonical HLD model has legitimately refined that same entity, the card may append one or more current-model pairs. Every appended model object must explicitly cite the card's baseline source ID through `source_refs` or `source_authority_refs`; unrelated entities, another baseline card, and unsealed material are rejected. This permits an author-approved HLD correction to reach the report without silently rewriting or discarding the original definition.

Author-visible fields must use concrete subject-action-consequence prose. Machine-facing city networks, resident portraits, season profiles, source IDs, and locators remain exact but hidden. Their required author-facing counterparts are `city_stories`, `route_stories`, `ordinary_people_stories`, and `season_story`. The runtime rejects machine/process wording, dense semicolon compression, exact substantive repetition, and incomplete reader-story coverage before canonical output.

## Internal package

Ready package closure is exactly:

- `hld-human-review-report.json`
- `generation-session.json`
- one or more `generation-evidence/*.json`
- `report-assembly-execution.json`
- `validation.json`
- `package-manifest.json`

The single `stage-result.json` sits outside the package, has `result_scope=composite_internal`, `result=ready`, `completion_ref=null`, and a non-null `internal_manifest_ref`. HH1-A never emits a stage completion.

Local report defects produce `revise` evidence. Missing or unsealed HP1 conclusions produce `blocked` evidence with `blocker_class=upstream_defect`. A post-admission execution fault produces sealed `runtime_error` evidence. Input closure and hash mismatches fail admission before canonical content is written. The harness, not the skill, resolves routing.
