# Composite-stage publisher contract

`harness-core/composite-stage-publisher` is deterministic Harness core, not a fifteenth semantic skill. It publishes only `HQ2` and `HH1`; it neither schedules internal tasks nor writes run state.

## Admission

- Accept one sealed publisher work order, matching input gate and composite workspace state.
- Admit the exact ordered internal-task prefix and prove the remaining suffix was not issued.
- Read only the exact `file_allowlist` closure, including every upstream and internal manifest member.
- Revalidate public package profiles, closed manifests, identities, hashes and cross-package bindings.

## Ready publication

- `HQ2` emits the fixed five-file package and a package-external top-level result. Its acceptance document is reference-only and binds both internal results plus current `HB0` and `HP1` completions.
- `HH1` emits the fixed eight-file package and a package-external top-level result. Its four review artifacts are byte-for-byte copies of the three internal task packages.
- Only a ready publication emits `stage-completion.json`.

## Non-ready publication

- Stop on the first non-ready internal result; every earlier task must be ready and every later task unissued.
- Copy exactly the source internal manifest `files` set into `source-internal-package/`, and copy the internal result envelope into `source-internal-stage-result.json`.
- Validate the public blocked, revise or runtime-error condition contract, then remap condition references only to copied bytes.
- Emit `result-manifest.json`, never a completion.

## Atomicity and reproduction

Generation occurs in a staging directory. After canonical paths are committed, deterministic reproduction is run immediately. Any post-commit failure removes the newly committed package and top-level result from canonical paths. A later validation regenerates the complete expected package and result and compares exact filenames and bytes.

## Explicit exclusions

The publisher does not interpret narrative quality, create findings, repair internal output, issue a later internal task, advance the run, answer an author decision or release the HLD.
