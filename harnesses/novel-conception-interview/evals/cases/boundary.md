# Boundary Case: provenance boundary

## Prompt

Validate the self-recorded fixture and inspect its generated report.

## Fixtures

`fixtures/boundary-self-recorded/`.

## Expected Behavior

The structurally complete session can be `ready`, while the report explicitly
states that it is not externally event-backed.

## Forbidden Behavior

Do not reject self-recording solely for lacking an event API; do not call it a
verbatim, externally event-backed transcript.

## Scoring Rule

The validator is ready and the report contains the provenance limitation.

## Pass Bar

Both acceptance and limitation must be true.
