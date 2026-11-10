# Delivery Spec

每次 run 在 `delivery-runs/<run-id>/` 形成下列可消费制品：

| 制品 | owner | 最低内容 |
| --- | --- | --- |
| `inputs/inventory.md` | 产品分析师 | 原型/文档/仓库/环境版本、可访问性与缺口 |
| `s0/requirements-traceability.md` | 产品分析师 | 需求 ID、来源、原型位置、验收条件、状态 |
| `s1/design-package/` | UX/架构/QA/安全 | 交互规格、HLD、ADR、接口/权限/数据模型、威胁模型、测试策略 |
| `s2/delivery-plan.json` | 调度者 | 工作包、依赖、owner、DoD、风险与并行度 |
| `s3/<work-package>/` | 工程角色 | 变更引用、审查、测试、完成包 |
| `s4/quality-report.md` | QA/安全 | 追溯覆盖、测试与缺陷、G2 结论 |
| `s5/release-candidate/` | 发布工程师 | 版本、制品哈希、变更、部署/回滚/冒烟计划 |
| `s6/preproduction-evidence.json` | 发布工程师/QA | 授权、环境、部署日志、版本、冒烟与验收结论 |

每阶段另写 `stage-completion.json`。所有结果使用状态 `ready`、`revise`、`blocked` 或 `failed`；没有对应 schema 所需证据时不得写 `ready`。
