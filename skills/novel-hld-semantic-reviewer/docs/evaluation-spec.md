# HQ1 评测规范

评测分六项，每项 0–2 分：职责边界、输入准入、输出契约、语义正确性、确定性与原子性、下游可消费性。通过要求六项均为 2，且无 blocker。

冻结案例至少包括：

- P01：真实公共 HB0–HK1 ready 包，完整对象证据，确定性 ready。
- N01：实际值与 canonical locator 不一致，必须 revise。
- N02：未被一手检查的对象只塞入 pass claim，必须 revise。
- N03：pass claim 使用另一份合法但不一致的证据并重新封装，必须 revise。
- B01：上游因果缺陷，必须 blocked，且不得输出最终路由字段。

任何输入 hash、allowlist、任务身份、schema 或 package profile 不一致均属准入失败，不得发布结果。
