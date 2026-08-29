# TASK-004: 实现 S1 故事线架构设计技能

## 目标

实现 S1 故事线架构设计技能，并以可运行制品、自动验证和可追溯 handoff 作为完成证据。

## 来源

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §4, §3.9, §14-§15, §16 item 4
- skills/novel-storyline-architecture-designer/SKILL.md

## 输入

- B0 baseline package
- storyline-architecture schema

## 交付

- skills/novel-storyline-architecture-designer/scripts/run_v2.py
- skills/novel-storyline-architecture-designer/references/runtime-contract.md
- skills/novel-storyline-architecture-designer/tests/test_v2_runtime.py

## Allowed scope

- 生成多维故事线、因果链、汇合/分叉/交叉点、悬念冲突和边界控制信息

## Forbidden scope

- 不设计世界、环境、事件目录或角色档案
- 不改写 B0 锁定事实
- 不把可选旋律线强制为正文

## Acceptance

- 输出通过正式 schema 和 lineage 校验
- 主体线覆盖起点—升级—转折—危机—收束，其他线有关系与连接点
- 每条线明确展开资格、主题作用、冲突/悬念和开发边界

## Verification

- python -m unittest skills.novel-storyline-architecture-designer.tests.test_v2_runtime
- 用通用 fixture 与缺线/断链/事实漂移负例验证

## Stop conditions

- B0 未完成或事实门失败
- 故事线冲突必须由作者裁决

## Handoff

- 向 W1 交付 S1 正式制品、completion、manifest 与控制信息

