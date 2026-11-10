# Novel HLD Autonomous Rules

## Authority order

1. Versioned schemas and the frozen contract catalog define fields and package profiles.
2. The portable core defines stage meaning and routing.
3. The current sealed work order defines this invocation.
4. Canonical stage JSON defines HLD content.
5. Markdown, HTML, chat and adapter wording are non-authoritative.

## Hard rules

- Preserve upstream `classification`, `open_item`, `authority_class` and canonical value hashes without reinterpretation.
- Keep source authority and HLD ownership in separate fields.
- Use stable IDs and RFC 6901 pointers for cross-artifact references.
- Reject absolute, escaping, missing, unlisted or hash-mismatched paths.
- Copy work-order `event_sequence` and `result_timestamp`; never use local time in deterministic artifacts.
- Keep content packages separate from the package-external result envelope.
- Write JSON as UTF-8 canonical compact JSON with a final LF.
- Treat `additionalProperties:false`, exact file sets and role uniqueness as release-blocking constraints.
- Do not mutate upstream packages, prior revisions, plans, plan states, completions or author events.

## Content boundary

HLD may decide macro position, sequence, function, information boundary and structural relation only within baseline freedom. It may not add or change conception facts, answer author-owned questions, write scene actions/dialogue/sensory prose, or publish novel prose.

## Human approval

Only an external author event can approve, revise, reject, answer a source-resolution question or retarget a superseded revision group. Runtime or skill output cannot impersonate that event.

## Done rule

Never report a run, skill or release ready unless the caller can independently reproduce the validator result from sealed inputs and the parent can determine exactly one next action from the official result envelope.
