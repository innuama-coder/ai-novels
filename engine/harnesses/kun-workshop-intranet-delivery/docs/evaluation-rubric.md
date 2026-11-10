# Evaluation Rubric

## Reviewer Role

由未承担被评审高风险实现的独立 reviewer 执行。leader 消费其结论但不能篡改评分。

## Dimensions

按 0–2 分评估：范围忠实度、工作流严谨性、角色责任分离、输入/输出追溯、质量门禁、安全与部署治理、运行时适配与发布可移植性。2 表示明确且可执行，1 表示存在但不完整，0 表示缺失或误导。

## Blocker Conditions

缺少人类部署授权、未标示需求冲突、调度者越权决策、实现者自批高风险变更、没有回滚方案、没有预发布证据、适配器隐藏降级，均为 blocker。

## Pass Bar

无 blocker 且总分至少 12/14 才为 `pass`；10–11 为 `pass_with_risks`，只能交 leader 决定，不能触发预发布部署；低于 10 为 `fail`。最终 `complete` 还要求 S6 真实证据。
