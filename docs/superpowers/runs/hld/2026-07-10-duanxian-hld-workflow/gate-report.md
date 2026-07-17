# HLD 入口门禁报告

| 检查项 | 结论 | 依据 |
|---|---|---|
| PRD Agent 质量结论 | `pass` | PRD 风险报告 |
| 人类 PRD 评审结论 | `pending` | PRD 风险报告 |
| HLD 入口结论 | `blocked_pending_human_review` | PRD 入口状态机 |
| Harness 行为 | 仅生成阻塞运行清单与本报告 | `novel-hld-workflow` 输入门禁 |
| HLD 业务事实 | 未生成 | 门禁阻止 artifact `01` 至 `12` |

## 放行条件

人类完成并确认 PRD 评审后，PRD 风险报告的 `Human review verdict` 必须更新为 `confirmed`，且 `HLD entry verdict` 必须更新为 `pass_to_hld`。在此之前，本运行保持阻塞状态。
