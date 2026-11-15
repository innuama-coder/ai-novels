# impl3-001 · A3 索引逐 Pointer 语义覆盖表（v3 新增 · ACC-F011 产物）

- 作业：duanxian-audit3-impl3-001（JOB #2471）；修订依据：`outputs/duanxian-audit3/acc2-001-acceptance.md` §A2/07 **ACC-F011**（阻断项）。
- 对象：`duanxian/conception-approved/human-review-report.json`（A3，约 2.84 MB 单行 JSON），BASE `92573f1cca40f37cee04d2beb8708ff33ba603d6`（blob OID `2bad572c1d6f2aee42fae2faa2ba0433195772c5`，SHA-256 `f3d848f15547e77bcb0a0d54b288efe9989e53e286470a200544966af173c640`）。
- 覆盖对象＝三个索引阵列的全部 Pointer 条目：`reduction_ledger` 4602＋`drilldown_index` 4602＋`source_coverage` 3924＝**12,128 条 Pointer 记录**。
- 阅读时间诚实声明：本表的语义覆盖读取全部发生于本轮 impl3-001 作业期间（2026-11-14/15）；**不溯及 impl-001/impl2-001 的历史阅读，不补造旧时间**。v2 账所称「distinct 值全读」（LEDGER L25）与「结构级全覆盖＋抽样值级」（LEDGER §3-9）按 acc2 ACC-F011 判定**不成立并撤回**，以本表为准。
- 关联交付：`impl-001-report.md` v3 §1.1/§11、`impl-001-reading-ledger.md` v3 §0/§3-9 的闭合声明与本表 §2 一致。
- **v4 修订（duanxian-audit3-impl4-001 / JOB #2493，2026-11-15）**：依据 `acc3-001-acceptance.md` §A3/08 **ACC-F015** 修正 §6 的 SC 双入口归类——**EV 族 148 组＝同来源双入口、同值 0、非 §8 复用镜像**；CE 321／PROP 159 双引用族与 §8 复用对的互证关系维持；新增 §6a 逐组分类表与语境摘要；§2 总声明同步。**525 真同值复用对（§8）零改动、不删条目不凑数**；P1 值体未读边界（§10）维持。

## 1. 方法与可复现映射（收据）

**语义覆盖的定义（本表执行口径）**：每条 Pointer 记录的**库内字段**（id/锚/阶段/来源/标签/指针/控制维度/exposure/优先级/rationale/relation/引用串）逐条程序化全量核验＋按语义组直读全部取值词表；`value_sha256` 指向的 **P1 值体不在库**（仅哈希），记「未读」，不以遍历计数、唯一值数或样本数冒充值体已读（ACC-F011 禁止项）。同文复用（同 `value_sha256`）逐对列出并做非等价语境核验（阶段/指针域/展示入口差异）。

**逐条核验项（全部 12,128 条，程序化，无抽样）**：

| # | 核验项 | 结果 |
|---|---|---|
| V1 | RL 锚 `source_anchor_id` 格式 `SRC-\d{6}` 且 1..4602 顺序连续 | 4602/4602 通过 |
| V2 | RL 全字段词表枚举（exposure/rationale/relation/review_priority/decision_control_ids） | 见 §3（18 组合闭合） |
| V3 | DI `id` 顺序连续 `EVID-CURRENT-SRC-000001..004602` | 4602/4602 通过 |
| V4 | DI `label`＝`stage＋" · "＋source_id` 公式 | 4602/4602 通过 |
| V5 | DI `json_pointer` 以数组下标结尾 | 4602/4602 通过 |
| V6 | 同索引锚配对 DI[i]↔RL[i]（`source_anchor_id` 相等） | 4602/4602 通过 |
| V7 | DI `value_sha256` 全部 `[0-9a-f]{64}` | 4602/4602 通过 |
| V8 | SC `source_id` 集合与 DI `source_id` 集合相等（双射） | 集合相等（各 3924） |
| V9 | SC 按 `source_id` 有序 | 通过 |
| V10 | SC `visible_element_ids` 引用解析（EVID→drilldown_index.id；MOD-/FRAG-→A3 内容域模块/片段锚） | 4626 次引用全解析，**0 断引用**（42 个 MOD-/FRAG- 全部落到 characters/storylines/world/fragments/review_path 锚，见 §7） |

**复现映射（本表即收据，可从 BASE 独立复算）**：探针脚本（结构/词表/分组/解析四轮）与全部中间输出存工作档案 `.kunora/impl3-work/`（gitignore，不入库）；下列内嵌脚本可从 BASE 一步复算本表全部合计数——

```python
# 复算脚本（与本表同源；执行：python3 -I <本文件路径下的脚本> 或从 BASE blob 管道输入 A3 JSON）
import json, re, collections, sys, subprocess
B="92573f1cca40f37cee04d2beb8708ff33ba603d6"
raw=subprocess.run(["git","show",f"{B}:duanxian/conception-approved/human-review-report.json"],capture_output=True).stdout
d=json.loads(raw); RL,DI,SC=d["reduction_ledger"],d["drilldown_index"],d["source_coverage"]
dom=lambda p:re.sub(r"/\d+(/.*)?$","",p)
assert len(RL)==4602 and len(DI)==4602 and len(SC)==3924
assert all(a=="SRC-%06d"%i for i,a in enumerate((e["source_anchor_id"] for e in RL),1))
assert all(DI[i]["source_anchor_id"]==RL[i]["source_anchor_id"] for i in range(4602))
assert all(e["label"]=="%s · %s"%(e["stage"],e["source_id"]) for e in DI)
combo=collections.Counter((tuple(sorted(e["decision_control_ids"])),e["exposure"],e["review_priority"],e["rationale"],e["relation"]) for e in RL)
sd=collections.Counter((e["stage"],dom(e["json_pointer"])) for e in DI)
vh=collections.defaultdict(list)
for i,e in enumerate(DI): vh[e["value_sha256"]].append(i)
pairs=[v for v in vh.values() if len(v)==2]
idset=set(e["id"] for e in DI)
anchors={}
def ids(o,ks=("id","module_id","name")):
    r=set()
    if isinstance(o,list):
        for x in o: r|=ids(x,ks)
    elif isinstance(o,dict):
        for k,v in o.items(): r|={v} if (k in ks and isinstance(v,str)) else ids(v,ks)
    return r
for t in ("characters","storylines","world","fragments"): anchors[t]=ids(d.get(t) or [])
rp=set(re.findall(r"(?:MOD|FRAG)-[A-Z0-9-]+",json.dumps(d["review_path"],ensure_ascii=False)))
pool=rp|set().union(*anchors.values())
mods={r for e in SC for r in e["visible_element_ids"] if re.match(r"^(MOD|FRAG)-",r)}
refs=set(r for e in SC for r in e["visible_element_ids"])
print("RL组合=%d DI组=%d 域=%d 阶段=%d SC族=%d"%(len(combo),len(sd),len(set(dom(e['json_pointer']) for e in DI)),len(set(e['stage'] for e in DI)),len(set(e['source_id'].split('-')[0] for e in SC))))
print("值哈希distinct=%d 复用对=%d"%(len(vh),len(pairs)))
print("MOD/FRAG引用=%d 解析=%d 断引用=%d"%(len(mods),len(mods&pool),len(mods-pool)))
print("EVID被引用=%d 未被引用=%d"%(len(refs&idset),len(idset-refs)))
```

预期输出（本表合计，acc3 可逐步对数）：`RL组合=18 DI组=91 域=78 阶段=6 SC族=64`、`值哈希distinct=4077 复用对=525`、`MOD/FRAG引用=42 解析=42 断引用=0`、`EVID被引用=4506 未被引用=96`。

## 2. 覆盖闭合总声明（与 REPORT v3 §1.1/§11 同文）

- **reduction_ledger 4602/4602 语义覆盖完全**：五字段全部取值词表已直读并闭合为 **18 个语义组合**（§3），无一组合、无一取值未读；rationale 全库单值、relation 全库单值（supports）、exposure 2 值、review_priority 2 值、decision_control_ids 12 组合。**未读＝无**。
- **drilldown_index 4602/4602 库内字段全核＋语义分组直读**：六字段（id/stage/source_id/label/json_pointer/value_sha256）逐条核验（V3–V7）；按 **6 阶段×78 指针域＝91 组**（§4）与 **78 域语义总表**（§5）直读；`source_id` 3924 个去重值、64 个首段源族（与 SC 侧同集）全部枚举。**未读＝value_sha256 指向的 P1 值体 4602 条**（#7 维持，不声称补出）。
- **source_coverage 3924/3924 全核＋64 源族直读**（§6）：`visible_element_ids` 引用 4626 次**双词表**——EVID-CURRENT-SRC-* 4506 次（去重 4506，指向 drilldown_index 条目）＋MOD-*/FRAG-* 120 次（去重 42，全部解析到 A3 内容域模块/片段锚）。**未读＝无（除经引用间接指向的 P1 值体同 DI）**。
- **同文复用映射闭合**：`value_sha256` 去重 4077 → **525 个复用对**（全部 size=2、全部同 source_id、仅 7 种域型），逐对全列（§8）；SC 侧 CE 321／PROP 159 双引用族与 §8 复用对（R1/R2 型）互证（§6）。**（v4，ACC-F015）** EV 族 148 组双入口＝同来源、**非同值**（148/148 组两侧 value_sha256 不同，同值 0），**不是 §8 复用对的镜像**——按 source_id 分组与按完整 value_sha256 分组必须分开比对，逐组分类见 §6a。
- **结构性观察（非断引用）**：96 个 EVID 无 SC 可见入口（仅经 drilldown_index 本身可达，全列 §9）；20 条 SC 条目 `visible_element_ids` 非字典序（全列 §9）。

## 3. reduction_ledger 18 语义组合（实际读取＝全字段词表直读；复用来源＝姊妹控制组共享同一指针集；语境检查＝V1/V6；未读＝无）

字段说明（ACC-F011 要求五列在本节及 §4–§6 的列组中逐组落实）：**实际读取**＝组内全部成员五字段值（18 组合即全部取值，已 100% 直读）；**复用来源**＝同伙伴指针的姊妹控制组（如 L03/L04 对同一 C1 指针集分别挂 AGENCY/NETWORK 镜头）＋rationale/relation 全库单值复用；**语境检查**＝锚顺序（V1）＋与 DI 同索引配对（V6）＋组内伙伴阶段/指针域分布（表列）；**摘要**＝组语义（控制维度×曝光×优先级）；**未读**＝无。

| 组 | 控制维度（实际读取） | exposure | 优先级 | 条数 | 索引范围 | 伙伴阶段（语境检查） | 伙伴域(top2)（语境检查） | 摘要 |
|---|---|---|---|---|---|---|---|---|
| L01 | DCTRL-FRAGMENTS-EVIDENCE | drilldown-only | supporting | 30 | 1–44 | B0×30 | /control_registry×25,/fact_dependencies×5 | 片段证据控制·仅钻取曝光·支撑级 |
| L02 | DCTRL-FRAGMENTS-EVIDENCE | default-and-drilldown | critical | 21 | 2–51 | B0×21 | /control_registry×21 | 片段证据控制·默认＋钻取双曝光·关键级 |
| L03 | DCTRL-CHAR-AGENCY | drilldown-only | supporting | 447 | 52–970 | C1×447 | /responsibility_matrix×324,/event_cast_coverage×74 | 人物能动性控制·仅钻取曝光·支撑级 |
| L04 | DCTRL-CHAR-NETWORK | drilldown-only | supporting | 447 | 53–971 | C1×447 | /responsibility_matrix×324,/event_cast_coverage×74 | 人物关系网控制·仅钻取曝光·支撑级 |
| L05 | DCTRL-CHAR-AGENCY | default-and-drilldown | critical | 25 | 732–996 | C1×25 | /relationships×11,/profiles×8 | 人物能动性控制·默认＋钻取双曝光·关键级 |
| L06 | DCTRL-CHAR-NETWORK | default-and-drilldown | critical | 26 | 733–997 | C1×26 | /relationships×12,/profiles×8 | 人物关系网控制·默认＋钻取双曝光·关键级 |
| L07 | DCTRL-CHAR-AGENCY+DCTRL-FRAGMENTS-EVIDENCE | default-and-drilldown | critical | 1 | 744–744 | C1×1 | /profiles×1 | 人物能动性＋片段证据控制·默认＋钻取双曝光·关键级 |
| L08 | DCTRL-WORLD-BEARING | drilldown-only | supporting | 393 | 998–4602 | E1×304,W1×89 | /capability_fact_registry×55,/capability_step_registry×46 | 世界承载控制·仅钻取曝光·支撑级 |
| L09 | DCTRL-WORLD-ONTOLOGY | drilldown-only | supporting | 394 | 999–4601 | E1×304,W1×90 | /capability_fact_registry×55,/capability_step_registry×46 | 世界本体控制·仅钻取曝光·支撑级 |
| L10 | DCTRL-WORLD-BEARING | default-and-drilldown | critical | 19 | 1078–4546 | E1×12,W1×7 | /institutions×7,/event_affordance_catalog×6 | 世界承载控制·默认＋钻取双曝光·关键级 |
| L11 | DCTRL-WORLD-ONTOLOGY | default-and-drilldown | critical | 20 | 1079–4547 | E1×12,W1×8 | /institutions×8,/event_affordance_catalog×6 | 世界本体控制·默认＋钻取双曝光·关键级 |
| L12 | DCTRL-STORY-ARCH | drilldown-only | supporting | 923 | 1630–4406 | T1×584,S1×339 | /causal_edges×107,/planned_causal_edges×107 | 故事结构控制·仅钻取曝光·支撑级 |
| L13 | DCTRL-STORY-SUSPENSE | drilldown-only | supporting | 925 | 1631–4405 | T1×585,S1×340 | /planned_causal_edges×107,/causal_edges×107 | 故事悬念控制·仅钻取曝光·支撑级 |
| L14 | DCTRL-STORY-CAUSAL | drilldown-only | supporting | 925 | 1632–4404 | T1×585,S1×340 | /causal_edges×107,/planned_causal_edges×107 | 故事因果控制·仅钻取曝光·支撑级 |
| L15 | DCTRL-FRAGMENTS-EVIDENCE+DCTRL-STORY-ARCH | default-and-drilldown | supporting | 2 | 1732–3683 | T1×1,S1×1 | /temporal_architecture/milestones×1,/major_events×1 | 片段证据＋故事结构控制·默认＋钻取双曝光·支撑级 |
| L16 | DCTRL-FRAGMENTS-EVIDENCE+DCTRL-STORY-SUSPENSE | default-and-drilldown | supporting | 1 | 1733–1733 | S1×1 | /temporal_architecture/milestones×1 | 片段证据＋故事悬念控制·默认＋钻取双曝光·支撑级 |
| L17 | DCTRL-STORY-ARCH | default-and-drilldown | critical | 1 | 2431–2431 | S1×1 | /storylines×1 | 故事结构控制·默认＋钻取双曝光·关键级 |
| L18 | DCTRL-FRAGMENTS-EVIDENCE+DCTRL-WORLD-BEARING | default-and-drilldown | supporting | 2 | 4566–4570 | W1×2 | /world_facts×2 | 片段证据＋世界承载控制·默认＋钻取双曝光·支撑级 |

合计 18 组＝4602/4602（30+21+447+447+25+26+1+393+394+19+20+923+925+925+2+1+1+2）。decision_control_ids 全库 12 组合：DCTRL-STORY-SUSPENSE 925／DCTRL-STORY-CAUSAL 925／DCTRL-STORY-ARCH 924／DCTRL-CHAR-NETWORK 473／DCTRL-CHAR-AGENCY 472／DCTRL-WORLD-ONTOLOGY 414／DCTRL-WORLD-BEARING 412／DCTRL-FRAGMENTS-EVIDENCE 51／DCTRL-FRAGMENTS-EVIDENCE+DCTRL-STORY-ARCH 2／DCTRL-FRAGMENTS-EVIDENCE+DCTRL-WORLD-BEARING 2／DCTRL-CHAR-AGENCY+DCTRL-FRAGMENTS-EVIDENCE 1／DCTRL-FRAGMENTS-EVIDENCE+DCTRL-STORY-SUSPENSE 1；exposure：drilldown-only 4484／default-and-drilldown 118；review_priority：supporting 4489／critical 113；rationale 单值「保留 current P1 来源对象的逐值审阅入口。」；relation 单值 `supports`。

## 4. drilldown_index 91 个（阶段×指针域）语义组（实际读取＝组内成员库内六字段程序化全核＋词表直读；复用来源＝「复用对成员」列→§8 逐对；语境检查＝V3–V7＋组内源族；未读＝组内全部 value_sha256 值体）

| 组 | 阶段 | 指针域 | 条数 | 索引区间 | 去重源（语境检查） | 主要源族 | 值哈希数 | 复用对成员 |
|---|---|---|---|---|---|---|---|---|
| G001 | B0 | `/control_registry` | 46 | 1–51 | 46 | NAR×10,WLD×8,CHR×8 | 46 | 0 |
| G002 | B0 | `/fact_dependencies` | 5 | 17–21 | 5 | FACT×5 | 5 | 0 |
| G003 | T1 | `/causal_edges` | 321 | 2652–3292 | 321 | CE×321 | 321 | 321 |
| G004 | T1 | `/connection_realization` | 10 | 3303–3312 | 10 | CR×10 | 10 | 0 |
| G005 | T1 | `/derivation_claims` | 157 | 3314–3470 | 157 | DRV×157 | 157 | 0 |
| G006 | T1 | `/design_decisions` | 1 | 3313–3313 | 1 | DEC×1 | 1 | 0 |
| G007 | T1 | `/event_coverage_ledger` | 9 | 3294–3302 | 9 | COV×9 | 9 | 0 |
| G008 | T1 | `/event_demands` | 9 | 3767–3775 | 9 | EVD×9 | 9 | 9 |
| G009 | T1 | `/information_changes` | 2 | 3776–3777 | 2 | INFO×2 | 2 | 0 |
| G010 | T1 | `/major_events` | 148 | 3471–3765 | 148 | EV×148 | 148 | 0 |
| G011 | T1 | `/narrative_timing_constraints` | 11 | 4396–4406 | 11 | TIME×11 | 11 | 0 |
| G012 | T1 | `/obligation_realizations` | 49 | 3778–3826 | 49 | OBR×49 | 49 | 0 |
| G013 | T1 | `/open_items` | 3 | 3827–3829 | 3 | OPEN×3 | 3 | 0 |
| G014 | T1 | `/planned_causal_edges` | 321 | 2653–3293 | 321 | CE×321 | 321 | 321 |
| G015 | T1 | `/planned_event_registry` | 148 | 3472–3766 | 148 | EV×148 | 148 | 0 |
| G016 | T1 | `/planned_proposition_registry` | 159 | 3830–4146 | 159 | PROP×159 | 159 | 159 |
| G017 | T1 | `/process_state_subject_registry` | 91 | 4148–4238 | 91 | PSS×91 | 91 | 0 |
| G018 | T1 | `/proposition_registry` | 159 | 3831–4147 | 159 | PROP×159 | 159 | 159 |
| G019 | T1 | `/state_ledger` | 148 | 4248–4395 | 148 | STL×148 | 148 | 0 |
| G020 | T1 | `/storyline_event_sequences` | 9 | 4239–4247 | 9 | SEQ×9 | 9 | 0 |
| G021 | S1 | `/character_requirements` | 9 | 1630–1638 | 9 | CHD×9 | 9 | 9 |
| G022 | S1 | `/connections` | 10 | 2438–2447 | 10 | SLC×10 | 10 | 0 |
| G023 | S1 | `/coverage_ledger` | 46 | 1639–1684 | 46 | COV×46 | 46 | 0 |
| G024 | S1 | `/cross_line_consistency` | 6 | 2448–2453 | 6 | SLCHECK×6 | 6 | 0 |
| G025 | S1 | `/derivation_claims` | 12 | 1694–1705 | 12 | DRV×12 | 12 | 0 |
| G026 | S1 | `/design_decisions` | 9 | 1685–1693 | 9 | DEC×9 | 9 | 0 |
| G027 | S1 | `/environment_requirements` | 9 | 1706–1714 | 9 | END×9 | 9 | 9 |
| G028 | S1 | `/event_requirements` | 9 | 1715–1723 | 9 | EVD×9 | 9 | 9 |
| G029 | S1 | `/open_items` | 3 | 1796–1798 | 3 | OPEN×3 | 3 | 0 |
| G030 | S1 | `/source_sequence_realizations` | 39 | 2595–2633 | 39 | SSR×39 | 39 | 0 |
| G031 | S1 | `/story_claim_atoms` | 315 | 1799–2113 | 315 | SCA×315 | 315 | 0 |
| G032 | S1 | `/story_claim_units` | 315 | 2114–2428 | 315 | SCU×315 | 315 | 0 |
| G033 | S1 | `/story_obligation_coverage` | 46 | 2549–2594 | 46 | SOC×46 | 46 | 0 |
| G034 | S1 | `/story_obligation_register` | 49 | 2500–2548 | 49 | SOB×49 | 49 | 0 |
| G035 | S1 | `/storyline_demands` | 46 | 2454–2499 | 46 | SLD×46 | 46 | 0 |
| G036 | S1 | `/storylines` | 9 | 2429–2437 | 9 | SL×9 | 9 | 0 |
| G037 | S1 | `/temporal_architecture/markers` | 36 | 1760–1795 | 36 | NM×36 | 36 | 0 |
| G038 | S1 | `/temporal_architecture/milestones` | 36 | 1724–1759 | 36 | MS×36 | 36 | 0 |
| G039 | S1 | `/temporal_architecture/phases` | 9 | 2634–2642 | 9 | TPH×9 | 9 | 0 |
| G040 | S1 | `/world_requirements` | 9 | 2643–2651 | 9 | WR×9 | 9 | 9 |
| G041 | C1 | `/aftermath_responsibility` | 9 | 714–722 | 9 | ASG×9 | 9 | 0 |
| G042 | C1 | `/agency_matrix` | 7 | 52–58 | 7 | AGY×7 | 7 | 0 |
| G043 | C1 | `/character_arcs` | 7 | 59–65 | 7 | ARC×7 | 7 | 0 |
| G044 | C1 | `/character_demands` | 9 | 723–731 | 9 | CHD×9 | 9 | 9 |
| G045 | C1 | `/derivation_claims` | 47 | 924–970 | 47 | DRV×47 | 47 | 0 |
| G046 | C1 | `/design_decisions` | 1 | 906–906 | 1 | DEC×1 | 1 | 0 |
| G047 | C1 | `/development_freedoms` | 17 | 907–923 | 17 | DEV×17 | 17 | 0 |
| G048 | C1 | `/event_cast_coverage` | 148 | 749–896 | 148 | COV×148 | 148 | 0 |
| G049 | C1 | `/information_matrix` | 1 | 971–971 | 1 | INFO×1 | 1 | 0 |
| G050 | C1 | `/open_items` | 3 | 972–974 | 3 | OPEN×3 | 3 | 0 |
| G051 | C1 | `/profiles` | 17 | 732–748 | 17 | CHR×17 | 17 | 0 |
| G052 | C1 | `/relationships` | 23 | 975–997 | 23 | REL×23 | 23 | 0 |
| G053 | C1 | `/responsibility_matrix` | 648 | 66–713 | 648 | ASG×648 | 648 | 0 |
| G054 | C1 | `/storyline_cast_coverage` | 9 | 897–905 | 9 | COV×9 | 9 | 0 |
| G055 | E1 | `/access_and_authority` | 12 | 1056–1067 | 12 | ACCESS×12 | 12 | 0 |
| G056 | E1 | `/actor_authority_bindings` | 58 | 998–1055 | 58 | AAB×58 | 58 | 0 |
| G057 | E1 | `/ambient_context_hosts` | 10 | 1068–1077 | 10 | ACH×10 | 10 | 0 |
| G058 | E1 | `/capability_fact_registry` | 110 | 1090–1199 | 110 | CF×110 | 110 | 0 |
| G059 | E1 | `/capability_occurrence_requirements` | 88 | 1212–1299 | 88 | COR×88 | 88 | 0 |
| G060 | E1 | `/capability_step_registry` | 92 | 1309–1400 | 92 | CSTEP×92 | 92 | 0 |
| G061 | E1 | `/derivation_claims` | 24 | 1408–1431 | 24 | DRV×24 | 24 | 0 |
| G062 | E1 | `/design_decisions` | 7 | 1401–1407 | 7 | DEC×7 | 7 | 0 |
| G063 | E1 | `/environment_demands` | 9 | 1441–1449 | 9 | END×9 | 9 | 9 |
| G064 | E1 | `/environment_topology` | 17 | 1492–1508 | 17 | TOP×17 | 17 | 0 |
| G065 | E1 | `/environments` | 12 | 1450–1461 | 12 | ENV×12 | 12 | 0 |
| G066 | E1 | `/event_affordance_catalog` | 12 | 1078–1089 | 12 | AFF×12 | 12 | 0 |
| G067 | E1 | `/functional_zones` | 53 | 1577–1629 | 53 | ZONE×53 | 53 | 0 |
| G068 | E1 | `/hazards_and_failure_modes` | 12 | 1462–1473 | 12 | HAZ×12 | 12 | 0 |
| G069 | E1 | `/initial_anchor_option_realization_ledger` | 10 | 1474–1483 | 10 | IAR×10 | 10 | 0 |
| G070 | E1 | `/obligation_occurrence_bindings` | 5 | 1484–1488 | 5 | OOB×5 | 5 | 0 |
| G071 | E1 | `/open_items` | 3 | 1489–1491 | 3 | OPEN×3 | 3 | 0 |
| G072 | E1 | `/resource_and_information_channels` | 12 | 1200–1211 | 12 | CHANNEL×12 | 12 | 0 |
| G073 | E1 | `/story_transition_support` | 56 | 1521–1576 | 56 | TRS×56 | 56 | 0 |
| G074 | E1 | `/storyline_environment_requirements` | 9 | 1432–1440 | 9 | END×9 | 9 | 9 |
| G075 | E1 | `/storyline_hosting_ledger` | 9 | 1300–1308 | 9 | COV×9 | 9 | 0 |
| G076 | E1 | `/transition_contracts` | 12 | 1509–1520 | 12 | TR×12 | 12 | 0 |
| G077 | W1 | `/authority_flows` | 14 | 4482–4495 | 14 | FLOW×14 | 14 | 0 |
| G078 | W1 | `/derivation_claims` | 37 | 4422–4458 | 37 | DRV×37 | 37 | 0 |
| G079 | W1 | `/design_decisions` | 6 | 4416–4421 | 6 | DEC×6 | 6 | 0 |
| G080 | W1 | `/environment_demands` | 9 | 4459–4467 | 9 | END×9 | 9 | 9 |
| G081 | W1 | `/history_pressures` | 3 | 4530–4532 | 3 | HIS×3 | 3 | 0 |
| G082 | W1 | `/information_flows` | 32 | 4468–4513 | 32 | FLOW×32 | 32 | 0 |
| G083 | W1 | `/institutions` | 15 | 4533–4547 | 15 | INST×15 | 15 | 0 |
| G084 | W1 | `/open_items` | 3 | 4548–4550 | 3 | OPEN×3 | 3 | 0 |
| G085 | W1 | `/reality_claims` | 5 | 4552–4556 | 5 | WF×5 | 5 | 0 |
| G086 | W1 | `/resource_flows` | 16 | 4514–4529 | 16 | FLOW×16 | 16 | 0 |
| G087 | W1 | `/rule_conflict_matrix` | 9 | 4580–4588 | 9 | WRC×9 | 9 | 0 |
| G088 | W1 | `/storyline_requirements` | 9 | 4571–4579 | 9 | WR×9 | 9 | 9 |
| G089 | W1 | `/storyline_support_ledger` | 9 | 4407–4415 | 9 | COV×9 | 9 | 0 |
| G090 | W1 | `/systems` | 14 | 4589–4602 | 14 | WS×14 | 14 | 0 |
| G091 | W1 | `/world_facts` | 15 | 4551–4570 | 15 | WF×15 | 15 | 0 |

## 5. 78 指针域语义总表（每域一行：实际读取＝域内全部 Pointer 的域字段＋阶段分布直读；摘要＝域语义）

