# Internal H1-B fidelity return transaction

`apply_internal_h1_fragment_return` is the production-owned recovery edge for
an H1-B package that passed mechanical publication but failed a later,
independent semantic fidelity review. It does not broaden `apply_stage_return`
or any skill-owned implementation catalog.

Admission is deliberately narrow:

- current run state has completions through P1, no H1 completion, and no active
  return;
- current H1 workspace is exactly `fragments_ready`, with only its sealed plan
  and fragment manifests;
- the supplied H1-B work order is the immutable order that produced that
  workspace and has an exact consumed marker;
- the fragment manifest is canonical and every `files`, `artifact_roles`,
  `validation`, and `implementation` reference resolves only beneath the
  manifest's single logical and physical package root; backslashes, escapes,
  foreign parents, and stale raw hashes fail before the transaction writes
  anything. Manifest-listed implementation schemas/docs may retain their
  source formatting; only contract-sealed JSON roles and validation must also
  match their canonical JSON hash. `fragments.md` remains a raw-byte artifact;
- `fragment-package.json` is the hash-bound sibling named by the manifest and
  exactly binds the current run/session, preserved P1 completion, and preserved
  H1 plan manifest. Its P1 field is a strict standard `{path, sha256}`
  reference, while the planned workspace retains the strict typed
  `{stage: P1, path, sha256}` completion locator; the transaction normalizes
  only the latter before exact comparison and rejects extra fields, wrong
  stage/path/hash, backslashes, and escaping paths;
- the independent failure artifact is already sealed under
  `reviews/h1-fragment-fidelity/`, binds the current fragment manifest, has a
  nonempty finding set, and has verdict `fail`;
- the routed request is exactly H1 / owner H1-B / resume point H1-B and carries
  only that review ID as evidence;
- any current pending work is the downstream H1-A assemble order, which is
  rejected by the same transaction.

The append-only transaction writes the return request, prepared journal, new
run revision with the active return, a fragment supersession marker, a fresh
return-resolution input gate and H1-B order, and a fresh qualification receipt.
It then points the current H1 workspace back to the same session's immutable
`planned` state. B0-P1 completions and the H1 plan remain unchanged. The old
fragment files are never overwritten or deleted.

The subsequent H1-B acceptance also remains append-only. Production derives
the `fragments_ready` workspace filename from the accepted fragment manifest
hash (`workspace-fragments_ready-<manifest-prefix>.json`). An exact replay
derives the same successor, while a corrected package in the preserved H1
session receives a distinct immutable successor path. The current-workspace
pointer and the following H1-A assemble order bind that exact fresh reference;
portable/non-production coordinator identities retain their legacy filenames.

Runs interrupted after an older worker sealed a state-only prepared intent are
recovered without editing that intent. Reconciliation verifies the exact
pending H1-B order and gate, current planned workspace, accepted manifest and
successor body hash, plus the supersession marker for the colliding historical
workspace. It then appends a deterministic relocation receipt under
`orchestration/h1-workspace-relocations/`, persists the same successor body at
the manifest-qualified path, and consumes the order against that effective
successor. Prepared-only and pointer-gap replay derive the identical receipt;
an untrusted collision, wrong parent, mismatched body, or receipt collision
fails closed.

Recovery replays the same prepared journal. Prepared-only, partially-derived,
complete-with-pointer-gap, and trusted complete states derive the identical
successor, marker, qualification, workspace pointer, gate, and order. Any
collision is rejected before the first transaction write. The fresh fragment
generation workspace/session remains the responsibility of the subsequent
H1-B start; this transaction never creates it.
