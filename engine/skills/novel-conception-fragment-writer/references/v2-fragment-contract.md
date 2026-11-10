# H1-B V2 片段交付契约

Fragment briefs bind one or more `DCTRL-*` fragment-domain decision controls.
H1-B copies those IDs into the formal fragment package. This proves which
bounded review judgment a scene demonstrates; source anchors still prove only
provenance and do not make the sample an authoritative conception fact.

## 1. 目的与权威层级

H1-B 把 H1-A 的评审计划转成供构思评审使用的小说场景样片。P1 是唯一控制事实
来源；plan/brief 只规定展示任务；片段是 `non_authoritative_sample`，不能反向修改
P1、回答开放问题或成为最终正文。

## 2. 输入契约

同一次调用必须提供：

| 输入 | 必须状态 | 硬绑定 |
| --- | --- | --- |
| P1 canonical package | formal P1 validator `ready` | completion hash、run |
| H1-A plan package | formal H1-A validator `ready` | P1 completion、run、session |
| initialized workspace | `initialized` | current P1 completion |
| planned workspace | `planned` | initialized hash、plan manifest |
| plan input gate | formal H1-A 使用的同一 sealed gate | gate reference、return binding |
| session workspace | `start` 创建、三次 `submit` 推进 | task/thread、前态 seal、forward hash |

任一输入陈旧、混 run、混 session、混 lineage、缺文件或在执行中发生改变，均不得
发布。

### Gate-authoritative plan package path

The planned workspace's sealed `artifacts.plan_manifest` is the sole logical
path authority for H1-B. The supplied physical `plan_package` must be the
exact H1 package named by that reference, and its sibling
`package-manifest.json` must match the sealed raw-byte SHA-256. Canonical
POSIX paths are required; backslashes, absolute paths, traversal, foreign
parents, path scanning, and caller substitution are rejected before a
fragment session is written. `H1/plan` remains the supported legacy package
name, while attempt-qualified and nested H1 package names are supported when
they are sealed by the workspace.

The same exact manifest reference is frozen into the H1-B session, every
phase evidence document, the fragment package, the execution record, and
public replay validation.

## 3. brief 实现

- 每个 brief 恰好产生一个同 ID 的片段，顺序不变，不得合并或遗漏。
- `target_words_min/max` 在 `zh-Hans-review-v1` 中使用；正式片段最少 320 unit，
  上下界至少相差 60 unit，最大不超过 1200 unit；
  `zh-Hans-combined-visible-units-v1`：一个 CJK 字符计一个 unit，一个 Latin
  word token 计一个 unit，空白与标点不计。总 unit 必须在闭区间内；CJK unit /
  combined unit 必须至少为 `0.70`。这只是机械的脚本占比下限，允许少量题材术语；
  它不能判定简繁体、自然语体或任意语言混写质量，这些仍由受控 Agent 的 style
  challenge 负责。
- brief 的 POV、感知通道、信息边界、scene contract、必写与禁写条件逐字段投影，
  不由写作者重新解释。
- 每个 source anchor 至少选一个真正控制场景的 scalar 字段；`id/name/title/label`
  不能单独充当事实投影。

## 4. fact projection

阶段一对每个投影记录：

```text
id
source_anchor_id
field_pointer
value_sha256
required_usage
```

validator 从 current P1 anchor 原值重新解析 `field_pointer` 并重算哈希。阶段三的
projection ledger 必须一一覆盖阶段一投影，并记录：

```text
fact_projection_id
source_anchor_id
source_value_sha256
field_value_sha256
story_specific_claim
evidence_quote
evidence_quote_sha256
challenge_result
challenge_notes
control_status=preserved
```

`evidence_quote` 必须是最终文本中的精确连续字符串，quote hash 可复算。required
demonstration 必须绑定至少一个 fact projection，不能只用人物名或地点名充数。

Python 仅实施保守下限：

- 字符串值与证据存在可靠 lexical fingerprint 时可标记 `lexically_grounded`；
- 合法转述可标记 `agent_verified_paraphrase`；
- 非字符串值可标记 `agent_verified_non_string`；
- 后两类必须由受控 Agent 写出具体 challenge notes。

