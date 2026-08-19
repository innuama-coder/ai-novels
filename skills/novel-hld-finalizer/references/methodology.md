# Methodology

## Content-addressed closure

Treat every input as immutable bytes identified by path and SHA-256. Recompute hashes from disk; never trust copied hash text. Verify the chain from work order to completion, manifest, validation, canonical artifact, author decision and final handoff before creating new evidence.

## Approval is a bound external event

Approval is valid only when an external, current, unconsumed event names the exact HP1, HQ2, HH1 and HTML hashes. Natural-language similarity or chat agreement has no authority. A changed upstream byte invalidates the event rather than being “close enough.”

## Fail-closed finalization

Absence, ambiguity, stale state, unknown target, hash mismatch, non-pass acceptance, active return, or unresolved plan prevents completion. Errors create durable evidence; they never downgrade checks, infer defaults, or silently reuse prior output.

## Deterministic release projection

Use work-order event time, stable ordering, UTF-8, sorted compact JSON, and explicit profiles. Approved generates new completion facts. Revise copies the external event and projects target values unchanged. Rejected records the decision for the harness; neither branch fabricates state.

## Separation of authority

The author decides. HF1 verifies and seals. The router creates return/revision/termination state. The LLD harness later consumes only a router-authorized completion. This prevents finalization code from becoming a hidden editor or orchestrator.

## Verification versus signing

This skill uses SHA-256 content binding and sealed-workspace authority supplied by the harness; it does not claim public-key non-repudiation. Hashes detect byte changes, while external-event authenticity is a harness gate. The distinction is recorded so a digest is never misrepresented as an author signature.
