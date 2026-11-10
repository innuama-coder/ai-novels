# 《断线》小说项目

数字生命题材长篇小说。构思已于 2026-08-17 获作者批准（构思自主 V2，run `duanxian-conception-v2-20260811-18`），当前处于 HLD→LLD 开发推进阶段。

## 目录

| 目录/文件 | 内容 |
|---|---|
| `conception-approved/` | 权威构思交付包：author-decision、conception-completion（SHA-256 绑定全链）、人审报告（md/json/html） |
| `conception-production/` | 构思生产 CLI（`run.py`，按冻结 STAGE_SPECS 驱动 engine 技能） |
| `design/specs/` | 早期设计稿：digital-life 系列 8 篇＋intake/proposal＋LLD 细化（characters/scenes/spaces 26 篇） |
| `design/runs/` | 工作流运行产物：proposal(15)／PRD(13)／旧 HLD v3.0(20)／LLD(1)——旧 HLD manifest 仍 `pending_hld_human_review` |
| `design/workflow-docs/` | 构思阶段的过程文档（意图卡、叙事契约、覆盖矩阵、发展图等 11 篇） |
| `design/design-tasks/` | 断线 HLD 设计任务包与 manifest |
| `design/reference/` | 写作风格参考（刘慈欣） |
| `writing/` | 写作素材（人物/场景/空间初稿） |
| `novel-text/` | 小说正文（草稿） |
| `testing/` | 断线专属构建器与测试（W1/E1/T1/C1/Q1/H1、run 驱动器）；运行期产物不入库 |

## 权威与状态

- 当前权威构思 = `conception-approved/`；`design/runs/` 里的旧 proposal/PRD/HLD 是历史链资产，不能与 V2 产物混用。
- 早期设计稿（`design/specs/`）是 2026-06 的立项材料；构思 V2 批准后以 `conception-approved/` 为准。
- 依赖 `engine/`（导入 harness runtime 与技能入口）；本目录内构建器已按 `engine/`＋`duanxian/` 双根寻址。
