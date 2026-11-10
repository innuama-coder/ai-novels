# HQ1 文件职责

| 文件 | 职责 |
|---|---|
| `SKILL.md` | 触发条件、职责、边界、执行方式和 ready 条件 |
| `references/runtime-contract.json` | 机器可读入口、实现闭包、拓扑、schema 与能力契约 |
| `references/runtime-contract.md` | 面向执行者解释公共契约 |
| `references/sop.md` | 可重复执行流程 |
| `references/methodology.md`、`semantic-rubric.md` | 语义审查方法和判定标尺 |
| `references/sources.md` | 15 项研究来源与吸收结论 |
| `schemas/hq1-semantic-review.schema.json` | HQ1 canonical 的 closed schema |
| `scripts/run_skill.py` | 唯一公共入口 |
| `harnesses/.../review_stage_runtime.py` | 准入、隔离、复验、语义校验、原子发布 |
| `evals/`、`tests/` | 冻结案例、公共包回归、篡改和边界测试 |

Ready 包包含 `hld-semantic-review.json`、`review-session.json`、`review-execution.json`、`validation.json`、`package-manifest.json`、`stage-completion.json`；`stage-result.json` 位于包外。