| 指针域 | 总条数 | 出现阶段（语境检查） | 语义摘要 |
|---|---|---|---|
| `/responsibility_matrix` | 648 | C1×648 | 责任矩阵（最大单域） |
| `/causal_edges` | 321 | T1×321 | 因果边（事件间因果连接） |
| `/planned_causal_edges` | 321 | T1×321 | 计划因果边（T1 规划侧；与已发生因果边同值复用对 R1） |
| `/story_claim_atoms` | 315 | S1×315 | 故事断言原子 |
| `/story_claim_units` | 315 | S1×315 | 故事断言单元（原子聚合） |
| `/derivation_claims` | 277 | T1×157＋S1×12＋C1×47＋E1×24＋W1×37 | 推导断言（由前提推出的设定结论） |
| `/planned_proposition_registry` | 159 | T1×159 | 计划命题注册表（与命题注册表同值复用对 R2） |
| `/proposition_registry` | 159 | T1×159 | 命题注册表（S1 立论命题） |
| `/event_cast_coverage` | 148 | C1×148 | 事件登场覆盖（事件涉及人物覆盖） |
| `/major_events` | 148 | T1×148 | 重大事件 |
| `/planned_event_registry` | 148 | T1×148 | 计划事件注册表 |
| `/state_ledger` | 148 | T1×148 | 状态账（实体状态变迁登记） |
| `/capability_fact_registry` | 110 | E1×110 | 能力事实注册表（已确立的能力事实） |
| `/capability_step_registry` | 92 | E1×92 | 能力步骤注册表（能力行使的分步序列） |
| `/process_state_subject_registry` | 91 | T1×91 | 过程状态主体注册表 |
| `/capability_occurrence_requirements` | 88 | E1×88 | 能力出现条件（能力成立所需情境） |
| `/actor_authority_bindings` | 58 | E1×58 | 行动者—授权绑定（谁能动用哪条权限） |
| `/story_transition_support` | 56 | E1×56 | 转场支撑要素 |
| `/functional_zones` | 53 | E1×53 | 功能分区 |
| `/obligation_realizations` | 49 | T1×49 | 义务实现记录 |
| `/story_obligation_register` | 49 | S1×49 | 故事义务登记 |
| `/control_registry` | 46 | B0×46 | 控制点注册表 |
| `/coverage_ledger` | 46 | S1×46 | 覆盖账（义务/事件覆盖登记） |
| `/story_obligation_coverage` | 46 | S1×46 | 故事义务覆盖 |
| `/storyline_demands` | 46 | S1×46 | 故事线需求（W1 线级） |
| `/source_sequence_realizations` | 39 | S1×39 | 来源序列实现（素材序列的落点） |
| `/temporal_architecture/markers` | 36 | S1×36 | 时间架构·标记点 |
| `/temporal_architecture/milestones` | 36 | S1×36 | 时间架构·里程碑 |
| `/information_flows` | 32 | W1×32 | 信息流 |
| `/design_decisions` | 24 | T1×1＋S1×9＋C1×1＋E1×7＋W1×6 | 设计决定 |
| `/relationships` | 23 | C1×23 | 人物关系条目 |
| `/environment_demands` | 18 | E1×9＋W1×9 | 环境需求（E1 侧表述；R5 对 W1 同名域） |
| `/development_freedoms` | 17 | C1×17 | 开发自由度（保留给写作期的自由空间） |
| `/environment_topology` | 17 | E1×17 | 环境拓扑（空间结构关系） |
| `/profiles` | 17 | C1×17 | 人物档案 |
| `/resource_flows` | 16 | W1×16 | 资源流 |
| `/institutions` | 15 | W1×15 | 制度机构 |
| `/open_items` | 15 | T1×3＋S1×3＋C1×3＋E1×3＋W1×3 | 开放项（待定事项） |
| `/world_facts` | 15 | W1×15 | 世界事实 |
| `/authority_flows` | 14 | W1×14 | 权限流转路径 |
| `/systems` | 14 | W1×14 | 世界系统 |
| `/access_and_authority` | 12 | E1×12 | 访问与授权条目（角色对信息/空间的权限） |
| `/environments` | 12 | E1×12 | 环境实例 |
| `/event_affordance_catalog` | 12 | E1×12 | 事件可供性目录（情境可支持的事件类型） |
| `/hazards_and_failure_modes` | 12 | E1×12 | 危险与失效模式 |
| `/resource_and_information_channels` | 12 | E1×12 | 资源与信息通道 |
| `/transition_contracts` | 12 | E1×12 | 转场契约 |
| `/narrative_timing_constraints` | 11 | T1×11 | 叙事时序约束 |
| `/ambient_context_hosts` | 10 | E1×10 | 环境语境宿主（场景氛围承载处） |
| `/connection_realization` | 10 | T1×10 | 线间连接的实现落点 |
| `/connections` | 10 | S1×10 | 线间连接定义 |
| `/initial_anchor_option_realization_ledger` | 10 | E1×10 | 初始锚点选项实现账 |
| `/aftermath_responsibility` | 9 | C1×9 | 事件后果责任分配 |
| `/character_demands` | 9 | C1×9 | 人物需求（C1 侧表述） |
| `/character_requirements` | 9 | S1×9 | 人物需求（S1 侧表述；与 C1 侧同值复用对 R3） |
| `/environment_requirements` | 9 | S1×9 | 环境需求（S1 侧表述；R4 对 E1 线级需求） |
| `/event_coverage_ledger` | 9 | T1×9 | 事件覆盖账 |
| `/event_demands` | 9 | T1×9 | 事件需求（T1 侧表述；R6 对 S1 事件需求） |
| `/event_requirements` | 9 | S1×9 | 事件需求（S1 侧表述） |
| `/rule_conflict_matrix` | 9 | W1×9 | 规则冲突矩阵 |
| `/storyline_cast_coverage` | 9 | C1×9 | 故事线登场覆盖 |
| `/storyline_environment_requirements` | 9 | E1×9 | 线级环境需求（E1 侧；R4 对 S1 环境需求） |
| `/storyline_event_sequences` | 9 | T1×9 | 线事件序列 |
| `/storyline_hosting_ledger` | 9 | E1×9 | 线宿主账（线承载登记） |
| `/storyline_requirements` | 9 | W1×9 | 线需求（W1 侧；R7 对 S1 世界需求） |
| `/storyline_support_ledger` | 9 | W1×9 | 线支撑账 |
| `/storylines` | 9 | S1×9 | 故事线本体 |
| `/temporal_architecture/phases` | 9 | S1×9 | 时间架构·阶段 |
| `/world_requirements` | 9 | S1×9 | 世界需求（S1 侧；R7 对 W1 线需求） |
| `/agency_matrix` | 7 | C1×7 | 能动性矩阵（谁在何环节有决定权） |
| `/character_arcs` | 7 | C1×7 | 人物弧线 |
| `/cross_line_consistency` | 6 | S1×6 | 跨线一致性约束 |
| `/fact_dependencies` | 5 | B0×5 | 事实依赖关系 |
| `/obligation_occurrence_bindings` | 5 | E1×5 | 义务出现绑定（义务在何处兑现） |
| `/reality_claims` | 5 | W1×5 | 现实断言（世界何以为真的声明） |
| `/history_pressures` | 3 | W1×3 | 历史压力（前史对当前的约束） |
| `/information_changes` | 2 | T1×2 | 信息变更事件 |
| `/information_matrix` | 1 | C1×1 | 信息矩阵（知情范围分布） |

## 6. source_coverage 64 源族（实际读取＝族内全部条目直读；复用来源＝EVID 引用指向 §4 组/§8 对；语境检查＝V8/V9/V10；未读＝无）

`visible_element_ids` 双词表：EVID 引用＝进入 drilldown_index 的可见入口；MOD-*/FRAG-* 引用＝A3 内容域模块/片段锚（characters 20／storylines 4／world 17／fragments 1，另全部 42 个在 `review_path` 模块路径中在列）。**（v4，ACC-F015 修正）** SC 侧多引用族按「来源分组 × 值哈希分组」分开判定：**CE 族 321 条×每条 2 引用与 PROP 族 159 条×2 的双 EVID 暴露＝§8 复用对（R1/R2 型）在 SC 侧的镜像**——两侧 DI 的 value_sha256 相同（CE 321/321、PROP 159/159），同来源同值；**EV 族 148 条×2（EVID 296＋FRAG-DX-03 1 次）＝同来源双入口而非复用**——148/148 组两侧 DI 的 value_sha256 **全部不同**（同值 0），§8 七域型不含 EV 对（§4 G010/G015 复用对成员均为 0）。SC 双入口仅证明「同一来源对象的两个展示入口均登记可见」（来源展示关联），不证明值身份复用；值身份复用只能由完整 value_sha256 相同判定，且二者均不证明缺失的 P1 原值已读（§10）。v3 将 CE/PROP/EV 三族并列等同「§8 复用对在 SC 侧的镜像」的表述，经 acc3 §A3/02.2 全量扩查（148 EV 对哈希全不同）判定为**非等价语境误归类，撤回**；逐组分类与语境摘要见 §6a。

| 源族 | SC条数 | 引用总数 | EVID引用 | MOD/FRAG引用 | 多引用条数 |
|---|---|---|---|---|---|
| ASG | 657 | 657 | 657 | 0 | 0 |
| CE | 321 | 642 | 642 | 0 | 321 |
| SCA | 315 | 315 | 315 | 0 | 0 |
| SCU | 315 | 315 | 315 | 0 | 0 |
| DRV | 277 | 277 | 277 | 0 | 0 |
| COV | 230 | 230 | 221 | 9 | 0 |
| PROP | 159 | 318 | 318 | 0 | 159 |
| EV | 148 | 297 | 296 | 1 | 148 |
| STL | 148 | 148 | 148 | 0 | 0 |
| CF | 110 | 110 | 110 | 0 | 0 |
| CSTEP | 92 | 92 | 92 | 0 | 0 |
| PSS | 91 | 91 | 91 | 0 | 0 |
| COR | 88 | 88 | 88 | 0 | 0 |
| FLOW | 62 | 62 | 62 | 0 | 0 |
| AAB | 58 | 58 | 58 | 0 | 0 |
| TRS | 56 | 56 | 56 | 0 | 0 |
| ZONE | 53 | 53 | 53 | 0 | 0 |
| OBR | 49 | 49 | 49 | 0 | 0 |
| SOB | 49 | 49 | 49 | 0 | 0 |
| SLD | 46 | 46 | 46 | 0 | 0 |
| SOC | 46 | 46 | 46 | 0 | 0 |
| SSR | 39 | 39 | 39 | 0 | 0 |
| MS | 36 | 38 | 36 | 2 | 2 |
| NM | 36 | 36 | 36 | 0 | 0 |
| DEC | 24 | 24 | 24 | 0 | 0 |
| CHR | 23 | 42 | 21 | 21 | 17 |
| REL | 23 | 23 | 0 | 23 | 0 |
| WF | 20 | 22 | 20 | 2 | 2 |
| END | 18 | 36 | 36 | 0 | 18 |
| DEV | 17 | 17 | 17 | 0 | 0 |
| TOP | 17 | 17 | 17 | 0 | 0 |
| INST | 15 | 15 | 0 | 15 | 0 |
| WS | 14 | 14 | 14 | 0 | 0 |
| ACCESS | 12 | 12 | 12 | 0 | 0 |
| AFF | 12 | 12 | 0 | 12 | 0 |
| CHANNEL | 12 | 12 | 12 | 0 | 0 |
| ENV | 12 | 12 | 0 | 12 | 0 |
| HAZ | 12 | 12 | 12 | 0 | 0 |
| OPEN | 12 | 15 | 12 | 3 | 3 |
| TR | 12 | 12 | 12 | 0 | 0 |
| TIME | 11 | 11 | 11 | 0 | 0 |
| ACH | 10 | 10 | 10 | 0 | 0 |
| CR | 10 | 10 | 10 | 0 | 0 |
| IAR | 10 | 10 | 10 | 0 | 0 |
| NAR | 10 | 10 | 7 | 3 | 0 |
| SLC | 10 | 10 | 10 | 0 | 0 |
| CHD | 9 | 18 | 18 | 0 | 9 |
| EVD | 9 | 18 | 18 | 0 | 9 |
| SEQ | 9 | 9 | 9 | 0 | 0 |
| SL | 9 | 9 | 8 | 1 | 0 |
| TPH | 9 | 9 | 9 | 0 | 0 |
| WR | 9 | 18 | 18 | 0 | 9 |
| WRC | 9 | 9 | 9 | 0 | 0 |
| CAU | 8 | 8 | 4 | 4 | 0 |
| WLD | 8 | 10 | 1 | 9 | 2 |
| AGY | 7 | 7 | 7 | 0 | 0 |
| ARC | 7 | 7 | 7 | 0 | 0 |
| INT | 6 | 6 | 4 | 2 | 0 |
| SLCHECK | 6 | 6 | 6 | 0 | 0 |
| SUB | 6 | 6 | 5 | 1 | 0 |
| FACT | 5 | 5 | 5 | 0 | 0 |
| OOB | 5 | 5 | 5 | 0 | 0 |
| HIS | 3 | 3 | 3 | 0 | 0 |
| INFO | 3 | 3 | 3 | 0 | 0 |

## 6a. EV 同来源双入口分类：148 组全列（v4 新增 · ACC-F015 产物）

**方法（与 §1 复算脚本同源，两种分组分开比对）**：① 按 `source_id` 分组——EV- 前缀来源共 **148 组**，每组恰 2 个 DI 成员（`/major_events` 3471–3765 ↔ `/planned_event_registry` 3472–3766，1-based DI 序号逐组相邻）；② 按完整 `value_sha256` 分组——4077 distinct、**525 个 size=2 真复用对**（§8；其中 EV- 来源 **0 对**）。交叉结论：**148/148 组两侧哈希不同（同值 0）**，无一 EV 组落入复用集合；对照组 CE 321/321、PROP 159/159 两侧哈希相同（真复用）。

**语境摘要（148 组逐组回读的一致项/差异项）**：阶段两侧同为 T1（148/148）；指针域恒为 `/major_events` ↔ `/planned_event_registry`（148/148）；`decision_control_ids` 两侧不同（**148/148**）；`exposure` 两侧不同 1 组（147/148 相同）；`review_priority` 两侧全部相同（148/148）。即 EV 双入口是「同来源、同阶段、同优先级、**不同控制语境**」的两个独立值对象（两侧哈希不同）——展示入口关联 ≠ 值身份复用，二者亦均不证明 P1 值体已读（§10 边界维持）。

复算脚本（自 BASE 一步重算本节全部数字，只读）：

```python
import collections, json, subprocess
B = "92573f1cca40f37cee04d2beb8708ff33ba603d6"
d = json.loads(subprocess.check_output(["git", "show", B + ":duanxian/conception-approved/human-review-report.json"]))
DI = d["drilldown_index"]
by_source, by_hash = collections.defaultdict(list), collections.defaultdict(list)
for i, e in enumerate(DI):
    by_source[e["source_id"]].append(i); by_hash[e["value_sha256"]].append(i)
ev = {s: v for s, v in by_source.items() if s.startswith("EV-")}
assert len(ev) == 148 and all(len(v) == 2 for v in ev.values())
assert sum(DI[v[0]]["value_sha256"] == DI[v[1]]["value_sha256"] for v in ev.values()) == 0
pairs = [v for v in by_hash.values() if len(v) == 2]
assert len(by_hash) == 4077 and len(pairs) == 525
assert sum(DI[p[0]]["source_id"].startswith("EV-") for p in pairs) == 0
ce = {s: v for s, v in by_source.items() if s.startswith("CE-")}
prop = {s: v for s, v in by_source.items() if s.startswith("PROP-")}
assert sum(DI[v[0]]["value_sha256"] == DI[v[1]]["value_sha256"] for v in ce.values()) == 321
assert sum(DI[v[0]]["value_sha256"] == DI[v[1]]["value_sha256"] for v in prop.values()) == 159
print("EV dual-entry=148 same-value=0; genuine pairs=525 (EV 0); CE same=321; PROP same=159")
```

**148 组全列（source → 两侧 DI（1-based）→ 各自指针与 hash → 分类；哈希为完整 64 字符，可直接与 BASE 比对）**：

