# 输入输出契约

## 公共准入

输入必须是通过 Harness schema 校验的 HQ2 `work-order.json` 与其 `input-gate.json`：`action=execute`、`exact_owner_skill=novel-hld-lld-readiness-evaluator`、上游顺序严格为 `[HB0, HP1]`，且 implementation、state、run、owner、revision、return binding 全部匹配。allowlist 中每个文件必须存在且 sha256 当前有效。

mode 不由调用者自由填写，而由 allowlist 的精确 role 闭包推导。role 集合多一项、少一项或混合两种 mode 都拒绝。

## consumer_test

精确输入 role：`hb0_run_binding`、`hp1_identity_metadata`、`lld_handoff`、`lld_handoff_schema`。

候选目录必须只含：

- `handoff-consumption-test.json`
- `review-session.json`

canonical 必须记录交接重建结果、故事线/角色弧/关键功能消费测试、约束与自由度测试、猜测缺口、findings、六维证据、verdict 与 defect origin。消费测试还必须证明 `chapter_designs[]` 完整覆盖全部章节壳，章序和工作单元正确，逐章核心内容、章末变化与故事线角色足以让详细设计直接开始工作，同时没有越界写成分场或成稿。每个测试项必须以稳定对象 ID 和 JSON Pointer 证据绑定实际读取文件。

## fidelity_test

精确输入 role：`canonical_model`、`cross_index`、`hld_spec`、`hp1_completion`、`hp1_manifest`、`hp1_validation`、`lld_handoff`、`novel_hld_package`、`sealed_consumption_manifest`、`sealed_consumption_test`、`traceability`。

候选目录必须只含：

- `handoff-fidelity-test.json`
- `review-session.json`

fidelity 必须证明：封存 consumer 为当前 run 的独立 ready 任务；LWR 与 LWK 双射；每个 HLD obligation 被覆盖；章节设计与 HS1 的 `HCD-*`/HA1 的 `HCH-*` 逐项同一；mandatory/open/required-elaboration/freedom/prohibition 分类不漂移；不存在 omission、enhancement、weakening。

## 精确读取

`review-session.actual_read_refs` 与 work order allowlist 必须集合相等、顺序无关、hash 完全一致；canonical 的 `source_artifacts` 必须与 actual reads 相等。任何越权或漏读都 fail closed。

## 内部交付

ready 时输出精确五文件 profile，并以 `package-manifest.json` 封存。顶层 `stage-result.json` 使用 `result_scope=composite_internal`；不生成 `stage-completion.json`。非 ready 也保留可验证内部包与 result，供 composite publisher 执行 first-nonready 代数。
