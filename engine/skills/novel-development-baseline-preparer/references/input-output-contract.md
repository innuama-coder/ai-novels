# Development Baseline Input and Output Contract

## 1. Boundary

The baseline is a deterministic view of an approved conception. P1 remains
the design authority. The baseline may route and explain controls for HLD, but
cannot add, delete, reinterpret, or resolve them.

## 2. Invocation input

The sole invocation input is `preparation-request.json`, validated by
`preparation-request.schema.json`. It contains exactly:

| Field | Contract |
| --- | --- |
| `schema_version` | `1.0` |
| `skill` | `novel-development-baseline-preparer` |
| `project_id` | Stable project ID |
| `baseline_version` | Semantic version for this baseline |
| `source_root` | Immutable conception run root |
| `completion_path` | Final completion path inside `source_root` |
| `current_state_pointer` | Current-state pointer inside `source_root` |
| `release_descriptor` | Frozen conception-stage release descriptor |
| `contract_dir` | Producer's formal Schema directory |
| `finalizer_source` | Released finalizer implementation |
| `output_dir` | Destination fully disjoint from `source_root` |
| `replace` | Explicit permission to replace that exact destination |

Relative invocation paths resolve from the request file. The completion and
current-state paths must remain inside `source_root`. The output must be
disjoint from `source_root`: it cannot equal it, descend from it, or contain it.

## 3. Source admission

The runtime, rather than the caller's claims, must prove all of the following:

- frozen `novel-conception-stage@1.0.0` release identity;
- exact match to the skill-pinned descriptor, formal contract catalog, and
  released finalizer hashes;
- exact final-package boundary and released-finalizer snapshot;
- formally valid final completion and final validation;
- external `approved` author decision;
- approval-state to current-state transition, ending at
  `development_status=ready` with no active return;
- all B0/S1/W1/E1/T1/C1/Q1/P1/H1 completions, manifests, validations,
  input-gate references, package roots, and hashes for one `run_id`;
- P1 and H1 manifests, roles, validations, file hashes, and bindings;
- Q1 review with no actionable finding;
- canonical P1 conception, author controls, design index, cross-model index,
  traceability, and development handoff;
- handoff `status=ready` and `next_stage=novel-development`.

For each stage, the completion, manifest, and validation share the stage package
root. The input gate is an external orchestration artifact: it remains inside
`source_root` and is verified by its exact path and hash, but does not need to
be copied into the stage package root.

H1 preserves upstream plan, fragment, assembly, and HTML manifests as snapshots
inside its stage package. The current external HTML package is accepted only
when the snapshot has the same hash and H1's manifest-bound execution record
binds the exact external path and hash used by final completion.

Any failed source condition discovered during admission or deterministic
projection produces the blocked branch. Configuration errors such as an invalid
request Schema or missing contract directory are runtime failures, not
source-readiness results.

## 4. Ready output

The directory contains exactly four files:

1. `development-baseline.json` — canonical HLD input, Schema version `2.0`;
2. `development-baseline.md` — deterministic human projection of the JSON;
3. `baseline-validation.json` — deterministic gate result;
4. `package-manifest.json` — SHA-256 bindings for the three content artifacts
   within the exact four-file ready-package boundary.

The JSON must validate against `development-baseline.schema.json`. It contains:

- release and run lineage with hashes;
- all admission verdicts;
- exact authoritative control bindings;
- complete six-domain inventory;
- fixed HLD assignment and change policy;
- deterministic preservation evidence.

The Markdown is non-authoritative and must equal the runtime rendering byte for
byte. The manifest and validation report must be recomputed after generation;
any drift fails validation.

## 5. Control projection

The three primary authority classes are disjoint:

- `mandatory`: downstream work must preserve the value;
- `freedom`: HLD may choose within the authoritative boundary;
- `must_ask`: the affected HLD choice requires an external author decision.

`open_items` is not a fourth competing authority class. It records unresolved
state and can overlap `must_ask`. An item that is open but in no primary class
is projected with primary classification `open`.

Every projected binding includes its stable ID, primary classification,
`open_item` flag, authority class, domain, root-aware source reference, exact
JSON Pointer locator, exact source value, canonical value hash, deterministic
HLD instruction, and unresolved-preservation flag.

Author-owned INT/SUB/WLD/CHR/CAU/NAR controls resolve from materialized
interview controls and must match the author-control registry hash. Autonomous
design IDs resolve through the cross-model index into a hash-bound canonical
model. Missing, duplicate, conflicting, or unresolvable authority blocks.

In the authoritative design index, `baseline_artifact` resolves from the B0
package root and `materialized` resolves from the P1 package root. Both copies
must exist, validate by hash, and have the same content hash. Do not interpret
the B0-relative source path as a P1-relative path.

## 6. Design inventory

The ready baseline must contain nonempty, source-addressable inventories for:

- storylines;
- world;
- environments;
- events;
- characters;
- narrative controls.

Entries preserve authoritative IDs, locations, values, and hashes. The
inventory is navigation for HLD, not new design content.

## 7. Blocked output

The directory contains exactly `development-readiness-report.json`, validated
by `development-readiness-report.schema.json`. It identifies a stable failure
code, evidence, exact owner, and one bounded required action. Revalidation must
repeat admission and deterministic projection and reproduce the same report
from the current source; stale reports fail.

No baseline, Markdown, validation report, or ready manifest may coexist with a
blocked report.

## 8. Acceptance

A delivery is accepted only when `validate_baseline.py` returns zero against
the same request and current source. Structural validity alone is insufficient:
the validator reconstructs the canonical JSON and Markdown, recalculates
hashes and reports, checks package boundaries, and compares exact results.