| source_id | DI A | 指针 A | value_sha256 A | DI B | 指针 B | value_sha256 B | 分类 |
|---|---|---|---|---|---|---|---|
| EV-STEP-0dea102b3c782457d437 | 3471 | `/major_events/79` | `616108a5d420555342da9467ad3d9434465e5434238e8bd2acae6b2e75cb5120` | 3472 | `/planned_event_registry/79` | `08f8e8fee15bebcf0b6bfcc334a3e4d0dd91695ccfb5a774b74b8e23fa2193ec` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-172d9162fd888ab62959 | 3473 | `/major_events/92` | `d3253c11624744f3c2b979dd712e7353db81c2c64d3bef4b67d49ca158109d83` | 3474 | `/planned_event_registry/92` | `80127d2a944864fb4944d880dbcc4bf5b97136dced96528be1eb91145dabaa02` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-18aebbec1eecc59a4ffe | 3475 | `/major_events/76` | `d0ac9700c1169381dadde70b78ff18351a84b522dbe5959e688595a43504dc09` | 3476 | `/planned_event_registry/76` | `55e686a6ceb968c747a4d23dd89fcab7e0f73cd5f9b5b536c37fd75953cb6c02` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-18b62bbcf77b4b5d79fe | 3477 | `/major_events/57` | `e69cd705d560831a12487823464cb33e27c5f01b80edae01d943c66f34a771fa` | 3478 | `/planned_event_registry/57` | `be376b04eb466e32fb4982f6fc106df477ee465d9401ef99b35a1e6df3b0b686` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-19dfd35b780799b69c29 | 3479 | `/major_events/95` | `d5ffc12ecb6a1d6934be0082bb79c9a6842c9fbd1a357b3991178859fb000b17` | 3480 | `/planned_event_registry/95` | `c52c922f420c40d4523b3def5e6e160eee0bfcc2c1f0d515f469ec3e00d74431` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-1c909116fba24cef75a8 | 3481 | `/major_events/97` | `e176f8a6407b9360b234759a195769ffbf5def9a6e9906d23621bdfefc5f16e6` | 3482 | `/planned_event_registry/97` | `da683225da0fae70957acd1f74f1eb46faa945277328d1d840aa13ae41570332` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-1fb4276e7018bac5ce44 | 3483 | `/major_events/107` | `0790fcbc49cc0e34c7bcea36fd1dfeee45336e5a477b27ac357d80594a6d23b5` | 3484 | `/planned_event_registry/107` | `37f620221e983366e0965816923190916fdfde37b2f4fa7c3289f3c0c2c97855` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-24a0a9ef678d045a3313 | 3485 | `/major_events/98` | `43109638f91bfb34235b445a9b32136b21fd7e137f158ca5fec2036de527da9d` | 3486 | `/planned_event_registry/98` | `5461cefd9ebbca97bd2cb2eabe06a6bc8c7c431cf683bb01917b3abc56da13a8` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-267760794761749d3045 | 3487 | `/major_events/112` | `347ed7933742760d5af21f5f8fa98dfc0d5fbed85979d0e011f9e5b255768890` | 3488 | `/planned_event_registry/112` | `17dda8322bca3f89c5a0a03c1ad7209df78e11d9c18c93721ae45e06205124d7` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-2acb731bc588bc784d1e | 3489 | `/major_events/58` | `d6476e26fd10a264e93903a5340f1ea21fbc765d039b7262681b6b50fa47f141` | 3490 | `/planned_event_registry/58` | `e1318446da44f44e108bb2968438e61403d99b7a6dde63c17a463c321ffd76d0` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-2d78c15735417277a13f | 3491 | `/major_events/77` | `041cde78697712f90f77f57677a42c524a83e4ca521eeb1d829a83581f3da7d1` | 3492 | `/planned_event_registry/77` | `24da4fe4ccaf0179ad4bdf682013d4f9525141e924cfeab28e5415cf2be6f0b4` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-340dbd1efedf7adad59f | 3493 | `/major_events/94` | `ecc29622324922275a59bd0f4851854c721f16909bf6daf86485d5880ea972bd` | 3494 | `/planned_event_registry/94` | `87a1282be5b48370f2feb7eb2d3360f0766f411ee4763763ee6a378aa1a8abc7` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-348d44428b7e7637841a | 3495 | `/major_events/63` | `f7968360c54681a72617c28670bcbdc60fb80c732bc0871c23502e2f0e644afd` | 3496 | `/planned_event_registry/63` | `3ee84bda96770ef6ce9e4f81e24f64723ed6aecc18b716064b15af908fd7b247` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-3525c6ddb5b970616fa5 | 3497 | `/major_events/66` | `2a8933e64a633523628944552fe356364431b9e00b7d7efc9ed36460487028c8` | 3498 | `/planned_event_registry/66` | `e5b20258e9100bc1f9ee40337264c937ba0ae2af2a1013abfabd54e1c8b030cc` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-35ebcbe1222c0470a9f8 | 3499 | `/major_events/104` | `ac81118c79f198bcb898016d5ff5ab59fdc3e4b1ac62ed9f09d497aa8af75b93` | 3500 | `/planned_event_registry/104` | `cc90422352f8036d0e19e2cf13f4e02c3b371ad073d11d70f5f0d92c62bf8112` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-36eb7ed3b5e377c78643 | 3501 | `/major_events/99` | `f8bc578a4b64907b067edf6a16b22735e6648319c335f7bcb61424a1e6ba5276` | 3502 | `/planned_event_registry/99` | `e11ab06fe81ed0e0040c9f7d206d4ec8441d4a577eaece8018dff96767e85a86` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-3aced419f99dd434d34c | 3503 | `/major_events/110` | `3dc2ad5e28a0e58ae6965c85234b2bac76e2507ff7e4e78d99821ea1cf228132` | 3504 | `/planned_event_registry/110` | `c0e71e91a53138d0375b1f37603a65b92df8e5137098441f2e0143b1ea2a909f` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-3b596fca920a5e0de634 | 3505 | `/major_events/141` | `48bde4018b7c75755c37b3875a225717fa24f928bcff5cab78ea3fccb3bb3097` | 3506 | `/planned_event_registry/141` | `2fe37cb846bf9136a4efc3b346a26bdf00c285c79ca7a3b60fcbc282907c7f41` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-3d5f6d06fcf17d90e438 | 3507 | `/major_events/116` | `e788c70c44c1e8bd74efc54b9e8343b81ce1e3ae551af5b8ae3c9278ef97c9b4` | 3508 | `/planned_event_registry/116` | `a8906f18352716640f751f1d39b2bdd89c74147700f3eaaeaee6085f7a2aad4f` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-3d981009cbe6bc28a097 | 3509 | `/major_events/115` | `ae3d26826856347805dfaf55b881a1b1c4c9905244d3e61c554cc91d517b14da` | 3510 | `/planned_event_registry/115` | `2aecce849d618dd5d1a11038e281743a07e58c4d077b08c62999464458905f54` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-3f6b3df08b98044336e2 | 3511 | `/major_events/142` | `04878843f0d4b3966d5ed15c487397740435a8b2b7fbdf70081bc0f452659c23` | 3512 | `/planned_event_registry/142` | `c26d713e9076d7d792d64284142c421615b0425e78e14ecca66ccc8750d71ab7` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-40e217447db25248abaf | 3513 | `/major_events/122` | `15a677ecfcb661247aad131a69bfa3bd13bb6b1dca86c8ff708186b13c7b7ec8` | 3514 | `/planned_event_registry/122` | `c75f6a9002e712f6725af8c58670d814713ad220e1a663a9251cfb44ac71a733` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-4f379e51a9275b670a94 | 3515 | `/major_events/84` | `288c1018b465342dc457f27094b8a464072f81e9a162cd5cd4d0c5f4a9950c90` | 3516 | `/planned_event_registry/84` | `47ca918b4947c7957616ee69f9e49524f9ab8c90af7d5a2fbab52b0d93b111c2` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-528f02a45822599b4af0 | 3517 | `/major_events/81` | `9434e998b858e5cb43637a71faa60809c8168b3e3acfa6794adaa1cd14ab7d48` | 3518 | `/planned_event_registry/81` | `270b020ebb19f441503b6879dc071942a4ce87b3b0faf9931642ee1cf9ae18bd` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-52c64e59ffd181ac3206 | 3519 | `/major_events/132` | `f92c98179cadb51dca7367365d71834fdd26dbe448a8e3cdddadd8e731afa6f4` | 3520 | `/planned_event_registry/132` | `713cab700aca3aeae23995d0bcfa314e4cb04aae8a4671c0bcab38ef88f63dd4` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-56bf5263aa22d95e5a12 | 3521 | `/major_events/103` | `f05d0e28c453c2022fb234130d4cb862dc94c94ad5861b47491c857aaf805b20` | 3522 | `/planned_event_registry/103` | `2802ffe4880a9f2ad13fd367d1b1c075fa8320214770c25e87161673e7632618` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-5953501ec9f6c35fd36a | 3523 | `/major_events/147` | `420b90a163a02ac10b1c3393c91bd76848238e9206f02d10afbf3bfed200577c` | 3524 | `/planned_event_registry/147` | `356d7907f1661f2480c508bf3e45c0313cf70776a2906037f43b3f6cb11f8978` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-59dd960f59b63857d1ff | 3525 | `/major_events/68` | `f561a38bba5bd7d8ef36060cbc4e6284951ce075f2f1e1ad6c8b28a3d81d22b9` | 3526 | `/planned_event_registry/68` | `2e591cc1afc4cf7f73cb5f7b03407c7d42ec01df79f89593d0dce3e95f9a8d01` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-5cad352f85015c3418fa | 3527 | `/major_events/86` | `df8b0b07ac4e5ee7a59024e808bcd09e1e5b8aa76d66baa891eaed5cdd478b36` | 3528 | `/planned_event_registry/86` | `185196b56c3363f8df29131f9782f4ffd1555990a4eeb2714acb62a99ed8a83b` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-5caef3977c7a95c2e4d9 | 3529 | `/major_events/133` | `3ec5128931ebaa97b07ff8466627d7765e520fa095a296e42a67ab8ac7374b4c` | 3530 | `/planned_event_registry/133` | `9310ef0971b96f9a673e50ebe890f45c63b3e27ebdbc1ea7f739ea156aee702a` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-60b2bbe7f340820a7006 | 3531 | `/major_events/136` | `7fa38e902153a5e5b90c75591641b5143ab5933fadc2fbc9eba7176acfb1586a` | 3532 | `/planned_event_registry/136` | `ece7568fbb43c140899648be13568f348ee51dd2e85a4539d2e808be126e09b0` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-60f5388292936582d629 | 3533 | `/major_events/61` | `386dfd031b0a0d097777e4ec3498f435b4164b04f87d9ca523f9d95e0a587b7f` | 3534 | `/planned_event_registry/61` | `2b906d2607140b1c8ec0297d969c0858b2e9f054f72eebd3b629a1d5ec64ce11` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-61bc434bc091129278fb | 3535 | `/major_events/144` | `69319c24a2f3be314a37a3aaff051bbf6733e6b91802e5d05dc355c8f01fd69f` | 3536 | `/planned_event_registry/144` | `15220f8eeccc190dc7121cbd863a3fb2a710a6da5425fcede7eaa8c47974de56` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-6591a6a12dd0cea3ca32 | 3537 | `/major_events/121` | `3722e726c40f157fb47e7e7fcec5e70e24e072cd6b835725ed456c4621416f42` | 3538 | `/planned_event_registry/121` | `c87533449a878c41e8db1cfea35c7fca31b193f57703cf9f82c5dd1c120640a2` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-667133f35fe90022ef49 | 3539 | `/major_events/118` | `6bc14fec9409441f7d7b5cd179b7c7a91485b237902fb487454275133da00dd2` | 3540 | `/planned_event_registry/118` | `0830c41ea6eef06df3d801c6d633ee4e1a64769ad03cfcb84bd89277601008c4` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-66e82007060d60b70177 | 3541 | `/major_events/140` | `ac0488c2db3093dd9a4587d9f95f4c2ac2414e687ef17d185739afee3f51aa2f` | 3542 | `/planned_event_registry/140` | `e8e4bcced7a52b1bd1af8ebbfe4a7b282cf01178045562101375c27dffae95b4` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-675c6bac3834deeafdf0 | 3543 | `/major_events/83` | `27b5d58856a73cdb2fdfa7cf5de38c1123b03b7621ede20cc762b8e13fb0c393` | 3544 | `/planned_event_registry/83` | `783133f52085f9d040d27ee93fded0ff59e73f9913041f364d9ada1ccba0af4d` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-6837f15ed80151533d3b | 3545 | `/major_events/82` | `ee6a31dd3a6289768570eddc5fcd81a5b0e8432e4c0d0023420c240dc4d11897` | 3546 | `/planned_event_registry/82` | `50579205e56ab17817756d862a50e4e91969ae0443a4989bc888e4abd7e6775c` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-6b994de132cb9f6f9e4f | 3547 | `/major_events/71` | `3b7a4de9a831d00615fa98ed5aa31b81ca1d5f89a766d6167b5ca95e6c90001e` | 3548 | `/planned_event_registry/71` | `7c33721680d1c0627c9ddf8a0cd9a5d1de444a0dd82779835ad9606e9993cf8f` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-6d4523892a04ae529e2c | 3549 | `/major_events/120` | `30b1bf46534fd92e0c55bc521644242f35028734318c732ffdb737a8c52a320b` | 3550 | `/planned_event_registry/120` | `e30ac704b7d569fbacf3ae84e8711299475ca436b99583e1112f0936eb2aa2e9` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-6db789879ca1be9047f8 | 3551 | `/major_events/134` | `a3e112b4640398bf24985fa90774713479b59815ed3b9d3afa55ae61c2eb98cb` | 3552 | `/planned_event_registry/134` | `86aeb1f5bc9bb3d38eeff47c5da510d47281a6ca5d9597d994402781f399f032` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-7318a405377f43454117 | 3553 | `/major_events/59` | `48048932608d162008b4a0a72017f0f77969b9055fa8ddb29a136b5ef1bdc2ec` | 3554 | `/planned_event_registry/59` | `128b0314d623670921eee1c1dbed9f4499f3be9a6e95250dd39224dd988dfb78` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-7629f324a08b084c61bb | 3555 | `/major_events/117` | `6a9acc94a4b15f101ae02e4970d4169e2e3650ee615b66d928d5a2b9928d72e3` | 3556 | `/planned_event_registry/117` | `5033a17a9496e484ac3ea3e00729b7b68d894c076f9f3a709cefcc301e8dd8af` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-78380a3589d0413cd1fd | 3557 | `/major_events/125` | `be9e604360af11d4cb23bc12fec4735b399721e6d71eb4d0038dd4e1fd002919` | 3558 | `/planned_event_registry/125` | `9117b2d7ad1dded8a0b886915340389f4f075db6123b74fae0e562504c02c21c` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-7d28d9844c23a20f52f3 | 3559 | `/major_events/75` | `864906186be4b02a1f32b5342aab1e2e7c56d2ae7c8c39e997748ed7d3ae7e0e` | 3560 | `/planned_event_registry/75` | `3ecfd438d4f3df8bd60ac24bf2d71ba413d05fe7655cff8bd826567724d62ead` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-85ffd0f519583479afd6 | 3561 | `/major_events/113` | `39b2bfcf09522022794516aed205962ada7602de90c5d400ffa6dfa48326a83c` | 3562 | `/planned_event_registry/113` | `83d7fe53e158d85d1610bafe630455334bcc73812a56726030ae87f0d8549185` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-862ee99733eb95672009 | 3563 | `/major_events/96` | `54f977dbed909732be4622c789932ceee419ea5b9e210d99324bc4e8594700ad` | 3564 | `/planned_event_registry/96` | `467b87c59c9f1c222814817295155cdabd756d8f930af166ebdd6f20619f5bb6` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-86a0a9868a8d5eb2135e | 3565 | `/major_events/64` | `14981513befe50f0a19b9742080d5059f5883a672538561afbd89261ccbfdc2e` | 3566 | `/planned_event_registry/64` | `d55dbfa0344bf49a85fc10b017edbe36fa2f46e8dab3065995ee07eb212a05f8` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-86da0d601d1dc23cc70e | 3567 | `/major_events/65` | `cddb65fea8d2601bc1e9c6ee1c4aeb4880002dcd22cc14f420b7ffc132bf06ce` | 3568 | `/planned_event_registry/65` | `7a4d6c94df9c086d67f9ce429defc9b9a8679b0d29f3935cc4ad6993a6e9ef7d` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-8943220c367ad6872c38 | 3569 | `/major_events/138` | `c4db49730b26476f346f6faf4b7d189153d974ab672706447bf846c1d61a1069` | 3570 | `/planned_event_registry/138` | `301af9077003df0db72ecc6cc4e0ce9e9f22beed46cce9f16c9b1f778ac7b7f1` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-8bee418690ec5353489e | 3571 | `/major_events/109` | `c31fe960a14527e0bf9af9ba1c3ccdc7c616cbdfafcd685be26e8a9f4287a6f9` | 3572 | `/planned_event_registry/109` | `4c3230f370d53096abf0dcdd23a7ece22ac6d9879fe5dc56c72ff942c1f4acaa` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-8c31fe85a3464b7e76f6 | 3573 | `/major_events/123` | `f41edf133ba31cc0ba678f126055ba524952ebf902f58e5e3208b731b4bb25b2` | 3574 | `/planned_event_registry/123` | `b4a8ac4bae472fccaeda96a39b26255c827b5aed1eec6f9961e542d3dc1f6739` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-90ef8170b86f26ecdf76 | 3575 | `/major_events/145` | `bfaa19f781409796bfc1515d938cc6b68b17fb47f5459674bf547fbb98d18637` | 3576 | `/planned_event_registry/145` | `2fd9c8fa160ec8c14b57134f6ffe37dc52eed666d199649d9459c8fe4f6961b8` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-9a112d7df56e03d943be | 3577 | `/major_events/124` | `55f174e7c8020eb31846c0e1cadc0b9cb725f461c2179f93df4dd34d78bd04a7` | 3578 | `/planned_event_registry/124` | `a6d96deb3088b458f430adeb1b8319548c5f7fa8fd08c2e282a500c2986280b4` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-9cf62f7f13ad2232106a | 3579 | `/major_events/87` | `8e2eaa23c4f74553748b00aa1c435421dcb965118bf54689b5f28d23cbcb1b9d` | 3580 | `/planned_event_registry/87` | `39526c885e31f00bca2e07b9764bf3c3d27fed6c1f1930f70e7771831d4c6981` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-a34f348d62dcf1823019 | 3581 | `/major_events/102` | `827069d51ab3736358cc8c86d1c8b1438e841213d490797cac996271148da682` | 3582 | `/planned_event_registry/102` | `e9bcf5f9875a4adacc9fb77b1d64c4e354d6ae8c8357303b28bbbd3b693207d1` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-acd32ff2eb8a5e8c28fd | 3583 | `/major_events/105` | `a00f1322c43eb56499c34b164c5930b51fdbf5f80d64c0a1df586c76f22f8573` | 3584 | `/planned_event_registry/105` | `c4a71886d7fb84c6282dcdceac52079f1bf1739598a84105c212b811734e199d` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-ad421c6949fe8b0d685e | 3585 | `/major_events/56` | `49edc1a4eb0a1f97b58ca9a351237c503df27f01fa8d7f8782a5b9bdf47c523f` | 3586 | `/planned_event_registry/56` | `24bc3203b49b6f39cd341f6af1c49abd71d2aae4b14711bfa4408f611c0c0c34` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-af4295924523a4c93a0a | 3587 | `/major_events/126` | `43e844cbda33660e8bf34690d81b0e9ee882454b5f0296300393528cd66c217c` | 3588 | `/planned_event_registry/126` | `b6c7f71d6b0ae62e90036b285b8c4ef5cb8a91507bf7c063cfbd901f9b04fb1f` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-b50cb2e8775246c032b5 | 3589 | `/major_events/93` | `43ef34a9d46b1ca37fba503ce8cbd4a6edf525545c2ac2bc09bf9afa1d0c2ae2` | 3590 | `/planned_event_registry/93` | `64a58336fa626c7ab48f6b3f7530ad6406ea9bba4aa340d15c9fc4e8e2913895` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-b61cbce869e9c5650a34 | 3591 | `/major_events/90` | `9c2367427730d2a93ef34251a846dbc729d3f6915d2ba68f1478bb0fa7f5c8bd` | 3592 | `/planned_event_registry/90` | `55cf98e09b1ea44f8462c1d1b014d3c719c14916e84edff29bb45dbe4c16759d` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-b6776de65d2f0be9a982 | 3593 | `/major_events/60` | `f4914b3078c9463e9dce532c9a5f327e73e8e6b8799aae58931496c1fbc2bf15` | 3594 | `/planned_event_registry/60` | `6ee408d6d1157c9ca50bc6152f5457d4a26c0e2d4be7a4e96d4e5aa149d15aae` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-b6f80226cf64474f2e7d | 3595 | `/major_events/135` | `f88a6efacaf49ddb0f1759f0847e973ac95bd519d4e0cf61a384f003b62e0e04` | 3596 | `/planned_event_registry/135` | `8659248ed78fb55467a46d64f27ed7c454768299b93575d1eca4ccd72a3c2cd4` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-b909dcc178715efc5fc6 | 3597 | `/major_events/72` | `73acdd341fa14f9eb0ca728a538bba71c81dbd860d8d22b20a5f22034abd0092` | 3598 | `/planned_event_registry/72` | `5fd7236d98608c4d2c28b99336250e2acec077b115e0d1824210b416589ef8a9` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-b9992dbd6cdee1ec1bac | 3599 | `/major_events/137` | `cd6853dbb3f0d0f17c190adc3d27b39faa7b68de1e34aa53ad0b55905d8e13af` | 3600 | `/planned_event_registry/137` | `bfb1bbfe0837bd56a594d830af5cb169cf4e0280828d79c94d63bf7be866b9ba` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-bc7c911e823d7df35b3e | 3601 | `/major_events/114` | `3b67110eb610672435045f53f36626f56818ef93b84da2269144b6d27561e7a8` | 3602 | `/planned_event_registry/114` | `77f8e51ad90b1a54ff7bc7e1482498eb863e359e460a1e2b11820da0bb9c3e37` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-bd40d2600545af70dd9b | 3603 | `/major_events/139` | `44092a2c05b8a5ee0012c78617ae9f24b48c2bda2025a121e8161685bf1be3b7` | 3604 | `/planned_event_registry/139` | `66f990602acd5b82f42580e235dff821b6a482a2308eefcd4d8217940c02be2e` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-c203e4bc4e90ab18efaa | 3605 | `/major_events/146` | `f1fd9aeccbedb0436be7a2a108fedbd9c910df91a99c8ff1c340daaafb981a10` | 3606 | `/planned_event_registry/146` | `4bea89d70588fa4acbe55b486ddaf14fc9217261f1ab17a7f16734ec5386c830` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-c274b1d52af404fbdbfa | 3607 | `/major_events/73` | `9ca3302692306eb63e39577a01bcd5e74352f2663f454dab80fce7b3b727f60f` | 3608 | `/planned_event_registry/73` | `27a725c02189bd44487fdd239bb33849e5a13e7d53206f8d760ff9b2f9fc038e` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-c31e527d54eacd7127d4 | 3609 | `/major_events/119` | `51c47bdea959cb0d5535e1b13219d171ebec71cafdd09ecffafe6399be3d129d` | 3610 | `/planned_event_registry/119` | `e1a617de6a33beb0a1b87227f0459a65ea82513ae832f00c5554d62bb7915f52` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-c5afd1674af1c9045e1d | 3611 | `/major_events/130` | `ba394788543673d5937dccc39d448cdbc03ab227db095a8e7cda6bfcfe014c6e` | 3612 | `/planned_event_registry/130` | `3094c29363966c6207f7d11746338a099b90bed20ce6eb5178fa5a66a37d0fee` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-c6c280dced1e478ce79a | 3613 | `/major_events/91` | `760cf74375309139d1342de774896edd7f34184bd6dc2d3c967dd53b2c88e609` | 3614 | `/planned_event_registry/91` | `5b60118d19ff309b169f244cd0ae2100f85d8850830bb34d32c6091b886a2849` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-c708fdd6cce3989e4b0f | 3615 | `/major_events/89` | `7ab6089e47db3ba0b739967c057d147e24fe9f0b6046551cffb211c676d4a372` | 3616 | `/planned_event_registry/89` | `3305a1330ea7a86990191ed56ddaf3691027392a82c6fa5a9a77942a0f82e643` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-cdb18e8fbc0c1e65134b | 3617 | `/major_events/128` | `fe8b56a3720f71f9e560e8fbfcfb4d5f28c7099140158804a92901920b45ccb2` | 3618 | `/planned_event_registry/128` | `d08ff4bf8b7804586447277ace1c9d71ad1d12a6bca1e9023e2465e7e50ca2c4` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-ce12466e16cfe543359f | 3619 | `/major_events/70` | `4edd20434ce0613471ba8c6968277113c59c50c62f943ec036f66ab5b42e51b3` | 3620 | `/planned_event_registry/70` | `7c52523e626c6918360419f9661fa812e724bd50844a32765389c0c8a43e8272` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-cf4084e153be1a9796a1 | 3621 | `/major_events/108` | `b18d08ea77945c71bb2cc55d86c609f2a048886a0b8d7f9c708979670e5fc051` | 3622 | `/planned_event_registry/108` | `acb262e854eefecd80f75b115c7f4a209228b59d24585a60663596c0631dbcab` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-d7270a1895b1a560c356 | 3623 | `/major_events/111` | `771271845f885e719d6b3a5f67a5c368a57efbb0c8d64d41aedd9f174a3b806d` | 3624 | `/planned_event_registry/111` | `57c9569e271af7c1761897a3bae8dd0a2f28d2b184b88cfa64b8fea9295ee95a` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-d7b09c8b2ceeb55be982 | 3625 | `/major_events/69` | `9e9c8b70166c8a4a5ccc5823c1a8ccfed434860f26ddaedc2bc50d5a21f994c0` | 3626 | `/planned_event_registry/69` | `6c2fbdefb5e52ace0e00dce1a763f390591e4a783b1016651465e51cf2a78696` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-da136f6b8e02013fc05c | 3627 | `/major_events/74` | `b1692b349896d872aae73a3c21b92ec23f9fff450dff2a19186e759b9beee926` | 3628 | `/planned_event_registry/74` | `6b7487c0bcc86c2ff03e65672606cd35e98925ab7dfd01849adf49799544fbc1` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-da626c3fdd728a5c56f5 | 3629 | `/major_events/67` | `95d1d800289fbf6e5b322fb8406c59f2ae37f9a96852e6dac53acea758eb8c9f` | 3630 | `/planned_event_registry/67` | `0f1e2f5a763aced22d68dedfaf0eb4fd7161dbd4abe89391a9fba34f115194d5` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-dc9b5d02dea6f315a4ea | 3631 | `/major_events/131` | `55dc3b4cee267c71f6b6aacea562e5a5d14b916f4ffdd3ce0a09f7933b09b184` | 3632 | `/planned_event_registry/131` | `49da9de56f63b1e1e8fb8e4a91c91098eb7b07e280ae69be15aecab30fe5718a` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-dfd3f15de89abf420a18 | 3633 | `/major_events/106` | `54d8f70a17e41555bdb5aeb0cd6f4d7082e1cfbd7ff370638a28284f5713828b` | 3634 | `/planned_event_registry/106` | `a62d8f82a6d0e36bd63b236e6922c8d5fc022b888c5ae51bb8d58cd3580fb9fd` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-e4431f2d35a4982a77ff | 3635 | `/major_events/129` | `7d514ac4f93e3409fe8a37fbdbd8f52ec3d16f5bc334d93ca893eb9903e94768` | 3636 | `/planned_event_registry/129` | `2e0819bd2683df7dfae41730bea20d91d9ca499c6916e4d4003a21cfbdd90b50` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-e709dae2c547e750d87d | 3637 | `/major_events/85` | `e48be3622b762dbfb068b5c46944ba45114d8842337578bdd95b20085c6f7ae2` | 3638 | `/planned_event_registry/85` | `ef671beb1c3f07fe1e2e1c29611830efe3daa45aff1da5dc7cac60694b5bb65d` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-e9ffd5bcb79bea403ccd | 3639 | `/major_events/80` | `3e237184ade5ad1f06ccf712e61094f3d56d6603013109cc0fc0c3b7df5cf436` | 3640 | `/planned_event_registry/80` | `4a0e540d1e2b31f62dbcadb1b6c23c994ce606f7b6e5ca523bc2b15e890611be` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-ead37a6af90b32844d25 | 3641 | `/major_events/127` | `2208da6f864697d550776304475ca9ef5dea31213d60023eda88a7aad65a8a53` | 3642 | `/planned_event_registry/127` | `4c0965587fde35b4f2135eb68c196836bd3a90f5821c4dac3377d4d9e05d814c` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-f503e2ea34f9423279bc | 3643 | `/major_events/78` | `87dd633d26f55c0ed3a1475abfd657febb83e51970015fc3e8f7c3962797d4bb` | 3644 | `/planned_event_registry/78` | `40610ad72b9a7565807cf45b94afdb185628917832321fea4c8a6b6ea477ee04` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-f67bf1ee252017192f04 | 3645 | `/major_events/88` | `489a545711c641f7ed8ceb433db0e57cf8b809dbf992131885aca6d5196fafb8` | 3646 | `/planned_event_registry/88` | `f7cd2cd4e8f4fb013aac3b7a93a3fdc0e778a8c20c4bd6437d13d9552e317146` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-f8e495926e62c726e27d | 3647 | `/major_events/62` | `e388908ebab3293e910aa609986cfc301e4ca3d9c4071dd9184dc80c8bbf4cc4` | 3648 | `/planned_event_registry/62` | `30a28474b6875b5c055db2b00c62cbfa5fc3b2aaa986df52dccf8b77f2daef9f` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-fb16ee1ed24e0f1807ce | 3649 | `/major_events/100` | `086a22027d8e8eb6e415d010c22bbfd02c19a6b9742595b4520eeb7a330bb212` | 3650 | `/planned_event_registry/100` | `b837934eae5f7a71a732c23a825d2feb3a29a5d4d1e94a559434598d7ac14464` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-fe4a98ada42ed625ec28 | 3651 | `/major_events/143` | `fac84aabfa40af073b5016b425b492134cad5e2260736277bf91648919633dca` | 3652 | `/planned_event_registry/143` | `66bf70a411d42a1b3ca31fd3bbb371a4d419e07d471bb32a8b25ebd08082549d` | 同来源双入口·非同值（非 §8 复用） |
| EV-STEP-ffc1d64571bf33c41599 | 3653 | `/major_events/101` | `31fb6021727380389cea83abc0559966afdbea01a2faf2068399f7c19de753fc` | 3654 | `/planned_event_registry/101` | `1bfcc67a04bc638558a6b3a1fc3f77b3babe3a3a1f8ff3239f114e0802b58fe4` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-0097a4c3b51f2bd1b351 | 3655 | `/major_events/6` | `0258d0bddc49bc3b9764f39027d6f0fd79b335314cbeed2361db337933ab8946` | 3656 | `/planned_event_registry/6` | `655890431ed1622cbedba97878086bed404a65b4c5d1e2b0b6f9c28d9ecb3d0e` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-0acca264b0bcfb485802 | 3657 | `/major_events/47` | `a81aa3ee48e8a69ee34e0c2b88c7f36991196d71f73937a412e4492f1245187e` | 3658 | `/planned_event_registry/47` | `14c8824f9b6e91a2fdeb09f0734dd1a6729c581e16f4279ce186cdc321bdf51d` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-0d8400f376e77cb9459d | 3659 | `/major_events/51` | `d1d0efa3a8a065a9ff32c2df49687e0c76bf2bbc023f7fdcf85e3a75a4475785` | 3660 | `/planned_event_registry/51` | `81d13ee9db0292d71ad648766879b30facbd8a249361bfba4919c82e3ffce8fd` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-10634a597c1d320fd7d5 | 3661 | `/major_events/0` | `094847d86046515d30422e8e38d8e4909ac90683f6f5602c32ca18251fb2652f` | 3662 | `/planned_event_registry/0` | `136e7442b21326857b8cea2c3fb13ce440e796fe651f81e1323ed0cb0baab915` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-132abd444312672ceefd | 3663 | `/major_events/26` | `e5b1a0132d834b8f9375e9422620d1593799a9656189f3387353eeab360d6bfc` | 3664 | `/planned_event_registry/26` | `d88c2219cd39a5e86ad93efc4932af18d42d2c176c62d2ad5d9cc40e965c43c0` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-152c0dc96afb91f1b214 | 3665 | `/major_events/9` | `8e64cc213f4eef3a98ca32546c761a3a177a3223e10f394174f76ff160251631` | 3666 | `/planned_event_registry/9` | `a9d3175da3c6014248905dc874f3ec97cfd1a422fc3595b338606fc468e66f68` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-212f6dbe5f8660ba9836 | 3667 | `/major_events/55` | `42cf045be372d8c74576024f8a66fdce1886b55bc0f47c3b66160c0a4001a5b1` | 3668 | `/planned_event_registry/55` | `6b152eaf1449dde4ff29d191b4bbd896e89808fa1fc70ad9dac3975d2c924e76` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-256ea625afd2b3ba5634 | 3669 | `/major_events/13` | `388af99acca2ceb2f7b98bba3f0c6c81250d56bad370f309ed2c7e4295c502bd` | 3670 | `/planned_event_registry/13` | `494e5ff7ae8d4fffb8793d4c233caf74ee2be9ed556311f9b043c4878dbea43b` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-26f45b7e203206fa2157 | 3671 | `/major_events/11` | `cf34ace0aff22852c9c35d95273a75063eb0c52274fd9292cb69201e50a2c716` | 3672 | `/planned_event_registry/11` | `54db5290df48dccee71ab5cfae0e4ee0aaaaaf6e8fb7eec1b14204c4b59bd918` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-27520ea47523f70c5646 | 3673 | `/major_events/4` | `cadc52b922ff9efad82f29d345374c25298e438450aec92931b522e892913935` | 3674 | `/planned_event_registry/4` | `6d7c40758b8c6e2e7d1001ab6f235051223249fa96fe954ab7c763bd3244fd3b` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-2cdca41aec1f074e28eb | 3675 | `/major_events/42` | `7d23a2ee48fc7cd1eda1c18367f8aa831283e091c09ac177a719e4d3d6dab4bd` | 3676 | `/planned_event_registry/42` | `0f0e25f9cb65ede50a4e3898ad2efcf5d1ec15c3e05fe2e5f1bf2f6b0ef3fa20` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-2e39ec0ce9389c16791e | 3677 | `/major_events/1` | `7b0cfcb7239716494ce047977afceea844c37f17faf9fbdf770d263bbc99f6c2` | 3678 | `/planned_event_registry/1` | `e4ba411aa92bbf89946ca812330ff87f608852529a6792e02f6af0a245005cd3` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-2f17287c9c8d81338673 | 3679 | `/major_events/7` | `0a092f3b0ac216240a4976fc3d386c382c3172157842e1f2e8e66d387fa03708` | 3680 | `/planned_event_registry/7` | `cd026c0d93d6f2c10ea945a393928075482f2cc98fa2f884aa8252116e924a2e` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-2f5c576913b75efdda18 | 3681 | `/major_events/35` | `37c75a1cb0fb1cd6392d2418ed31fa001af96a184e045ef8dda59736351591ce` | 3682 | `/planned_event_registry/35` | `a218781f38a3ef6d57c86801dcb52705251110d800f2664fcfc5da26f6b38140` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-3d275aff39f35d69807d | 3683 | `/major_events/8` | `8090695e80df4f0e1dcc40dd5da34b6e38fc93c0f247c0a3779058ce8550ecdb` | 3684 | `/planned_event_registry/8` | `30b8be16f5dcd98612d5f7dbc4c6440c94a66b6094df9f893cc9f97919e7039f` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-3eee4f7b59eb78942eb1 | 3685 | `/major_events/33` | `3fc3de19125329c1164aa27252252bcc7c28bea5198428774be4e43fd9c9eec3` | 3686 | `/planned_event_registry/33` | `aceccdbbde35ff0b3186d7f91154812c0aee9603ec51b65b51fdd230532312e9` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-57e5eebe85bbf3056d7c | 3687 | `/major_events/24` | `a19abcc3811880884c80917fb720c24e56e51a772a95cbc83804cd8183814489` | 3688 | `/planned_event_registry/24` | `735803b7588979224fe0a6fe68a6e1ae3f2f9300096eaabe244fda843a2744d3` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-59335fbe86bd2d0ecce0 | 3689 | `/major_events/5` | `f1b8284b024ec53c907280fee925e7383c57d4dca7f7aeb9bb34a54965d07886` | 3690 | `/planned_event_registry/5` | `e372f089ba2be57537b32eaea6efdb1b121416e83b6da749118b77f2bb3ff1e4` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-59d8b0c1e3772bb7d5d7 | 3691 | `/major_events/52` | `4abed9f410cccf29e60acfd3dd0574c324e00bf8810d2b973685276b4d4df633` | 3692 | `/planned_event_registry/52` | `059b339feacb12a693f443101662dcad909023556e6f67e7b94b6e6f6fc08926` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-5d01eaf7506805b4f694 | 3693 | `/major_events/22` | `68d40e358c36193cb9052cccafd59456d69493c4bd35b0e45bbf509adecb7d61` | 3694 | `/planned_event_registry/22` | `08a0e010e2f7fac434ae6219b17623fff1a4a7e2b550c807779df55da82bc879` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-693e12301d1c9fa59213 | 3695 | `/major_events/54` | `cf554e938c78e1480057224ef40e9fa7cd87610d4ecc5a1423e4ecfd39798e57` | 3696 | `/planned_event_registry/54` | `2a6fb088eb72995bb384a6d47fb347887e732e3cad105005d3f881f8d548fd3b` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-69cd64d1defc993193a2 | 3697 | `/major_events/38` | `b57886fc0fdc86cf9106e351a7e7426f59a7e915bd3d97dbad2eea3783aaf7fb` | 3698 | `/planned_event_registry/38` | `5fbbe7f5a6db4f2938b7f33206eb51daacc143cdfcf50f0040032d8092f4f329` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-6b7bb71cd35c0bca67ef | 3699 | `/major_events/45` | `fb48f31f455e8f5bdb303bfe444e5d33aa7a4a4dafe4211ca63bbf4fc3fcb5a3` | 3700 | `/planned_event_registry/45` | `00e0a252ee4068d3c92509341ef09047fd9fc94fb9c70d98e2ed4938db1f191e` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-70db62aaf5f15c4c0844 | 3701 | `/major_events/28` | `da28995bc29019bab6620f8b7213d59c04b8dd27c5a238a19c9e70a3a9a2f9f3` | 3702 | `/planned_event_registry/28` | `2a60a1b084561da779e25180f04a4daa1e1af364c920b466cfb4bb3fc7aa8279` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-74423c39d10c81ede34e | 3703 | `/major_events/19` | `d0e8cf3adb1dc4a62dfc694c078b9f50c940cc6cea4915d99275e36793b167dd` | 3704 | `/planned_event_registry/19` | `59cbdfe2a2d84c9dbd4b197513453b433def015d58c52b2de1a486ffb1a75908` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-7503c06b836ceb145954 | 3705 | `/major_events/12` | `1f097b99e405d2c3c6c0cd003b5c33e50a86e7c5674b7780ffdaea25942813a5` | 3706 | `/planned_event_registry/12` | `083eece06ea5b25a368342626cad22d6d943c181bfc7e8036fed1cf5783ec2fa` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-7509cb258d2726497f64 | 3707 | `/major_events/44` | `99301bba3af7bdab5c3a7d24d329bee53787d0f953b56d09a553f5b7d1066bfa` | 3708 | `/planned_event_registry/44` | `a3610d85d1e8fa5582b67e867f29bb29bc6f680d41aac7e4821335de45ec46bb` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-7a97c808afdfdaacafb6 | 3709 | `/major_events/39` | `5aaec20440e4521008c037427321d9517526dff37a5ccc9ad8c21847deacc849` | 3710 | `/planned_event_registry/39` | `44ad9b27104d2a1b55863bcbee9dc9365c659c401b8620be24db7e3d2d1b0123` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-7ba791bea812bbeb73cf | 3711 | `/major_events/30` | `62e2a124f60193dd59b8e54a6c26205c748b49fa62a443eec7330dd13a44e1b2` | 3712 | `/planned_event_registry/30` | `b4247be6853bd5d87186a602180b37a95cdc3c42372ae7cd6c62732befa0064f` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-7c1056a9be646462e912 | 3713 | `/major_events/14` | `a56982a22f74bb3dd7bca5b928c51e601be6839d984edcfabce44ad9d9929c68` | 3714 | `/planned_event_registry/14` | `7644c9456b34c3c440d192b2bca18903814319669f98a3af6dedf81a09809674` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-7d7f9d88a7ebac87a289 | 3715 | `/major_events/41` | `59e1ad9869fe9093c38c84a65ff636ad19cbe67603c3eee7979ce1dcd7bab63b` | 3716 | `/planned_event_registry/41` | `e0e53582053fa30ec979f0f88ad5839d8c31f3cfc10995c5baf5f581f9ebd8e5` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-81f821d7264ab39a3c13 | 3717 | `/major_events/23` | `96858db88ef6067f4275e72850f6c4f9eb7cee64d555a59d6e60bbb12aeded42` | 3718 | `/planned_event_registry/23` | `30d2b094949c5335d3b20ad480a04249465d7e4c885da19f78054c1bc7ffb45b` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-8345fab150bbba719504 | 3719 | `/major_events/18` | `f098736475eaa3464fa3b6357d46a749e078bb05765d3e61bf36baeefbd3bbe8` | 3720 | `/planned_event_registry/18` | `6fd408ec9b33408ad18b826b245f43ccab9d4235242275a3888c15e0e4c08ce5` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-86021c2f5d90bc4d040f | 3721 | `/major_events/31` | `6305cf441324df193b963b8fa69fc0c1e3626ae7e1fdc0c241957a67e92fc753` | 3722 | `/planned_event_registry/31` | `4fe038201b9996de8070feb901d7a08a3ade32f7e84edb3b24743cd67e07717c` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-86755a8df561f0cefc25 | 3723 | `/major_events/29` | `e823f6d3f7f71554acbec8d8ec862dabd61c78117f0cb846ee921ad5ad4ec4c9` | 3724 | `/planned_event_registry/29` | `2aae4eea916931c142a76301329acdaf0f53ae96be30c5b5d0aa77c6ace6e3f3` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-93b7c1cdbc0ea37856b1 | 3725 | `/major_events/17` | `9581b5d0fb3bb6763e10221643dca67a395f3d5ce7897e15d925140215304bbd` | 3726 | `/planned_event_registry/17` | `e7ea9fddacfc5596ec906df7f0fad926cf87db6458c26378e9fbf8298f9a2503` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-9781a1e2b934a26a7081 | 3727 | `/major_events/34` | `15c0e2dd16d67bfa648b7ca312abdc5bcb34defcbd42fafd4ea02d84f90eb7aa` | 3728 | `/planned_event_registry/34` | `3ec4915d24af1cde8f8600cd237450f8d2d59450bd2333ed6a797ce0991da1a5` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-9b43b03eed0558490150 | 3729 | `/major_events/32` | `586279eb7a449383e8baadb978713335e732b8979191e963bd12cf40240cd8e3` | 3730 | `/planned_event_registry/32` | `24ed6b0b819ac0482b87045183062b4a6a3e4fb1950ced1a59e0d33a4d746f03` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-a0e5ac90fc8c2801722e | 3731 | `/major_events/46` | `2ee97532a7f4d12f612e3bb706252ff6a9d327ec00143e118f97cbfa3a705deb` | 3732 | `/planned_event_registry/46` | `741e1b7621bc31de752eb62cbac7810665157530c7b04d613851460de0f2555a` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-a6810598e0f1c416b0d4 | 3733 | `/major_events/2` | `46f7543a548b5b4b68eeaaacb33524ba54c273d575aecbc1c62a6e44a7443f54` | 3734 | `/planned_event_registry/2` | `4169824905df0dcbb176ecd3bb3d84f017a6638f860c6d25730fc88d9ada4715` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-a877b5738798049486c7 | 3735 | `/major_events/16` | `f6e9f295890ed1fb1801fc9e5b36ab73c110dd436ad5cfb113e43c844a94d62d` | 3736 | `/planned_event_registry/16` | `415c50b591498373a6e4216fe2ab302bb1fb1134446230093202c09614b41a57` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-b24255ff21de912bc14b | 3737 | `/major_events/36` | `063029a48458921cb39c140145673ddbaed3c25f93c3c691d24acd4580272d1d` | 3738 | `/planned_event_registry/36` | `008058ebf5218344715eef99d59f7670ce43e379402d4a727aab0608b3abf270` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-beaf2c53c216e85bb282 | 3739 | `/major_events/53` | `40d79cc542b21de21f301595625cce2d2c8ca222b41d420ae914f2c214973883` | 3740 | `/planned_event_registry/53` | `dc2b7630d49dcbb5749db9c9bc5a5e1755abd1a679e11376f332a0cb4e8e0376` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-c04d7ffd096945c557a3 | 3741 | `/major_events/49` | `5946cd5216a579f0f88841b2f9b27398d72c1ff3dc854182725ff3cc0d3d8276` | 3742 | `/planned_event_registry/49` | `018fc12f5a1df77a9c2b9dace4d0a5d30d427a74b43fd48ec674800f56fa5e88` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-cabeaa02432d882dd924 | 3743 | `/major_events/21` | `ecb139d0b74543e72fe0af036cb42da497b2e23fc82563ebc12ef44c3d915b2e` | 3744 | `/planned_event_registry/21` | `9d854619db26e66d16d5bf0388a445ab334c8ad4931652b2cbbd410394e5f2a9` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-cd2b1fea5f4ead0bb0fb | 3745 | `/major_events/10` | `4a5427c82b5a096fb3a2af6570ae55474a4c5ef2945e4f8d3356a89d68277992` | 3746 | `/planned_event_registry/10` | `b57158c84a5652bfa69f5c7a747cfc9641dc8f05f1f27ec5c4069644a9abf0fc` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-cdcc30d2e25e8721a13e | 3747 | `/major_events/40` | `c8bf45239755bd61586e3c2d03d03678cd12a4f4a4c4b13f42a79a5bb2be265d` | 3748 | `/planned_event_registry/40` | `66234abd36f494451bb7244d383d2acd4dd3ac4d13d8b9af838bcc1d43f7fef9` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-ce05e6b134aaf26a90d1 | 3749 | `/major_events/20` | `5d1cdc7294ecff0b874260b0215c21898336fde7f3b036b21686f638b1ae96a8` | 3750 | `/planned_event_registry/20` | `a2f0b99a76a86a65850219af7834a1eb1fc2f8b6b829611188f5787d6ab8bc9a` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-d49a684c43f2dfaed43a | 3751 | `/major_events/48` | `fa020811c082d59540abec687bd4a718fb510baabe02fc446740d593071db996` | 3752 | `/planned_event_registry/48` | `6a1ff6cc0ba5625acbc870cd848f5791710edad5abb852215576549926222deb` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-e596d43dc72e71f2ec96 | 3753 | `/major_events/3` | `c1cc9b1ba071ced63f7598ffed8eae6e6b3f4fbcef6d1f9f2c7071dee0929948` | 3754 | `/planned_event_registry/3` | `86a494244a8038a1cabeef4ce63cb99af9cf12f6a85faf484541219e188d2b78` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-e6340d419e1f064c61fb | 3755 | `/major_events/15` | `6312c891333f6a5c741682879f2aee2511da9711396da3c60e9098f3c5902eef` | 3756 | `/planned_event_registry/15` | `098b9a135b88332ccd0dce84eb007255ca03f6109b44df70f8cbe9e297685b6c` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-f751c1fba6c9901605b1 | 3757 | `/major_events/27` | `5b87cbf587da0f46829c1a75dc65aca0163710037c87d502c5bb052353e5afdd` | 3758 | `/planned_event_registry/27` | `47037a89821021b1a87a9387327c6952fabdcb7f774c92a3ed34a8495e78562d` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-f9c7135e7d5c5facf43e | 3759 | `/major_events/50` | `dda275ad5f718b563805fc364bb950e84bf90cf59c253cf7e7113a42c1fdc51d` | 3760 | `/planned_event_registry/50` | `d7692c31fe9d8b13715b0af251523390cea74b96d611c9f4a3f0027243867e3e` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-fa5164070e329ea9af36 | 3761 | `/major_events/37` | `96f08bb27ed630bb48cbdc59cbae8347e73ce198834561036e81d17084d3ee83` | 3762 | `/planned_event_registry/37` | `5a9f77d9a3d5ca40e037ba09f7f222a9b96c1ff2ed5c950e7185c6f512b5e674` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-facfac7fa83ce106838b | 3763 | `/major_events/25` | `96d3aabedffe2584cf2c310f65337c5d21a743c5b4a29fc3a450f40398df6cf2` | 3764 | `/planned_event_registry/25` | `46c5a05154f948d085506553c200e051bda1c6ec501403ec974d5cb2cf0554c1` | 同来源双入口·非同值（非 §8 复用） |
| EV-TR-fe03e23b7e231f587f9f | 3765 | `/major_events/43` | `8385209ed9a16b99380e88c8ba3fa624ba43caf21bad5c4146eabfb4507967d8` | 3766 | `/planned_event_registry/43` | `1a698f87a3561a07368758cb48c28af8e3bae5122ea09bb5878a9a9737b80865` | 同来源双入口·非同值（非 §8 复用） |

