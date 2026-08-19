# Implementation plan

1. 冻结两个 task kind、各自有序 role 闭包、canonical schema 与 ready profile。
2. 实现最小上游准入：只读取 allowlist 中的 completion、manifest、work order 与当前任务实际需要的成员，禁止全包遍历。
3. 实现 handoff-only consumer 重建与全量故事线、角色、关键功能、约束测试。
4. 实现 sealed-consumer fidelity 双射、obligation、分类和漂移测试。
5. 实现对象级证据、verdict/origin 代数、任务隔离、原子双构建与回滚。
6. 接入 owner registry 的 closed runtime contract，绑定相对路径+内容 digest。
7. 用真实 composite 流程、读取审计校准和篡改负例完成验收。
