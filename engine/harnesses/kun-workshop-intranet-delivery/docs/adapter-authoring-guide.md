# Adapter Authoring Guide

适配器只翻译 runtime 的委派、文件、审批和工具语法，不能改写 portable core 的阶段、角色权限或门禁。每个 `mapping.md` 必须逐项把核心要求标记为 `native`、`prompt`、`tool`、`manual` 或 `unsupported`，并说明降级后如何保留证据。若 runtime 无法可靠隔离角色或采集部署日志，相关门禁必须以人工桥接执行，不能伪称自动通过。
