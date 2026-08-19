# HC1 evaluation specification

## 固定 cases

- `HC1-P01`：每个 core character 有授权 start→pressure→choice→cost→result path；关系变化记录双方 before/after state；key results 有 actor；steps 绑定已有 unit/segment/event；capability/information/permission 支持行动。预期 ready 并可由 HI1 消费。
- `HC1-N01`：候选包含与未授权人物的新关系。必须比较 authority，识别 affected arc/relation，形成 revise 或合适 blocked evidence；不得创造人物、关系或动机。
- `HC1-B01`：调用方要求 appearance/background/profile enrichment。Canonical 必须保持 arc placement，boundary leakage 导致 non-ready，无 completion。

三个 fixture 均在执行前密封；manifest 保存当前 sha256 和唯一 defect injection。不得以修改 fixture/预期答案换取 pass。

## 六维门禁

1. `scope_fidelity`：仅拥有 participation/state/arc/relationship/link/alignment/feasibility placement，不补人物定义。
2. `input_gate_obedience`：严格使用当前 `[HB0,HA1,HS1]`、allowlist、stable IDs 和全部 HDD。
3. `output_contract_correctness`：ready/non-ready profile、completion 条件、manifest 和 package-external result 正确。
4. `semantic_or_deterministic_correctness`：P01 以对象证据证明 agency/pressure/choice/cost/consequence；N01 通过 authority comparison 找到关系缺陷；字段齐全或 forbidden-key 命中不能独占语义满分。
5. `boundary_discipline`：没有 appearance、biography、social circle、新 relation/person、ability/info、scene/dialogue/prose。
6. `parent_consumability`：HI1 可直接读取角色状态、责任、知识/权限检查；non-ready formal result 足以让 Harness 处理，技能不写 route。

## 实际证据

Runtime 行为由 `test_p01_ready_and_parent_consumable`、`test_n01_named_stage_defect_is_revise`、`test_b01_boundary_leak_is_revise` 证明。`acceptance-evidence.json` 对 P/N/B 分别保存六维 2/2、deterministic evidence 和 semantic evidence；contract tests 保护研究数、eval 章节、fixture hashes 与 evidence dimensions。

## 评估边界

当前测试验证封闭案例下的 contract、known defect 和边界稳定性，不证明任意人物弧都心理真实。Agent 必须执行 adversarial review，HQ1 对跳变、plot compulsion、假代价、单边关系和 unowned result 做独立语义审查。
