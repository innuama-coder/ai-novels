# Input and output contract

## Admission

The sealed work order uses stage `HH1`, exact owner `novel-hld-presentation-fidelity-reviewer`, and action `execute`; the top-level semantic baseline remains current HP1. The exact ordered allowlist is fixed in `runtime-contract.json`: HP1 completion/manifest/machine package and six canonical-model copies, plus sealed HH1-A report/manifest/generation-session/work-order. No directory discovery is allowed.

Hard gates:

- reviewer task ID differs from HH1-A producer task ID;
- candidate report bytes match its internal manifest;
- report `hp1_content_binding` equals the current HP1 package hash;
- allowlist excludes chat, old reports, HTML, render registries, templates, CSS, SVG, and raw conception.
- allowlist excludes sample chapters and all novel prose; prose realization is outside this review's comparison boundary.

## Canonical review

`presentation-fidelity-review.json` contains identity and compared-artifact bindings plus:

- `fact_fidelity`
- `structure_and_relation_fidelity`
- `coverage_fidelity`
- `authority_and_open_item_fidelity`
- `visual_data_fidelity`
- `material_drift_findings[]`
- `reading_budget_validation`
- `decision_retrieval_tests[]`
- `cognitive_overload_findings[]`
- `defect_origin=none|reviewer_local|upstream_content`
- `verdict=pass|revise|fail`

Each fidelity dimension records `verdict`, claims, adversarial challenges, HP1 locators, and report element IDs. Findings identify drift/overload type, affected HRE/HVG IDs, HP1 sources/locators, report evidence, material impact, and requested correction without prescribing rewritten content.

Retrieval codes are exactly `architecture_progression`, `mandatory_storyline_connections`, `core_arc_choices`, `pov_knowledge_boundaries`, `continuity_constraints`, `key_functions_and_climax`, and `open_items_and_lld_boundary`. Every pass answer is derived only from the report and returns non-empty report-element IDs, source IDs, and locators.

`reading_budget_validation` independently recounts author-visible CJK characters, Latin words, and HVG count using the HH1-A fixed formula. It records declared and recomputed values and passes only when they match and remain `<=24`.

## Verdict algebra

- `pass + none`: all five dimensions, budget, and ten retrieval tests pass; both finding arrays empty.
- `revise + reviewer_local`: the review evidence itself is defective and must be redone locally.
- `fail + upstream_content`: report omission, weakening, enhancement, misattribution, visual drift, budget failure, cognitive overload, or retrieval failure; affected report IDs are returned for the composite publisher/router.

## Package

Ready internal package is exactly `presentation-fidelity-review.json`, `review-session.json`, `fidelity-review-execution.json`, `validation.json`, and `package-manifest.json`. The only `stage-result.json` is outside the package, always uses `result_scope=composite_internal`, and never contains a completion. HH1-C consumes only a sealed pass.
