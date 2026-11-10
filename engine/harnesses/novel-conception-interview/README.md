# novel-conception-interview

The canonical orchestration layer for the repository's novel-conception
interviews. Start with [workflow.md](workflow.md), then run:

```powershell
python validators/validate_harness.py .
python evals/run_evals.py .
python tools/build_release.py .
```

The leaf skills under `engine/skills/` make creative judgments; this harness alone owns
cross-skill order, evidence and approval gates.
