# TASK-005: 实现 W1 虚拟世界模型设计技能

## 目标

实现 W1 虚拟世界模型设计技能，并以可运行制品、自动验证和可追溯 handoff 作为完成证据。

## 来源

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §5, §3.9, §14-§15, §16 item 5
- skills/novel-world-model-designer/SKILL.md

## 输入

- B0 baseline
- S1 storyline architecture

## 交付

- skills/novel-world-model-designer/scripts/run_v2.py
- skills/novel-world-model-designer/references/runtime-contract.md
- skills/novel-world-model-designer/tests/test_v2_runtime.py

## Allowed scope

- 依据全部故事线定义世界规则、制度、技术/资源、地理时空、社会运行与边界

## Forbidden scope

- 不枚举具体场景
- 不写事件链
- 不创建角色档案

## Acceptance

- 每条故事线所依赖的世界能力、限制和代价均有规则承载
- 规则含适用范围、例外、代价与一致性检查
- 输出不越界吸收 E1/T1/C1 职责

## Verification

- python -m unittest skills.novel-world-model-designer.tests.test_v2_runtime
- 正反 fixture 验证规则覆盖、矛盾和越界

## Stop conditions

- S1 未完成或 lineage 不匹配
- 世界规则无法同时承载已批准故事线且需要改 S1

## Handoff

- 向 E1 交付 W1 正式制品和故事线到规则的 coverage

