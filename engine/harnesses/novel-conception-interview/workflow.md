# Workflow Contract

> Autonomous-stage migration notice: this file remains authoritative for I0–I5, V1, V2 and
> the V2 interview approval only. Its historical `D1 -> R1` tail is not a valid autonomous V2
> production route. After V2 approval, continue with
> [`conception-autonomous-workflow-v2.md`](../../engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md):
> `B0 -> S1 -> W1 -> E1 -> T1 -> C1 -> Q1 -> P1 -> H1`.

## Stage graph

```text
I0 Intent ─> I1 Subject ─> I2 World ─> I3 Characters ─> I4 Causality ─> I5 Narrative
                                                                          │
                                                                          v
                         V1 deterministic + semantic integrity gate <────┘
                                      │
                                      v
                         V2 HTML author-review brief ─> Author approval
                                                              │
                                                              v
                      autonomous V2 handoff: B0 ─> S1 ─> W1 ─> E1 ─> T1
                                                        ─> C1 ─> Q1 ─> P1 ─> H1
```

This is a DAG with bounded returns, not a collection of skills that may call
one another directly. In particular, I1 never hands off directly to I3: I2
establishes the world in which characters operate.

## Stage contracts

| Stage | Creative owner | Required inputs | Required output | Entry/exit gate |
| --- | --- | --- | --- | --- |
| I0 | intent facilitator | author's idea | intent card + session + `control-projection.json` | author accepts intended meaning and boundaries; projection uses `INT-` IDs |
| I1 | subject designer | I0 completion | subject design + session + `control-projection.json` | I0 `ready`; subject's central conflict is usable; projection uses `SUB-` IDs |
| I2 | world interviewer | I0–I1 completions | world operating contract + session + `control-projection.json` | I1 `ready`; environment, operating logic and limits are coherent; projection uses `WLD-` IDs |
| I3 | character interviewer | I0–I2 completions | character design + session + `control-projection.json` | I2 `ready`; agency and relationships can operate under world limits; projection uses `CHR-` IDs |
| I4 | causality architect | I0–I3 completions | causal storyline + session + `control-projection.json` | I3 `ready`; causes, costs and constraints connect; projection uses `CAU-` IDs |
| I5 | narrative designer | I0–I4 completions | narrative contract + session + `control-projection.json` | I4 `ready`; reveal/POV/time structure can carry the causal story; projection uses `NAR-` IDs |
| V1 | integrity auditor + validators | six contract-version 2.0 completion packets | integrity report + semantic-review packet + `fact-dependency-register.json` | all session and projection validators `ready`; fact register valid; hash-bound semantic verdict must be `pass` with six-area evidence |
| V2 | brief generator | V1 `pass`, six artifacts | immutable HTML review brief + V2 completion | no missing evidence or hidden uncertainty; this stage cannot create author approval |
| V2 author approval | author, recorded as an external event | current V2 completion and exact HTML hash | `author-approval.json` | explicit `approved`, `revise`, or `rejected`; silence is never approval |
| Autonomous V2 handoff | coordinator | current I0–I5 + V1 pass + current V2 completion and approval | immutable source state accepted by B0 | this interview harness stops creating new story facts; B0–H1 are governed only by the autonomous V2 contract |

Every conception run also owns a hash-bound `run-state.json`. Every stage
completion consumes that state and hash-binds every upstream completion. The
state records the current valid I0–I5 completion references; a new stage must
consume those references rather than choose among historical packets. An
active return package blocks every stage except its named target; that target
must carry the same `{path, sha256}` in `return_resolution`. The next run state
records the immutable package plus the target's corrected completion in
`resolved_returns`, and downstream stages must consume that corrected packet.
Every interview session is stored under
`<project>/interview-sessions/<stage>/<session-id>/` with versioned
`plan.vN.json`, append-only-by-contract `events.ndjson`, regenerated `report.md`,
`validation.json`, and `stage-completion.json`. A completion packet names the
design artifact and validation evidence; downstream stages consume the packet,
not a conversational assertion.

Every new I0–I5 completion uses `contract_version: "2.0"` and hash-binds one
`control-projection.json`. The projection must identify the same run, stage and
session, bind the exact design artifact, classify each control's authority, and
bind every control to hashed source line ranges. V1 uses the same contract
version and hash-binds `fact-dependency-register.json`; when no external fact is
needed, the register still contains an explicit `not_applicable` record. These
records are the formal interview-to-B0 interface, not optional summaries.

## Bounded return rules

Only one active return package may exist at a time. It conforms to
`return-package.schema.json`, is registered in `run-state.json`, and states `origin_stage`,
`target_stage`, defect, evidence, requested decision, and affected artifacts.

- I2 may return to I1 only when the subject choice cannot operate in the world;
  it may return to I0 only for a contradiction in intent.
- I3 returns world gaps to I2, not to I1; it returns a central-subject defect to
  I1 and an intent contradiction to I0.
- I4 returns world facts to I2, character agency or relationship facts to I3,
  subject conflict to I1, and authorial intent to I0.
- I5 returns operational-world facts to I2 and causal facts to I4. It never
  silently repairs upstream meaning.
- V1 issues an interview return package. Autonomous Q1 returns are governed by the V2
  `return-request` and autonomous run-state contracts. For an interview return, the named target repeats its session
  with a new plan revision and emits a completion whose `return_resolution`
  hash-binds that package. The run state then records the package and corrected
  target completion as `resolved_returns`; all affected downstream completion
  packets become `superseded` and must be regenerated from the corrected input.
  The origin never rewrites the run state it consumed: it emits a next run state
  with the active return, and the coordinator promotes that validated state.
  References in different directories are compared by resolved path and hash,
  not by identical relative-path spelling.
- If the V2 author decision is `revise`, the harness may create a structured
  return package with origin `V2` only when it hash-binds that exact approval
  packet; the author chooses the affected target stage. A V2 `rejected` decision
  leaves the run `blocked` until the author gives new direction.

Maximum two return rounds per source stage in one conception run. A third
unresolved return produces `blocked` and requires author direction.

## Handoff and approval rules

`ready` means: exact plan presentation was validated, all planned question-answer
pairs were recorded (or an author-approved early close exists), the complete
report was regenerated from the event log and hash-bound, and the design
artifact has an explicit uncertainty register. V1 also requires the semantic
audit. V2 is review-only: its author approval is a separate
`author-approval.json` packet with scope, decision, unresolved items and date.
No downstream agent may infer approval from silence.
