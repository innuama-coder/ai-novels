# TASK-006: 实现 E1 环境系统设计技能

## 目标

实现 E1 环境系统设计技能，并以可运行制品、自动验证和可追溯 handoff 作为完成证据。

## 来源

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §6, §3.9, §14-§15, §16 item 6
- skills/novel-environment-system-designer/SKILL.md

## 输入

- B0、S1、W1 正式制品

## 交付

- skills/novel-environment-system-designer/scripts/run_v2.py
- skills/novel-environment-system-designer/references/runtime-contract.md
- skills/novel-environment-system-designer/tests/test_v2_runtime.py

## Allowed scope

- 把世界规则展开为可承载具体事件的环境，定义空间、设施、感知、权限、风险、资源和转场

## Forbidden scope

- 不新增故事线
- 不决定事件结果
- 不编写场景正文

## Acceptance

- 所有需落地的故事线节点均有可执行环境承载
- 环境具有事件所需入口、限制、可感知信息、行动接口和转场关系
- 环境只从 W1 展开且不违背世界规则

## Verification

- python -m unittest skills.novel-environment-system-designer.tests.test_v2_runtime
- 覆盖承载充分性、不可达转场、缺行动接口与规则冲突

## Stop conditions

- W1 未完成
- 故事线要求无法由现有世界规则支持

## Handoff

- 向 T1 交付环境目录、连接图和 storyline coverage

