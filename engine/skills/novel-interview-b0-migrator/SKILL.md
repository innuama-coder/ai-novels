---
name: novel-interview-b0-migrator
description: Build and finalize a hash-bound compatibility migration when a previously approved novel-conception interview chain (I0-I5, V1, V2 and its approval) predates the B0 control-projection and fact-dependency contracts. Use it to extract exact Markdown sections into B0-compatible controls and facts. Support either exhaustive migration review or an explicit author process decision delegating compatibility conversion while reserving human review for the final four-part conception report. Never revise story meaning, invent author approval, or create a B0 handoff.
---

# Novel Interview B0 Migrator

Create a compatibility layer without altering the approved interview artifacts. Human
review is optional only when the author explicitly delegates this technical conversion
and reserves review for the final world/story/characters/fragments report.

## Required workflow

1. Read [contract.md](references/contract.md).
2. Prepare `projection-plan.json` against the current I0-I5/V1/V2 completions and V2
   approval. Select exact H2/H3 Markdown headings; never select metadata sections.
3. Build a review candidate:

   ```powershell
   python scripts/build_candidate.py projection-plan.json <new-candidate-directory>
   ```

4. Choose exactly one explicit decision route:
   - For migration-content review, open `migration-review.html` and obtain a decision
     matching [author-decision.schema.json](references/author-decision.schema.json).
   - When the author states that migration is internal work and only the final conception
     is human-reviewed, record that statement with
     [author-process-decision.schema.json](references/author-process-decision.schema.json).
     Do not show or request approval of the migration candidate.
   Silence, an earlier V2 approval, or an agent preference satisfies neither route.
6. Finalize into a different, new directory:

   ```powershell
   python scripts/finalize_migration.py <candidate-directory> compatibility-decision.json <new-final-directory>
   ```

7. Validate independently:

   ```powershell
   python scripts/validate_package.py <candidate-or-final-directory>
   ```

## Hard boundaries

- Preserve source bytes; snapshot them and bind every snapshot by SHA-256.
- Extract a section from its exact heading through the next heading of equal or higher
  level. Reject ambiguous, missing, empty, metadata, or overlapping selections.
- Preserve extracted wording. Do not summarize, combine, repair, classify, or invent it.
- Under item review, every fact classification requires fresh author acceptance. Under
  process delegation, the converter owns classification correctness and Q1 must audit it;
  the author reviews only the final four-part H1 result.
- Candidate projections remain `waiting_author` and are deliberately invalid as B0-ready
  projections.
- Never emit `author-approval.json`, a content-approval assertion, a final handoff, or a B0
  baseline. `migration-finalization.json` only proves that the separately supplied author
  compatibility decision authorizes the conversion route; the autonomous harness owns B0.
- Reject changed snapshots, stale decisions, partial decisions, duplicate IDs, cross-run
  inputs, invalid legacy approval, and non-empty output directories.

## Output contract

Candidate output contains snapshots, six waiting-author control projections, a
waiting-author fact candidate register, source inventory, review JSON/HTML, validation and
`candidate-manifest.json`.

Final output contains the same immutable snapshots, six canonical `ready` projections, a
canonical `ready` fact-dependency register, the supplied compatibility-decision snapshot,
validation and `migration-finalization.json`. See [contract.md](references/contract.md) for
the exact fields and status semantics.
