# 鲲工坊内网交付 AI 团队

这是一个可移植的团队交付 harness，而不是一组可以任意互相调用的提示词。
它接收可交互原型和产品说明文档，在明确权限和环境约束下，产出经过设计、
实现、测试与预发布验证的内网系统发布候选。

从 [`docs/team-definition.md`](docs/team-definition.md) 开始了解团队边界，
从 [`workflow.md`](workflow.md) 执行分阶段交付。角色职责和能力单元分别见
[`docs/role-cards.md`](docs/role-cards.md) 与 [`docs/capability-skills.md`](docs/capability-skills.md)。

本版本不会自动创建云资源、读取生产数据或向预发布环境发布；这些动作须由具备
环境权限的人明确授权后，才可由发布工程师执行。
