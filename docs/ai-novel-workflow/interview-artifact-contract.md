# 访谈产物与真实性契约（已由 harness 取代）

> **权威迁移**：本文件的历史目录、`plan.json` 和报告格式不再是可执行契约。
> 请使用 [novel-conception-interview harness](../../harnesses/novel-conception-interview/README.md)
> 中的 `plan.vN.json`、`events.ndjson`、`report.md`、`validation.json` 与
> `stage-completion.json`。若以下历史说明与其不一致，必须忽略以下说明。

本文件是六个构思访谈的唯一可执行产物契约。技能说明和编排不得重新定义计划、逐轮记录、版本或准入字段。

## 1. 会话文件

每次访谈在项目构思目录创建一个会话目录：

```text
interviews/<interview-id>/
  plan.json
  report.md
  validation.json
```

`interview-id` 由 `<project>-<stage>-v<major>-r<round>` 组成。设计产物的元信息必须引用最新完成会话的 ID。

## 2. 计划契约

在提出第一条实质问题前写入不可覆盖的 `plan.json`。最低字段：

```json
{
  "schema_version": "1.0",
  "interview_id": "…",
  "stage": "I0|I1|I2|I3|I4|I5",
  "input_versions": {"artifact": "version"},
  "question_budget": 24,
  "groups": [{"id": "A", "budget": 3}],
  "estimated_minutes": 60,
  "completion_conditions": ["…"],
  "transcript_assurance": "self_recorded|event_backed"
}
```

`question_budget` 必须等于所有组 `budget` 之和，且是本次访谈的确定整数，不得使用区间。任何超出预算的问答前，追加 `plan_revision`，记录旧/新预算、原因、作者同意和下游影响。

## 3. 逐轮报告契约

每收到一次作者回答、且在提出下一实质问题前，立即追加 `report.md`。每轮必须含：轮次号、计划组、问题号、Agent 原文、作者原文、回显/候选、确认语、当轮决定、状态、会话时间或不可用声明、来源标识。

报告只能追加。修订结论必须新增“旧决定 → 新决定 → 原因 → 受影响版本”，不得改写旧轮次。

`event_backed` 仅在运行时能提供不可伪造的会话/消息 ID 时使用；否则必须标为 `self_recorded`。验证器只能验证结构和序列，不能证明 `self_recorded` 原文与平台日志逐字一致。

## 4. 完成与消费

会话结束时，设计产物引用该会话 ID 与 `validation.json`。只有计划、报告和验证均通过，且设计产物为 `ready`，下游才能消费。V1 必须拒绝缺少任一文件、存在未批准超预算、轮次不连续或保证等级被伪称为 `event_backed` 的输入。
