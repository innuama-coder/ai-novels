# ai-novels

小说创作工作流与 Agent 工程仓库。根目录只有两个子目录：

- **`engine/`** — 小说生产流水线引擎：81 个 `novel-*` 技能、3 个自主编排 harness、契约校验器、JSON Schema 契约真源与运行时测试。业务规范入口：`engine/docs/ai-novel-workflow/README.md`。
- **`duanxian/`** — 《断线》小说项目：已批准的构思交付包（`conception-approved/`）、构思生产 CLI（`conception-production/`）、三代设计稿与运行产物（`design/`）、写作素材（`writing/`、`novel-text/`）、项目专属构建器与测试（`testing/`）。

## 快速导览

| 想了解/做什么 | 去哪里 |
|---|---|
| 工作流怎么运转（构思→HLD→LLD→写作→评审） | `engine/docs/ai-novel-workflow/README.md` |
| 流水线技能清单（按阶段） | `engine/skills/novel-*/SKILL.md` |
| 自主编排运行时 | `engine/harnesses/novel-conception-autonomous/`、`engine/harnesses/novel-hld-autonomous/` |
| 契约校验器（proposal/PRD/HLD/发布/设计任务） | `engine/scripts/validate_*.py` |
| 《断线》构思批准包 | `duanxian/conception-approved/README.md` |
| 《断线》设计总览（PRD/HLD/LLD） | `duanxian/design/specs/`、`duanxian/design/runs/hld/2026-07-13-duanxian-hld-workflow/` |

注意：运行期产物（conception-runs、run-states、human-review 等）不入库，路径见 `.gitignore`。