（对照：按完整 value_sha256 分组的真同值复用对共 525 对，全列于 §8；其中 EV- 来源 0 对）

## 7. MOD-/FRAG- 引用逐条解析（42/42；0 断引用）

v2 未做此解析（当时把非 EVID 格式引用误计为「不存在」）；本轮逐条解析结果：42 个引用串全部命中 A3 锚——`characters`（人物模块，20）、`storylines`（故事线模块，4）、`world`（世界模块，17）、`fragments`（片段，1：FRAG-DX-03），且 42/42 同时出现在顶层 `review_path`（审阅路径模块表）中。命中由 §1 复算脚本独立复验（0 断引用）。

## 8. 同文复用映射：525 对全列（复用来源列的核心证据）

7 种域型（型内对数合计 525；每对＝同一 P1 值（同 sha256）在两个 Pointer 语境下的双暴露，全部同 source_id；跨域 516 对、跨阶段 45 对、9 对甚至指针路径完全相同仅阶段不同（E1·/environment_demands ↔ W1·/environment_demands）；语境检查＝A/B 两侧阶段与域差异逐对可回读）：

| 型 | 阶段A·域A | 阶段B·域B | 对数 | 成员索引(A例) | 值哈希(前12) |
|---|---|---|---|---|---|
| R1 | T1·/causal_edges | T1·/planned_causal_edges | 321 | 2652,2654,2656,2658,2660,2662,2664,2666 | 0ec5aad0d52c… |
| R2 | T1·/planned_proposition_registry | T1·/proposition_registry | 159 | 3830,3832,3834,3836,3838,3840,3842,3844 | 0d292a1d16b7… |
| R3 | C1·/character_demands | S1·/character_requirements | 9 | 723,724,725,726,727,728,729,730 | db8011029ecf… |
| R4 | E1·/storyline_environment_requirements | S1·/environment_requirements | 9 | 1432,1433,1434,1435,1436,1437,1438,1439 | c6354036e719… |
| R5 | E1·/environment_demands | W1·/environment_demands | 9 | 1441,1442,1443,1444,1445,1446,1447,1448 | aa7751451c8c… |
| R6 | S1·/event_requirements | T1·/event_demands | 9 | 1715,1716,1717,1718,1719,1720,1721,1722 | 48c0999da578… |
| R7 | S1·/world_requirements | W1·/storyline_requirements | 9 | 2643,2644,2645,2646,2647,2648,2649,2650 | 834849b83fda… |

逐对全列（525 行；格式：索引A 阶段A 指针A｜源 → 索引B 阶段B 指针B｜源 哈希12）：

