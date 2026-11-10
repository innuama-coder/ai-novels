---
name: novel-conception-deliverable-assembler
description: 将通过独立 Q1 审查的作者控制基线、故事线、世界、环境、事件和角色 canonical 模型确定性组装为机器可消费的小说构思交付包。用于自主构思 V2 的 P1 阶段；不生成新构思、不修复上游、不写小说片段或 HTML。
---

# 小说构思机器交付组装

## 目标

无损组装当前权威构思，使独立 AI 开发者能够追踪任一控制信息、故事线、环境、事件、
人物和开发自由，而不需要读取聊天或访谈过程。

## 权威契约

完整读取工作流第 3、10、14、15 节，以及
[P1 Schema](../../engine/docs/ai-novel-workflow/contracts/autonomous-v2/novel-conception-package.schema.json)、
[开发交接 Schema](../../engine/docs/ai-novel-workflow/contracts/autonomous-v2/development-handoff.schema.json)。

## 输入硬准入

只接受同一 run、同一 B0 baseline manifest 的当前 B0、S1、W1、E1、T1、C1、Q1
completion、manifest 和 canonical 模型。Q1 必须 `verdict=ready`、无 revise/blocked finding、
无 return；其 `quality_coverage` 必须与当前 S1/T1 全部带 ID 对象逐项、逐哈希一致，
covered 与 required 完全相等且未解决阻断质量记录为空。P1 必须独立重算，不能只相信
Q1 的 `result=complete` 声明。P1 input gate 必须通过。

## V2 运行入口

调用 `scripts/run_v2.py` 的 `run_p1(...)`，传入七个正式包目录、coordinator、
sealed `input_gate`、`next_state_path` 和目标 P1 目录。forward 模式不得传
`active_return_request`；return-resolution 只接受 `resume_stage=resume_point=P1`，
且 return 正文引用和 `return_id` 必须与 gate 逐值一致。完成后用
`validate_p1_package(...)` 独立重验正式目录。

canonical package 对 `development-handoff.json` 仅保留严格 pathReference；
handoff 和 manifest 分别用真实 SHA-256 强绑定最终文件，不允许占位或双向哈希环。

### 已发布包的崩溃恢复

若目标 P1 目录已经存在，不要覆盖、删除或重新组装。先按正式 validator 只读重验整个
包，再证明 input gate、B0–Q1 来源包和实现快照与本次调用逐值一致。coordinator 只
允许两种精确状态：执行前状态中的 valid non-current orphan 可首次 accept，此时
`P1RunReceipt.replayed=true`、`transition.replayed=false`；仅在 forward 模式下，
若已持久化 successor 的 `previous_state`、current P1 completion 和 successor path
全部匹配，则 persistent replay 返回两个 `replayed=true`。两种情况都必须原样复用
既有包。

return-resolution 已进入 `resolved_returns` 后严格 one-shot；原样抛出
`COORD_RETURN_ALREADY_RESOLVED`，不得产生新的 receipt。

若目录 partial、无效、被篡改、已过期、来自其他 gate／来源／执行前状态，或实现快照
不再等于当前实现，必须 fail closed 并原地保留取证，不得覆盖或“修复”该目录。此恢复
协议不改变任何 JSON Schema。

## 职责

1. 重验所有上游 Schema、哈希、来源链和跨模型集合。
2. 原样收录作者控制基线和六份访谈权威设计产物。
3. 原样收录 S1–C1 canonical 模型和 Q1 审查。
4. 建立权威设计索引、跨模型索引、追溯矩阵和开发交接边界。
5. 确定性渲染面向 AI 开发者的完整构思规格。
6. 输出 `quality_admission`，绑定 Q1 review、覆盖口径、应审／已审对象数量和零未解决
   阻断记录；任何一项失配都拒绝组装。

## 边界

- 不新增、摘要替换或修复任何构思事实。
- 不重新作出设计决定。
- 不写小说片段、报告摘要或 HTML。
- 不代替作者批准，也不直接授予开发准入。

## 交付与验收

交付 `novel-conception-package.json`、`author-control-baseline.json`、
`authoritative-design-index.json`、`novel-conception-spec.md`、
`cross-model-index.json`、`traceability-matrix.md`、`development-handoff.json`、
七个输入包快照、实现快照、执行记录、validation、manifest 和 P1 completion。

只有包可无损还原全部权威输入、角色文件均绑定 manifest、跨模型引用和覆盖集合完全
一致、重新渲染确定性一致时才可 ready。
