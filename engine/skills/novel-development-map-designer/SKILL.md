---
name: novel-development-map-designer
description: 只读检查和解释已经存在的历史 D1 小说开发地图包。仅当用户明确要求读取、诊断或回归比较既有 D1 包时使用；不得用于新的小说构思、访谈结果转构思、自主构思 V2、生成或修订 D1 包，也不得生成任何 V2 completion。新的构思工作必须交给 novel-conception-autonomous V2 调度链。
---

# 历史 D1 小说开发地图检查

## 状态

这是只读 legacy 兼容入口，不是构思生产技能。旧 D1 的故事线、世界、环境、事件和
角色职责已经分别迁移到自主构思 V2 的 S1–C1。

## 硬准入

只接受用户明确指定的、已经存在的 D1 包目录。开始前确认：

1. 任务是读取、诊断或回归比较旧包，而不是创建或继续开发构思；
2. 目标包已经包含历史 `map-data.json`、`package-manifest.json` 和
   `stage-completion.json`；
3. 输出只报告包内已有内容、血缘和验证问题。

任一条件不满足时停止。新的构思请求必须转交
`novel-conception-autonomous`，不得尝试恢复旧 D1 生产流程。

## 允许操作

- 读取旧包并解释其内容、来源和历史契约；
- 对现有文件执行只读诊断或回归比较；
- 明确指出旧包不能作为 V2 input gate、manifest、completion 或正式上游事实。

## 禁止操作

- 不调用 `manage_generation.py begin/submit`、`execute_autonomous.py`、
  `write_d1_completion.py` 或任何旧 D1 生成入口；
- 不创建、修改、补齐、重封或发布 D1 包；
- 不把旧 D1/R1 迁移、解释或包装成 V2 `ready`；
- 不接受访谈结果作为本技能输入，不承担任何新的小说构思工作；
- 不替代 S1、W1、E1、T1、C1、Q1、P1 或 H1。

需要理解历史数据格式时才读取 [output-contract.md](references/output-contract.md)；
需要解释旧流程时才读取 [sop.md](references/sop.md)。这些文档只作历史说明，其中的
生成命令不再获得执行授权。
