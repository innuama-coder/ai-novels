# Autonomous Conception V2 Development Tasks

This is a multi-subtask implementation package. Its relationship, dependency, execution order, acceptance, and handoff rules are normative for execution.

## Subtask relationship and dependency

| Order | Task | Responsibility | Dependency |
|---:|---|---|---|
| 1 | TASK-001 | 建立 V2 正式契约运行时 | none |
| 2 | TASK-002 | 实现运行状态、拓扑与返工路由 | TASK-001 |
| 3 | TASK-003 | 实现 B0 基线封装、事实门与完成判定 | TASK-001, TASK-002 |
| 4 | TASK-004 | 实现 S1 故事线架构设计技能 | TASK-003 |
| 5 | TASK-005 | 实现 W1 虚拟世界模型设计技能 | TASK-004 |
| 6 | TASK-006 | 实现 E1 环境系统设计技能 | TASK-005 |
| 7 | TASK-007 | 实现 T1 事件时间线设计技能 | TASK-006 |
| 8 | TASK-008 | 实现 C1 角色系统设计技能 | TASK-007 |
| 9 | TASK-009 | 迁移 Q1 构思审查技能到 V2 双任务审查 | TASK-002, TASK-008 |
| 10 | TASK-010 | 实现 P1 机器构思交付物组装技能 | TASK-009 |
| 11 | TASK-011 | 迁移 H1-A 人审报告设计与组装技能 | TASK-010 |
| 12 | TASK-012 | 迁移 H1-B 小说评审片段编写技能 | TASK-011 |
| 13 | TASK-013 | 迁移 H1-C HTML 报告生成与 H1 完成技能 | TASK-011, TASK-012 |
| 14 | TASK-014 | 实现作者裁决与最终构思完成流程 | TASK-002, TASK-010, TASK-013 |
| 15 | TASK-015 | 组装自主构思主 Harness、适配器与发布验证 | TASK-004, TASK-005, TASK-006, TASK-007, TASK-008, TASK-009, TASK-010, TASK-011, TASK-012, TASK-013, TASK-014 |
| 16 | TASK-016 | 建立通用与《断线》整链前向验收套件 | TASK-015 |
| 17 | TASK-017 | 执行最终交付验收并出具报告 | TASK-001, TASK-002, TASK-003, TASK-004, TASK-005, TASK-006, TASK-007, TASK-008, TASK-009, TASK-010, TASK-011, TASK-012, TASK-013, TASK-014, TASK-015, TASK-016 |

## Execution order

1. TASK-001
2. TASK-002
3. TASK-003
4. TASK-004
5. TASK-005
6. TASK-006
7. TASK-007
8. TASK-008
9. TASK-009
10. TASK-010
11. TASK-011
12. TASK-012
13. TASK-013
14. TASK-014
15. TASK-015
16. TASK-016
17. TASK-017

No parallel group is declared. The domain stages consume the accepted artifact of the previous stage, so forced concurrency would violate the contract chain.

## Acceptance and handoff

Each subtask must pass its own acceptance and verification before handoff. TASK-017 is the only final delivery acceptance task; it depends on every non-deferred implementation subtask and must fail on missing evidence, failed tests, uncovered source requirements, or unresolved blockers.

