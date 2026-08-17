# Codex Installation

Install the complete repo-shaped release bundle. The bundle root must retain:

```text
SKILL.md
skills/<ten exact V2 owner skills>/
harnesses/novel-conception-autonomous/
docs/ai-novel-workflow/
```

Do not extract or install only the adapter. Before first use and every resume,
run `validators/validate_harness.py` from the nested harness directory. A
release invocation additionally requires `dependency-lock.json`; the
dependency validator checks every required skill, public runtime API and
SHA-256 locked file.

Expose the bundle-root `SKILL.md` as the `novel-conception-autonomous` entry.
The scheduler discovers stage owners from `dependency-spec.json`; it never
falls back to a similarly described skill. If users also need direct stage
invocation, register the ten `skills/*/SKILL.md` directories as sibling Codex
skills without moving their directories away from the bundle root.

The historical `novel-development-map-designer` must not be installed from
this release. It is not a V2 dependency or production owner.