```
723 C1 /character_demands/3|CHD-EVIDENCE-CLOSURE -> 1630 S1 /character_requirements/3|CHD-EVIDENCE-CLOSURE db8011029ecf
724 C1 /character_demands/5|CHD-GEOPOLITICAL-PRESSURE -> 1631 S1 /character_requirements/5|CHD-GEOPOLITICAL-PRESSURE a9810df9756f
725 C1 /character_demands/0|CHD-GUHENG-PRECURSOR -> 1632 S1 /character_requirements/0|CHD-GUHENG-PRECURSOR 14ea43e2caed
726 C1 /character_demands/7|CHD-IDENTITY-ETHICS-MELODY -> 1633 S1 /character_requirements/7|CHD-IDENTITY-ETHICS-MELODY 31e67a0f4960
727 C1 /character_demands/4|CHD-INSTITUTIONAL-ETHICS -> 1634 S1 /character_requirements/4|CHD-INSTITUTIONAL-ETHICS cb2958647878
728 C1 /character_demands/6|CHD-KINSHIP-PROTECTION -> 1635 S1 /character_requirements/6|CHD-KINSHIP-PROTECTION d63d15eda97b
729 C1 /character_demands/8|CHD-LONG-HORIZON-OPEN-MELODY -> 1636 S1 /character_requirements/8|CHD-LONG-HORIZON-OPEN-MELODY 678cb6151ff5
730 C1 /character_demands/2|CHD-R07-SHENYU-MAIN -> 1637 S1 /character_requirements/2|CHD-R07-SHENYU-MAIN 5fba1d0118da
731 C1 /character_demands/1|CHD-SHENYU-ACCEPTANCE -> 1638 S1 /character_requirements/1|CHD-SHENYU-ACCEPTANCE 6dc9ef48aa1f
1432 E1 /storyline_environment_requirements/3|END-EVIDENCE-CLOSURE -> 1706 S1 /environment_requirements/3|END-EVIDENCE-CLOSURE c6354036e719
1433 E1 /storyline_environment_requirements/5|END-GEOPOLITICAL-PRESSURE -> 1707 S1 /environment_requirements/5|END-GEOPOLITICAL-PRESSURE 84272ded9531
1434 E1 /storyline_environment_requirements/0|END-GUHENG-PRECURSOR -> 1708 S1 /environment_requirements/0|END-GUHENG-PRECURSOR 2d01adeef26d
1435 E1 /storyline_environment_requirements/7|END-IDENTITY-ETHICS-MELODY -> 1709 S1 /environment_requirements/7|END-IDENTITY-ETHICS-MELODY dd7d145151bb
1436 E1 /storyline_environment_requirements/4|END-INSTITUTIONAL-ETHICS -> 1710 S1 /environment_requirements/4|END-INSTITUTIONAL-ETHICS f2ac47b98096
1437 E1 /storyline_environment_requirements/6|END-KINSHIP-PROTECTION -> 1711 S1 /environment_requirements/6|END-KINSHIP-PROTECTION 56fec270e54c
1438 E1 /storyline_environment_requirements/8|END-LONG-HORIZON-OPEN-MELODY -> 1712 S1 /environment_requirements/8|END-LONG-HORIZON-OPEN-MELODY 79de72817999
1439 E1 /storyline_environment_requirements/2|END-R07-SHENYU-MAIN -> 1713 S1 /environment_requirements/2|END-R07-SHENYU-MAIN cdce2952e539
1440 E1 /storyline_environment_requirements/1|END-SHENYU-ACCEPTANCE -> 1714 S1 /environment_requirements/1|END-SHENYU-ACCEPTANCE 1a3261e2eab2
1441 E1 /environment_demands/3|END-W1-EVIDENCE-CLOSURE -> 4459 W1 /environment_demands/3|END-W1-EVIDENCE-CLOSURE aa7751451c8c
1442 E1 /environment_demands/5|END-W1-GEOPOLITICAL-PRESSURE -> 4460 W1 /environment_demands/5|END-W1-GEOPOLITICAL-PRESSURE 3eea43d89b92
1443 E1 /environment_demands/0|END-W1-GUHENG-PRECURSOR -> 4461 W1 /environment_demands/0|END-W1-GUHENG-PRECURSOR 41aa8f103104
1444 E1 /environment_demands/7|END-W1-IDENTITY-ETHICS-MELODY -> 4462 W1 /environment_demands/7|END-W1-IDENTITY-ETHICS-MELODY fd4bb69f83a1
1445 E1 /environment_demands/4|END-W1-INSTITUTIONAL-ETHICS -> 4463 W1 /environment_demands/4|END-W1-INSTITUTIONAL-ETHICS f512e3ef1e2e
1446 E1 /environment_demands/6|END-W1-KINSHIP-PROTECTION -> 4464 W1 /environment_demands/6|END-W1-KINSHIP-PROTECTION ea93446912b1
1447 E1 /environment_demands/8|END-W1-LONG-HORIZON-OPEN-MELODY -> 4465 W1 /environment_demands/8|END-W1-LONG-HORIZON-OPEN-MELODY e279b8f64f01
1448 E1 /environment_demands/2|END-W1-R07-SHENYU-MAIN -> 4466 W1 /environment_demands/2|END-W1-R07-SHENYU-MAIN ec0661288b28
1449 E1 /environment_demands/1|END-W1-SHENYU-ACCEPTANCE -> 4467 W1 /environment_demands/1|END-W1-SHENYU-ACCEPTANCE 5e21c3946f60
1715 S1 /event_requirements/3|EVD-EVIDENCE-CLOSURE -> 3767 T1 /event_demands/3|EVD-EVIDENCE-CLOSURE 48c0999da578
1716 S1 /event_requirements/5|EVD-GEOPOLITICAL-PRESSURE -> 3768 T1 /event_demands/5|EVD-GEOPOLITICAL-PRESSURE 10e19fa7388b
1717 S1 /event_requirements/0|EVD-GUHENG-PRECURSOR -> 3769 T1 /event_demands/0|EVD-GUHENG-PRECURSOR 3b2d425f18b1
1718 S1 /event_requirements/7|EVD-IDENTITY-ETHICS-MELODY -> 3770 T1 /event_demands/7|EVD-IDENTITY-ETHICS-MELODY d13839b0731b
1719 S1 /event_requirements/4|EVD-INSTITUTIONAL-ETHICS -> 3771 T1 /event_demands/4|EVD-INSTITUTIONAL-ETHICS 4364ff216969
1720 S1 /event_requirements/6|EVD-KINSHIP-PROTECTION -> 3772 T1 /event_demands/6|EVD-KINSHIP-PROTECTION ce0a3096c932
1721 S1 /event_requirements/8|EVD-LONG-HORIZON-OPEN-MELODY -> 3773 T1 /event_demands/8|EVD-LONG-HORIZON-OPEN-MELODY ffba7d694e77
1722 S1 /event_requirements/2|EVD-R07-SHENYU-MAIN -> 3774 T1 /event_demands/2|EVD-R07-SHENYU-MAIN 2fa6e960c415
1723 S1 /event_requirements/1|EVD-SHENYU-ACCEPTANCE -> 3775 T1 /event_demands/1|EVD-SHENYU-ACCEPTANCE 682c3c86fbb8
2643 S1 /world_requirements/3|WR-EVIDENCE-CLOSURE -> 4571 W1 /storyline_requirements/3|WR-EVIDENCE-CLOSURE 834849b83fda
2644 S1 /world_requirements/5|WR-GEOPOLITICAL-PRESSURE -> 4572 W1 /storyline_requirements/5|WR-GEOPOLITICAL-PRESSURE dded69788b0f
2645 S1 /world_requirements/0|WR-GUHENG-PRECURSOR -> 4573 W1 /storyline_requirements/0|WR-GUHENG-PRECURSOR 629516709120
2646 S1 /world_requirements/7|WR-IDENTITY-ETHICS-MELODY -> 4574 W1 /storyline_requirements/7|WR-IDENTITY-ETHICS-MELODY 8da94ce8440c
2647 S1 /world_requirements/4|WR-INSTITUTIONAL-ETHICS -> 4575 W1 /storyline_requirements/4|WR-INSTITUTIONAL-ETHICS 80fc07101065
2648 S1 /world_requirements/6|WR-KINSHIP-PROTECTION -> 4576 W1 /storyline_requirements/6|WR-KINSHIP-PROTECTION 9a1a3cc2287d
2649 S1 /world_requirements/8|WR-LONG-HORIZON-OPEN-MELODY -> 4577 W1 /storyline_requirements/8|WR-LONG-HORIZON-OPEN-MELODY e8b294a48948
2650 S1 /world_requirements/2|WR-R07-SHENYU-MAIN -> 4578 W1 /storyline_requirements/2|WR-R07-SHENYU-MAIN 208601c44224
2651 S1 /world_requirements/1|WR-SHENYU-ACCEPTANCE -> 4579 W1 /storyline_requirements/1|WR-SHENYU-ACCEPTANCE 5deb1a81af78
2652 T1 /causal_edges/34|CE-24-04f84de7cd705ac7a271 -> 2653 T1 /planned_causal_edges/34|CE-24-04f84de7cd705ac7a271 0ec5aad0d52c
2654 T1 /causal_edges/45|CE-24-054f31aba2a30df7e96b -> 2655 T1 /planned_causal_edges/45|CE-24-054f31aba2a30df7e96b 853fc0a3d610
2656 T1 /causal_edges/308|CE-24-06df962d881794895d6f -> 2657 T1 /planned_causal_edges/308|CE-24-06df962d881794895d6f f1a53a5f69bc
2658 T1 /causal_edges/251|CE-24-07d47c4b2217e44de97b -> 2659 T1 /planned_causal_edges/251|CE-24-07d47c4b2217e44de97b 83bfa57f37c6
2660 T1 /causal_edges/98|CE-24-086ebadf504bb45a157f -> 2661 T1 /planned_causal_edges/98|CE-24-086ebadf504bb45a157f aec4c8678825
2662 T1 /causal_edges/252|CE-24-08fdf06d89a7c441580a -> 2663 T1 /planned_causal_edges/252|CE-24-08fdf06d89a7c441580a 3ccfdfb2ca86
2664 T1 /causal_edges/219|CE-24-09f5555693afcc9da886 -> 2665 T1 /planned_causal_edges/219|CE-24-09f5555693afcc9da886 b99e2f7d3bf2
2666 T1 /causal_edges/55|CE-24-12101f7cb4ec354a80c3 -> 2667 T1 /planned_causal_edges/55|CE-24-12101f7cb4ec354a80c3 b03df1678bfb
2668 T1 /causal_edges/259|CE-24-13e500db671420166f9a -> 2669 T1 /planned_causal_edges/259|CE-24-13e500db671420166f9a 7dd406ac52a0
2670 T1 /causal_edges/255|CE-24-13ec1e3c6ee4ac978820 -> 2671 T1 /planned_causal_edges/255|CE-24-13ec1e3c6ee4ac978820 a0538b8efb47
2672 T1 /causal_edges/275|CE-24-13f6e50f28c1b6408175 -> 2673 T1 /planned_causal_edges/275|CE-24-13f6e50f28c1b6408175 60ebb6d33787
2674 T1 /causal_edges/18|CE-24-145815b759804cd4f189 -> 2675 T1 /planned_causal_edges/18|CE-24-145815b759804cd4f189 d27c5a431e77
2676 T1 /causal_edges/134|CE-24-1478dd3fce3055892a1d -> 2677 T1 /planned_causal_edges/134|CE-24-1478dd3fce3055892a1d 9d4a33a03b4b
2678 T1 /causal_edges/118|CE-24-1513ce7f68ef446f72e1 -> 2679 T1 /planned_causal_edges/118|CE-24-1513ce7f68ef446f72e1 62182c904b8d
2680 T1 /causal_edges/257|CE-24-152c57cf252a32b4c8b6 -> 2681 T1 /planned_causal_edges/257|CE-24-152c57cf252a32b4c8b6 b0390b99b83b
2682 T1 /causal_edges/291|CE-24-15d5d64d71a3f19f7f33 -> 2683 T1 /planned_causal_edges/291|CE-24-15d5d64d71a3f19f7f33 a64a1d140ca9
2684 T1 /causal_edges/270|CE-24-1665257bb23ae05aa3b6 -> 2685 T1 /planned_causal_edges/270|CE-24-1665257bb23ae05aa3b6 abbf692b2e8f
2686 T1 /causal_edges/212|CE-24-167419d9b4cabf4abd94 -> 2687 T1 /planned_causal_edges/212|CE-24-167419d9b4cabf4abd94 3db50c633bc4
2688 T1 /causal_edges/268|CE-24-16ed253cea97d177d5f0 -> 2689 T1 /planned_causal_edges/268|CE-24-16ed253cea97d177d5f0 448120ec86f5
2690 T1 /causal_edges/2|CE-24-170c94b7b1140ead8e43 -> 2691 T1 /planned_causal_edges/2|CE-24-170c94b7b1140ead8e43 4c8b391d9e7c
2692 T1 /causal_edges/306|CE-24-177511fd8e5aee61be8d -> 2693 T1 /planned_causal_edges/306|CE-24-177511fd8e5aee61be8d 6771a37171c7
2694 T1 /causal_edges/209|CE-24-178b257bb656ee83f80b -> 2695 T1 /planned_causal_edges/209|CE-24-178b257bb656ee83f80b a5434d753b48
2696 T1 /causal_edges/260|CE-24-19081186df764cc5278e -> 2697 T1 /planned_causal_edges/260|CE-24-19081186df764cc5278e a12dc3dd5efe
2698 T1 /causal_edges/160|CE-24-1a3e0f4d6914920cf88e -> 2699 T1 /planned_causal_edges/160|CE-24-1a3e0f4d6914920cf88e 0ee6e794ff13
2700 T1 /causal_edges/223|CE-24-1bc9cb6d710663cc169a -> 2701 T1 /planned_causal_edges/223|CE-24-1bc9cb6d710663cc169a b36f27f29149
2702 T1 /causal_edges/80|CE-24-1d52ba0b9e2b473d47ed -> 2703 T1 /planned_causal_edges/80|CE-24-1d52ba0b9e2b473d47ed c949d4a5ab48
2704 T1 /causal_edges/293|CE-24-1e094bfa21bf00978f45 -> 2705 T1 /planned_causal_edges/293|CE-24-1e094bfa21bf00978f45 d6ab7a3284f4
2706 T1 /causal_edges/282|CE-24-1f30b511a9a9f35ed823 -> 2707 T1 /planned_causal_edges/282|CE-24-1f30b511a9a9f35ed823 d13ed77d5f12
2708 T1 /causal_edges/201|CE-24-1fbcc2fe595ff4d3dd63 -> 2709 T1 /planned_causal_edges/201|CE-24-1fbcc2fe595ff4d3dd63 20b3ddca48a1
2710 T1 /causal_edges/61|CE-24-2105c2a189e1892e3fbe -> 2711 T1 /planned_causal_edges/61|CE-24-2105c2a189e1892e3fbe 304c3ff4296d
2712 T1 /causal_edges/249|CE-24-2149b657d7bf6fdc5234 -> 2713 T1 /planned_causal_edges/249|CE-24-2149b657d7bf6fdc5234 69fc6684a4cb
2714 T1 /causal_edges/147|CE-24-2290320557a531a699f1 -> 2715 T1 /planned_causal_edges/147|CE-24-2290320557a531a699f1 a40dc5bc3521
2716 T1 /causal_edges/20|CE-24-246a7136cd31787c73f3 -> 2717 T1 /planned_causal_edges/20|CE-24-246a7136cd31787c73f3 e0b7d34cbb79
2718 T1 /causal_edges/22|CE-24-24c552cc29e22c55446c -> 2719 T1 /planned_causal_edges/22|CE-24-24c552cc29e22c55446c 6e068230e2f1
2720 T1 /causal_edges/314|CE-24-2609ea912d3ec440153a -> 2721 T1 /planned_causal_edges/314|CE-24-2609ea912d3ec440153a 2387bbbfd75b
2722 T1 /causal_edges/248|CE-24-2706a4944dc7d54c0191 -> 2723 T1 /planned_causal_edges/248|CE-24-2706a4944dc7d54c0191 15565cab8feb
2724 T1 /causal_edges/94|CE-24-27f2bebe2cc0f7ca5941 -> 2725 T1 /planned_causal_edges/94|CE-24-27f2bebe2cc0f7ca5941 127f5678faf1
2726 T1 /causal_edges/187|CE-24-28ec372eb577c0282892 -> 2727 T1 /planned_causal_edges/187|CE-24-28ec372eb577c0282892 5e77b2318caa
2728 T1 /causal_edges/265|CE-24-29c9d3c3a9ded9578743 -> 2729 T1 /planned_causal_edges/265|CE-24-29c9d3c3a9ded9578743 2e2c87c9e3ca
2730 T1 /causal_edges/199|CE-24-2b47b97886cb1be633db -> 2731 T1 /planned_causal_edges/199|CE-24-2b47b97886cb1be633db 9ca5e61553de
2732 T1 /causal_edges/114|CE-24-2c02e9429f9020e8da60 -> 2733 T1 /planned_causal_edges/114|CE-24-2c02e9429f9020e8da60 47cd233bf2fc
2734 T1 /causal_edges/158|CE-24-2cfbe3333ae719e10140 -> 2735 T1 /planned_causal_edges/158|CE-24-2cfbe3333ae719e10140 aebfc1f809a5
2736 T1 /causal_edges/289|CE-24-2f0afc7d2a013b6b97e5 -> 2737 T1 /planned_causal_edges/289|CE-24-2f0afc7d2a013b6b97e5 461084cbf7b7
2738 T1 /causal_edges/266|CE-24-2f15e9ba76fa123aeb92 -> 2739 T1 /planned_causal_edges/266|CE-24-2f15e9ba76fa123aeb92 cb7d706ca573
2740 T1 /causal_edges/26|CE-24-2f272c1e29e133660262 -> 2741 T1 /planned_causal_edges/26|CE-24-2f272c1e29e133660262 92b8a6ab925e
2742 T1 /causal_edges/232|CE-24-30ed962e57442606f444 -> 2743 T1 /planned_causal_edges/232|CE-24-30ed962e57442606f444 ac540fd139f3
2744 T1 /causal_edges/278|CE-24-314fa645bdd9370091de -> 2745 T1 /planned_causal_edges/278|CE-24-314fa645bdd9370091de b4a54dc3c092
2746 T1 /causal_edges/111|CE-24-32141b00ae23ee49fc2f -> 2747 T1 /planned_causal_edges/111|CE-24-32141b00ae23ee49fc2f 4ad5d9b1b517
2748 T1 /causal_edges/246|CE-24-325d0b11d7bcb43fd279 -> 2749 T1 /planned_causal_edges/246|CE-24-325d0b11d7bcb43fd279 70f1c8e143b9
2750 T1 /causal_edges/284|CE-24-32c1394c3e3ec68fee2f -> 2751 T1 /planned_causal_edges/284|CE-24-32c1394c3e3ec68fee2f a3b1414df680
2752 T1 /causal_edges/37|CE-24-3641ff617e3d423b4946 -> 2753 T1 /planned_causal_edges/37|CE-24-3641ff617e3d423b4946 b86b132af190
2754 T1 /causal_edges/52|CE-24-36434462473532c0004f -> 2755 T1 /planned_causal_edges/52|CE-24-36434462473532c0004f 3d5a51dc8313
2756 T1 /causal_edges/169|CE-24-3653ae83a510f29a2a72 -> 2757 T1 /planned_causal_edges/169|CE-24-3653ae83a510f29a2a72 b5061440b08c
2758 T1 /causal_edges/133|CE-24-38556402dfdb787e68b4 -> 2759 T1 /planned_causal_edges/133|CE-24-38556402dfdb787e68b4 b56d94a5de17
2760 T1 /causal_edges/180|CE-24-389aaf5bf414223b1cab -> 2761 T1 /planned_causal_edges/180|CE-24-389aaf5bf414223b1cab 413a04e21a51
2762 T1 /causal_edges/200|CE-24-3912d41d07d09bce4672 -> 2763 T1 /planned_causal_edges/200|CE-24-3912d41d07d09bce4672 43b5e8e6cbe5
2764 T1 /causal_edges/137|CE-24-3a583c83e88e42330ff6 -> 2765 T1 /planned_causal_edges/137|CE-24-3a583c83e88e42330ff6 acaad424c2b0
2766 T1 /causal_edges/6|CE-24-3b43810b4650683e7f37 -> 2767 T1 /planned_causal_edges/6|CE-24-3b43810b4650683e7f37 802daa7e0bfb
2768 T1 /causal_edges/150|CE-24-3c4fad841ad2041b964c -> 2769 T1 /planned_causal_edges/150|CE-24-3c4fad841ad2041b964c ac24b762e9d8
2770 T1 /causal_edges/5|CE-24-3ce1b4a66da633cb5d27 -> 2771 T1 /planned_causal_edges/5|CE-24-3ce1b4a66da633cb5d27 7ff8b4a01ddd
2772 T1 /causal_edges/79|CE-24-3ec12d90fb98cd54b1d2 -> 2773 T1 /planned_causal_edges/79|CE-24-3ec12d90fb98cd54b1d2 fab79114523c
2774 T1 /causal_edges/74|CE-24-40292decc866ed64a198 -> 2775 T1 /planned_causal_edges/74|CE-24-40292decc866ed64a198 0da2bded5883
2776 T1 /causal_edges/220|CE-24-4294d366e98276aa52bd -> 2777 T1 /planned_causal_edges/220|CE-24-4294d366e98276aa52bd c219ae2ba0f6
2778 T1 /causal_edges/119|CE-24-42cada78e3aeaf16ce5e -> 2779 T1 /planned_causal_edges/119|CE-24-42cada78e3aeaf16ce5e d46bc18a416b
2780 T1 /causal_edges/40|CE-24-42e6b432c1f99f039b9b -> 2781 T1 /planned_causal_edges/40|CE-24-42e6b432c1f99f039b9b 560f89c4fdf7
2782 T1 /causal_edges/299|CE-24-43d74d899d7ddeb00602 -> 2783 T1 /planned_causal_edges/299|CE-24-43d74d899d7ddeb00602 c99f972ba854
2784 T1 /causal_edges/91|CE-24-447e1ae12ae3053cf57f -> 2785 T1 /planned_causal_edges/91|CE-24-447e1ae12ae3053cf57f 7dded37eb245
2786 T1 /causal_edges/222|CE-24-448612c1a6915a26ef20 -> 2787 T1 /planned_causal_edges/222|CE-24-448612c1a6915a26ef20 842286874650
2788 T1 /causal_edges/214|CE-24-44af24a36d6e5caf831a -> 2789 T1 /planned_causal_edges/214|CE-24-44af24a36d6e5caf831a dc066fae6b5b
2790 T1 /causal_edges/112|CE-24-45f4077ab6e50ad91da1 -> 2791 T1 /planned_causal_edges/112|CE-24-45f4077ab6e50ad91da1 c1c5d8c4ff97
2792 T1 /causal_edges/159|CE-24-460be60f794bf6770bd0 -> 2793 T1 /planned_causal_edges/159|CE-24-460be60f794bf6770bd0 6142b70c8c80
2794 T1 /causal_edges/68|CE-24-462bc7f1fe4949eb7966 -> 2795 T1 /planned_causal_edges/68|CE-24-462bc7f1fe4949eb7966 dbff31e57dea
2796 T1 /causal_edges/103|CE-24-48f1a5266c1e43cc2567 -> 2797 T1 /planned_causal_edges/103|CE-24-48f1a5266c1e43cc2567 a4cce3af1bd1
2798 T1 /causal_edges/190|CE-24-490e30453e7532e35af9 -> 2799 T1 /planned_causal_edges/190|CE-24-490e30453e7532e35af9 a48d8033200e
2800 T1 /causal_edges/258|CE-24-4964dea4baf961da64ac -> 2801 T1 /planned_causal_edges/258|CE-24-4964dea4baf961da64ac 0e2dd532f930
2802 T1 /causal_edges/67|CE-24-4991e2fc70c650394716 -> 2803 T1 /planned_causal_edges/67|CE-24-4991e2fc70c650394716 69965ed55f14
2804 T1 /causal_edges/104|CE-24-4a16ffeea2f255182ac9 -> 2805 T1 /planned_causal_edges/104|CE-24-4a16ffeea2f255182ac9 1db96fd73ec0
2806 T1 /causal_edges/44|CE-24-4ae9d3bfbbd8fc627751 -> 2807 T1 /planned_causal_edges/44|CE-24-4ae9d3bfbbd8fc627751 c6997ca9c024
2808 T1 /causal_edges/54|CE-24-4bffb4edf6970febf4d9 -> 2809 T1 /planned_causal_edges/54|CE-24-4bffb4edf6970febf4d9 bcf195c92a79
2810 T1 /causal_edges/21|CE-24-4d1c08e1d3cb0d0d3a81 -> 2811 T1 /planned_causal_edges/21|CE-24-4d1c08e1d3cb0d0d3a81 d12cd13c4fc7
2812 T1 /causal_edges/244|CE-24-4de1263ad40b30b65ddb -> 2813 T1 /planned_causal_edges/244|CE-24-4de1263ad40b30b65ddb bad1d7bbc978
2814 T1 /causal_edges/286|CE-24-4f494f7ba83d3ad77265 -> 2815 T1 /planned_causal_edges/286|CE-24-4f494f7ba83d3ad77265 215e1b52bfa6
2816 T1 /causal_edges/210|CE-24-5072d75515bab8b65ee3 -> 2817 T1 /planned_causal_edges/210|CE-24-5072d75515bab8b65ee3 112711ca17d0
2818 T1 /causal_edges/28|CE-24-515ad4337781597381be -> 2819 T1 /planned_causal_edges/28|CE-24-515ad4337781597381be 904b0ebc428c
2820 T1 /causal_edges/276|CE-24-518652b41dd523a5599f -> 2821 T1 /planned_causal_edges/276|CE-24-518652b41dd523a5599f 5d344b0196bb
2822 T1 /causal_edges/213|CE-24-522bc922c7ca6f4af88f -> 2823 T1 /planned_causal_edges/213|CE-24-522bc922c7ca6f4af88f 86ec8a5c2089
2824 T1 /causal_edges/191|CE-24-527199c4f886af690872 -> 2825 T1 /planned_causal_edges/191|CE-24-527199c4f886af690872 f10acf2718e3
2826 T1 /causal_edges/196|CE-24-53dc3b9d058f654b91a7 -> 2827 T1 /planned_causal_edges/196|CE-24-53dc3b9d058f654b91a7 5907d910c01d
2828 T1 /causal_edges/176|CE-24-53fed13ae4c80db41c9d -> 2829 T1 /planned_causal_edges/176|CE-24-53fed13ae4c80db41c9d 2f9f2c98d4d7
2830 T1 /causal_edges/132|CE-24-542ff5bf87325197290b -> 2831 T1 /planned_causal_edges/132|CE-24-542ff5bf87325197290b f3d41a81cdd9
2832 T1 /causal_edges/127|CE-24-544301050f191f4c9348 -> 2833 T1 /planned_causal_edges/127|CE-24-544301050f191f4c9348 6448d3aa799f
2834 T1 /causal_edges/313|CE-24-56564d578b50b7f1f502 -> 2835 T1 /planned_causal_edges/313|CE-24-56564d578b50b7f1f502 4edce8ab9212
2836 T1 /causal_edges/221|CE-24-59f65c90b858575a7f82 -> 2837 T1 /planned_causal_edges/221|CE-24-59f65c90b858575a7f82 e818f03aee97
2838 T1 /causal_edges/271|CE-24-5bb158b52f62c5fd4b85 -> 2839 T1 /planned_causal_edges/271|CE-24-5bb158b52f62c5fd4b85 0d4be7a87986
2840 T1 /causal_edges/101|CE-24-5cb2a27846d79debc17a -> 2841 T1 /planned_causal_edges/101|CE-24-5cb2a27846d79debc17a 812a3e75c519
2842 T1 /causal_edges/107|CE-24-5da45b47ed440469a8bd -> 2843 T1 /planned_causal_edges/107|CE-24-5da45b47ed440469a8bd 5af9e882019a
2844 T1 /causal_edges/146|CE-24-5ed53281cd943cbc645d -> 2845 T1 /planned_causal_edges/146|CE-24-5ed53281cd943cbc645d bc813e7306bc
2846 T1 /causal_edges/262|CE-24-612d8a2ea66063d0eb53 -> 2847 T1 /planned_causal_edges/262|CE-24-612d8a2ea66063d0eb53 283a2cec1504
2848 T1 /causal_edges/63|CE-24-61571fcb3f89e1ca7462 -> 2849 T1 /planned_causal_edges/63|CE-24-61571fcb3f89e1ca7462 4cc6e1a7a088
2850 T1 /causal_edges/263|CE-24-61705e8d17594cb58789 -> 2851 T1 /planned_causal_edges/263|CE-24-61705e8d17594cb58789 ff052fe88e51
2852 T1 /causal_edges/217|CE-24-61afb4ff26e4b9251941 -> 2853 T1 /planned_causal_edges/217|CE-24-61afb4ff26e4b9251941 97746bfa01d8
2854 T1 /causal_edges/165|CE-24-61ea4d921f87b32fa8e7 -> 2855 T1 /planned_causal_edges/165|CE-24-61ea4d921f87b32fa8e7 abb4427f573d
2856 T1 /causal_edges/288|CE-24-628803b74b94a7c17d21 -> 2857 T1 /planned_causal_edges/288|CE-24-628803b74b94a7c17d21 1660be29c456
2858 T1 /causal_edges/215|CE-24-62dc5edf7d999f74c4c2 -> 2859 T1 /planned_causal_edges/215|CE-24-62dc5edf7d999f74c4c2 65befd6d4b82
2860 T1 /causal_edges/84|CE-24-6380f7a49cbace06e883 -> 2861 T1 /planned_causal_edges/84|CE-24-6380f7a49cbace06e883 55fb2084f8b7
2862 T1 /causal_edges/86|CE-24-63c7ffaf45628bd4ab17 -> 2863 T1 /planned_causal_edges/86|CE-24-63c7ffaf45628bd4ab17 86d750ec3737
2864 T1 /causal_edges/108|CE-24-650f9602acf55e82e0b5 -> 2865 T1 /planned_causal_edges/108|CE-24-650f9602acf55e82e0b5 a8134bd9a3ea
2866 T1 /causal_edges/243|CE-24-65b2aa7637d797a7813e -> 2867 T1 /planned_causal_edges/243|CE-24-65b2aa7637d797a7813e 8a2585195625
2868 T1 /causal_edges/31|CE-24-67f5a71a6738b106fe30 -> 2869 T1 /planned_causal_edges/31|CE-24-67f5a71a6738b106fe30 dbe55b169cc5
2870 T1 /causal_edges/96|CE-24-6849a5a0d0ba0b32e057 -> 2871 T1 /planned_causal_edges/96|CE-24-6849a5a0d0ba0b32e057 162f99c06abd
2872 T1 /causal_edges/48|CE-24-6979760b3e15c8e595c4 -> 2873 T1 /planned_causal_edges/48|CE-24-6979760b3e15c8e595c4 cdf8e993cf7a
2874 T1 /causal_edges/183|CE-24-6a0631bc293dd16f4f5e -> 2875 T1 /planned_causal_edges/183|CE-24-6a0631bc293dd16f4f5e fcdbe3285671
2876 T1 /causal_edges/57|CE-24-6c37448264fb5e35899a -> 2877 T1 /planned_causal_edges/57|CE-24-6c37448264fb5e35899a 9dae7ed6cf3e
2878 T1 /causal_edges/161|CE-24-6c653d778324a6584ffa -> 2879 T1 /planned_causal_edges/161|CE-24-6c653d778324a6584ffa 99895d23668d
2880 T1 /causal_edges/153|CE-24-6d1d4b4ed9af4db7af71 -> 2881 T1 /planned_causal_edges/153|CE-24-6d1d4b4ed9af4db7af71 d86b5d912867
2882 T1 /causal_edges/56|CE-24-6dc8c432565646941989 -> 2883 T1 /planned_causal_edges/56|CE-24-6dc8c432565646941989 af3fca0a5762
2884 T1 /causal_edges/175|CE-24-6f9164cf08f6cba09783 -> 2885 T1 /planned_causal_edges/175|CE-24-6f9164cf08f6cba09783 0bff8fd660cf
2886 T1 /causal_edges/172|CE-24-7208c91d9bb56211cf5d -> 2887 T1 /planned_causal_edges/172|CE-24-7208c91d9bb56211cf5d 25d808cf2eb1
2888 T1 /causal_edges/295|CE-24-72d728edfc366681eb78 -> 2889 T1 /planned_causal_edges/295|CE-24-72d728edfc366681eb78 ad3213660cf4
2890 T1 /causal_edges/253|CE-24-734bbb28d5816ea52bca -> 2891 T1 /planned_causal_edges/253|CE-24-734bbb28d5816ea52bca bbef43f45213
2892 T1 /causal_edges/197|CE-24-73cfe52f01870480ab8b -> 2893 T1 /planned_causal_edges/197|CE-24-73cfe52f01870480ab8b f6916e49c214
2894 T1 /causal_edges/62|CE-24-748c61d42ed04fc8bbc4 -> 2895 T1 /planned_causal_edges/62|CE-24-748c61d42ed04fc8bbc4 665620dba35d
2896 T1 /causal_edges/168|CE-24-752812c2762f5ba0b2b8 -> 2897 T1 /planned_causal_edges/168|CE-24-752812c2762f5ba0b2b8 f133feddfaff
2898 T1 /causal_edges/10|CE-24-752d0987418900bf6a46 -> 2899 T1 /planned_causal_edges/10|CE-24-752d0987418900bf6a46 b68719c7fe1b
2900 T1 /causal_edges/75|CE-24-77e4f44365242db71b83 -> 2901 T1 /planned_causal_edges/75|CE-24-77e4f44365242db71b83 c69f716ebb28
2902 T1 /causal_edges/13|CE-24-784776ec096834d51549 -> 2903 T1 /planned_causal_edges/13|CE-24-784776ec096834d51549 6421c8ff4278
2904 T1 /causal_edges/16|CE-24-784867091c21fc425adc -> 2905 T1 /planned_causal_edges/16|CE-24-784867091c21fc425adc 79e9bc8c82db
2906 T1 /causal_edges/4|CE-24-78d3a2e01075301693f7 -> 2907 T1 /planned_causal_edges/4|CE-24-78d3a2e01075301693f7 b2255fe0d8a5
2908 T1 /causal_edges/178|CE-24-79e6e1f5f3f6c98e3f78 -> 2909 T1 /planned_causal_edges/178|CE-24-79e6e1f5f3f6c98e3f78 58a41203a58e
2910 T1 /causal_edges/70|CE-24-7a2301ea679c3426dd5a -> 2911 T1 /planned_causal_edges/70|CE-24-7a2301ea679c3426dd5a a4af2ec91bd9
2912 T1 /causal_edges/218|CE-24-7a2be884541c191b920d -> 2913 T1 /planned_causal_edges/218|CE-24-7a2be884541c191b920d 04fe957b1237
2914 T1 /causal_edges/162|CE-24-7a4498bb685ea5d5fbaa -> 2915 T1 /planned_causal_edges/162|CE-24-7a4498bb685ea5d5fbaa a79e538e939a
2916 T1 /causal_edges/182|CE-24-7b7df77c4d1f23380f27 -> 2917 T1 /planned_causal_edges/182|CE-24-7b7df77c4d1f23380f27 ba00fe463b6e
2918 T1 /causal_edges/41|CE-24-7ca632954478fc7951e6 -> 2919 T1 /planned_causal_edges/41|CE-24-7ca632954478fc7951e6 9e1aa90f0ec2
2920 T1 /causal_edges/238|CE-24-7d17170877014bbcdea6 -> 2921 T1 /planned_causal_edges/238|CE-24-7d17170877014bbcdea6 ede8b4bf4a7f
2922 T1 /causal_edges/53|CE-24-7d83505896005e0d51d8 -> 2923 T1 /planned_causal_edges/53|CE-24-7d83505896005e0d51d8 3f2670fbebdd
2924 T1 /causal_edges/186|CE-24-7e392ababa2e5d58d263 -> 2925 T1 /planned_causal_edges/186|CE-24-7e392ababa2e5d58d263 18cee63aa74f
2926 T1 /causal_edges/38|CE-24-7f1ed9d68e7b30d659b3 -> 2927 T1 /planned_causal_edges/38|CE-24-7f1ed9d68e7b30d659b3 5fa70c3e5ca3
2928 T1 /causal_edges/167|CE-24-7f21f723fd33598694ab -> 2929 T1 /planned_causal_edges/167|CE-24-7f21f723fd33598694ab 6966d56fee97
2930 T1 /causal_edges/126|CE-24-7f2f4bc44b6019a7a90d -> 2931 T1 /planned_causal_edges/126|CE-24-7f2f4bc44b6019a7a90d db9b562dfde9
2932 T1 /causal_edges/177|CE-24-7f8aa4fac7e34466be61 -> 2933 T1 /planned_causal_edges/177|CE-24-7f8aa4fac7e34466be61 a5571032f3a8
2934 T1 /causal_edges/135|CE-24-7fe4b7b2de5c1a759800 -> 2935 T1 /planned_causal_edges/135|CE-24-7fe4b7b2de5c1a759800 8de67dbdd1d4
2936 T1 /causal_edges/164|CE-24-80dc710e6f68d984fe23 -> 2937 T1 /planned_causal_edges/164|CE-24-80dc710e6f68d984fe23 66f8c3046256
2938 T1 /causal_edges/23|CE-24-80fa8fa6234cb4f00e94 -> 2939 T1 /planned_causal_edges/23|CE-24-80fa8fa6234cb4f00e94 1e54216d7b1e
2940 T1 /causal_edges/64|CE-24-817bf8c9def59d0e5426 -> 2941 T1 /planned_causal_edges/64|CE-24-817bf8c9def59d0e5426 904ee1e48be7
2942 T1 /causal_edges/120|CE-24-81ef936b1009805b07f1 -> 2943 T1 /planned_causal_edges/120|CE-24-81ef936b1009805b07f1 ca4fcdaebdc0
2944 T1 /causal_edges/58|CE-24-820eec99a54c0b93fe58 -> 2945 T1 /planned_causal_edges/58|CE-24-820eec99a54c0b93fe58 1f58f8adff3c
2946 T1 /causal_edges/24|CE-24-822b5658a7bc08d270c5 -> 2947 T1 /planned_causal_edges/24|CE-24-822b5658a7bc08d270c5 5b3208f001f4
2948 T1 /causal_edges/148|CE-24-825114327590acb3601a -> 2949 T1 /planned_causal_edges/148|CE-24-825114327590acb3601a d485750cf86e
2950 T1 /causal_edges/60|CE-24-826f8fa6a9b61820a161 -> 2951 T1 /planned_causal_edges/60|CE-24-826f8fa6a9b61820a161 3dc478d6c184
2952 T1 /causal_edges/198|CE-24-834c364946c452afb838 -> 2953 T1 /planned_causal_edges/198|CE-24-834c364946c452afb838 36122f5fb84c
2954 T1 /causal_edges/129|CE-24-83a5869cb9430bc4a0a4 -> 2955 T1 /planned_causal_edges/129|CE-24-83a5869cb9430bc4a0a4 9253fa161d18
2956 T1 /causal_edges/154|CE-24-83d019223d32cddd680d -> 2957 T1 /planned_causal_edges/154|CE-24-83d019223d32cddd680d 46e642caab6a
2958 T1 /causal_edges/25|CE-24-84041cd5c81e23afbc51 -> 2959 T1 /planned_causal_edges/25|CE-24-84041cd5c81e23afbc51 847818c42c95
2960 T1 /causal_edges/1|CE-24-84829f4b9c40b74beeff -> 2961 T1 /planned_causal_edges/1|CE-24-84829f4b9c40b74beeff 48e1bf91fe54
2962 T1 /causal_edges/241|CE-24-859327b0b7a7fa3184f8 -> 2963 T1 /planned_causal_edges/241|CE-24-859327b0b7a7fa3184f8 9376c400fc7a
2964 T1 /causal_edges/12|CE-24-86c9a8eb135d41917364 -> 2965 T1 /planned_causal_edges/12|CE-24-86c9a8eb135d41917364 4a3212463330
2966 T1 /causal_edges/145|CE-24-86e67cfe77370ac2b6b0 -> 2967 T1 /planned_causal_edges/145|CE-24-86e67cfe77370ac2b6b0 ccfb79c5ac4e
2968 T1 /causal_edges/100|CE-24-86ea6bab6c1b92727115 -> 2969 T1 /planned_causal_edges/100|CE-24-86ea6bab6c1b92727115 26b1b0664b52
2970 T1 /causal_edges/181|CE-24-8758970f41acf69baeec -> 2971 T1 /planned_causal_edges/181|CE-24-8758970f41acf69baeec 52c2221863be
2972 T1 /causal_edges/36|CE-24-8761b121d64e724bf703 -> 2973 T1 /planned_causal_edges/36|CE-24-8761b121d64e724bf703 25f6cb23aaff
2974 T1 /causal_edges/173|CE-24-87a8ecc00e58d3cf85b9 -> 2975 T1 /planned_causal_edges/173|CE-24-87a8ecc00e58d3cf85b9 3747a87f6cd1
2976 T1 /causal_edges/317|CE-24-87ef13b3e2083ec987e6 -> 2977 T1 /planned_causal_edges/317|CE-24-87ef13b3e2083ec987e6 c2cfe8bd7a1b
2978 T1 /causal_edges/115|CE-24-899df92afdb4ce88bbb8 -> 2979 T1 /planned_causal_edges/115|CE-24-899df92afdb4ce88bbb8 0fc48167e46a
2980 T1 /causal_edges/59|CE-24-8a78b766de4ecfe31e3b -> 2981 T1 /planned_causal_edges/59|CE-24-8a78b766de4ecfe31e3b e12ad623fa6a
2982 T1 /causal_edges/43|CE-24-8a85badf94a52ecf1ee8 -> 2983 T1 /planned_causal_edges/43|CE-24-8a85badf94a52ecf1ee8 6fa636110f55
2984 T1 /causal_edges/303|CE-24-8bbf63d8cdf41d58d8b0 -> 2985 T1 /planned_causal_edges/303|CE-24-8bbf63d8cdf41d58d8b0 9635cea00eab
2986 T1 /causal_edges/97|CE-24-8c5d415a9601c5cdb106 -> 2987 T1 /planned_causal_edges/97|CE-24-8c5d415a9601c5cdb106 10f5bc997bc8
2988 T1 /causal_edges/234|CE-24-8d24a12efd4393f342ac -> 2989 T1 /planned_causal_edges/234|CE-24-8d24a12efd4393f342ac 6ac19caa4fa4
2990 T1 /causal_edges/29|CE-24-8d6a6c0bcb40006b9b1a -> 2991 T1 /planned_causal_edges/29|CE-24-8d6a6c0bcb40006b9b1a fd7c48a8d066
2992 T1 /causal_edges/309|CE-24-8e7f596d4daed54c9c44 -> 2993 T1 /planned_causal_edges/309|CE-24-8e7f596d4daed54c9c44 8676fa41879d
2994 T1 /causal_edges/7|CE-24-8f86f5cc5d07578d0d5b -> 2995 T1 /planned_causal_edges/7|CE-24-8f86f5cc5d07578d0d5b bb5b43aa5bc0
2996 T1 /causal_edges/77|CE-24-9007fcf42f93baf7e609 -> 2997 T1 /planned_causal_edges/77|CE-24-9007fcf42f93baf7e609 93baa86a0b4f
2998 T1 /causal_edges/319|CE-24-90b7fb61edec2466d3fc -> 2999 T1 /planned_causal_edges/319|CE-24-90b7fb61edec2466d3fc 67561b89bd0d
3000 T1 /causal_edges/301|CE-24-9120db06cfa7c840762e -> 3001 T1 /planned_causal_edges/301|CE-24-9120db06cfa7c840762e 7e7aad173e0e
3002 T1 /causal_edges/33|CE-24-913cbe7a0c97f6f9ad43 -> 3003 T1 /planned_causal_edges/33|CE-24-913cbe7a0c97f6f9ad43 64372d22fdb5
3004 T1 /causal_edges/300|CE-24-92af67af38db046a9caa -> 3005 T1 /planned_causal_edges/300|CE-24-92af67af38db046a9caa 810bf46fab7c
3006 T1 /causal_edges/42|CE-24-92f6eb0060c27d8d260f -> 3007 T1 /planned_causal_edges/42|CE-24-92f6eb0060c27d8d260f 07037d26f077
3008 T1 /causal_edges/228|CE-24-9304d0461dfd5d942307 -> 3009 T1 /planned_causal_edges/228|CE-24-9304d0461dfd5d942307 dab3b795368c
3010 T1 /causal_edges/318|CE-24-931f02dfcc1d2339e797 -> 3011 T1 /planned_causal_edges/318|CE-24-931f02dfcc1d2339e797 7c8619e2af96
3012 T1 /causal_edges/88|CE-24-9336cbc0df3427c3b57b -> 3013 T1 /planned_causal_edges/88|CE-24-9336cbc0df3427c3b57b 0372119faf70
3014 T1 /causal_edges/8|CE-24-939fc8fafa6fc5106c0c -> 3015 T1 /planned_causal_edges/8|CE-24-939fc8fafa6fc5106c0c beea3dc12367
3016 T1 /causal_edges/320|CE-24-942c8788dd59f5705074 -> 3017 T1 /planned_causal_edges/320|CE-24-942c8788dd59f5705074 09d4a44d45b9
3018 T1 /causal_edges/207|CE-24-96982165050c5ba8edc2 -> 3019 T1 /planned_causal_edges/207|CE-24-96982165050c5ba8edc2 4e999812e852
3020 T1 /causal_edges/225|CE-24-97fa3fa1dc3171088288 -> 3021 T1 /planned_causal_edges/225|CE-24-97fa3fa1dc3171088288 5a49263710d1
3022 T1 /causal_edges/9|CE-24-98488d43871004b30a09 -> 3023 T1 /planned_causal_edges/9|CE-24-98488d43871004b30a09 e4ef8bb83ef2
3024 T1 /causal_edges/131|CE-24-98a6ca5bfd90962f3f70 -> 3025 T1 /planned_causal_edges/131|CE-24-98a6ca5bfd90962f3f70 a26cc9fef9bd
3026 T1 /causal_edges/93|CE-24-98c75c56251da6e15958 -> 3027 T1 /planned_causal_edges/93|CE-24-98c75c56251da6e15958 5e6d928f15e2
3028 T1 /causal_edges/141|CE-24-9a38e4b80cd42b05fe5a -> 3029 T1 /planned_causal_edges/141|CE-24-9a38e4b80cd42b05fe5a 54beeacf5209
3030 T1 /causal_edges/156|CE-24-9a51d84d6b00b229236b -> 3031 T1 /planned_causal_edges/156|CE-24-9a51d84d6b00b229236b 44f3c5fd3e8a
3032 T1 /causal_edges/113|CE-24-9e79d0a1ff07b967e222 -> 3033 T1 /planned_causal_edges/113|CE-24-9e79d0a1ff07b967e222 e52014339fb2
3034 T1 /causal_edges/273|CE-24-9f2d534d7409c1961db3 -> 3035 T1 /planned_causal_edges/273|CE-24-9f2d534d7409c1961db3 9680239754be
3036 T1 /causal_edges/240|CE-24-a03d9e6c5963473ee107 -> 3037 T1 /planned_causal_edges/240|CE-24-a03d9e6c5963473ee107 bc6e264d2c7f
3038 T1 /causal_edges/189|CE-24-a0ebfb4ee9f25cd7aa70 -> 3039 T1 /planned_causal_edges/189|CE-24-a0ebfb4ee9f25cd7aa70 5c8cad0b0b4b
3040 T1 /causal_edges/76|CE-24-a1372f97c986f8950ac9 -> 3041 T1 /planned_causal_edges/76|CE-24-a1372f97c986f8950ac9 b4e010f94f6d
3042 T1 /causal_edges/130|CE-24-a1c34573f82a4a4a72a8 -> 3043 T1 /planned_causal_edges/130|CE-24-a1c34573f82a4a4a72a8 d3288d729e56
3044 T1 /causal_edges/90|CE-24-a27f81bcaf6a83af6219 -> 3045 T1 /planned_causal_edges/90|CE-24-a27f81bcaf6a83af6219 6a7eed1bef74
3046 T1 /causal_edges/143|CE-24-a29f92eefa029a6639c1 -> 3047 T1 /planned_causal_edges/143|CE-24-a29f92eefa029a6639c1 7a1c7c506fca
3048 T1 /causal_edges/205|CE-24-a3b6e4ca4af507846444 -> 3049 T1 /planned_causal_edges/205|CE-24-a3b6e4ca4af507846444 2adf34da8cd4
3050 T1 /causal_edges/82|CE-24-a3d597a1868d38495782 -> 3051 T1 /planned_causal_edges/82|CE-24-a3d597a1868d38495782 7f2e675c2742
3052 T1 /causal_edges/136|CE-24-a565e5294bc9c8f20051 -> 3053 T1 /planned_causal_edges/136|CE-24-a565e5294bc9c8f20051 8a4c2157c867
3054 T1 /causal_edges/239|CE-24-a56c7a994b8082f75263 -> 3055 T1 /planned_causal_edges/239|CE-24-a56c7a994b8082f75263 722a08fb13f0
3056 T1 /causal_edges/269|CE-24-a57d3b8a7708a6895c23 -> 3057 T1 /planned_causal_edges/269|CE-24-a57d3b8a7708a6895c23 dbcff1d4ea06
3058 T1 /causal_edges/157|CE-24-a7d7cd5634cab39ddff6 -> 3059 T1 /planned_causal_edges/157|CE-24-a7d7cd5634cab39ddff6 88594e38280c
3060 T1 /causal_edges/99|CE-24-a80e1fd7e128f6c9085f -> 3061 T1 /planned_causal_edges/99|CE-24-a80e1fd7e128f6c9085f 640d58b813f9
3062 T1 /causal_edges/274|CE-24-a847f29f13e441e4fc8d -> 3063 T1 /planned_causal_edges/274|CE-24-a847f29f13e441e4fc8d 8a3ce23cbe5e
3064 T1 /causal_edges/27|CE-24-a8e097e0082f48bb8115 -> 3065 T1 /planned_causal_edges/27|CE-24-a8e097e0082f48bb8115 660a2b21be7d
3066 T1 /causal_edges/144|CE-24-aa2d2090b3f3f50de967 -> 3067 T1 /planned_causal_edges/144|CE-24-aa2d2090b3f3f50de967 cc54e2c8c07e
3068 T1 /causal_edges/124|CE-24-aa7cdb9a0a18fba161da -> 3069 T1 /planned_causal_edges/124|CE-24-aa7cdb9a0a18fba161da 475a5ef1fa7c
3070 T1 /causal_edges/73|CE-24-ab3074ac63f77308122f -> 3071 T1 /planned_causal_edges/73|CE-24-ab3074ac63f77308122f caac9911815d
3072 T1 /causal_edges/261|CE-24-ab996f58b1e04e960619 -> 3073 T1 /planned_causal_edges/261|CE-24-ab996f58b1e04e960619 9802cd175bba
3074 T1 /causal_edges/281|CE-24-ae445533f551f703b106 -> 3075 T1 /planned_causal_edges/281|CE-24-ae445533f551f703b106 9ed1a6fdccb3
3076 T1 /causal_edges/283|CE-24-ae65e269e1d45d1a343f -> 3077 T1 /planned_causal_edges/283|CE-24-ae65e269e1d45d1a343f 2d625c27a795
3078 T1 /causal_edges/194|CE-24-afefce3c0b66f44dac4a -> 3079 T1 /planned_causal_edges/194|CE-24-afefce3c0b66f44dac4a 7d300e38ba44
3080 T1 /causal_edges/312|CE-24-aff67d94bdc3e11152fb -> 3081 T1 /planned_causal_edges/312|CE-24-aff67d94bdc3e11152fb 70b7fd4b612a
3082 T1 /causal_edges/65|CE-24-b0229960615ed0224e1f -> 3083 T1 /planned_causal_edges/65|CE-24-b0229960615ed0224e1f 39120b45dea3
3084 T1 /causal_edges/179|CE-24-b027d5bb7417db989e26 -> 3085 T1 /planned_causal_edges/179|CE-24-b027d5bb7417db989e26 5ccec397e4a7
3086 T1 /causal_edges/272|CE-24-b210cf2516fa3d148bd8 -> 3087 T1 /planned_causal_edges/272|CE-24-b210cf2516fa3d148bd8 c996924d64ac
3088 T1 /causal_edges/109|CE-24-b31ce8c480cab4b84262 -> 3089 T1 /planned_causal_edges/109|CE-24-b31ce8c480cab4b84262 6a89c77c84d0
3090 T1 /causal_edges/149|CE-24-b372f954ecc57d00363c -> 3091 T1 /planned_causal_edges/149|CE-24-b372f954ecc57d00363c 8df03c00f4e7
3092 T1 /causal_edges/166|CE-24-b58c5e71d64a575c5b7d -> 3093 T1 /planned_causal_edges/166|CE-24-b58c5e71d64a575c5b7d e66e17a632d5
3094 T1 /causal_edges/50|CE-24-b5b7f15b8d74b4f61321 -> 3095 T1 /planned_causal_edges/50|CE-24-b5b7f15b8d74b4f61321 7857faea1a0f
3096 T1 /causal_edges/102|CE-24-b5b8c4c5228ca4245730 -> 3097 T1 /planned_causal_edges/102|CE-24-b5b8c4c5228ca4245730 9c9287789bed
3098 T1 /causal_edges/116|CE-24-b7aa2bf406c8db317a86 -> 3099 T1 /planned_causal_edges/116|CE-24-b7aa2bf406c8db317a86 1c9fe6680cae
3100 T1 /causal_edges/247|CE-24-b7da686cea5855de30e9 -> 3101 T1 /planned_causal_edges/247|CE-24-b7da686cea5855de30e9 25d5bc880e6f
3102 T1 /causal_edges/69|CE-24-b8d6aae94bead036fff3 -> 3103 T1 /planned_causal_edges/69|CE-24-b8d6aae94bead036fff3 98889a2aaa5c
3104 T1 /causal_edges/294|CE-24-b901c686e8cc8655f01c -> 3105 T1 /planned_causal_edges/294|CE-24-b901c686e8cc8655f01c 0f19dddceb16
3106 T1 /causal_edges/227|CE-24-baca43f088225f280a99 -> 3107 T1 /planned_causal_edges/227|CE-24-baca43f088225f280a99 8ed4233ddd5d
3108 T1 /causal_edges/287|CE-24-bb43bdb3af1664b9c0c9 -> 3109 T1 /planned_causal_edges/287|CE-24-bb43bdb3af1664b9c0c9 a3c78e0270d7
3110 T1 /causal_edges/123|CE-24-bbee15ec5330ccd9663d -> 3111 T1 /planned_causal_edges/123|CE-24-bbee15ec5330ccd9663d 5b6c72dc9369
3112 T1 /causal_edges/236|CE-24-bc581e5676dba697c934 -> 3113 T1 /planned_causal_edges/236|CE-24-bc581e5676dba697c934 48beca2f9115
3114 T1 /causal_edges/310|CE-24-bc589364f72254f93a71 -> 3115 T1 /planned_causal_edges/310|CE-24-bc589364f72254f93a71 2a1ddcc9d867
3116 T1 /causal_edges/290|CE-24-bc903631d52388a4c0e4 -> 3117 T1 /planned_causal_edges/290|CE-24-bc903631d52388a4c0e4 00c336143fb7
3118 T1 /causal_edges/304|CE-24-be48359e7cccd5f11fb8 -> 3119 T1 /planned_causal_edges/304|CE-24-be48359e7cccd5f11fb8 12ebf5a3eaf1
3120 T1 /causal_edges/302|CE-24-be8f91d5ad75ff151984 -> 3121 T1 /planned_causal_edges/302|CE-24-be8f91d5ad75ff151984 ab6063822ea6
3122 T1 /causal_edges/139|CE-24-c0da1866a7424688638c -> 3123 T1 /planned_causal_edges/139|CE-24-c0da1866a7424688638c 56ce7b359786
3124 T1 /causal_edges/171|CE-24-c1f152e774e8ca99a498 -> 3125 T1 /planned_causal_edges/171|CE-24-c1f152e774e8ca99a498 e2bbda78ff60
3126 T1 /causal_edges/81|CE-24-c2a9918b579d6ef8bf5e -> 3127 T1 /planned_causal_edges/81|CE-24-c2a9918b579d6ef8bf5e 826cdd61d327
3128 T1 /causal_edges/140|CE-24-c42b5033cd6101cfd8ae -> 3129 T1 /planned_causal_edges/140|CE-24-c42b5033cd6101cfd8ae e329da8f1fd1
3130 T1 /causal_edges/226|CE-24-c42dc17b0eeb49d08cdf -> 3131 T1 /planned_causal_edges/226|CE-24-c42dc17b0eeb49d08cdf d3d7b2cf7bff
3132 T1 /causal_edges/211|CE-24-c5f6241e6f2f86779faf -> 3133 T1 /planned_causal_edges/211|CE-24-c5f6241e6f2f86779faf 3437897625ec
3134 T1 /causal_edges/242|CE-24-c681170cea3947d46990 -> 3135 T1 /planned_causal_edges/242|CE-24-c681170cea3947d46990 a9b76f529ae8
3136 T1 /causal_edges/105|CE-24-c709056721d1f11e27b8 -> 3137 T1 /planned_causal_edges/105|CE-24-c709056721d1f11e27b8 606465e918f3
3138 T1 /causal_edges/184|CE-24-c7276d9821d86b97e0ff -> 3139 T1 /planned_causal_edges/184|CE-24-c7276d9821d86b97e0ff 9dc5de889e4f
3140 T1 /causal_edges/121|CE-24-c76b42446aa62b5054ae -> 3141 T1 /planned_causal_edges/121|CE-24-c76b42446aa62b5054ae eab85a5a7927
3142 T1 /causal_edges/170|CE-24-c821516b1944115314fa -> 3143 T1 /planned_causal_edges/170|CE-24-c821516b1944115314fa c9db0504fcda
3144 T1 /causal_edges/122|CE-24-c843d25bbcef9f992c92 -> 3145 T1 /planned_causal_edges/122|CE-24-c843d25bbcef9f992c92 5e1bb9f56076
3146 T1 /causal_edges/298|CE-24-c85aa03f60195534b08f -> 3147 T1 /planned_causal_edges/298|CE-24-c85aa03f60195534b08f 69d14319b171
3148 T1 /causal_edges/231|CE-24-c8eed4e2f49a9fd6e8b2 -> 3149 T1 /planned_causal_edges/231|CE-24-c8eed4e2f49a9fd6e8b2 ae2556f8a82a
3150 T1 /causal_edges/185|CE-24-c995aa2fe8b231c4d71d -> 3151 T1 /planned_causal_edges/185|CE-24-c995aa2fe8b231c4d71d 5d0f460afd49
3152 T1 /causal_edges/216|CE-24-ca385d845ad30913ea2d -> 3153 T1 /planned_causal_edges/216|CE-24-ca385d845ad30913ea2d 3a6e15b4d659
3154 T1 /causal_edges/277|CE-24-ccf585d4a87fb3ad2cb6 -> 3155 T1 /planned_causal_edges/277|CE-24-ccf585d4a87fb3ad2cb6 72e9ea6aac18
3156 T1 /causal_edges/208|CE-24-ce0e913a14490f8905b6 -> 3157 T1 /planned_causal_edges/208|CE-24-ce0e913a14490f8905b6 b0dd95b89d1c
3158 T1 /causal_edges/11|CE-24-ce6034e0fec864fc5e8d -> 3159 T1 /planned_causal_edges/11|CE-24-ce6034e0fec864fc5e8d 9e7361ac9eff
3160 T1 /causal_edges/296|CE-24-cf0bfed49946f3ee4260 -> 3161 T1 /planned_causal_edges/296|CE-24-cf0bfed49946f3ee4260 76237caa1773
3162 T1 /causal_edges/193|CE-24-cff64a580ad0fcc2cbce -> 3163 T1 /planned_causal_edges/193|CE-24-cff64a580ad0fcc2cbce bdf4ae26ea86
3164 T1 /causal_edges/35|CE-24-d0542ad216fd7f477508 -> 3165 T1 /planned_causal_edges/35|CE-24-d0542ad216fd7f477508 1284897fbda7
3166 T1 /causal_edges/72|CE-24-d0ab25ecadc9d28ccd52 -> 3167 T1 /planned_causal_edges/72|CE-24-d0ab25ecadc9d28ccd52 3f2957787069
3168 T1 /causal_edges/17|CE-24-d0c60aa28b254ab06c67 -> 3169 T1 /planned_causal_edges/17|CE-24-d0c60aa28b254ab06c67 9d23fad5d99d
3170 T1 /causal_edges/245|CE-24-d1e4b30242763b2f6cd3 -> 3171 T1 /planned_causal_edges/245|CE-24-d1e4b30242763b2f6cd3 33274f78c20b
3172 T1 /causal_edges/237|CE-24-d232fb3640ac680b340e -> 3173 T1 /planned_causal_edges/237|CE-24-d232fb3640ac680b340e c6c43fa3b78d
3174 T1 /causal_edges/315|CE-24-d4a4ee9c123ed487b0c5 -> 3175 T1 /planned_causal_edges/315|CE-24-d4a4ee9c123ed487b0c5 252ddbe41d4c
3176 T1 /causal_edges/125|CE-24-d528e8f735d390408cad -> 3177 T1 /planned_causal_edges/125|CE-24-d528e8f735d390408cad d370f1630148
3178 T1 /causal_edges/66|CE-24-d547614d4ea3aab76810 -> 3179 T1 /planned_causal_edges/66|CE-24-d547614d4ea3aab76810 fe10c8c3ea37
3180 T1 /causal_edges/32|CE-24-d7e6c41249ee6cd6b086 -> 3181 T1 /planned_causal_edges/32|CE-24-d7e6c41249ee6cd6b086 ee8f3adc5518
3182 T1 /causal_edges/155|CE-24-d7fef3d9c6b5d9fb8785 -> 3183 T1 /planned_causal_edges/155|CE-24-d7fef3d9c6b5d9fb8785 fbb4948791e8
3184 T1 /causal_edges/151|CE-24-d80b63968b66233d8ab8 -> 3185 T1 /planned_causal_edges/151|CE-24-d80b63968b66233d8ab8 f6ca42d5a28a
3186 T1 /causal_edges/316|CE-24-d81b95e07378574418b6 -> 3187 T1 /planned_causal_edges/316|CE-24-d81b95e07378574418b6 b9db32820cd5
3188 T1 /causal_edges/152|CE-24-d87421be389cd2ac69e6 -> 3189 T1 /planned_causal_edges/152|CE-24-d87421be389cd2ac69e6 f14da72f844c
3190 T1 /causal_edges/3|CE-24-d8a7f1c2877b1bc89550 -> 3191 T1 /planned_causal_edges/3|CE-24-d8a7f1c2877b1bc89550 a52ff892edff
3192 T1 /causal_edges/230|CE-24-d904804709811cae9611 -> 3193 T1 /planned_causal_edges/230|CE-24-d904804709811cae9611 456a1975f4ba
3194 T1 /causal_edges/117|CE-24-d909df35d7c38e8d9312 -> 3195 T1 /planned_causal_edges/117|CE-24-d909df35d7c38e8d9312 722f579b7377
3196 T1 /causal_edges/15|CE-24-d9c1f58a4c79942c9c76 -> 3197 T1 /planned_causal_edges/15|CE-24-d9c1f58a4c79942c9c76 b4758dff04dc
3198 T1 /causal_edges/92|CE-24-d9d238ae5bf35f4a9ee5 -> 3199 T1 /planned_causal_edges/92|CE-24-d9d238ae5bf35f4a9ee5 5a94794befe3
3200 T1 /causal_edges/250|CE-24-da6a6fb1e057c895bc07 -> 3201 T1 /planned_causal_edges/250|CE-24-da6a6fb1e057c895bc07 5d96bddc46d2
3202 T1 /causal_edges/202|CE-24-dc98d966db658f4da880 -> 3203 T1 /planned_causal_edges/202|CE-24-dc98d966db658f4da880 2e17c2bc87ee
3204 T1 /causal_edges/163|CE-24-dd2a3237bab094f21b64 -> 3205 T1 /planned_causal_edges/163|CE-24-dd2a3237bab094f21b64 7c1b6fd6aea2
3206 T1 /causal_edges/206|CE-24-dd59f238bed9b5f1e197 -> 3207 T1 /planned_causal_edges/206|CE-24-dd59f238bed9b5f1e197 cb47841a24b9
3208 T1 /causal_edges/46|CE-24-ddccc4e1dcf2d6fbb4b5 -> 3209 T1 /planned_causal_edges/46|CE-24-ddccc4e1dcf2d6fbb4b5 32a20f2d25ce
3210 T1 /causal_edges/78|CE-24-de0008713ff498aef103 -> 3211 T1 /planned_causal_edges/78|CE-24-de0008713ff498aef103 f5e9149b0c33
3212 T1 /causal_edges/264|CE-24-de9c2df96ca29b7f59b1 -> 3213 T1 /planned_causal_edges/264|CE-24-de9c2df96ca29b7f59b1 5f757c39a29e
3214 T1 /causal_edges/267|CE-24-def1d49c8b8f2fbd6924 -> 3215 T1 /planned_causal_edges/267|CE-24-def1d49c8b8f2fbd6924 220da3846210
3216 T1 /causal_edges/204|CE-24-df4fdea83f25de883055 -> 3217 T1 /planned_causal_edges/204|CE-24-df4fdea83f25de883055 d8808484ca9c
3218 T1 /causal_edges/0|CE-24-df9df06ede740f302097 -> 3219 T1 /planned_causal_edges/0|CE-24-df9df06ede740f302097 1bb8d7eb2fe2
3220 T1 /causal_edges/106|CE-24-e120e750c97edfe26202 -> 3221 T1 /planned_causal_edges/106|CE-24-e120e750c97edfe26202 85e326861776
3222 T1 /causal_edges/311|CE-24-e1302a6e7a94b617926c -> 3223 T1 /planned_causal_edges/311|CE-24-e1302a6e7a94b617926c 9192969c492a
3224 T1 /causal_edges/128|CE-24-e22a4f8701e610a0d4ab -> 3225 T1 /planned_causal_edges/128|CE-24-e22a4f8701e610a0d4ab 822c237ce7c9
3226 T1 /causal_edges/14|CE-24-e246e32f7b1594a3f984 -> 3227 T1 /planned_causal_edges/14|CE-24-e246e32f7b1594a3f984 4e9e219095e1
3228 T1 /causal_edges/39|CE-24-e2f39bbd3c1775b82998 -> 3229 T1 /planned_causal_edges/39|CE-24-e2f39bbd3c1775b82998 810ee8cda0ad
3230 T1 /causal_edges/51|CE-24-e3698ce7bdf9d18bdcdd -> 3231 T1 /planned_causal_edges/51|CE-24-e3698ce7bdf9d18bdcdd 2a9fee116f12
3232 T1 /causal_edges/279|CE-24-e3c69bc78aec36da7e81 -> 3233 T1 /planned_causal_edges/279|CE-24-e3c69bc78aec36da7e81 7fcb79c072ff
3234 T1 /causal_edges/280|CE-24-e4325c825afb05b0dd2a -> 3235 T1 /planned_causal_edges/280|CE-24-e4325c825afb05b0dd2a 586275439b9d
3236 T1 /causal_edges/87|CE-24-e51d90aed757bad86156 -> 3237 T1 /planned_causal_edges/87|CE-24-e51d90aed757bad86156 73447476bc81
3238 T1 /causal_edges/195|CE-24-e84e7b33c66484008640 -> 3239 T1 /planned_causal_edges/195|CE-24-e84e7b33c66484008640 0e8d5c85ad28
3240 T1 /causal_edges/292|CE-24-e91eeab56c1d9eeb7583 -> 3241 T1 /planned_causal_edges/292|CE-24-e91eeab56c1d9eeb7583 fa9c4689b1ae
3242 T1 /causal_edges/229|CE-24-ea25894a43f2aaa08337 -> 3243 T1 /planned_causal_edges/229|CE-24-ea25894a43f2aaa08337 23340737b2fe
3244 T1 /causal_edges/174|CE-24-ea8bd1fac070fa38db09 -> 3245 T1 /planned_causal_edges/174|CE-24-ea8bd1fac070fa38db09 2562deecbd5d
3246 T1 /causal_edges/95|CE-24-eb5eadafbde5c7012ebe -> 3247 T1 /planned_causal_edges/95|CE-24-eb5eadafbde5c7012ebe f48c47d603e4
3248 T1 /causal_edges/188|CE-24-ec0ecef86ead9cec2d89 -> 3249 T1 /planned_causal_edges/188|CE-24-ec0ecef86ead9cec2d89 09d81def8343
3250 T1 /causal_edges/110|CE-24-ec9763fd0c88424733ff -> 3251 T1 /planned_causal_edges/110|CE-24-ec9763fd0c88424733ff 71caeaf26d0a
3252 T1 /causal_edges/83|CE-24-ecdb6d784e56fc541469 -> 3253 T1 /planned_causal_edges/83|CE-24-ecdb6d784e56fc541469 196f70ab5eba
3254 T1 /causal_edges/297|CE-24-ed03997bec75971c95ce -> 3255 T1 /planned_causal_edges/297|CE-24-ed03997bec75971c95ce 72f5c30fccde
3256 T1 /causal_edges/305|CE-24-ef7f766c8ff4f35dd7f1 -> 3257 T1 /planned_causal_edges/305|CE-24-ef7f766c8ff4f35dd7f1 213c774ec27b
3258 T1 /causal_edges/85|CE-24-ef8a175b4907b0e469ef -> 3259 T1 /planned_causal_edges/85|CE-24-ef8a175b4907b0e469ef 4d9c3b349196
3260 T1 /causal_edges/89|CE-24-efab69a9f6821d0b2bc2 -> 3261 T1 /planned_causal_edges/89|CE-24-efab69a9f6821d0b2bc2 95d6748e9f1d
3262 T1 /causal_edges/203|CE-24-efb29c12005d68c4559f -> 3263 T1 /planned_causal_edges/203|CE-24-efb29c12005d68c4559f 758b4080ecbf
3264 T1 /causal_edges/47|CE-24-f0ebe5fce66bc46c16da -> 3265 T1 /planned_causal_edges/47|CE-24-f0ebe5fce66bc46c16da ce51570b1491
3266 T1 /causal_edges/254|CE-24-f11e8a92113b04186f03 -> 3267 T1 /planned_causal_edges/254|CE-24-f11e8a92113b04186f03 e2facd4ba8b7
3268 T1 /causal_edges/30|CE-24-f1dc2d73043e006b324a -> 3269 T1 /planned_causal_edges/30|CE-24-f1dc2d73043e006b324a 4ed6da6f751a
3270 T1 /causal_edges/224|CE-24-f21f437272ed5211fc3d -> 3271 T1 /planned_causal_edges/224|CE-24-f21f437272ed5211fc3d d76a0b3b657c
3272 T1 /causal_edges/49|CE-24-f42b2cb0a71ddbbb69ca -> 3273 T1 /planned_causal_edges/49|CE-24-f42b2cb0a71ddbbb69ca 4abb2cfc00c5
3274 T1 /causal_edges/138|CE-24-f4d2014183149ea542f7 -> 3275 T1 /planned_causal_edges/138|CE-24-f4d2014183149ea542f7 6711eded5128
3276 T1 /causal_edges/233|CE-24-f5268148f5bf48b3a611 -> 3277 T1 /planned_causal_edges/233|CE-24-f5268148f5bf48b3a611 ca97b3c8c884
3278 T1 /causal_edges/285|CE-24-f56084236f6a5ad51fbd -> 3279 T1 /planned_causal_edges/285|CE-24-f56084236f6a5ad51fbd 3486d2d4c5f2
3280 T1 /causal_edges/19|CE-24-f5b25622e0da2ccc2e92 -> 3281 T1 /planned_causal_edges/19|CE-24-f5b25622e0da2ccc2e92 1f7deda77996
3282 T1 /causal_edges/307|CE-24-f6485ca6edae7ec7ce82 -> 3283 T1 /planned_causal_edges/307|CE-24-f6485ca6edae7ec7ce82 7666c6d6e733
3284 T1 /causal_edges/142|CE-24-f7d6fef592697a75f130 -> 3285 T1 /planned_causal_edges/142|CE-24-f7d6fef592697a75f130 0dd76b814113
3286 T1 /causal_edges/71|CE-24-f839faf47a10f1712481 -> 3287 T1 /planned_causal_edges/71|CE-24-f839faf47a10f1712481 bc72847c1999
3288 T1 /causal_edges/235|CE-24-fdd78b140452d3069161 -> 3289 T1 /planned_causal_edges/235|CE-24-fdd78b140452d3069161 f0720c80ccdb
3290 T1 /causal_edges/192|CE-24-fdda355b934edab22525 -> 3291 T1 /planned_causal_edges/192|CE-24-fdda355b934edab22525 a6afd0d3a38a
3292 T1 /causal_edges/256|CE-24-ffc86a3a50255a900150 -> 3293 T1 /planned_causal_edges/256|CE-24-ffc86a3a50255a900150 f7f3b3ea6997
3830 T1 /planned_proposition_registry/91|PROP-EVENT-STEP-0dea102b3c782457d437-RESULT -> 3831 T1 /proposition_registry/91|PROP-EVENT-STEP-0dea102b3c782457d437-RESULT 0d292a1d16b7
3832 T1 /planned_proposition_registry/104|PROP-EVENT-STEP-172d9162fd888ab62959-RESULT -> 3833 T1 /proposition_registry/104|PROP-EVENT-STEP-172d9162fd888ab62959-RESULT 32ea19acf1f0
3834 T1 /planned_proposition_registry/88|PROP-EVENT-STEP-18aebbec1eecc59a4ffe-RESULT -> 3835 T1 /proposition_registry/88|PROP-EVENT-STEP-18aebbec1eecc59a4ffe-RESULT 5f4fa89f551c
3836 T1 /planned_proposition_registry/69|PROP-EVENT-STEP-18b62bbcf77b4b5d79fe-RESULT -> 3837 T1 /proposition_registry/69|PROP-EVENT-STEP-18b62bbcf77b4b5d79fe-RESULT befd93fc4fff
3838 T1 /planned_proposition_registry/108|PROP-EVENT-STEP-1c909116fba24cef75a8-RESULT -> 3839 T1 /proposition_registry/108|PROP-EVENT-STEP-1c909116fba24cef75a8-RESULT 2b469b32ec6c
3840 T1 /planned_proposition_registry/118|PROP-EVENT-STEP-1fb4276e7018bac5ce44-RESULT -> 3841 T1 /proposition_registry/118|PROP-EVENT-STEP-1fb4276e7018bac5ce44-RESULT ebb610da7f4f
3842 T1 /planned_proposition_registry/109|PROP-EVENT-STEP-24a0a9ef678d045a3313-RESULT -> 3843 T1 /proposition_registry/109|PROP-EVENT-STEP-24a0a9ef678d045a3313-RESULT df2dd1d70eff
3844 T1 /planned_proposition_registry/123|PROP-EVENT-STEP-267760794761749d3045-RESULT -> 3845 T1 /proposition_registry/123|PROP-EVENT-STEP-267760794761749d3045-RESULT b0fcb95f143a
3846 T1 /planned_proposition_registry/70|PROP-EVENT-STEP-2acb731bc588bc784d1e-RESULT -> 3847 T1 /proposition_registry/70|PROP-EVENT-STEP-2acb731bc588bc784d1e-RESULT f586cd7c1ab5
3848 T1 /planned_proposition_registry/89|PROP-EVENT-STEP-2d78c15735417277a13f-RESULT -> 3849 T1 /proposition_registry/89|PROP-EVENT-STEP-2d78c15735417277a13f-RESULT d7bb7d8caea7
3850 T1 /planned_proposition_registry/106|PROP-EVENT-STEP-340dbd1efedf7adad59f-RESULT -> 3851 T1 /proposition_registry/106|PROP-EVENT-STEP-340dbd1efedf7adad59f-RESULT 0c01bd9acef3
3852 T1 /planned_proposition_registry/75|PROP-EVENT-STEP-348d44428b7e7637841a-RESULT -> 3853 T1 /proposition_registry/75|PROP-EVENT-STEP-348d44428b7e7637841a-RESULT 00de09e8b146
3854 T1 /planned_proposition_registry/78|PROP-EVENT-STEP-3525c6ddb5b970616fa5-RESULT -> 3855 T1 /proposition_registry/78|PROP-EVENT-STEP-3525c6ddb5b970616fa5-RESULT d792afc74613
3856 T1 /planned_proposition_registry/115|PROP-EVENT-STEP-35ebcbe1222c0470a9f8-RESULT -> 3857 T1 /proposition_registry/115|PROP-EVENT-STEP-35ebcbe1222c0470a9f8-RESULT 19f16267bb48
3858 T1 /planned_proposition_registry/110|PROP-EVENT-STEP-36eb7ed3b5e377c78643-RESULT -> 3859 T1 /proposition_registry/110|PROP-EVENT-STEP-36eb7ed3b5e377c78643-RESULT fd0a5e734872
3860 T1 /planned_proposition_registry/121|PROP-EVENT-STEP-3aced419f99dd434d34c-RESULT -> 3861 T1 /proposition_registry/121|PROP-EVENT-STEP-3aced419f99dd434d34c-RESULT 2073e15e278b
3862 T1 /planned_proposition_registry/152|PROP-EVENT-STEP-3b596fca920a5e0de634-RESULT -> 3863 T1 /proposition_registry/152|PROP-EVENT-STEP-3b596fca920a5e0de634-RESULT 287c033bf871
3864 T1 /planned_proposition_registry/127|PROP-EVENT-STEP-3d5f6d06fcf17d90e438-RESULT -> 3865 T1 /proposition_registry/127|PROP-EVENT-STEP-3d5f6d06fcf17d90e438-RESULT c3649f93ef25
3866 T1 /planned_proposition_registry/126|PROP-EVENT-STEP-3d981009cbe6bc28a097-RESULT -> 3867 T1 /proposition_registry/126|PROP-EVENT-STEP-3d981009cbe6bc28a097-RESULT 0f8b910cb6d6
3868 T1 /planned_proposition_registry/153|PROP-EVENT-STEP-3f6b3df08b98044336e2-RESULT -> 3869 T1 /proposition_registry/153|PROP-EVENT-STEP-3f6b3df08b98044336e2-RESULT fb9b1734fb29
3870 T1 /planned_proposition_registry/133|PROP-EVENT-STEP-40e217447db25248abaf-RESULT -> 3871 T1 /proposition_registry/133|PROP-EVENT-STEP-40e217447db25248abaf-RESULT 6a3b1abdb1c4
3872 T1 /planned_proposition_registry/96|PROP-EVENT-STEP-4f379e51a9275b670a94-RESULT -> 3873 T1 /proposition_registry/96|PROP-EVENT-STEP-4f379e51a9275b670a94-RESULT 31d606da2055
3874 T1 /planned_proposition_registry/93|PROP-EVENT-STEP-528f02a45822599b4af0-RESULT -> 3875 T1 /proposition_registry/93|PROP-EVENT-STEP-528f02a45822599b4af0-RESULT 2b4da15514f2
3876 T1 /planned_proposition_registry/143|PROP-EVENT-STEP-52c64e59ffd181ac3206-RESULT -> 3877 T1 /proposition_registry/143|PROP-EVENT-STEP-52c64e59ffd181ac3206-RESULT 509a5a82b247
3878 T1 /planned_proposition_registry/114|PROP-EVENT-STEP-56bf5263aa22d95e5a12-RESULT -> 3879 T1 /proposition_registry/114|PROP-EVENT-STEP-56bf5263aa22d95e5a12-RESULT c8149682294f
3880 T1 /planned_proposition_registry/158|PROP-EVENT-STEP-5953501ec9f6c35fd36a-RESULT -> 3881 T1 /proposition_registry/158|PROP-EVENT-STEP-5953501ec9f6c35fd36a-RESULT 19a3d6dbbb78
3882 T1 /planned_proposition_registry/80|PROP-EVENT-STEP-59dd960f59b63857d1ff-RESULT -> 3883 T1 /proposition_registry/80|PROP-EVENT-STEP-59dd960f59b63857d1ff-RESULT d75d28ad342d
3884 T1 /planned_proposition_registry/98|PROP-EVENT-STEP-5cad352f85015c3418fa-RESULT -> 3885 T1 /proposition_registry/98|PROP-EVENT-STEP-5cad352f85015c3418fa-RESULT 794d76ccdef8
3886 T1 /planned_proposition_registry/144|PROP-EVENT-STEP-5caef3977c7a95c2e4d9-RESULT -> 3887 T1 /proposition_registry/144|PROP-EVENT-STEP-5caef3977c7a95c2e4d9-RESULT e7ab590dfd44
3888 T1 /planned_proposition_registry/147|PROP-EVENT-STEP-60b2bbe7f340820a7006-RESULT -> 3889 T1 /proposition_registry/147|PROP-EVENT-STEP-60b2bbe7f340820a7006-RESULT 17579464f8b0
3890 T1 /planned_proposition_registry/73|PROP-EVENT-STEP-60f5388292936582d629-RESULT -> 3891 T1 /proposition_registry/73|PROP-EVENT-STEP-60f5388292936582d629-RESULT b126951b87bd
3892 T1 /planned_proposition_registry/155|PROP-EVENT-STEP-61bc434bc091129278fb-RESULT -> 3893 T1 /proposition_registry/155|PROP-EVENT-STEP-61bc434bc091129278fb-RESULT 349dfca25cbb
3894 T1 /planned_proposition_registry/132|PROP-EVENT-STEP-6591a6a12dd0cea3ca32-RESULT -> 3895 T1 /proposition_registry/132|PROP-EVENT-STEP-6591a6a12dd0cea3ca32-RESULT a5fbeb8c1b66
3896 T1 /planned_proposition_registry/129|PROP-EVENT-STEP-667133f35fe90022ef49-RESULT -> 3897 T1 /proposition_registry/129|PROP-EVENT-STEP-667133f35fe90022ef49-RESULT 0ab44c584977
3898 T1 /planned_proposition_registry/151|PROP-EVENT-STEP-66e82007060d60b70177-RESULT -> 3899 T1 /proposition_registry/151|PROP-EVENT-STEP-66e82007060d60b70177-RESULT fe0b1db0deda
3900 T1 /planned_proposition_registry/95|PROP-EVENT-STEP-675c6bac3834deeafdf0-RESULT -> 3901 T1 /proposition_registry/95|PROP-EVENT-STEP-675c6bac3834deeafdf0-RESULT ae92a4bcb9a0
3902 T1 /planned_proposition_registry/94|PROP-EVENT-STEP-6837f15ed80151533d3b-RESULT -> 3903 T1 /proposition_registry/94|PROP-EVENT-STEP-6837f15ed80151533d3b-RESULT 4d9f73eae6df
3904 T1 /planned_proposition_registry/83|PROP-EVENT-STEP-6b994de132cb9f6f9e4f-RESULT -> 3905 T1 /proposition_registry/83|PROP-EVENT-STEP-6b994de132cb9f6f9e4f-RESULT 7ac378cc4994
3906 T1 /planned_proposition_registry/131|PROP-EVENT-STEP-6d4523892a04ae529e2c-RESULT -> 3907 T1 /proposition_registry/131|PROP-EVENT-STEP-6d4523892a04ae529e2c-RESULT 281cb32e4052
3908 T1 /planned_proposition_registry/145|PROP-EVENT-STEP-6db789879ca1be9047f8-RESULT -> 3909 T1 /proposition_registry/145|PROP-EVENT-STEP-6db789879ca1be9047f8-RESULT 25224a034166
3910 T1 /planned_proposition_registry/71|PROP-EVENT-STEP-7318a405377f43454117-RESULT -> 3911 T1 /proposition_registry/71|PROP-EVENT-STEP-7318a405377f43454117-RESULT 24727b7d2f30
3912 T1 /planned_proposition_registry/128|PROP-EVENT-STEP-7629f324a08b084c61bb-RESULT -> 3913 T1 /proposition_registry/128|PROP-EVENT-STEP-7629f324a08b084c61bb-RESULT af644a362a2b
3914 T1 /planned_proposition_registry/136|PROP-EVENT-STEP-78380a3589d0413cd1fd-RESULT -> 3915 T1 /proposition_registry/136|PROP-EVENT-STEP-78380a3589d0413cd1fd-RESULT f7237d5c4b76
3916 T1 /planned_proposition_registry/87|PROP-EVENT-STEP-7d28d9844c23a20f52f3-RESULT -> 3917 T1 /proposition_registry/87|PROP-EVENT-STEP-7d28d9844c23a20f52f3-RESULT e477e5240a2a
3918 T1 /planned_proposition_registry/124|PROP-EVENT-STEP-85ffd0f519583479afd6-RESULT -> 3919 T1 /proposition_registry/124|PROP-EVENT-STEP-85ffd0f519583479afd6-RESULT 19e6043260b5
3920 T1 /planned_proposition_registry/107|PROP-EVENT-STEP-862ee99733eb95672009-RESULT -> 3921 T1 /proposition_registry/107|PROP-EVENT-STEP-862ee99733eb95672009-RESULT 451d03270de3
3922 T1 /planned_proposition_registry/76|PROP-EVENT-STEP-86a0a9868a8d5eb2135e-RESULT -> 3923 T1 /proposition_registry/76|PROP-EVENT-STEP-86a0a9868a8d5eb2135e-RESULT 5162c8d79d5d
3924 T1 /planned_proposition_registry/77|PROP-EVENT-STEP-86da0d601d1dc23cc70e-RESULT -> 3925 T1 /proposition_registry/77|PROP-EVENT-STEP-86da0d601d1dc23cc70e-RESULT 80e9dfb30910
3926 T1 /planned_proposition_registry/149|PROP-EVENT-STEP-8943220c367ad6872c38-RESULT -> 3927 T1 /proposition_registry/149|PROP-EVENT-STEP-8943220c367ad6872c38-RESULT 3d57992b52b2
3928 T1 /planned_proposition_registry/120|PROP-EVENT-STEP-8bee418690ec5353489e-RESULT -> 3929 T1 /proposition_registry/120|PROP-EVENT-STEP-8bee418690ec5353489e-RESULT 535d8502f001
3930 T1 /planned_proposition_registry/134|PROP-EVENT-STEP-8c31fe85a3464b7e76f6-RESULT -> 3931 T1 /proposition_registry/134|PROP-EVENT-STEP-8c31fe85a3464b7e76f6-RESULT dc944ecc067c
3932 T1 /planned_proposition_registry/156|PROP-EVENT-STEP-90ef8170b86f26ecdf76-RESULT -> 3933 T1 /proposition_registry/156|PROP-EVENT-STEP-90ef8170b86f26ecdf76-RESULT 0d25d8f4b4e0
3934 T1 /planned_proposition_registry/135|PROP-EVENT-STEP-9a112d7df56e03d943be-RESULT -> 3935 T1 /proposition_registry/135|PROP-EVENT-STEP-9a112d7df56e03d943be-RESULT b26141a0dab0
3936 T1 /planned_proposition_registry/99|PROP-EVENT-STEP-9cf62f7f13ad2232106a-RESULT -> 3937 T1 /proposition_registry/99|PROP-EVENT-STEP-9cf62f7f13ad2232106a-RESULT 5e911b8d8737
3938 T1 /planned_proposition_registry/113|PROP-EVENT-STEP-a34f348d62dcf1823019-RESULT -> 3939 T1 /proposition_registry/113|PROP-EVENT-STEP-a34f348d62dcf1823019-RESULT 0703bee9041e
3940 T1 /planned_proposition_registry/116|PROP-EVENT-STEP-acd32ff2eb8a5e8c28fd-RESULT -> 3941 T1 /proposition_registry/116|PROP-EVENT-STEP-acd32ff2eb8a5e8c28fd-RESULT 6d5cbd4e2c42
3942 T1 /planned_proposition_registry/68|PROP-EVENT-STEP-ad421c6949fe8b0d685e-RESULT -> 3943 T1 /proposition_registry/68|PROP-EVENT-STEP-ad421c6949fe8b0d685e-RESULT cb0fc2b67d9b
3944 T1 /planned_proposition_registry/137|PROP-EVENT-STEP-af4295924523a4c93a0a-RESULT -> 3945 T1 /proposition_registry/137|PROP-EVENT-STEP-af4295924523a4c93a0a-RESULT ab56a89ca8b6
3946 T1 /planned_proposition_registry/105|PROP-EVENT-STEP-b50cb2e8775246c032b5-RESULT -> 3947 T1 /proposition_registry/105|PROP-EVENT-STEP-b50cb2e8775246c032b5-RESULT 418af2343bd5
3948 T1 /planned_proposition_registry/102|PROP-EVENT-STEP-b61cbce869e9c5650a34-RESULT -> 3949 T1 /proposition_registry/102|PROP-EVENT-STEP-b61cbce869e9c5650a34-RESULT a63be7d673cb
3950 T1 /planned_proposition_registry/72|PROP-EVENT-STEP-b6776de65d2f0be9a982-RESULT -> 3951 T1 /proposition_registry/72|PROP-EVENT-STEP-b6776de65d2f0be9a982-RESULT 2a746308417c
3952 T1 /planned_proposition_registry/146|PROP-EVENT-STEP-b6f80226cf64474f2e7d-RESULT -> 3953 T1 /proposition_registry/146|PROP-EVENT-STEP-b6f80226cf64474f2e7d-RESULT 2229f9ae3e58
3954 T1 /planned_proposition_registry/84|PROP-EVENT-STEP-b909dcc178715efc5fc6-RESULT -> 3955 T1 /proposition_registry/84|PROP-EVENT-STEP-b909dcc178715efc5fc6-RESULT f0c61dc620a6
3956 T1 /planned_proposition_registry/148|PROP-EVENT-STEP-b9992dbd6cdee1ec1bac-RESULT -> 3957 T1 /proposition_registry/148|PROP-EVENT-STEP-b9992dbd6cdee1ec1bac-RESULT 74770ae0c863
3958 T1 /planned_proposition_registry/125|PROP-EVENT-STEP-bc7c911e823d7df35b3e-RESULT -> 3959 T1 /proposition_registry/125|PROP-EVENT-STEP-bc7c911e823d7df35b3e-RESULT fefd606b3578
3960 T1 /planned_proposition_registry/150|PROP-EVENT-STEP-bd40d2600545af70dd9b-RESULT -> 3961 T1 /proposition_registry/150|PROP-EVENT-STEP-bd40d2600545af70dd9b-RESULT 8d172b31c9fc
3962 T1 /planned_proposition_registry/157|PROP-EVENT-STEP-c203e4bc4e90ab18efaa-RESULT -> 3963 T1 /proposition_registry/157|PROP-EVENT-STEP-c203e4bc4e90ab18efaa-RESULT 3ae648eae148
3964 T1 /planned_proposition_registry/85|PROP-EVENT-STEP-c274b1d52af404fbdbfa-RESULT -> 3965 T1 /proposition_registry/85|PROP-EVENT-STEP-c274b1d52af404fbdbfa-RESULT 8efe4cdfe92f
3966 T1 /planned_proposition_registry/130|PROP-EVENT-STEP-c31e527d54eacd7127d4-RESULT -> 3967 T1 /proposition_registry/130|PROP-EVENT-STEP-c31e527d54eacd7127d4-RESULT 9f770fe95665
3968 T1 /planned_proposition_registry/141|PROP-EVENT-STEP-c5afd1674af1c9045e1d-RESULT -> 3969 T1 /proposition_registry/141|PROP-EVENT-STEP-c5afd1674af1c9045e1d-RESULT 40418cff0566
3970 T1 /planned_proposition_registry/103|PROP-EVENT-STEP-c6c280dced1e478ce79a-RESULT -> 3971 T1 /proposition_registry/103|PROP-EVENT-STEP-c6c280dced1e478ce79a-RESULT ffda95bea36c
3972 T1 /planned_proposition_registry/101|PROP-EVENT-STEP-c708fdd6cce3989e4b0f-RESULT -> 3973 T1 /proposition_registry/101|PROP-EVENT-STEP-c708fdd6cce3989e4b0f-RESULT 939824be80b2
3974 T1 /planned_proposition_registry/139|PROP-EVENT-STEP-cdb18e8fbc0c1e65134b-RESULT -> 3975 T1 /proposition_registry/139|PROP-EVENT-STEP-cdb18e8fbc0c1e65134b-RESULT 7b5e24bb211f
3976 T1 /planned_proposition_registry/82|PROP-EVENT-STEP-ce12466e16cfe543359f-RESULT -> 3977 T1 /proposition_registry/82|PROP-EVENT-STEP-ce12466e16cfe543359f-RESULT 37ddaee0bc5b
3978 T1 /planned_proposition_registry/119|PROP-EVENT-STEP-cf4084e153be1a9796a1-RESULT -> 3979 T1 /proposition_registry/119|PROP-EVENT-STEP-cf4084e153be1a9796a1-RESULT 0c1343e736c4
3980 T1 /planned_proposition_registry/122|PROP-EVENT-STEP-d7270a1895b1a560c356-RESULT -> 3981 T1 /proposition_registry/122|PROP-EVENT-STEP-d7270a1895b1a560c356-RESULT c0917e0cbb14
3982 T1 /planned_proposition_registry/81|PROP-EVENT-STEP-d7b09c8b2ceeb55be982-RESULT -> 3983 T1 /proposition_registry/81|PROP-EVENT-STEP-d7b09c8b2ceeb55be982-RESULT a5631b457105
3984 T1 /planned_proposition_registry/86|PROP-EVENT-STEP-da136f6b8e02013fc05c-RESULT -> 3985 T1 /proposition_registry/86|PROP-EVENT-STEP-da136f6b8e02013fc05c-RESULT caa895bc5bb9
3986 T1 /planned_proposition_registry/79|PROP-EVENT-STEP-da626c3fdd728a5c56f5-RESULT -> 3987 T1 /proposition_registry/79|PROP-EVENT-STEP-da626c3fdd728a5c56f5-RESULT f259738bb444
3988 T1 /planned_proposition_registry/142|PROP-EVENT-STEP-dc9b5d02dea6f315a4ea-RESULT -> 3989 T1 /proposition_registry/142|PROP-EVENT-STEP-dc9b5d02dea6f315a4ea-RESULT 8dee34264731
3990 T1 /planned_proposition_registry/117|PROP-EVENT-STEP-dfd3f15de89abf420a18-RESULT -> 3991 T1 /proposition_registry/117|PROP-EVENT-STEP-dfd3f15de89abf420a18-RESULT a8d9c8927412
3992 T1 /planned_proposition_registry/140|PROP-EVENT-STEP-e4431f2d35a4982a77ff-RESULT -> 3993 T1 /proposition_registry/140|PROP-EVENT-STEP-e4431f2d35a4982a77ff-RESULT 263252a0b255
3994 T1 /planned_proposition_registry/97|PROP-EVENT-STEP-e709dae2c547e750d87d-RESULT -> 3995 T1 /proposition_registry/97|PROP-EVENT-STEP-e709dae2c547e750d87d-RESULT 36eff59555d2
3996 T1 /planned_proposition_registry/92|PROP-EVENT-STEP-e9ffd5bcb79bea403ccd-RESULT -> 3997 T1 /proposition_registry/92|PROP-EVENT-STEP-e9ffd5bcb79bea403ccd-RESULT fb30a9d0a4c3
3998 T1 /planned_proposition_registry/138|PROP-EVENT-STEP-ead37a6af90b32844d25-RESULT -> 3999 T1 /proposition_registry/138|PROP-EVENT-STEP-ead37a6af90b32844d25-RESULT a025bfeba36d
4000 T1 /planned_proposition_registry/90|PROP-EVENT-STEP-f503e2ea34f9423279bc-RESULT -> 4001 T1 /proposition_registry/90|PROP-EVENT-STEP-f503e2ea34f9423279bc-RESULT 38b26c4ace13
4002 T1 /planned_proposition_registry/100|PROP-EVENT-STEP-f67bf1ee252017192f04-RESULT -> 4003 T1 /proposition_registry/100|PROP-EVENT-STEP-f67bf1ee252017192f04-RESULT 4394505088fa
4004 T1 /planned_proposition_registry/74|PROP-EVENT-STEP-f8e495926e62c726e27d-RESULT -> 4005 T1 /proposition_registry/74|PROP-EVENT-STEP-f8e495926e62c726e27d-RESULT 696ed69a76a7
4006 T1 /planned_proposition_registry/111|PROP-EVENT-STEP-fb16ee1ed24e0f1807ce-RESULT -> 4007 T1 /proposition_registry/111|PROP-EVENT-STEP-fb16ee1ed24e0f1807ce-RESULT fb56ee0571bb
4008 T1 /planned_proposition_registry/154|PROP-EVENT-STEP-fe4a98ada42ed625ec28-RESULT -> 4009 T1 /proposition_registry/154|PROP-EVENT-STEP-fe4a98ada42ed625ec28-RESULT be875057a8f8
4010 T1 /planned_proposition_registry/112|PROP-EVENT-STEP-ffc1d64571bf33c41599-RESULT -> 4011 T1 /proposition_registry/112|PROP-EVENT-STEP-ffc1d64571bf33c41599-RESULT a9dff3a9e973
4012 T1 /planned_proposition_registry/59|PROP-EVENT-TR-0acca264b0bcfb485802-RESULT -> 4013 T1 /proposition_registry/59|PROP-EVENT-TR-0acca264b0bcfb485802-RESULT 978e90f00c20
4014 T1 /planned_proposition_registry/63|PROP-EVENT-TR-0d8400f376e77cb9459d-RESULT -> 4015 T1 /proposition_registry/63|PROP-EVENT-TR-0d8400f376e77cb9459d-RESULT 433dc4bf0fdc
4016 T1 /planned_proposition_registry/47|PROP-EVENT-TR-132abd444312672ceefd-RESULT -> 4017 T1 /proposition_registry/47|PROP-EVENT-TR-132abd444312672ceefd-RESULT 6d13a58ddc31
4018 T1 /planned_proposition_registry/67|PROP-EVENT-TR-212f6dbe5f8660ba9836-RESULT -> 4019 T1 /proposition_registry/67|PROP-EVENT-TR-212f6dbe5f8660ba9836-RESULT 144da730a687
4020 T1 /planned_proposition_registry/46|PROP-EVENT-TR-27520ea47523f70c5646-RESULT -> 4021 T1 /proposition_registry/46|PROP-EVENT-TR-27520ea47523f70c5646-RESULT 3d84775c1250
4022 T1 /planned_proposition_registry/50|PROP-EVENT-TR-2f5c576913b75efdda18-RESULT -> 4023 T1 /proposition_registry/50|PROP-EVENT-TR-2f5c576913b75efdda18-RESULT f46cdb99748f
4024 T1 /planned_proposition_registry/48|PROP-EVENT-TR-3eee4f7b59eb78942eb1-RESULT -> 4025 T1 /proposition_registry/48|PROP-EVENT-TR-3eee4f7b59eb78942eb1-RESULT 01aebe685e87
4026 T1 /planned_proposition_registry/64|PROP-EVENT-TR-59d8b0c1e3772bb7d5d7-RESULT -> 4027 T1 /proposition_registry/64|PROP-EVENT-TR-59d8b0c1e3772bb7d5d7-RESULT 6d42835af227
4028 T1 /planned_proposition_registry/66|PROP-EVENT-TR-693e12301d1c9fa59213-RESULT -> 4029 T1 /proposition_registry/66|PROP-EVENT-TR-693e12301d1c9fa59213-RESULT 02463fb34a71
4030 T1 /planned_proposition_registry/52|PROP-EVENT-TR-69cd64d1defc993193a2-RESULT -> 4031 T1 /proposition_registry/52|PROP-EVENT-TR-69cd64d1defc993193a2-RESULT bdaa990f2e8f
4032 T1 /planned_proposition_registry/57|PROP-EVENT-TR-6b7bb71cd35c0bca67ef-RESULT -> 4033 T1 /proposition_registry/57|PROP-EVENT-TR-6b7bb71cd35c0bca67ef-RESULT 7199d04f4527
4034 T1 /planned_proposition_registry/56|PROP-EVENT-TR-7509cb258d2726497f64-RESULT -> 4035 T1 /proposition_registry/56|PROP-EVENT-TR-7509cb258d2726497f64-RESULT adbc6114c931
4036 T1 /planned_proposition_registry/53|PROP-EVENT-TR-7a97c808afdfdaacafb6-RESULT -> 4037 T1 /proposition_registry/53|PROP-EVENT-TR-7a97c808afdfdaacafb6-RESULT fbfd1f255487
4038 T1 /planned_proposition_registry/55|PROP-EVENT-TR-7d7f9d88a7ebac87a289-RESULT -> 4039 T1 /proposition_registry/55|PROP-EVENT-TR-7d7f9d88a7ebac87a289-RESULT 372f33c91cea
4040 T1 /planned_proposition_registry/49|PROP-EVENT-TR-9781a1e2b934a26a7081-RESULT -> 4041 T1 /proposition_registry/49|PROP-EVENT-TR-9781a1e2b934a26a7081-RESULT 9a9699447fa3
4042 T1 /planned_proposition_registry/58|PROP-EVENT-TR-a0e5ac90fc8c2801722e-RESULT -> 4043 T1 /proposition_registry/58|PROP-EVENT-TR-a0e5ac90fc8c2801722e-RESULT 069684c7ee93
4044 T1 /planned_proposition_registry/65|PROP-EVENT-TR-beaf2c53c216e85bb282-RESULT -> 4045 T1 /proposition_registry/65|PROP-EVENT-TR-beaf2c53c216e85bb282-RESULT 3352dc913f88
4046 T1 /planned_proposition_registry/61|PROP-EVENT-TR-c04d7ffd096945c557a3-RESULT -> 4047 T1 /proposition_registry/61|PROP-EVENT-TR-c04d7ffd096945c557a3-RESULT 8a5c170bc257
4048 T1 /planned_proposition_registry/54|PROP-EVENT-TR-cdcc30d2e25e8721a13e-RESULT -> 4049 T1 /proposition_registry/54|PROP-EVENT-TR-cdcc30d2e25e8721a13e-RESULT 02c5a844bd5e
4050 T1 /planned_proposition_registry/60|PROP-EVENT-TR-d49a684c43f2dfaed43a-RESULT -> 4051 T1 /proposition_registry/60|PROP-EVENT-TR-d49a684c43f2dfaed43a-RESULT ad7a21c3864f
4052 T1 /planned_proposition_registry/45|PROP-EVENT-TR-e596d43dc72e71f2ec96-RESULT -> 4053 T1 /proposition_registry/45|PROP-EVENT-TR-e596d43dc72e71f2ec96-RESULT 56f054e9466c
4054 T1 /planned_proposition_registry/62|PROP-EVENT-TR-f9c7135e7d5c5facf43e-RESULT -> 4055 T1 /proposition_registry/62|PROP-EVENT-TR-f9c7135e7d5c5facf43e-RESULT 3423dd006b92
4056 T1 /planned_proposition_registry/51|PROP-EVENT-TR-fa5164070e329ea9af36-RESULT -> 4057 T1 /proposition_registry/51|PROP-EVENT-TR-fa5164070e329ea9af36-RESULT 3d0932e125e5
4058 T1 /planned_proposition_registry/24|PROP-EVIDENCE-CLOSURE-04-RESULT -> 4059 T1 /proposition_registry/24|PROP-EVIDENCE-CLOSURE-04-RESULT e392fc6e2d5b
4060 T1 /planned_proposition_registry/25|PROP-EVIDENCE-CLOSURE-07-RESULT -> 4061 T1 /proposition_registry/25|PROP-EVIDENCE-CLOSURE-07-RESULT 9124d20dacdf
4062 T1 /planned_proposition_registry/26|PROP-EVIDENCE-CLOSURE-09-RESULT -> 4063 T1 /proposition_registry/26|PROP-EVIDENCE-CLOSURE-09-RESULT d87027164ac5
4064 T1 /planned_proposition_registry/27|PROP-EVIDENCE-CLOSURE-12-RESULT -> 4065 T1 /proposition_registry/27|PROP-EVIDENCE-CLOSURE-12-RESULT d563c626226d
4066 T1 /planned_proposition_registry/28|PROP-EVIDENCE-CLOSURE-15-RESULT -> 4067 T1 /proposition_registry/28|PROP-EVIDENCE-CLOSURE-15-RESULT e16b47afb102
4068 T1 /planned_proposition_registry/29|PROP-EVIDENCE-CLOSURE-18-RESULT -> 4069 T1 /proposition_registry/29|PROP-EVIDENCE-CLOSURE-18-RESULT 2f9fb31a523c
4070 T1 /planned_proposition_registry/34|PROP-FIRST-ACTION-INTEL -> 4071 T1 /proposition_registry/34|PROP-FIRST-ACTION-INTEL 284c712ddfa0
4072 T1 /planned_proposition_registry/31|PROP-GEOPOLITICAL-PRESSURE-11-RESULT -> 4073 T1 /proposition_registry/31|PROP-GEOPOLITICAL-PRESSURE-11-RESULT 1b550d3b0432
4074 T1 /planned_proposition_registry/32|PROP-GEOPOLITICAL-PRESSURE-15-RESULT -> 4075 T1 /proposition_registry/32|PROP-GEOPOLITICAL-PRESSURE-15-RESULT 776924243f9c
4076 T1 /planned_proposition_registry/0|PROP-GUHENG-PRECURSOR-01-RESULT -> 4077 T1 /proposition_registry/0|PROP-GUHENG-PRECURSOR-01-RESULT 32bd259a4eca
4078 T1 /planned_proposition_registry/1|PROP-GUHENG-PRECURSOR-07-RESULT -> 4079 T1 /proposition_registry/1|PROP-GUHENG-PRECURSOR-07-RESULT a12d235be491
4080 T1 /planned_proposition_registry/2|PROP-GUHENG-PRECURSOR-12-RESULT -> 4081 T1 /proposition_registry/2|PROP-GUHENG-PRECURSOR-12-RESULT e4cfb61cb823
4082 T1 /planned_proposition_registry/41|PROP-INIT-16cc8b81a704230f08 -> 4083 T1 /proposition_registry/41|PROP-INIT-16cc8b81a704230f08 f79e198cbda8
4084 T1 /planned_proposition_registry/40|PROP-INIT-68236446dc681d1b44 -> 4085 T1 /proposition_registry/40|PROP-INIT-68236446dc681d1b44 9394304dfe4e
4086 T1 /planned_proposition_registry/38|PROP-INIT-68e5b15fc7fbbc700d -> 4087 T1 /proposition_registry/38|PROP-INIT-68e5b15fc7fbbc700d ae3284cdd198
4088 T1 /planned_proposition_registry/44|PROP-INIT-8ab7f64bf706fc1138 -> 4089 T1 /proposition_registry/44|PROP-INIT-8ab7f64bf706fc1138 311b65b52dea
4090 T1 /planned_proposition_registry/36|PROP-INIT-932bcb4b83eafb2e0e -> 4091 T1 /proposition_registry/36|PROP-INIT-932bcb4b83eafb2e0e 767233118bda
4092 T1 /planned_proposition_registry/42|PROP-INIT-b0dbd851ac1fad50ac -> 4093 T1 /proposition_registry/42|PROP-INIT-b0dbd851ac1fad50ac 06d82d31cd15
4094 T1 /planned_proposition_registry/39|PROP-INIT-ce77612dabdc2a4d44 -> 4095 T1 /proposition_registry/39|PROP-INIT-ce77612dabdc2a4d44 e7c6877622fe
4096 T1 /planned_proposition_registry/37|PROP-INIT-edf91f71d659f383c4 -> 4097 T1 /proposition_registry/37|PROP-INIT-edf91f71d659f383c4 a847d1b29f22
4098 T1 /planned_proposition_registry/43|PROP-INIT-fe32330726251aedd1 -> 4099 T1 /proposition_registry/43|PROP-INIT-fe32330726251aedd1 9f0c036a56c9
4100 T1 /planned_proposition_registry/33|PROP-INITIAL-R07-SHENYU-MAIN -> 4101 T1 /proposition_registry/33|PROP-INITIAL-R07-SHENYU-MAIN 8ed96d538cb6
4102 T1 /planned_proposition_registry/30|PROP-INSTITUTIONAL-ETHICS-11-RESULT -> 4103 T1 /proposition_registry/30|PROP-INSTITUTIONAL-ETHICS-11-RESULT 96b87c297be0
4104 T1 /planned_proposition_registry/6|PROP-R07-SHENYU-MAIN-01-RESULT -> 4105 T1 /proposition_registry/6|PROP-R07-SHENYU-MAIN-01-RESULT 131a3889ec97
4106 T1 /planned_proposition_registry/7|PROP-R07-SHENYU-MAIN-02-RESULT -> 4107 T1 /proposition_registry/7|PROP-R07-SHENYU-MAIN-02-RESULT 47f0807664f6
4108 T1 /planned_proposition_registry/8|PROP-R07-SHENYU-MAIN-03-RESULT -> 4109 T1 /proposition_registry/8|PROP-R07-SHENYU-MAIN-03-RESULT 36ced1c3090e
4110 T1 /planned_proposition_registry/9|PROP-R07-SHENYU-MAIN-04-RESULT -> 4111 T1 /proposition_registry/9|PROP-R07-SHENYU-MAIN-04-RESULT de1cf9a91f27
4112 T1 /planned_proposition_registry/10|PROP-R07-SHENYU-MAIN-05-RESULT -> 4113 T1 /proposition_registry/10|PROP-R07-SHENYU-MAIN-05-RESULT 39b30c9c00c3
4114 T1 /planned_proposition_registry/11|PROP-R07-SHENYU-MAIN-06-RESULT -> 4115 T1 /proposition_registry/11|PROP-R07-SHENYU-MAIN-06-RESULT 5a2fdd255b65
4116 T1 /planned_proposition_registry/12|PROP-R07-SHENYU-MAIN-07-RESULT -> 4117 T1 /proposition_registry/12|PROP-R07-SHENYU-MAIN-07-RESULT 40409d990f57
4118 T1 /planned_proposition_registry/13|PROP-R07-SHENYU-MAIN-08-RESULT -> 4119 T1 /proposition_registry/13|PROP-R07-SHENYU-MAIN-08-RESULT dfa132e09330
4120 T1 /planned_proposition_registry/14|PROP-R07-SHENYU-MAIN-09-RESULT -> 4121 T1 /proposition_registry/14|PROP-R07-SHENYU-MAIN-09-RESULT 670b097d01c1
4122 T1 /planned_proposition_registry/15|PROP-R07-SHENYU-MAIN-10-RESULT -> 4123 T1 /proposition_registry/15|PROP-R07-SHENYU-MAIN-10-RESULT 97ea44bdc84b
4124 T1 /planned_proposition_registry/16|PROP-R07-SHENYU-MAIN-11-RESULT -> 4125 T1 /proposition_registry/16|PROP-R07-SHENYU-MAIN-11-RESULT a9eecb26c266
4126 T1 /planned_proposition_registry/17|PROP-R07-SHENYU-MAIN-12-RESULT -> 4127 T1 /proposition_registry/17|PROP-R07-SHENYU-MAIN-12-RESULT 229bd59ae760
4128 T1 /planned_proposition_registry/18|PROP-R07-SHENYU-MAIN-13-RESULT -> 4129 T1 /proposition_registry/18|PROP-R07-SHENYU-MAIN-13-RESULT 1e8e3fe5da21
4130 T1 /planned_proposition_registry/19|PROP-R07-SHENYU-MAIN-14-RESULT -> 4131 T1 /proposition_registry/19|PROP-R07-SHENYU-MAIN-14-RESULT ab23129c1c84
4132 T1 /planned_proposition_registry/20|PROP-R07-SHENYU-MAIN-15-RESULT -> 4133 T1 /proposition_registry/20|PROP-R07-SHENYU-MAIN-15-RESULT 9f2d7c1d6388
4134 T1 /planned_proposition_registry/21|PROP-R07-SHENYU-MAIN-16-RESULT -> 4135 T1 /proposition_registry/21|PROP-R07-SHENYU-MAIN-16-RESULT 3353e708347d
4136 T1 /planned_proposition_registry/22|PROP-R07-SHENYU-MAIN-17-RESULT -> 4137 T1 /proposition_registry/22|PROP-R07-SHENYU-MAIN-17-RESULT e4da38ae55b8
4138 T1 /planned_proposition_registry/23|PROP-R07-SHENYU-MAIN-18-RESULT -> 4139 T1 /proposition_registry/23|PROP-R07-SHENYU-MAIN-18-RESULT c87e49ae8a11
4140 T1 /planned_proposition_registry/35|PROP-R07-TERMINATION-DECISION -> 4141 T1 /proposition_registry/35|PROP-R07-TERMINATION-DECISION e6444bdfc8b2
4142 T1 /planned_proposition_registry/3|PROP-SHENYU-ACCEPTANCE-07-RESULT -> 4143 T1 /proposition_registry/3|PROP-SHENYU-ACCEPTANCE-07-RESULT 7d8c5dbacd8e
4144 T1 /planned_proposition_registry/4|PROP-SHENYU-ACCEPTANCE-12-RESULT -> 4145 T1 /proposition_registry/4|PROP-SHENYU-ACCEPTANCE-12-RESULT ea991d3b9c4b
4146 T1 /planned_proposition_registry/5|PROP-SHENYU-ACCEPTANCE-18-RESULT -> 4147 T1 /proposition_registry/5|PROP-SHENYU-ACCEPTANCE-18-RESULT 2094c9a0510c
```

