# Development Baseline Preparation SOP

## 1. Prepare the request

Create one request from explicit paths. Do not discover “the newest” run and do
not accept a standalone HTML, a P1 directory, or a verbal approval as a source.
Set `replace=true` only when replacing the exact requested output is intended.

Validate the request before touching the destination. `output_dir` and
`source_root` must be fully disjoint: neither may equal, descend from, or
contain the other. Required external resources are runtime preconditions.

## 2. Run formal admission

The runtime validates the producer's own Schemas and closes the hash chain in
this order:

1. release descriptor, compatibility-lock hashes, and exact final-package boundary;
2. final completion and final validation;
3. author decision, approval state, and current ready state;
4. all nine stage completions and their manifest/validation/input-gate package
   bindings;
5. P1 manifest, validation, roles, and artifacts;
6. H1 HTML manifest, validation, and author-decision bindings;
7. Q1 manifest, review, traceability, and no-actionable-finding result;
8. canonical conception models, author controls, indexes, and handoff.

Require each stage completion, manifest, and validation to share one stage
package root. Verify the referenced input gate under `source_root` by path and
hash; preserve the production topology where gates live under
`orchestration/input-gates/` rather than inside stage packages.

For H1, validate the stage-local HTML manifest snapshot, then require its hash
to match the final HTML manifest and require the manifest-bound execution record
to bind that final manifest's exact external path and hash. Do not compare the
snapshot path to the external package path.

The approval state and current state are intentionally different points in the
append-only chain. Do not require the approval state itself to be development
ready.

## 3. Resolve authority

Take authority classifications only from `development-handoff.json`.

For author-owned controls, resolve the materialized interview value and verify
it against the author-control registry. For autonomous design IDs, resolve the
cross-model definition to a canonical model JSON Pointer and verify the value
hash. Never search prose for a convenient sentence and never invent missing
source text.

Resolve each design-index `baseline_artifact` against B0 and each `materialized`
artifact against P1, then require equal hashes before using the P1 copy. These
two references intentionally use different package roots.

Treat primary classifications as exclusive. Treat `open_items` as an
independent flag. Reject only real authority collisions: mandatory vs freedom,
mandatory vs must-ask, or freedom vs must-ask.

## 4. Build the deterministic baseline

For every handoff ID, emit the exact source value and a fixed instruction for
its authority class. Build six inventories from authoritative source IDs and
canonical values. Attach the fixed HLD contract:

- responsibilities HLD owns;
- conception, LLD, and prose work it must not perform;
- capabilities its later delivery must prove;
- unresolved author questions;
- change and escalation policy.

Do not insert an act structure, chapter count, POV plan, scene list, or other
HLD answer. If a required HLD decision is author-owned, preserve it as
`must_ask`; do not edit the upstream handoff.

## 5. Publish transactionally

Generate in a staging directory. For a ready source, write canonical JSON,
derive Markdown from it, compute validation, then compute the manifest. Validate
the complete staging package before publishing. When replacing a prior package,
move it aside and restore it if publication fails. Publish only the complete
branch, then validate the destination again.

For a source that fails admission or deterministic projection, write only the
deterministic readiness report and publish that one-file branch. Never mix
ready and blocked artifacts.

## 6. Revalidate independently

Run:

```powershell
uv run --offline --with jsonschema python scripts/validate_baseline.py <preparation-request.json>
```

The validator re-admits and re-projects the current source. For a ready package
it reconstructs the baseline and all derived files. For a blocked package it
reproduces the current admission or projection failure report. Therefore source
changes, manual edits, stale reports, extra files, missing files, and hash drift
all fail.

## 7. Route failures

| Failure class | Owner |
| --- | --- |
| final closure, release, stage state | conception final/orchestrator |
| external approval or decision binding | author-decision gate |
| P1 package, handoff, index, or authority defect | P1 assembler or recorded originating stage |
| H1 package or author-review binding | H1 presentation chain |
| Q1 review or traceability defect | Q1 reviewer |
| baseline projection or packaging drift | this skill |

Return the narrowest recorded owner and required action. Never repair an
upstream artifact inside the baseline.
