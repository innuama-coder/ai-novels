# TASK-012: 迁移 H1-B 小说评审片段编写技能

## Responsibility

迁移 H1-B 小说评审片段编写技能。只拥有 skills/novel-conception-fragment-writer。

## Source and inputs

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §11.3, §3.8-§3.9, §14-§15, §16 item 12
- skills/novel-conception-fragment-writer/SKILL.md
- H1-A fragment-input-package
- P1 source anchors
- 既有固定风格与语言硬约束

## Expected outputs

- skills/novel-conception-fragment-writer/scripts/run_v2.py
- skills/novel-conception-fragment-writer/references/v2-fragment-contract.md
- skills/novel-conception-fragment-writer/tests/test_v2_runtime.py

## Allowed scope

- 按批准槽位生成足量、可审阅、风格固定且源事实一致的小说片段

## Forbidden scope

- 不补设定或改变剧情结论
- 不把片段当正式正文
- 不绕过 P1 anchors

## Acceptance

- 每个片段承担明确评审问题且总量满足报告计划
- 固定语言/风格、视角、信息边界和决定性心理活动限制均被验证
- 片段事实逐项回链 P1，虚构表面细节不产生新控制信息

## Verification

- python -m unittest skills.novel-conception-fragment-writer.tests.test_v2_runtime
- 验证数量、风格、锚点、越权事实和禁写心理活动

## Stop conditions

- H1-A 输入槽位不足或相互冲突
- 固定风格无法表达指定评审问题

## Handoff

- 向 H1-C 交付 fragment package、验证报告和 workspace 更新

