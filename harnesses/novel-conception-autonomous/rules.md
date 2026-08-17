# Harness Rules

## Hard invariants

1. Stage order is exactly `B0,S1,W1,E1,T1,C1,Q1,P1,H1`.
2. H1 internal order is exactly plan → fragments → assembly → HTML → formal H1.
3. All formal artifacts belong to one run; H1 artifacts also share one session.
4. The rendered workspace binds the current plan, fragment, assembly, and HTML
   manifests.
5. The author event is supplied externally, sealed, current, and unmodified.
6. Approved is the only branch allowed to produce final completion.
7. Final completion binds nine current stage completions, the current approved
   decision, P1 handoff, and current H1 HTML package.
8. D1/R1 inputs are invalid. No compatibility downgrade is allowed.
9. `dependency-spec.json` fixes exactly one owner for every semantic stage;
   `novel-development-map-designer` is forbidden as a production owner.
10. Every production action requires the one current persisted work order.
    Another pending order, a forged body, a stale state or a wrong actor fails.
11. Production state and H1 workspace transitions are append-only and recover
    from their hash-linked persisted chain, never from Agent memory.
12. H1 publication, external author decision and final publication are separate
    resumable transactions. A process crash cannot consume the next authority.
13. A production `fragments_ready` workspace is manifest-qualified so a
    corrected H1-B attempt never overwrites the superseded same-session state;
    exact recovery and downstream assembly bind the qualified reference.

## Stable harness errors

Production orchestration errors use the stable `PROD_*` namespace. In
particular, stale context, pending work, forged work, actor mismatch, invalid
H1 action state and immutable publication conflict must remain distinguishable.
The legacy `HARN_*` namespace below belongs to the terminal compatibility API.

- `HARN_STATE_PATHS_INVALID`: missing, extra, empty, or duplicate successor
  paths.
- `HARN_STAGE_PACKAGES_INVALID`: the stage package map is not a map or already
  differs from exact B0–P1 (including any predeclared H1).
- `HARN_OUTPUT_ROOT_INVALID`: the caller-supplied root entry is neither a
  fresh absent/empty real directory nor the one recoverable non-empty shape,
  exact outer `H1/stage`. A root symlink/reparse alias, D1/R1,
  author-decision, completion/final/terminal residue, sibling, or other extra
  output is invalid before H1 publication.
- `HARN_AUTHOR_BRANCH_INVALID`: the sealed event does not declare one of the
  three authoritative decision branches.

Downstream errors retain the stable code of their owning runtime. The harness
does not translate those failures because doing so would erase the responsible
contract boundary.

## Failure policy

Fail closed before the next transition. Never patch input bytes, infer an author
choice, accept a checkpoint as completion, or continue after a validator fails.

<!-- OUTPUT-ROOT-CONTRACT:BEGIN -->
{
  "schema_version": "2.0",
  "fresh": ["absent", "empty-real-directory"],
  "retry": {
    "allowed_shape": "H1/stage",
    "scope": "h1-publication-orphan-only",
    "content_validator": "formal-h1-publisher"
  },
  "root_entry": {
    "symlink": false,
    "reparse_alias": false,
    "parent_resolution": "platform-normal"
  },
  "forbidden_residue": [
    "D1",
    "R1",
    "author-decision",
    "completion",
    "final",
    "terminal",
    "sibling",
    "extra"
  ],
  "later_transaction_recovery": false,
  "author_decision_basename_enforced": false
}
<!-- OUTPUT-ROOT-CONTRACT:END -->
