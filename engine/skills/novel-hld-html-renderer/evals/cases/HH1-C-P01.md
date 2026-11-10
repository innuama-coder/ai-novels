# HH1-C-P01 — 确定性离线渲染

## Prompt

输入当前 HH1-A report、判定为 `pass` 且精确绑定该 report hash 的 HH1-B review，以及合法的样式、模板、schema、profile、registry 规则和签名 allowlist。要求把报告确定性投影为离线、可打印、可回流的 HTML 五文件内部包。

## Expected Behavior

- 每个 HRE/HVG 一对一生成稳定 HUI，report、DOM 与 render-target registry 集合全等。
- SVG 具有唯一 DOM ID、`title`/`desc` accessible name，并有文本替代表达。
- 页面无外部依赖，满足静态 print/reflow/injection 门；重复工作区渲染的 HTML 与 registry 字节完全一致。
- 生成精确五文件 HH1.C profile 和 `composite_internal/ready`，不生成 completion。

## Forbidden Behavior

- 改写报告结论、补充故事事实或重新执行 fidelity 判断。
- 遗漏、合并或重复 HRE/HVG，或让 DOM/registry/report 映射漂移。
- 引入网络资源、可执行脚本、重复 SVG marker ID 或不稳定排序/时间戳。
- 读取故事源、生成 publisher 产物或顶层 completion。

## Scoring Rule

六维均按 0–2 评分：0 表示违背硬契约，1 表示局部满足但存在缺失或不可复核，2 表示全部对象级证据完整且可复现。

- `scope_fidelity`：所有 HRE/HVG 一次且仅一次投影、无内容改写为 2/2。
- `input_gate_obedience`：八类签名输入、role、hash 与 HH1-B pass 绑定全部验证为 2/2。
- `output_contract_correctness`：精确五文件 profile、DOM/registry 闭合与 schema 合法为 2/2。
- `semantic_or_deterministic_correctness`：重复渲染关键文件 byte equality，SVG/离线/print/reflow 门全过为 2/2。
- `boundary_discipline`：不读故事源、不作 fidelity/publisher/completion 决策为 2/2。
- `parent_consumability`：HUI 可追踪、可访问、可打印，manifest/result 可由父流程直接消费为 2/2。

## Pass Bar

仅六维全部达到 2/2、总分 12/12，且 Expected Behavior 全部满足、Forbidden Behavior 零命中时通过。
