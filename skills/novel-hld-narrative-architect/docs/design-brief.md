# HA1 design brief

## 要解决的问题

HA1 把 HB0 已承认的构思义务组织成后续所有 HLD 技能共同使用的宏观叙事坐标。它必须在不增加故事事实的前提下，确定结构形态、阶段、叙事单元、章节壳、重大转折锚点以及每个单元的进入/退出状态。直接消费者是 HS1；如果 HA1 坐标不稳定，故事线、人物弧线和信息结构都会各自建立冲突的时间轴。

## thinking skill 的 Agent 工作

Agent 先对全部 `HDD-HA1-*` 未决投影作处分；出现 `required_now` 时在候选产生前停止。随后从 allowlist 中盘点重大事件、结局控制、必选线、规模约束和禁止决定，比较至少两个在 canonical 字段及代价上真正不同的结构。只有权威证据排除其他方案时，才允许提交单一方案说明。

Agent 的语义责任包括：证明所选结构不是机械三幕模板；检查完整跨度、事件锚定、因果状态连续、故事线容量、结局继承与 LLD 边界；为选择和反证挑战引用具体 source/HST/HNU/HCH ID。Agent 最终提供 `canonical.json`、读取会话和五份有序 generation evidence。

## 确定性 runtime 的责任

`scripts/run_skill.py` 只证明可机械判断的契约事实：work order/input gate 身份、`[HB0]` 拓扑、allowlist 读取、HDD 全量覆盖、稳定 ID、authority/ownership 分离、phase→unit→chapter 包含关系、每个 unit 的状态合同覆盖、禁止字段、精确 package profile 和外部 result envelope。它封装 ready/revise/blocked 结果，但不能判断结构是否真正有叙事力度、候选差异是否有艺术意义或转折是否有效；这些仍由 Agent 证据和 HQ1 裁决。

## 边界

HA1 不编排故事线内容，不设计人物弧、POV、信息揭示、节奏曲线、场景动作、对白、感官细节或正文；不修改构思权威，也不把 must-ask 变成 HLD 决定。章节壳只是容量和顺序容器，不是场景开发。

## 完成定义

P01 必须形成可供 HS1 直接引用的无环坐标和 top-level ready envelope。N01 的权威转折缺失必须形成 durable revise，不能补造事件。B01 的场景细节泄漏必须被拒绝。三项 case 的六维门禁均为 2/2，且确定性证据与语义证据分开记录，才视为实现达到当前验收基线。
