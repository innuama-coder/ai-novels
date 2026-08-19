# HQ1 实现计划

1. 冻结公共入口、实现 hash 闭包和 HQ1 closed schemas。
2. 复用 Harness 的 work-order、input-gate、package-envelope 与 SchemaCatalog。
3. 实现独立读取闭包、producer task 隔离、来源原值和上游包复验。
4. 实现领域、跨域、挑战、HDD、finding、pass claim 与全对象覆盖规则。
5. 实现 ready/revise/blocked 三类公共结果与原子发布。
6. 用真实公共包、单缺陷夹具、篡改、重复运行和 Router 边界测试验收。
