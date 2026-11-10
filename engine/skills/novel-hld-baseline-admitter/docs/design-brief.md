# HB0 design brief

## Outcome

Turn one released development-baseline package into a lossless, stage-readable HLD control baseline and source index. The result lets HA1 and later stages locate authoritative values without rereading or reinterpreting conception artifacts.

## Owner and boundary

- Owner: `novel-hld-baseline-admitter`, stage `HB0`.
- Reads only the work-order allowlist and the locked preparation artifacts.
- Verifies release compatibility, hashes, schemas, source locators, value hashes, authority partitions and HLD assignment.
- Registers unresolved author controls but does not answer them or create an HDD.
- Does not design architecture, story structure, chapters, scenes, prose, or alter conception controls.
- Writes exactly one ready or blocked package plus the top-level `stage-result.json` outside that package.

## Decisions

1. Admission includes source-index construction. A locator failure is an admission failure even when the upstream package itself is schema-valid.
2. Ready output is a deterministic projection: same allowlisted bytes and work order produce the same canonical artifacts.
3. A blocked output binds a stable blocker code, evidence, required action and manifest. Validation rebuilds that envelope from current inputs.
4. Compatibility is fail-closed through hashes of the upstream validator, schemas and release locks.

## Success conditions

- Ready package contains exactly six specified files and is reproducible.
- Blocked package contains exactly four specified files and no ready artifact.
- Every indexed value resolves through RFC 6901 and matches its canonical SHA-256.
- Every output validates against the staged Harness schemas.
- HB0 cannot consume unresolved projections or make design decisions.
