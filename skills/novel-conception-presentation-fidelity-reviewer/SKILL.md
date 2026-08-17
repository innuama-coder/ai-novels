---
name: novel-conception-presentation-fidelity-reviewer
description: 独立审查小说构思的人审内容是否忠实、完整且不越权地呈现同一 P1 机器构思包，并生成可被 H1-A 组装硬门消费的语义一致性审查。用于人审报告候选已确定、正式组装发布之前；不修改构思、报告、样章或 HTML。
---

# 小说构思呈现一致性审查

## 目标

证明人审内容与机器构思在实质意义上保持一致：没有改变作者意图、世界规则、故事线、
事件因果、角色定义和开放边界；没有把样章的局部表现升级为权威事实；没有用“来源已
覆盖”替代语义忠实。

## 必须读取

完整读取 [审查契约](references/review-contract.md)，以及当前正式 P1、H1-A plan、
H1-B fragment package、候选 `human-review-report.json` 和 source inventory。

## 独立性

审查必须由与 H1-A 规划、H1-B 写作不同的任务执行。审查者不得读取生成者的聊天、
推理草稿或预期答案，只读取上述正式制品。若不能证明任务独立，输出 `blocked`，不得
伪造 `pass`。

## 职责

1. 逐一审查默认可见的世界、故事线、角色、图形、样章和决定提示元素。
2. 对每个元素核对其完整内容哈希和 plan 中绑定的精确 source anchors。
3. 判断呈现是忠实改写、合法取舍还是非权威样片，不允许出现第三种未声明权威状态。
4. 检查实质矛盾、关键限定遗漏、强调失真、开放项闭合和权威升级。
5. 用故事专属的呈现引文和判断理由留下证据。

## 边界

- 不修改 P1、plan、fragment 或报告候选。
- 不补写遗漏内容；发现问题必须返回 H1-A plan 或 H1-B。
- 不评价市场性、个人偏好或正文完成度。
- 不把字段存在、来源 ID、哈希一致或 HTML 字节一致当作语义通过。

## 输出与硬门

无论通过、需修订还是因输入/独立性不足而阻断，都输出一个符合
[`presentation-fidelity-review.schema.json`](../../docs/ai-novel-workflow/contracts/autonomous-v2/presentation-fidelity-review.schema.json)
的 `presentation-fidelity-review.json`。失败项使用 `revise`，无法完成审查使用
`blocked` 并填写 blockers。只有以下条件同时成立才可 `pass`：

- 五个审查维度全部通过；
- 默认可见元素集合与 review plan 精确相等，逐项且仅审查一次；
- 每项内容哈希、source anchors 和最终呈现引文均可重算；
- 普通元素结论为 `faithful`，样章结论为 `non_authoritative_sample`；
- `no_material_omission`、`no_contradiction`、`no_authority_escalation` 全部为真；
- blockers 为空。

H1-A assembler 必须独立重算以上结构并消费 verdict。`revise` 或 `blocked` 不得生成
ready assembly package；审查文件不能作为旁路附件被忽略。
