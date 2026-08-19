# HS1 文件计划

| 文件组 | 职责 | 不负责 |
|---|---|---|
| `SKILL.md`、`references/*.md` | 定义故事线编排目标、边界、SOP、契约和方法论 | 代替确定性验证 |
| `references/runtime-contract.json` | 冻结 HS1 上下游、对象和能力契约 | 存放小说实例 |
| `schemas/hs1-canonical.schema.json` | 闭合故事线 canonical | 证明连接有叙事价值 |
| `scripts/run_skill.py` | 提供 HS1 语义回调并调用共享运行时 | 设计 POV 或场景 |
| `evals/`、`tests/` | P/N/B、篡改与公共封装回归 | 替代父级/HQ1 语义验收 |

Ready 包与公共设计阶段 profile 完全一致，顶层结果只通过包外 `stage-result.json` 返回。
