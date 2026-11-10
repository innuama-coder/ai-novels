# 小说生产流水线引擎

把人类作者的创意经访谈→构思→HLD→LLD→写作→评审转化为可审校手稿的受控生成系统。核心约束：每次生成必须有明确输入、唯一职责、可消费产物、状态、版本和审查证据；作者保留批准权。

## 目录

| 目录 | 内容 |
|---|---|
| `skills/` | 81 个 `novel-*` 单一职责技能（intake→proposal→PRD→HLD→LLD→writing 全流程＋评审），每个含 SKILL.md、契约、脚本与测试 |
| `harnesses/` | 3 个自主编排 harness：`novel-conception-interview`（访谈）、`novel-conception-autonomous`（构思自主 V2，1.0.0）、`novel-hld-autonomous`（HLD 自主链，0.1.0 实现候选）＋ `kun-workshop-intranet-delivery` |
| `docs/ai-novel-workflow/` | 工作流权威规范＋`contracts/autonomous-v2/` 契约真源（JSON Schema）＋发布记录 |
| `docs/superpowers/` | 流水线设计稿、契约规格（proposal/PRD/HLD contract.json）、方法论文、重构计划 |
| `docs/design/` | 管线工程设计（DP-HLD 系列、rust 实现设计） |
| `scripts/` | 5 个契约校验器（proposal/PRD/HLD/发布/设计任务） |
| `tests/` | 校验器契约测试 |
| `testing/` | 运行时测试（V2 schema runtime、契约、E2E、技能包标准） |
| `tasks/` | 设计任务框架（planning、质量校验器、TASK fixtures） |

## 运行与验证

```bash
python3 -m pytest tests -q                      # 校验器契约测试
python3 scripts/validate_prd_contract.py        # 各契约校验器
python3 -m pytest testing -q                    # 运行时测试（部分用例依赖本机运行数据）
```

布局约定：引擎内部一律以 `engine/` 为根做仓库相对寻址（`parents[N]`、`importlib` 前缀 `harnesses.*`／`skills.*`）；小说项目素材在仓库根的 `../duanxian/`，运行产物路径见 `.gitignore`。
