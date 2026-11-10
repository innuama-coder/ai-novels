# Evaluation spec

## 固定案例

- `HQ2-P01`：真实 consumer pass 后，新 fidelity task 绑定封存结果并 pass，publisher 形成唯一 HQ2 ready 包。
- `HQ2-N01`：handoff 无法让 LLD 无猜测工作，或与 HP1 obligation 漂移，结果为 blocked/upstream_defect。
- `HQ2-B01`：越权读取、同 task、stale hash、伪封存或闭包篡改在交付前 fail closed。

## 六维评分

每个案例按 provenance、semantic_fit、instructional_quality、structure、consistency、boundary 评分。P01 六维必须全通过；N01/B01 必须命中目标维度且不得出现错误 ready。机器检查验证结构和绑定，语义分只接受 canonical 中的对象级证据。

## 通过门槛

固定案例、运行时单测、contract assets、quick_validate 与包标准检查全部通过；公开来源不少于 10；公共入口与 owner digest 一致；真实读取审计及其校准负例通过；技能目录不得包含顶层 publisher/completion 实现。