词汇交集不是语义充分证明；词汇不重叠也不是转述错误。机械层不能识别所有伪造的
paraphrase、隐藏升级或语境性矛盾，这些残余风险由受控 Agent challenge 和独立验收
承担，validator 不得宣称已经普遍解决语义理解。

## 5. 文本与场景硬约束

- 固定 `zh-Hans-review-v1`、`restrained-concrete-scene-v1`、
  `third_person_limited`。
- 至少两个自然段，场景主体是连续当下，不得输出大纲、脚本、评审说明。
- scene contract 的前态、即时目标、压力、阻碍、必要选择、直接后果、后态均有
  exact final-text evidence。
- phase 1 必须交付 `character-grounded-scene-v1` 的人物化场景设计；phase 3 必须
  逐项证明人物专属注意、矛盾欲望、刺激—赋义—行动、递进阻力、潜台词、挣得的
  转折、读者推断空间和无解释性收束。
- 只展示 POV 可获得的信息。
- 允许过程性权衡、感觉、回忆、推断和可观察反应；不得直接公布尚应悬置的最终
  决定、秘密计划或确定答案。固定模式检测只是最低防线，不能替代 Agent 复核。
- 不得把样片称为正文终稿或最终章节。

## 6. 表层细节边界

表层细节必须：

```text
authority_status=fragment_local_non_authoritative
control_effect=none
scope=fragment_only
causal_role=none
history_claim=false
rule_claim=false
relationship_claim=false
reused_across_fragments=false
```

表层细节可以提供动作质感、临时物件状态或非控制性的感官纹理；一旦承担权限规则、
历史解释、关系定义、事件因果或跨片段稳定设定，即属于新控制事实，必须拒绝。

## 7. 三阶段协议

1. `brief-and-source-challenge`
2. `scene-draft`
3. `boundary-and-style-revision`

协议固定为：

1. `start_fragment_session`：完整调用 formal P1/H1-A validators，冻结 P1/plan
   tree、plan input gate、两个 workspace refs、manifest、identity 与 skill profile；
   原子创建 immutable session 和 `next_phase_index=1` 的状态。
2. `submit_fragment_phase`：每次只收一个当前阶段。提交前重验 frozen inputs、当前
   identity、旧 evidence 和前态 seal；写一份不可覆盖 evidence，并原子推进 next
   phase、previous state hash 与 forward hash。
3. `finalize_fragment_package` / `run`：不接受 phase payload；只读完成态 session
   workspace，重新验证三阶段链和 current inputs，再复制 immutable session、
   evidence 与 completion 到正式包。

每阶段 payload 使用 exact field set；三份证据串联前序 reference，并绑定同一
identity、plan manifest、plan input gate、pre-state hash 和 payload hash。最终片段
必须是第三阶段经审计的文本，不能用第二阶段或包外文本替换。乱序、重复、跨 thread、
阶段间输入改变、旧 evidence 改写、会话外倒填及 incomplete finalize 必须失败。

## 8. 包、事务与状态

允许的根文件仅为正式产物、session completion、三阶段 evidence 与 implementation
snapshot。包内 session/evidence/completion 必须与完成工作区逐字同哈希；
execution 必须绑定 completion 和 plan input gate。manifest 覆盖所有正式文件且
不得自包含。发布流程：

1. 写入同父目录 staging；
2. 正式 validator 验 staging；
3. 再确认 P1 与 plan 未变；
4. 原子 rename；
5. 正式 validator 验发布目录；
6. coordinator 接受 `planned -> fragments_ready`。

staging 或发布前失败时不得存在部分正式目录。若 destination 已原子发布并通过正式
重验、但 coordinator 拒绝状态转换，必须保留该完整包作为 non-current orphan：
它仍可复验，但未被 workspace 引用，不能冒充 current，也不能推进状态或生成顶层
H1 completion。不得删除或回滚已经发布且验证通过的包。

## 9. 验收攻击

至少覆盖：

- 只有通用人名/地点文字、却携带真实 anchor 的伪合规包；
- 重封包后引入新控制事实；
- 决定性心理泄漏，即使审计声称 `false`；
- 把表层细节升级为规则、历史、关系或因果控制；
- 同 ID 但 P1 字段取相反值后复用旧 projection/evidence；
- 合法转述正例、非字符串 projection、长度边界、缺片段、乱阶段和陈旧 workspace。
