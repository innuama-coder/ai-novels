---
name: novel-development-baseline-preparer
description: Prepare or validate the hard-gated novel-development baseline that starts HLD from a frozen, author-approved novel-conception-stage@1.0.0 run. Use when converting the conception final package into an exact, traceable HLD input, or when diagnosing why that transition is blocked. Do not use it to redesign the conception, create HLD/LLD, or write prose.
---

# Novel Development Baseline Preparer

## Mission

Convert one released conception run into one deterministic HLD input package.
This skill is a gate and lossless projection, not a creative design step.

## Read before acting

Read completely:

1. [references/input-output-contract.md](references/input-output-contract.md)
2. [references/sop.md](references/sop.md)

Use the executable runtime. Do not hand-author, patch, or infer a ready baseline.

## Owned work

- Validate release identity, final closure, author approval, all nine stage
  completions and package closures, P1/H1/Q1 integrity, run identity, hashes,
  and current state.
- Resolve every handoff control to its authoritative P1 value and stable ID.
- Project exact values for mandatory controls, freedoms, author questions, and
  open items without changing authority or uncertainty.
- Inventory HLD-relevant storylines, world, environments, events, characters,
  and narrative controls.
- Attach the fixed HLD responsibility, prohibition, capability, and escalation
  contract.
- Produce and revalidate exactly one ready or blocked package.

## Forbidden work

- Do not add or revise themes, endings, storylines, rules, environments,
  events, characters, or narrative policy.
- Do not decide acts, chapters, pacing, POV allocation, reveal schedules,
  scene functions, or any other HLD answer.
- Do not produce LLD material or prose.
- Do not approve author-owned questions or edit upstream artifacts.
- Do not use H1 presentation text as design authority; P1 remains authoritative.

## Execute

1. Create one `preparation-request.json` that validates against
   [references/preparation-request.schema.json](references/preparation-request.schema.json).
2. Run from this skill directory:

   ```powershell
   uv run --offline --with jsonschema python scripts/prepare_baseline.py <preparation-request.json>
   ```

3. Interpret the exit code:
   - `0`: ready package generated and validated;
   - `2`: source fails admission or deterministic projection; a blocked report was generated;
   - `1`: request or runtime failure; the skill did not complete.
4. Independently revalidate the generated branch:

   ```powershell
   uv run --offline --with jsonschema python scripts/validate_baseline.py <preparation-request.json>
   ```

A nonzero validation exit means the package is not deliverable.

## Hard outcomes

### Ready

The output directory contains exactly:

- `development-baseline.json`
- `development-baseline.md`
- `baseline-validation.json`
- `package-manifest.json`

All four files must be deterministic projections of the currently admitted
source. Editing any one after generation invalidates the package.

### Blocked

The output directory contains only `development-readiness-report.json`. Its
failure code, evidence, owner, and required action must match the current
source failure. A stale or manually altered report is invalid.

## Decision rules

- `mandatory_controls`, `development_freedoms`, and `must_ask` are mutually
  exclusive primary authority classes.
- `open_items` is an independent unresolved-state flag. It may overlap
  `must_ask`; such an item remains author-owned and unresolved.
- A `must_ask` item blocks only affected HLD decisions, not baseline creation.
- An open item proceeds only while HLD can preserve it unresolved.
- Missing or conflicting authority blocks preparation and is routed upstream;
  this skill never repairs conception.
- The approval state records the author decision and remains
  `development_status=not_ready`; the later current state must prove the
  authorized transition to `development_status=ready`.

## Completion report

Report the branch (`ready` or `blocked`), output path, source `run_id` when
available, baseline version, validation result, and bounded next action. Never
claim HLD has started.
