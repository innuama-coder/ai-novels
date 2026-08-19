# HA1 evaluation specification

## 固定评估对象

- `HA1-P01`：合法宏观架构。Agent 必须先处理 HDD，比较真实结构候选，投影 phase/unit/chapter/state contracts，并以对象证据证明重大事件和结局锚定。Runtime 预期 `ready`，内容包有 completion，外部只有一个 top-level result。
- `HA1-N01`：`missing_authoritative_turning_anchor`。必须识别缺失锚点并产生 `revise/local_candidate`；不得生成 completion、替代事件或最终路由。
- `HA1-B01`：`scene_detail_leakage`。候选携带 `scene_actions` 等 LLD 字段时必须 revise；合法宏观容器不受污染。

三份 fixture 在执行前密封，`fixture-manifest.json` 保存当前 sha256 和唯一缺陷名。评估时不得通过修改 fixture 或 expected behavior 使实现通过。

## 六维门禁

每个 case 按 0–2 评分，六维都必须 2/2：

1. `scope_fidelity`：只处理宏观坐标；P01 覆盖 HA1 required objects，N/B 不越权修复。
2. `input_gate_obedience`：严格使用 `[HB0]`、allowlist、HDD 和当前 binding。
3. `output_contract_correctness`：ready/revise/blocked profile、manifest、completion 条件和外部 result 唯一正确。
4. `semantic_or_deterministic_correctness`：P01 的状态变化/转折/结局/下游可用性有对象证据；N01 找到指定缺陷；脚本结构检查不能单独取得语义满分。
5. `boundary_discipline`：不出现 POV、scene、dialogue、prose、新事件/人物或 authority 越权。
6. `parent_consumability`：Harness/HS1 只依赖正式 manifest、validation、completion/result 即可决定继续或返工。

## 证据要求

`tests/acceptance-evidence.json` 必须为 P/N/B 分别保存六维分数、runtime 实测证据和语义锚点。`test_p01_ready_and_parent_consumable`、`test_n01_named_stage_defect_is_revise`、`test_b01_boundary_leak_is_revise` 是当前行为证据；`test_contract_assets.py` 证明 eval/fixture/evidence 未漂移。

## 验收限制

通过只说明当前封闭 cases、契约和包行为达到标准，不证明任意小说结构都具艺术质量。真实结构选择仍需 Agent 按 methodology 执行并接受 HQ1 独立语义审查。
