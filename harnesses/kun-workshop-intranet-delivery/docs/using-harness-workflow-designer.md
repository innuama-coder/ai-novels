# Using Harness Workflow Designer

本项目遵循 harness-first：团队协作是有阶段、制品、门禁与回流的编排，不能实现为单一 “workflow skill”。能力技能只承担有界判断或确定性工作，不能重定义 stage graph。修改本定义时，先更新 portable core，再更新 adapters 与 evals，最后运行 source validator 和 release build。
