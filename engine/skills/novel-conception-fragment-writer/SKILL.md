---
name: novel-conception-fragment-writer
description: 读取自主构思 V2 中同一次 H1 运行的 current P1、正式 H1-A review plan 与 planned workspace，通过受控 Agent 的三阶段挑战和写作，交付固定中文文风、第三人称受限视角、非权威的小说评审样片。用于 H1-B；不写最终章节、不补充控制事实、不修改构思、不组装人审报告。
---

# 小说构思评审片段编写（H1-B）

## 必须读取

执行前完整读取：

1. [V2 片段契约](references/v2-fragment-contract.md)；
2. [固定文风契约](references/style-contract.md)；
3. [人物化场景方法](references/deep-scene-method.md)；
4. 当前 P1 包、H1-A plan 包、同 session 的 `initialized` 与 `planned` workspace。

旧版 D1/R1 scripts、场景契约和历史 references 仅供 1.x 使用，不得参与 V2
准入、生成、验收或 completion。

## 目标

用非权威小说场景样片验证 P1 控制信息能否形成预期阅读体验。样片必须让评审人
看见具体压力、人物选择、直接后果和状态变化，而不是复述构思。

## 硬准入

只接受：

- formal P1 validator 判定为 `ready` 的 current P1；
- formal H1-A validator 判定为 `ready` 的 current plan；
- plan manifest、review plan、source inventory、全部 briefs 同 run/session/lineage；
- 与该 plan manifest 精确绑定且状态为 `planned` 的 workspace；
- 每个 brief 的 POV 和 source anchors 均可由 P1 原值重算。

缺一项即停止；不得从聊天、访谈逐字稿、旧稿或外部资料补事实。

## 固定写作合同

以下值不可协商：

```text
language_contract_id: zh-Hans-review-v1
style_contract_id: restrained-concrete-scene-v1
depth_contract_id: character-grounded-scene-v1
pov_mode: third_person_limited
decisive_interiority_policy: process-only-no-unresolved-decision-disclosure
surface_detail_policy: fragment-local-non-authoritative-v1
purpose: conception_review_sample
```

只允许 brief 明示的感知通道、信息范围和 P1 source-value bindings。表层细节可用于
可读性，但只能是片段局部、非权威、无因果控制作用，不得建立规则、历史、关系或
跨片段复用。

每个 brief 还必须绑定 H1-A 已验收的 `decision_control_ids`。H1-B 只能把这些 ID
确定性复制到对应 fragment，不能新增、删除或重新解释控制项；片段是决策控制面的
阅读体验证据，不替代全量 P1 drill-down。

## 持久化受控 Agent 三阶段

必须先调用 `start_fragment_session`。它在受控 identity 下完整重验 formal P1、
formal H1-A plan（包括相同 `plan_input_gate`）、initialized/planned workspace，
冻结输入 tree、sealed refs 和当前 skill profile，并原子创建 session workspace。

随后只能调用 `submit_fragment_phase`，每次提交当前一个阶段：

阶段必须严格按顺序、各执行一次：

1. `brief-and-source-challenge`：逐 brief 投影所有字段；每个 source anchor 至少选择
   一个非 ID/名称字段，记录 JSON Pointer、原值哈希和 required usage；挑战必写与
   禁写、信息边界和相反输入；同时建立矛盾欲望、解释偏差、自我保护策略、五至十个
   推进节拍、转折代价和余震组成的 `narrative_scene_design`。写作支架不得逐项进入正文。
2. `scene-draft`：逐 brief 写连续场景初稿；固定简体中文、第三人称受限视角、长度
   预算、压力—选择—后果和结尾状态变化。长度使用
   `zh-Hans-combined-visible-units-v1`，且 CJK unit 占比不得低于 70%。
3. `boundary-and-style-revision`：先删除解释性叙述、增加阻力、进入人物意识并恢复
   读者推断空间，再交付最终样片及逐 projection 的 exact final quote、
   quote hash、story-specific claim、challenge result/notes；逐项复核 brief、场景、
   信息、文风、决定性内心和表层细节边界。

每次提交前都重验 task/thread、输入 tree、formal plan、前态 seal 和已有 evidence
链；提交不可覆盖，只能原子推进 `session-state.json` 的 next phase 与 forward hash。
缺阶段、乱序、重复、跨 identity、替换旧 payload、会话外倒填或事后补审计均失败。
`finalize_fragment_package` / `run` 不接收 Agent payload，只能读取已经完成的 session
workspace。

## 职责、边界与约束

职责：

- 严格实现全部 brief，数量与顺序一一对应；
- 把投影出的 P1 控制值转化为故事专属场景证据；
- 让人物以矛盾欲望、解释偏差、关系策略和受阻行动显形，禁止把 scene contract
  七字段依次改写成正文；
- 让规则进入行动，让 POV 人物承担选择，让直接后果抵达 after state；
- 留下可复算的来源、文本、执行、实现和事务证据。

边界：

- 不修改 P1、plan、brief 或 workspace；
- 不新增权威世界事实、人物历史、关系、事件结果、规则或开放项答案；
- 不泄露仍应保持悬念的决定性心理结论；
- 不写完整章节、最终正文、HTML、CSS、可视化或人审结论。

每个片段至少 320 个中文可见 unit、至少五个自然段和十个句末标记。长度只是允许
人物化场景发生的最低空间，不是质量本身；最终还必须逐项提交八类
`narrative_quality_checks` 的两处正文证据。

机械校验只能证明结构、哈希、JSON Pointer、exact quote、保守的 scalar lexical
grounding、常量、边界声明和事务绑定。它不声称理解任意转述；合法转述和非字符串
值由受控 Agent challenge 负责，并留下明确 notes，最终仍需独立评审。

## 交付与验收

完整包必须包含：

- `fragment-package.json`、`fragments.md`；
- `generation-session.json`、三份 `generation-evidence/*.json` 及 index；
- 完成态 `session-workspace-completion.json`；
- `execution-record.json`、`validation.json`、`package-manifest.json`；
- 当前 runner、skill、V2 contract、style contract 和 schemas 的 implementation
  snapshot。

正式验收入口是：

```python
validate_fragment_package(
    fragment_package,
    *,
    p1_package,
    plan_package,
    plan_input_gate,
    plan_workspace_state,
    workspace_state,
    plan_active_return_request,
    runtime
)
```

只有 staging 和已发布目录均通过同一正式 validator、输入未变、manifest 完整且
原子发布成功后，才能请求 coordinator 将 workspace 推进到 `fragments_ready`。
本技能不生成顶层 H1 completion。
