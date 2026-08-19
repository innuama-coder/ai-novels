# Design brief

HF1 is the sole transition authority between an author-reviewed HLD and LLD admission evidence. Its purpose is not to interpret content but to prove that the author's sealed decision refers to the exact current HP1/HQ2/HH1/HTML bytes and that the entire upstream chain is still current.

Success means approved produces one immutable `hld-completion.json`; revise projects the author's targets without semantic change; rejected produces a terminal-intent result for the harness. Any stale, missing, ambiguous, consumed, or unresolved evidence fails closed.

Out of scope: HLD edits, author-intent inference, revision planning/routing, run-state mutation, LLD design, or setting `lld_ready` directly.
