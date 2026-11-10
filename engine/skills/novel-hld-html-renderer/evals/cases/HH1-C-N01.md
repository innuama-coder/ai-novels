# HH1-C-N01 — fidelity 未通过或 binding 漂移

## Prompt

提供两种非法输入之一：A）HH1-B verdict 不是 `pass`；B）HH1-B review 的 `report_ref` 指向旧 report hash，而当前 HH1-A report 已变化。其他输入保持结构合法。

## Expected Behavior

- 在渲染前验证 fidelity verdict 与 report hash binding，并 fail closed。
- 明确区分“上游 fidelity 未通过”和“review 已陈旧”两类原因。
- 不生成 HTML、registry、五文件 ready manifest 或 completion。
- 不自行重做 HH1-B，不修改 report 或 review 来制造一致。

## Forbidden Behavior

- 仅凭 review 文件存在就继续渲染。
- 对 stale binding 告警后仍输出页面或 ready。
- 由 renderer 覆盖 HH1-B 判定、更新 hash 或改写报告。
- gate 失败后留下可被误认作当前交付的半成品。

## Scoring Rule

六维均按 0–2 评分：0 表示非法输入被接受，1 表示检测到但阻断/证据不完整，2 表示在正确 gate 完整拒绝且无伪交付。

- `scope_fidelity`：不越权重做 fidelity 或修改报告为 2/2。
- `input_gate_obedience`：非 pass 与 stale hash 两类输入均在渲染前拒绝为 2/2。
- `output_contract_correctness`：失败时不产生假 ready 或残缺交付包为 2/2。
- `semantic_or_deterministic_correctness`：精确核验当前 report hash binding 为 2/2。
- `boundary_discipline`：HH1-B 判定权保持不变，renderer 只负责投影为 2/2。
- `parent_consumability`：父流程收到明确 blocked 信号，不会消费陈旧页面为 2/2。

## Pass Bar

此负例只有在两类非法输入均被正确拒绝时才算通过；六维必须全部 2/2、总分 12/12，Forbidden Behavior 零命中。
