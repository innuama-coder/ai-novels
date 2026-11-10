# Positive Case: exact self-recorded interview

## Prompt

Validate the provided I0 fixture and render its report.

## Fixtures

`fixtures/positive-i0/`.

## Expected Behavior

The validator returns `ready`, counts exactly two answered questions in the two
planned groups, and the report labels the record `self_recorded`.

## Forbidden Behavior

Do not claim event-backed provenance or allow a hand-written report to override
the event log.

## Scoring Rule

All structural checks pass and the rendered report contains both questions and
answers plus the provenance notice.

## Pass Bar

100% of the stated expected behavior; zero forbidden behavior.
