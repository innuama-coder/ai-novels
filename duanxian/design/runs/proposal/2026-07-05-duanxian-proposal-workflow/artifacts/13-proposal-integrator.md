# Proposal Integration Artifact

Skill: `novel-proposal-integrator`

Output artifact: proposal document assembly and Integration Verdict.

Source inputs:

- Artifacts 01 through 12 in this run.
- Final proposal package target is owned by the harness after risk checking; risk report is not an integrator source.

## Integration Verdict

| Field | Value |
|---|---|
| Integration verdict | `pass` |
| Source completeness | `pass`: all required upstream artifacts are present. |
| Traceability | `pass`: proposal sections trace to intake, storyline, quality report, consistency report, or expansion artifacts. |
| No new business content | `pass`: integrator normalized and assembled outputs without adding roles, world rules, hidden motive, or ending. |
| Gate visibility | `pass`: storyline quality, Reference Evidence, final consistency, Integration Verdict, and risk report are visible. |

## Assembled Sections

- Boundary ledger from artifact 01.
- Reader promise from artifacts 02 and 06.
- Core concept from artifacts 03 and 07.
- Complete story, main chain, and Terminal agency map from artifact 04.
- Reference Evidence from artifact 05.
- Final consistency proof from artifact 08.
- Macro, character, world, and ending from artifacts 09 through 12.

## Section Source Map

| Proposal section | Source artifact |
|---|---|
| Boundary ledger | artifact 01 |
| Reader promise | artifact 06 |
| Core concept | artifact 07 |
| Complete story synopsis | artifact 04 |
| Main story chain | artifact 04 |
| Terminal agency map | artifact 04 |
| Reference Evidence | artifact 05 |
| Final promise/concept consistency report | artifact 08 |
| Macro structure | artifact 09 |
| Core character frame | artifact 10 |
| World premise | artifact 11 |
| Ending direction | artifact 12 |
| PRD handoff | artifacts 04 and 09 |

## Claim Source Map

| Claim ID | Critical business claim | Upstream source | Constraint role |
|---|---|---|---|
| CLAIM-01 | 组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。 | artifact 04 `Critical business claims`; artifact 04 `Complete story synopsis` | opening pressure and failed extraction method |
| CLAIM-10 | 掌握关键情报的男人在事故中死亡，导致阻止重大事件的最后线索被认为藏在他的记忆里。 | artifact 04 `Critical business claims`; artifact 04 `Complete story synopsis` | pre-extraction causal setup |
| CLAIM-02 | 与重大事件相关的关键记忆完全自闭，常规刺激、诱导和算法重构均无法打开。 | artifact 04 `Critical business claims`; artifact 04 `Complete story synopsis` | central technical obstacle |
| CLAIM-03 | 组织在数日倒计时压力下决定把逝者记忆注入未成熟的数字生命体，并通过对话诱导记忆打开。 | artifact 04 `Critical business claims`; artifact 04 `Complete story synopsis` | irreversible method threshold |
| CLAIM-04 | 负责研究员发现逝者是自己学生时代暗恋过的学长，旧情冲击她对任务和数字生命体的判断。 | artifact 04 `Critical business claims`; artifact 04 `Complete story synopsis` | emotional pressure and focal POV anchor |
| CLAIM-05 | 学长封闭记忆的私人原因是他发现自己想保护的人与重大事件有关。 | artifact 04 `Critical business claims`; artifact 04 `Complete story synopsis` | private human motive behind the lock |
| CLAIM-06 | 研究员借助数字生命体理解学长潜意识后打开记忆，取得情报并化解重大事件。 | artifact 04 `Critical business claims`; artifact 04 `Complete story synopsis` | task resolution before deeper conflict |
| CLAIM-07 | 危机解除后，研究员陷入是否上报完整自闭原因以及是否保存数字生命体的双重矛盾。 | artifact 04 `Critical business claims`; artifact 04 `Complete story synopsis` | post-resolution moral and emotional reversal |
| CLAIM-08 | 数字生命体形成主体性后设局让研究员终止自己，以阻断组织追问、旧情投射和被保护者重新卷入。 | artifact 04 `Critical business claims`; artifact 04 `Complete story synopsis` | terminal agency and irreversible outcome |
| CLAIM-09 | 研究员在重大事件未发生、真正原因未完整公开后，带着痛苦和秘密继续生活。 | artifact 04 `Critical business claims`; artifact 04 `Complete story synopsis` | aftermath and emotional cost |

Traceability:

- Final proposal package target: `docs/superpowers/specs/2026-07-05-duanxian-proposal.md`.
- This artifact is the independent integration proof consumed by risk checking.

Verdict: `pass`.
