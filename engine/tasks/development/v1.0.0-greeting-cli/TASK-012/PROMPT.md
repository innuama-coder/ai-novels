# TASK-012 Prompt

## Execution Objective

完成 current task「迁移 H1-B 小说评审片段编写技能」并提供运行证据。

## Scope

Allowed:
- 按批准槽位生成足量、可审阅、风格固定且源事实一致的小说片段

Forbidden:
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

## Constraints

服从 source authority；只改 owned areas；legacy 只作迁移参考；stop condition 出现时停止。

## Decision Principles

契约优先，证据优先；先负例后实现；不以文件存在、宽松校验或人工说明代替完成。

