# File plan

| 路径 | 职责 |
|---|---|
| `SKILL.md`, `agents/openai.yaml` | 触发说明与执行边界 |
| `references/*.md/json` | 研究、方法、SOP、输入输出和 runtime 常量 |
| `references/*.schema.json` | report、registry 的严格 JSON schema |
| `assets/template.html`, `assets/styles.css` | 受 hash 控制的单文件容器与屏幕/打印样式 |
| `scripts/run_skill.py` | gate、确定性渲染、包与 internal result |
| `scripts/render_validation.py` | 标准库结构/DOM/registry/offline/profile 校验库 |
| `scripts/validate_render.py` | 独立 CLI validator |
| `evals/cases/HH1-C-*.md` | 正、负、边界行为规范 |
| `tests/fixtures/*`, `tests/test_*.py` | 固定 fixtures 与真实执行验收 |
| `tests/acceptance-evidence.json` | Harness 六维证据 |

所有实现限定在本技能目录；不实现 HH1 publisher。
