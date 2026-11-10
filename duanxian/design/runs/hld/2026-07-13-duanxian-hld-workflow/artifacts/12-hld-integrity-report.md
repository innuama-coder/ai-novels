## Artifact Metadata

| Field | Value |
|---|---|
| Artifact id | 12 |
| Owner skill | novel-hld-integrity-checker |
| Run id | 2026-07-13-duanxian-hld-workflow |
| Upstream package | artifacts 01-11 and canonical world facts v3.0 |
| Input artifacts | artifacts 01-11 |
| Output path | artifacts/12-hld-integrity-report.md |
| Version | v3.0 |

## Output

| Field | Value |
|---|---|
| Agent quality verdict | fail |
| HLD human review state | pending_required |
| LLD entry verdict | blocked_revision_required |

## Risks

| Risk | Severity | Source refs | Owner artifact | Rerun target | Handling | Blocking verdict effect |
|---|---|---|---|---|---|---|
| HLD-TRACE-CLOSURE | P1 | scene:PRD-S01,scene:PRD-S03 | artifact 01 | artifact 01 | open: HLD Fact Trace 未逐字段绑定初始库存的 Upstream evidence，严格契约校验失败。 | Agent quality must fail; LLD entry remains blocked. |
| HLD human review pending | P2 | scene:PRD-S00,scene:PRD-S18 | artifact 12 | artifact 12 | pending human assessment of v3.0 world design | Blocks LLD entry until confirmed. |

## Verdict consistency matrix

| Verdict | Required condition | Actual evidence | Resolved value | Consistency |
|---|---|---|---|---|
| Agent quality verdict | Semantic consistency and formal HLD trace closure both pass. | Semantic consistency passes, but artifact 01 trace closure fails strict validation. | fail | pass |
| HLD human review state | Human review is required for complete world design. | v2.0 is newly presented after material world reconstruction. | pending_required | pass |
| LLD entry verdict | Agent pass plus confirmed human review. | Trace closure P1 remains open. | blocked_revision_required | pass |

## Artifact rubric coverage

| Artifact | Good delivery evidence | Blocking failure check | Coverage verdict |
|---|---|---|---|
| Artifact 01 | Required entities route from PRD and canonical facts to one owner. | Missing protected person, digital life, organization, event, environment, information object or time layer blocks. | pass |
| Artifact 02 | Support questions name an owner, answer and boundary. | Unowned or unconsumed support blocks. | pass |
| Artifact 03 | Technology, protocol, information, authority and security limits are explicit. | Any direct memory extraction or external control blocks. | pass |
| Artifact 04 | Concrete motive, relationship target, information permission and digital-life identity boundary are explicit. | Abstract motive, missing relationship target, or R-07 equals the dead intelligence officer blocks. | pass |
| Artifact 05 | Inventory coverage, spatial relation, state-change dimension, state transition, event state realization and source map trace closure are recorded. | Environment without event integration blocks. | pass |
| Artifact 06 | Cause, action, causal role, consequence, visibility and environment integration form one chain. | Trigger without cause, action or consequence blocks. | pass |
| Artifact 07 | Information inventory, story anchor, time layer, narrative reveal phase, disclosure tier, knowledge state, reveal predecessor, reveal event, reveal action, condition type, condition refs and source map trace closure are recorded. | Complete cause before operational intelligence blocks. | pass |
| Artifact 08 | Main, hidden, emotional, theme, institutional and identity thread function, required pressure, thread progression, crossover and closure outcome are explicit. | Missing required thread or closure blocks. | pass |
| Artifact 09 | POV, narrative distance, information access, digital-life interiority, dialogue, image system, prohibited expression, language style, access policy, information refs, thread refs, reader disclosure mode, language profile directives, type-specific behavior, vague expression, execution reference closure, focalizer resolution, structured design fact, POV permission, execution fields and LLD handoff are explicit. | Unbounded interiority or vague style rule blocks. | pass |
| Artifact 10 | Subject register, origin binding, canonical merge, single final inventory id, amendment blocking and continuity are checked. | Identity drift or duplicate final ID blocks. | pass |
| Artifact 11 | Fact-level source map closure for artifact 03-09 and LLD handoff index ready state are supplied. | Missing handoff mapping blocks. | pass |
| Artifact 12 | Risk, verdict and convergence conclusions remain routeable. | Unresolved P0/P1 with agent pass blocks. | pass |

## HLD Convergence Log

| Stable issue id | Severity | Root cause | Fix hypothesis | Regression proof | Attempt count | Rerun target | Status |
|---|---|---|---|---|---|---|---|
| HLD-TRACE-CLOSURE | P1 | 事实追踪表在重建时以摘要表达，未逐字段复述业务表的每个可校验字段。 | 由结构化事实源生成或逐字段重建 Fact Trace，并与业务表逐行比对。 | `validate_hld_contract.py` 当前在 artifact 01 报 trace binding 失败。 | 1 | artifact 01 | open |
| HLD-HUMAN-REVIEW | P2 | HLD acceptance requires human assessment after a material world reconstruction. | Human confirms or reopens v3.0. | Review outcome updates the Output verdict. | 1 | artifact 12 | blocked |

## HLD Fact Trace

| Fact trace id | Upstream fact id | Upstream fact atom | HLD fact atom | Source refs | Expansion mode | Support mechanism | Preservation status |
|---|---|---|---|---|---|---|---|
| HLD-TRACE-CLOSURE | UPF-PRD-S03-01 | 关键记忆完全自闭。 | Integrity report records that artifact 01 Fact Trace lacks exact field-level binding required by the contract. | scene:PRD-S01,scene:PRD-S03 | constrain | artifact 01 trace binding | risk_reported |
| HLD-HUMAN-REVIEW | UPF-PRD-S18-01 | 研究员长期承担后果。 | Integrity report requires human review before LLD entry. | scene:PRD-S00,scene:PRD-S18 | handoff | final HLD design review | risk_reported |

## Skill Verdict

| Field | Value |
|---|---|
| Skill quality verdict | pass |
| Source closure | closed |
| Inventory coverage | closed |
| Boundary obedience | pass |
| Downstream readiness | blocked:human HLD review required |
| Blocking issue | HLD-HUMAN-REVIEW |
| Rerun target | artifact 12 |