## 9. 结构性观察清单（诚实登记，非断引用；均不修改 A3）

96 个 EVID 无 SC 可见入口（分布：B0×21、S1×1、C1×35、E1×24、W1×15；集中域 /relationships×23、/control_registry×21、/institutions×15）——这些条目仅经 drilldown_index 本身（D 层入口）可达：

```
| 索引 | id | 阶段 | 指针 | 源 |
| 2 | EVID-CURRENT-SRC-000002 | B0 | `/control_registry/1` | CAU-EMOTIONAL-SEPARATION |
| 4 | EVID-CURRENT-SRC-000004 | B0 | `/control_registry/3` | CAU-GLOBAL-SPINE |
| 7 | EVID-CURRENT-SRC-000007 | B0 | `/control_registry/6` | CAU-PRESERVED-OPEN |
| 8 | EVID-CURRENT-SRC-000008 | B0 | `/control_registry/7` | CAU-RESOLVED |
| 9 | EVID-CURRENT-SRC-000009 | B0 | `/control_registry/8` | CHR-BOUNDARIES |
| 11 | EVID-CURRENT-SRC-000011 | B0 | `/control_registry/10` | CHR-GU-HENG-MEMORY |
| 13 | EVID-CURRENT-SRC-000013 | B0 | `/control_registry/12` | CHR-RELATIONSHIP-EVOLUTION |
| 15 | EVID-CURRENT-SRC-000015 | B0 | `/control_registry/14` | CHR-SHEN-R07-CAUSALITY |
| 25 | EVID-CURRENT-SRC-000025 | B0 | `/control_registry/19` | INT-READER-QUESTIONS |
| 27 | EVID-CURRENT-SRC-000027 | B0 | `/control_registry/21` | INT-STORY-PROMISE |
| 31 | EVID-CURRENT-SRC-000031 | B0 | `/control_registry/25` | NAR-ENDING-PRESERVED-OPEN |
| 33 | EVID-CURRENT-SRC-000033 | B0 | `/control_registry/27` | NAR-FAIRNESS |
| 36 | EVID-CURRENT-SRC-000036 | B0 | `/control_registry/30` | NAR-R07-INFORMATION-BOUNDARY |
| 39 | EVID-CURRENT-SRC-000039 | B0 | `/control_registry/33` | SUB-DUAL-AGENCY |
| 45 | EVID-CURRENT-SRC-000045 | B0 | `/control_registry/39` | WLD-GEOPOLITICAL-PRESSURE |
| 46 | EVID-CURRENT-SRC-000046 | B0 | `/control_registry/40` | WLD-HANDOFF-BOUNDARY |
| 47 | EVID-CURRENT-SRC-000047 | B0 | `/control_registry/41` | WLD-INFORMATION-ETHICS |
| 48 | EVID-CURRENT-SRC-000048 | B0 | `/control_registry/42` | WLD-OPERATING-RULES |
| 49 | EVID-CURRENT-SRC-000049 | B0 | `/control_registry/43` | WLD-PREMISE |
| 50 | EVID-CURRENT-SRC-000050 | B0 | `/control_registry/44` | WLD-TERMINATION-CONTINUITY |
| 51 | EVID-CURRENT-SRC-000051 | B0 | `/control_registry/45` | WLD-THREAT-EVIDENCE-ACTION |
| 897 | EVID-CURRENT-SRC-000897 | C1 | `/storyline_cast_coverage/0` | COV-C1-SL-001 |
| 898 | EVID-CURRENT-SRC-000898 | C1 | `/storyline_cast_coverage/1` | COV-C1-SL-002 |
| 899 | EVID-CURRENT-SRC-000899 | C1 | `/storyline_cast_coverage/2` | COV-C1-SL-003 |
| 900 | EVID-CURRENT-SRC-000900 | C1 | `/storyline_cast_coverage/3` | COV-C1-SL-004 |
| 901 | EVID-CURRENT-SRC-000901 | C1 | `/storyline_cast_coverage/4` | COV-C1-SL-005 |
| 902 | EVID-CURRENT-SRC-000902 | C1 | `/storyline_cast_coverage/5` | COV-C1-SL-006 |
| 903 | EVID-CURRENT-SRC-000903 | C1 | `/storyline_cast_coverage/6` | COV-C1-SL-007 |
| 904 | EVID-CURRENT-SRC-000904 | C1 | `/storyline_cast_coverage/7` | COV-C1-SL-008 |
| 905 | EVID-CURRENT-SRC-000905 | C1 | `/storyline_cast_coverage/8` | COV-C1-SL-009 |
| 972 | EVID-CURRENT-SRC-000972 | C1 | `/open_items/0` | OPEN-C1-001 |
| 973 | EVID-CURRENT-SRC-000973 | C1 | `/open_items/1` | OPEN-C1-002 |
| 974 | EVID-CURRENT-SRC-000974 | C1 | `/open_items/2` | OPEN-C1-003 |
| 975 | EVID-CURRENT-SRC-000975 | C1 | `/relationships/20` | REL-CSTATE-DIPLO |
| 976 | EVID-CURRENT-SRC-000976 | C1 | `/relationships/21` | REL-DIPLO-MSTATE |
| 977 | EVID-CURRENT-SRC-000977 | C1 | `/relationships/11` | REL-GU-LIANG |
| 978 | EVID-CURRENT-SRC-000978 | C1 | `/relationships/10` | REL-GU-QIN |
| 979 | EVID-CURRENT-SRC-000979 | C1 | `/relationships/17` | REL-HE-DMITRI |
| 980 | EVID-CURRENT-SRC-000980 | C1 | `/relationships/18` | REL-ILYA-DMITRI |
| 981 | EVID-CURRENT-SRC-000981 | C1 | `/relationships/19` | REL-ILYA-MSTATE |
| 982 | EVID-CURRENT-SRC-000982 | C1 | `/relationships/15` | REL-LIANG-HE |
| 983 | EVID-CURRENT-SRC-000983 | C1 | `/relationships/16` | REL-LIANG-ILYA |
| 984 | EVID-CURRENT-SRC-000984 | C1 | `/relationships/14` | REL-QIN-CSTATE |
| 985 | EVID-CURRENT-SRC-000985 | C1 | `/relationships/12` | REL-QIN-LIANG |
| 986 | EVID-CURRENT-SRC-000986 | C1 | `/relationships/13` | REL-QIN-LUO |
| 987 | EVID-CURRENT-SRC-000987 | C1 | `/relationships/3` | REL-R07-CHENG |
| 988 | EVID-CURRENT-SRC-000988 | C1 | `/relationships/1` | REL-R07-GUHENG |
| 989 | EVID-CURRENT-SRC-000989 | C1 | `/relationships/4` | REL-R07-LUO |
| 990 | EVID-CURRENT-SRC-000990 | C1 | `/relationships/0` | REL-R07-SHENYU |
| 991 | EVID-CURRENT-SRC-000991 | C1 | `/relationships/5` | REL-R07-TANG |
| 992 | EVID-CURRENT-SRC-000992 | C1 | `/relationships/2` | REL-R07-ZHOULAN |
| 993 | EVID-CURRENT-SRC-000993 | C1 | `/relationships/9` | REL-SHEN-HE |
| 994 | EVID-CURRENT-SRC-000994 | C1 | `/relationships/7` | REL-SHEN-LUO |
| 995 | EVID-CURRENT-SRC-000995 | C1 | `/relationships/8` | REL-SHEN-TANG |
| 996 | EVID-CURRENT-SRC-000996 | C1 | `/relationships/6` | REL-SHEN-XU |
| 997 | EVID-CURRENT-SRC-000997 | C1 | `/relationships/22` | REL-TANG-FUTURE |
| 1078 | EVID-CURRENT-SRC-001078 | E1 | `/event_affordance_catalog/3` | AFF-BASE-INTAKE-GOVERNANCE |
| 1079 | EVID-CURRENT-SRC-001079 | E1 | `/event_affordance_catalog/10` | AFF-CM-LIAISON-CONFIRMATION |
| 1080 | EVID-CURRENT-SRC-001080 | E1 | `/event_affordance_catalog/9` | AFF-EVIDENCE-RESPONSE-HUB |
| 1081 | EVID-CURRENT-SRC-001081 | E1 | `/event_affordance_catalog/1` | AFF-FIELD-SOURCE-HANDOFF |
| 1082 | EVID-CURRENT-SRC-001082 | E1 | `/event_affordance_catalog/0` | AFF-GUHENG-MISSION-INCIDENT |
| 1083 | EVID-CURRENT-SRC-001083 | E1 | `/event_affordance_catalog/5` | AFF-HOSTAGE-RESCUE-TRANSFER |
| 1084 | EVID-CURRENT-SRC-001084 | E1 | `/event_affordance_catalog/7` | AFF-INDEPENDENT-EXPERT-LAB |
| 1085 | EVID-CURRENT-SRC-001085 | E1 | `/event_affordance_catalog/2` | AFF-MEMORY-READ-SEAL-LAB |
| 1086 | EVID-CURRENT-SRC-001086 | E1 | `/event_affordance_catalog/11` | AFF-POSTCRISIS-OPEN-ARCHIVE |
| 1087 | EVID-CURRENT-SRC-001087 | E1 | `/event_affordance_catalog/6` | AFF-PROTECTED-CONTACT-NODE |
| 1088 | EVID-CURRENT-SRC-001088 | E1 | `/event_affordance_catalog/4` | AFF-R07-ISOLATION-SUITE |
| 1089 | EVID-CURRENT-SRC-001089 | E1 | `/event_affordance_catalog/8` | AFF-REALITY-HARDWARE-CONTROL |
| 1450 | EVID-CURRENT-SRC-001450 | E1 | `/environments/3` | ENV-BASE-INTAKE-GOVERNANCE |
| 1451 | EVID-CURRENT-SRC-001451 | E1 | `/environments/10` | ENV-CM-LIAISON-CONFIRMATION |
| 1452 | EVID-CURRENT-SRC-001452 | E1 | `/environments/9` | ENV-EVIDENCE-RESPONSE-HUB |
| 1453 | EVID-CURRENT-SRC-001453 | E1 | `/environments/1` | ENV-FIELD-SOURCE-HANDOFF |
| 1454 | EVID-CURRENT-SRC-001454 | E1 | `/environments/0` | ENV-GUHENG-MISSION-INCIDENT |
| 1455 | EVID-CURRENT-SRC-001455 | E1 | `/environments/5` | ENV-HOSTAGE-RESCUE-TRANSFER |
| 1456 | EVID-CURRENT-SRC-001456 | E1 | `/environments/7` | ENV-INDEPENDENT-EXPERT-LAB |
| 1457 | EVID-CURRENT-SRC-001457 | E1 | `/environments/2` | ENV-MEMORY-READ-SEAL-LAB |
| 1458 | EVID-CURRENT-SRC-001458 | E1 | `/environments/11` | ENV-POSTCRISIS-OPEN-ARCHIVE |
| 1459 | EVID-CURRENT-SRC-001459 | E1 | `/environments/6` | ENV-PROTECTED-CONTACT-NODE |
| 1460 | EVID-CURRENT-SRC-001460 | E1 | `/environments/4` | ENV-R07-ISOLATION-SUITE |
| 1461 | EVID-CURRENT-SRC-001461 | E1 | `/environments/8` | ENV-REALITY-HARDWARE-CONTROL |
| 2431 | EVID-CURRENT-SRC-002431 | S1 | `/storylines/0` | SL-GUHENG-PRECURSOR |
| 4533 | EVID-CURRENT-SRC-004533 | W1 | `/institutions/11` | INST-CONSCIOUSNESS-SHUTDOWN |
| 4534 | EVID-CURRENT-SRC-004534 | W1 | `/institutions/7` | INST-EVIDENCE-VERIFICATION |
| 4535 | EVID-CURRENT-SRC-004535 | W1 | `/institutions/13` | INST-EXPERIMENTAL-STATUS |
| 4536 | EVID-CURRENT-SRC-004536 | W1 | `/institutions/9` | INST-GEO-CRISIS-RESPONSE |
| 4537 | EVID-CURRENT-SRC-004537 | W1 | `/institutions/6` | INST-HARDWARE-CONTROL-CUSTODY |
| 4538 | EVID-CURRENT-SRC-004538 | W1 | `/institutions/5` | INST-INDEPENDENT-EXPERT-REVIEW |
| 4539 | EVID-CURRENT-SRC-004539 | W1 | `/institutions/12` | INST-INFORMATION-ETHICS |
| 4540 | EVID-CURRENT-SRC-004540 | W1 | `/institutions/2` | INST-MEMORY-INPUT-CUSTODY |
| 4541 | EVID-CURRENT-SRC-004541 | W1 | `/institutions/1` | INST-PARTICIPATION-CONSENT |
| 4542 | EVID-CURRENT-SRC-004542 | W1 | `/institutions/0` | INST-PATH-AUTHORIZATION |
| 4543 | EVID-CURRENT-SRC-004543 | W1 | `/institutions/4` | INST-PROTECTED-CONTACT-ACCESS |
| 4544 | EVID-CURRENT-SRC-004544 | W1 | `/institutions/10` | INST-PUBLIC-CONFIRMATION |
| 4545 | EVID-CURRENT-SRC-004545 | W1 | `/institutions/3` | INST-R07-CARRIER-CUSTODY |
| 4546 | EVID-CURRENT-SRC-004546 | W1 | `/institutions/8` | INST-REALITY-EXECUTION |
| 4547 | EVID-CURRENT-SRC-004547 | W1 | `/institutions/14` | INST-WORLD-AUDIT-SINK |
```

