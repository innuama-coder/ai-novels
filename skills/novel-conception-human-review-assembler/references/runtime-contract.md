# H1-A V2 runtime contract

`scripts/run_v2.py` is the sole H1-A production runtime. The Agent authors the
five ordered review-plan phase submissions. Python validates, seals, publishes,
and coordinates state; it does not invent review semantics or rewrite P1.

The five generation phases are an execution protocol, not five author-facing
content dimensions. The report exposes exactly four content dimensions—world,
storylines, characters, and fragments—followed by one decision operation.

## Exact production sequence

1. Start from the current validator-ready P1 package, its exact H1 input gate,
   and an `initialized` workspace bound to the same run and P1 completion.
2. Call `run_plan()` once with exactly the five `PLAN_PHASES` submissions and
   `work_title`. It validates the complete plan, publishes the immutable plan
   package, and requests the `initialized -> planned` transition.
3. Let `novel-conception-fragment-writer` consume that exact published plan and
   `planned` workspace. It must publish a ready fragment package and produce the
   corresponding `fragments_ready` workspace in the same H1 session.
4. Give the deterministic candidate report to a separate task using
   `novel-conception-presentation-fidelity-reviewer`. It must read only the
   sealed P1, plan, fragments, source inventory and candidate report, and
   return a passing `presentation-fidelity-review.json`.
5. Call `run_assemble()` once with the exact P1, plan package, plan gate,
   `planned` workspace, fragment package, `fragments_ready` workspace, and the
   coordinator-issued assembly workspace, plus that exact independent review.
   It formally revalidates both
   upstream packages, deterministically assembles the report, publishes it,
   and requests the `fragments_ready -> assembled` transition.

`run_plan()` and `run_assemble()` are the only production entry points owned by
H1-A. The other scripts in this skill and `validate_plan_package()` /
`validate_assembly_package()` are diagnostic or read-only validation surfaces;
they cannot independently prove H1-A execution.

## Storyline time-spine presentation contract

When S1 provides `TPH-*`, `MS-*`, and `NM-*` controls, the
`major_event_timeline` is the principal human-facing storyline view. It must:

- place milestones sharing one temporal phase at the same horizontal position;
- use lanes to preserve parallel storylines and show their convergence;
- expose every temporal phase, milestone, and narrative marker from S1;
- distinguish at least setup, probe, turning point, climax, and payoff;
- form one connected progression graph rather than unrelated mini timelines.

The timeline presents S1's abstract story development. It may bind T1 events as
realization evidence, but it must not invent, reorder, or replace S1 controls.
The storyline architecture graph remains complementary and cannot substitute
for the time spine.

## Hard prohibitions

- Do not handwrite or edit the published plan, report, validation, manifest, or
  workspace transition.
- Do not substitute the old R1/D1 report scripts or an old H1 plan.
- Do not call assemble before a formally ready H1-B package exists.
- Do not publish an assembly without a passing independent fidelity review;
  the H1-A planner and H1-B writer may not act as that reviewer.
- Do not mix run IDs, H1 session IDs, P1 completions, gates, workspace states,
  active returns, logical package paths, or package manifests.
- Do not treat an H1-A package as the top-level H1 completion or author approval.

Any changed P1, plan, fragment package, gate, workspace, return, or coordinator
state invalidates the current operation and requires the owning stage to rerun.

The author-facing projection is distinct from the machine report. JSON keeps
all immutable ids and bindings, while Markdown headings use author titles and
natural Chinese labels. The plan supplies a plain `work_title`; the runtime
derives exactly `《作品名》构思人审报告` and rejects pre-wrapped legacy labels.
Both H1-A assembly validation and H1-C HTML validation apply the same visible-
copy lint before publication. Internal ids may survive only in non-visible
machine fields or `data-*` attributes.
