# 构思访谈共同协议（兼容性说明）

> **权威迁移**：六个访谈均以
> [novel-conception-interview harness](../../harnesses/novel-conception-interview/workflow.md)
> 的 `workflow.md`、`rules.md` 和 `schemas/` 为唯一产物与真实性契约。本文件
> 仅为旧链接提供背景；若后文出现 `plan.json`、旧测试路径或不同规则，一律不
> 可用于运行或验收。

## 1. 访谈容量

| 门 | 决策组 | 单次计划上限 | 默认时长 |
| --- | ---: | ---: | ---: |
| I0 意图 | 4 | 16 | 20–35 分钟 |
| I1 主体 | 4 | 16 | 20–35 分钟 |
| I2 世界 | 8 | 30 | 45–75 分钟 |
| I3 角色 | 5 | 首位 18；每增加一位核心角色 +12 | 35–70 分钟 |
| I4 因果 | 4 | 22 | 35–55 分钟 |
| I5 叙述 | 4 | 20 | 30–45 分钟 |

上限不是计划。开始前必须在不可变 `plan.v1.json` 写入本次的精确 `question_budget`、每组精确配额与时长估计；所有需要作者回应的提问均计数。作者回答可覆盖多个点，但不会使未问的问题被伪记为已完成。变更预算必须创建新的 `plan.vN.json`，并追加获得作者同意的 `plan_revision` 事件。

## 2. 执行纪律

每轮只处理一个控制点，最多三条短问题。每次作者回答后、下一条实质问题前，按产物契约即时追加报告。每轮区分作者原话、作者确认、Agent 推断、授权决定、暂定项与开放项；技能只能冻结自己拥有的控制点。

## 3. 完成与交接

访谈完成需要：当前设计产物为 `ready`，会话目录的不可变 `plan.vN.json`、追加式 `events.ndjson`、由日志重建的 `report.md`、验证器生成的 `validation.json` 与 `stage-completion.json` 均存在且一致。下游只消费 completion packet；报告用于审计和回退，不是可继承设定。

运行：

```powershell
python harnesses/novel-conception-interview/validators/validate_session.py interview-sessions/I0/<session-id>
```
