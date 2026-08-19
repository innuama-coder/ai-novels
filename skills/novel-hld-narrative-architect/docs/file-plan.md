# HA1 文件计划

| 文件组 | 职责 | 不负责 |
|---|---|---|
| `SKILL.md`、`references/*.md` | 定义目标、边界、SOP、输入输出和方法论 | 代替可执行准入 |
| `references/runtime-contract.json` | 冻结 stage、上游、字段、对象数组和下游能力 | 存放实例内容 |
| `schemas/ha1-canonical.schema.json` | 闭合 HA1 canonical 的字段、类型、枚举和引用形状 | 判断叙事质量 |
| `scripts/run_skill.py` | 提供 HA1 语义回调并调用共享设计运行时 | 修改 Harness 状态或路由 |
| `harnesses/.../runtime/design_stage_runtime.py` | 公共准入、溯源、证据、封装和确定性校验 | 代替 HA1 语义判断 |
| `evals/`、`tests/` | 固定 P/N/B、攻击回归、封存夹具与验收证据 | 生成生产构思 |

Ready 包含 canonical、session、五份 evidence、execution、preview、validation、manifest、completion；`stage-result.json` 位于包外。
