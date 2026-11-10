# 方法论来源（复核日期：2026-08-06）

以下 13 个独立公开来源均在实现阶段重新访问；只吸收可迁移的方法，不把软件术语硬套为小说结论。

1. [Martin Fowler：Consumer-Driven Contracts](https://martinfowler.com/articles/consumerDrivenContracts.html) — 只验证消费者真正依赖的契约面，并显式暴露 provider obligation。
2. [Pact：How Pact works](https://docs.pact.io/getting_started/how_pact_works) — consumer 先形成独立期望，再由 provider verification 核验。
3. [Pact：Conceptual overview](https://docs.pact.io/getting_started/conceptual_overview) — 封存 consumer artifact，避免验证时悄然改写期望。
4. [Pact specification](https://docs.pact.io/implementation_guides/pact_specification) — 使用版本化、机器可验证的数据结构承载契约测试结果。
5. [Martin Fowler：Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) — 用少量高价值端到端路径配合更密集的局部负例。
6. [NASA Systems Engineering Handbook Appendices](https://www.nasa.gov/reference/system-engineering-handbook-appendix/) — 用 verification matrix 和稳定 requirement ID 维持双向追溯。
7. [NASA Systems Engineering Handbook PDF](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf) — 区分“符合规定”的 verification 与“满足用途”的 validation。
8. [ISTQB Acceptance Testing syllabus](https://www.istqb.org/wp-content/uploads/2024/11/ISTQB-CT-AcT_Syllabus_v1.0_2019.pdf) — acceptance criteria 应明确、可验证并可回溯业务目标。
9. [W3C PROV-O](https://www.w3.org/TR/prov-o/) — 用 entity/activity/agent 关系表达生成、使用和派生链。
10. [JSON Schema 2020-12 Validation](https://json-schema.org/draft/2020-12/json-schema-validation) — 把结构断言与语义判断分层，封闭 schema 只证明可机器检查的事实。
11. [OpenAPI Specification](https://spec.openapis.org/oas/latest.html) — 显式定义输入输出、错误响应和版本化契约，减少隐式调用假设。
12. [SLSA v1.0 Terminology](https://slsa.dev/spec/v1.0/terminology) — artifact provenance 与 digest binding 防止内容在验证链中被替换。
13. [IEEE 1012](https://standards.ieee.org/ieee/1012/12536/) — V&V 活动应有独立性、完整记录和与风险相称的严格度。

## 吸收结论

- 先做 handoff-only consumer test，再用新任务做正式包 fidelity test。
- schema、hash、allowlist、task identity 和 provenance 由机器硬验证；语义由对象级证据支撑。
- 正向路径必须跑过真实 coordinator→consumer→fidelity→publisher，负例覆盖越权读取、篡改重封、伪绑定、部分证明与 first-nonready。
- 只有可重复、原子、闭包受控且可追溯的结果，才具备 Harness Engineering 意义上的可接受性。
