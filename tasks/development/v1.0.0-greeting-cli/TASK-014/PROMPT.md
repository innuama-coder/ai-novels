# TASK-014 Prompt

实现 H1 顶层 completion、外部作者决定三分支和最终构思 completion。

严格遵守以下顺序：

1. 重验 current P1、H1-A/B/C、rendered workspace、input gate 和 run-state。
2. 暂存、自验并原子发布 H1 completion；目的地复验后交 coordinator。
3. 原样接收 sealed author event；approved/rejected 记录状态，revise 由 workflow 计算唯一 owner 和恢复点。
4. 仅 approved 分支暂存、自验并原子发布最终 completion；目的地复验后交 coordinator 授予开发准入。

不得推断作者意图、让作者填写 owner、让 revise/rejected 生成最终 completion，或让 H1-C 越权生成 H1 completion。

完成时报告文件、测试证据、剩余风险和 TASK-015 handoff；不得自行宣称验收。
