# Application Spec

The coordinator opens a run folder, executes stages in `workflow.md` order, and
calls a leaf skill only through its stage contract. Before each stage it presents
the plan's exact question total and estimated minutes. After each author answer
it appends and validates the event log. The author receives the rendered full
record and, after V1, a compact V2 HTML brief organized as world, story and
characters. A brief is a review surface, never a replacement for evidence.
