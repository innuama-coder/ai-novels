# Scope Definition

## Mission

Create a durable conception record that lets an author review the world, story
line and characters before prose development, while preserving how every
material decision was obtained.

## Non-goals

This harness does not draft chapters, choose an author's values, claim external
research without sources, guarantee commercial quality, or turn a summary into
a proof that an interview occurred.

## Target runtimes

Codex is the current fully mapped runtime. Claude, Gemini, OpenClaw and Hermas
ship portable adapters with their limitations explicitly documented.

## Assumptions

The runtime can persist JSON and Markdown files. It may not provide an event
API; in that normal case, records are correctly marked `self_recorded`.