20 条 SC 条目 `visible_element_ids` 非字典序（引用本身全部有效，仅排序不规范）：

```
| 源 | 原序(截断) |
| CHR-C-STATE-REP | MOD-CHAR-PROFILE-C-STATE-REP,EVID-CURRENT-SRC-000732 |
| CHR-CHENG-YUAN | MOD-CHAR-PROFILE-CHENG-YUAN,EVID-CURRENT-SRC-000733 |
| CHR-DIPLOMATIC-LIAISON | MOD-CHAR-PROFILE-DIPLOMATIC-LIAISON,EVID-CURRENT-SRC-000734 |
| CHR-DMITRI-VOLKOV | MOD-CHAR-PROFILE-DMITRI-VOLKOV,EVID-CURRENT-SRC-000735 |
| CHR-FUTURE-CUSTODIAN | MOD-CHAR-PROFILE-FUTURE-CUSTODIAN,EVID-CURRENT-SRC-000736 |
| CHR-GUHENG | MOD-CHAR-PROFILE-GUHENG,EVID-CURRENT-SRC-000737 |
| CHR-HE-WENJUN | MOD-CHAR-PROFILE-HE-WENJUN,EVID-CURRENT-SRC-000738 |
| CHR-ILYA-SAVIN | MOD-CHAR-PROFILE-ILYA-SAVIN,EVID-CURRENT-SRC-000739 |
| CHR-LIANG-CE | MOD-CHAR-PROFILE-LIANG-CE,EVID-CURRENT-SRC-000740 |
| CHR-LUO-JINGMING | MOD-CHAR-PROFILE-LUO-JINGMING,EVID-CURRENT-SRC-000741 |
| CHR-M-STATE-REP | MOD-CHAR-PROFILE-M-STATE-REP,EVID-CURRENT-SRC-000742 |
| CHR-QIN-ZHENG | MOD-CHAR-PROFILE-QIN-ZHENG,EVID-CURRENT-SRC-000743 |
| CHR-R07 | EVID-CURRENT-SRC-000012,MOD-CHAR-PROFILE-R07,EVID-CURRENT-SRC-000744 |
| CHR-SHEN-YU | EVID-CURRENT-SRC-000016,MOD-CHAR-PROFILE-SHEN-YU,EVID-CURRENT-SRC-000745 |
| CHR-TANG-LI | MOD-CHAR-PROFILE-TANG-LI,EVID-CURRENT-SRC-000746 |
| CHR-XU-MANQING | MOD-CHAR-PROFILE-XU-MANQING,EVID-CURRENT-SRC-000747 |
| CHR-ZHOULAN | MOD-CHAR-PROFILE-ZHOULAN,EVID-CURRENT-SRC-000748 |
| EV-TR-3d275aff39f35d69807d | EVID-CURRENT-SRC-003683,FRAG-DX-03,EVID-CURRENT-SRC-003684 |
| WLD-GEOPOLITICAL-PRESSURE | MOD-WORLD-DEFINITION,MOD-WORLD-CONSTRAINTS |
| WLD-INFORMATION-ETHICS | MOD-WORLD-DEFINITION,MOD-WORLD-CONSTRAINTS |
```

## 10. 未读清单与边界（ACC-F011 正确边界）

1. **P1 值体 4602 条**：DI 每条的 `value_sha256` 所指对象（P1 `stage-completion.json` 等）不在库（LEDGER §3-1、#7）。本表仅做哈希身份绑定（含 525 对同值复用判定），**不声称值体已读、不声称补出 P1 原值**。
2. 以上之外，三阵列库内字段**零未读**（V1–V10）。
3. 本表不修改 A3 任何字节；探针工作档案不入库（§1 复现映射即回读收据）。

## 11. 与其他交付的一致性

REPORT v3 §1.1/§11、LEDGER v3 §0-4/L25/§3-9 的 A3 覆盖声明均改写为与本表 §2 同文的口径；v2 的「三索引阵列全量机器审计＋EVID 分层抽样 78 条」表述按本表降级/升级为「库内字段语义全覆盖＋值体未读（#7）」。**v4（ACC-F015）**：REPORT v4 §1.1/§11、LEDGER v4 §0-4/n=7/§3-9 的覆盖闭合描述与本表 §2/§6/§6a 同步——EV 148 组＝同来源双入口、同值 0、非复用；525 真复用对不变；「SC 双入口＝§8 镜像」仅对 CE/PROP 成立。
