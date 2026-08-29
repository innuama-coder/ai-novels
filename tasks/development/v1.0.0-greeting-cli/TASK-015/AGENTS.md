# TASK-015 AGENTS.md

## Karpathy-style Context Engineering

current task 只加载必要来源、输入与验收上下文。

## Source Order

1. docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §2, §13-§16
2. docs/ai-novel-workflow/conception-orchestration.md

## Current task

组装自主构思主 Harness、适配器与发布验证。入口从当前 rendered H1 开始，
先发布正式 H1 completion，再消费外部作者决定；只有 approved 产生 final。

## Constraints

- 不复制领域逻辑到 orchestration
- 不保留 D1/R1 作为 V2 成功路径
- 不以文档声明替代可运行调用
- 不 patch H1 validator；测试仅允许明确记录的正式 P1 fixture 边界
- revise/rejected 必须 `final=None`

## Verification

- uv run --offline --with-requirements harnesses/novel-conception-autonomous/requirements.txt python harnesses/novel-conception-autonomous/validators/validate_harness.py
- 运行全体单元/契约测试并检查发布包清单

## Handoff

- 向 E2E 任务交付唯一整链入口、运行说明和 harness 自检证据
