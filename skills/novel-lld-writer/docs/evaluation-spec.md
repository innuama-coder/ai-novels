# Evaluation Spec

## Objective Gate

Run:

```powershell
C:\Users\54256213\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe skills\novel-lld-writer\scripts\validate_lld_structure.py <artifact> --json
```

The objective gate must return `pass` for complete LLD artifacts and `fail` when required sections are missing or forbidden boundary drift is detected.

## Semantic Review Verdicts

Use only:

- `pass`: all required dimensions are acceptable and no blocker exists.
- `revise`: one or two dimensions need improvement, with no blocker.
- `fail`: any blocker exists or any required dimension is absent.

Do not use `blocked` as a final verdict.

## Review Dimensions

### HLD Inheritance

Pass:

- The LLD explicitly traces the HLD character architecture, route nodes, key scene functions, spaces, and POV/style constraints.
- The LLD does not alter PRD direction or HLD architecture.

Fail:

- The LLD invents a new route, role arc, key scene function, theme, or style baseline.

### Character Detail

Pass:

- Characters include behavior patterns, language cues, motivation triggers, scenario-specific reactions, and continuity markers.

Fail:

- Characters remain high-level summaries or become prose scenes.

### Space Detail

Pass:

- Spaces include sensory state, object state, movement constraints, atmosphere, and role-space interaction.

Fail:

- Spaces are only named locations or drift into worldbuilding beyond HLD scope.

### Route-Node Materialization

Pass:

- Each route node receives usable material demands: visible evidence, emotional pressure, information transfer, behavior choices, and continuity hooks.

Fail:

- Nodes only restate HLD functions or rewrite HLD structure.

### Key Scene Blueprint

Pass:

- Key scenes define time, place, scene function, value shift, conflict pressure, turning point, decision, exit state, materials, and writing constraints.

Fail:

- The output contains final prose, full dialogue, or chapter text.

### Writing Handoff

Pass:

- The Writing Agent can draft from the LLD without asking what to show, what to preserve, or what to avoid.

Fail:

- The handoff lacks concrete materials or boundary constraints.

## Blockers

Any of these force `fail`:

- No HLD or equivalent architecture packet.
- Missing character detail, space detail, route-node materialization, or key scene blueprint.
- Redefines PRD or HLD.
- Writes final prose or full dialogue.
- No Writing Agent handoff.
