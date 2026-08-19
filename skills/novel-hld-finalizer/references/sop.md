# SOP

1. Validate work-order/input-gate identity, stage, owner/version/implementation, mode, state ref, revision-plan refs, run, revision, exact upstream order, and exact input roles.
2. Recompute every allowlisted hash; stop on the first mismatch without creating completion.
3. Load current run-state. Require `waiting_author_decision`, `current_stage=null`, no active return, no revision plan/state, and exact accepted-completion chain.
4. For each HB0-HH1 completion: verify canonical `path/sha256`, completion and manifest hashes, the public acyclic envelope (`manifest` closes content excluding itself and `stage-completion`; completion binds manifest/validation/canonical), exact member hashes/artifact roles, stage order, ready status, run identity, owner implementation, upstream topology and readiness bindings. Preserve historical revision and return-binding facts; do not mistake them for staleness when the current accepted chain binds them exactly. Accept the composite publisher identity for HQ2/HH1.
5. Verify HP1 manifest binds package/handoff/cross-index; HQ2 manifest/completion bind a ready acceptance whose HP1 and HB0 completion refs are exact; HH1 manifest binds HTML and render registry.
6. Verify the external author decision is current, unconsumed, external, and bound exactly to HP1/Q2/HH1/HTML.
7. Branch only on the sealed `decision` value.
8. Approved: require zero targets; revalidate handoff/Q2 binding; generate final validation, completion, execution, manifest, then external top-level ready result.
9. Revise: require targets; resolve each kind/ID; parse the restricted RFC6901 locator and prove it addresses current author text or that target's requested change; copy author decision bytes; value-copy targets to revision report; generate external-author-request revise result. Generate no completion.
10. Rejected: require zero targets; generate gate/blocked evidence and `author_rejected` result. Generate no completion.
11. Validate exact package profile, hashes, result conditional fields, and forbidden artifacts.
12. Repeat execution against the same fresh inputs in evaluation; outputs must be byte-identical. Leave all routing and state transition to the harness.
