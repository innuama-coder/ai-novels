# H1 human-readability review

This production-owned contract is deliberately outside the shared autonomous
schema catalog. It therefore does not change the sealed B0--P1 implementation
identity.

Before H1 publication, an independent reviewer must cover the author-facing
report and all fragment texts and return `pass` on these ordered dimensions:

1. `natural_zh`
2. `readability`
3. `humanized_character_voice`
4. `scene_not_spec`
5. `excludes_internal_ids_and_audit_jargon`

The review binds the exact rendered HTML, report, fragment manifest, fragment
package, and ordered fragment text hashes. A post-publication failure also
binds the typed H1 completion locator and H1 manifest. Every failure finding
names its dimension and contains an exact substring from the bound report or
fragment.

The prepublish review must have no findings and all five dimensions must pass.
The failure review must have at least one failing dimension and at least one
bound finding. Reviewer task and thread identities must differ from both the
plan and fragment producer identities.

The only internal failure route is H1 to `H1-A-plan`. It is legal solely while
the run is `waiting_author` with no author decision, pending work order, or
active return. It invalidates the complete H1 suffix, preserves B0--P1, creates
a fresh initialized H1 workspace, and never writes an author decision.
