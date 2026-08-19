# File plan

| 路径 | 职责 |
|---|---|
| `SKILL.md` / `agents/openai.yaml` | 触发、执行和边界说明 |
| `references/input-output-contract.md` | 两个 mode 的硬输入输出契约 |
| `references/methodology.md` / `sop.md` / `sources.md` | 研究结论与操作步骤 |
| `references/runtime-contract.json` | owner、闭包、role、schema 和 profile 的机器契约 |
| `schemas/hq2-*.schema.json` | 封闭 canonical/session/execution/validation/contract schema |
| `scripts/run_skill.py` | 薄公共入口 |
| `harnesses/.../hq2_stage_runtime.py` | 唯一运行时实现 |
| `evals/cases/HQ2-*.md` | 正向、语义负例和边界负例 |
| `tests/test_skill.py` | 真实 coordinator→双任务→publisher 与读取审计 |
| `tests/test_contract_assets.py` | 文档、来源、闭包、owner 与防篡改契约测试 |
