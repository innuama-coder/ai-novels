# Delivery Spec

For each I-stage, deliver one design artifact plus a session evidence directory:

```text
interview-sessions/I#/session-id/
  plan.v1.json [plan.v2.json ...]
  events.ndjson
  report.md
  control-projection.json
  validation.json
  stage-completion.json
```

Each I0–I5 completion uses contract version `2.0`, binds the listed control
projection and its design artifact by SHA-256, and exposes its uncertainty
register and exact input completion references. Each projected control binds
one whole H2/H3 section; its heading and string value must exactly reproduce
that section's heading and non-blank body. Partial sections, multiple ranges,
structured rewrites and hash-valid paraphrases are rejected.

The V1 bundle contains `interview-integrity-report.md`, `semantic-review.json`,
`fact-dependency-register.json`, `validation.json`, and a contract-version 2.0
`stage-completion.json`. V1 must consume and canonically revalidate all six
current I-stage completions.

V2 delivers one immutable HTML review brief and its completion. The author's
decision is a separate external `author-approval.json` event that binds the
exact HTML hash; V2 does not create or infer it. Once the current V2 completion
and explicit approval are present, this harness delivers only the immutable
I0–I5/V1/V2/approval evidence chain to autonomous B0. A development map,
conception review, autonomous design package, and H1 human-review report are
not interview deliverables.
