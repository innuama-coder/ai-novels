# HS1 evaluation specification

## 固定 cases

- `HS1-P01`：全部实际权威线有唯一合法 disposition；placed line 有 segments；连接 typed 且有功能；主干连续；mandatory line 有完整运动或合法开放；subject reconstruction 以 IDs 证明。预期 ready 和 HC1 可消费 package/result。
- `HS1-N01`：`LINE-002` 为 placed 却没有 segment。必须指出 disposition/segment 矛盾并 revise；不得发 completion、虚构 segment/event 或静默改 optional。
- `HS1-B01`：合法 optional melody 保持 `optional-not-activated`，候选中的 `pov_assignment` 被识别为 HI1 权限泄漏并 revise。

Fixture manifest 冻结三个输入的 hash、sealed-before-execution 和唯一 defect injection。测试不得改变 fixture 来迎合 runtime。

## 六维 2/2 门禁

1. `scope_fidelity`：只拥有 register/segment/matrix/connection/disposition/reconstruction；optional line 处理忠于 authority。
2. `input_gate_obedience`：只用当前 `[HB0,HA1]`、HA1 stable coordinates、allowlist 和全部 HDD。
3. `output_contract_correctness`：ready 与 revise package、completion 条件、包外 result 唯一且 profile 精确。
4. `semantic_or_deterministic_correctness`：P01 的 line necessity/connection function/subject reconstruction 有对象证据；N01 找到 orphan；set check 只是证据，不替代断线影响解释。
5. `boundary_discipline`：不增加事件、角色内在变化、POV、pacing、scene 或 prose；不为“丰满”强制激活 optional。
6. `parent_consumability`：HC1 能从正式 register/segments/connections/event placement 开始，不需重建网络；non-ready 结果能被 Harness 唯一处理。

## 实际证据

`test_p01_ready_and_parent_consumable`、`test_n01_named_stage_defect_is_revise` 和 `test_b01_boundary_leak_is_revise` 是 runtime 行为证据。`tests/acceptance-evidence.json` 记录三 case 的六维分数及语义解释。Contract asset tests 保证不少于十项研究、eval 固定章节、fixture hash 和 evidence 集合不漂移。

## 结论边界

当前 pass 证明封闭输入中的 network 结构、边界和 parent contract 合格，不证明任意 connection 都有文学质量。Agent 必须真实执行逐线测试和 adversarial reconstruction，HQ1 仍负责最终语义审查。
