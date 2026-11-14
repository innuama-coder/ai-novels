# duanxian-audit3-impl-001 · 新 ISSUE 提交登记

- 作业：JOB #2382（duanxian-audit3-impl-001，R3 审视实施）
- 审计基线 BASE：`92573f1cca40f37cee04d2beb8708ff33ba603d6`；定义书 @ `024ef15a201a536592162b5f8442cf6a57699a8d`
- 输入快照：`.kunora/inputs/open-issues-snapshot-20261114b.md`（SHA-256 `f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90`）
- 提交规程：定义书 §5.1（POST 仅 title+body；201 判成功；逐条 GET 回读核对标题/标记/正文 SHA-256；标记格式 `<!-- duanxian-audit3-impl-001:DX3-Fnnn:base=<BASE> -->`）
- 提交时点实时核验：`GET /repos/innuama-coder/ai-novels/issues?state=all` 分页全量＝13 条、与冻结快照一致、无 PR、无第三方新增。

## 本次创建（编号 · 标题 · 链接）

| 编号 | ISSUE | 标题 | 链接 | 回读 |
|---|---|---|---|---|
| DX3-F001 | #14 | [断线审视] 多层设计产物的文档路径与引用在重构后失配（既有三条 ISSUE 范围外的路径漂移族） | https://github.com/innuama-coder/ai-novels/issues/14 | OK（SHA-256 一致） |
| DX3-F002 | #15 | [断线审视] 审阅简报 brief.html 版本链引用全失效、处于审阅真空并含已废止内容 | https://github.com/innuama-coder/ai-novels/issues/15 | OK |
| DX3-F003 | #16 | [断线审视] 主体定义 v1.1 残留旧终局口径而构思审计全 passed 未捕获 | https://github.com/innuama-coder/ai-novels/issues/16 | OK |
| DX3-F004 | #17 | [断线审视] HLD-04 与 HLD-07 对处置组是否掌握行动层情报的表述相反 | https://github.com/innuama-coder/ai-novels/issues/17 | OK |
| DX3-F005 | #18 | [断线审视] PRD 终包对 HLD 入口门状态自述矛盾（L34 与 L281 相反） | https://github.com/innuama-coder/ai-novels/issues/18 | OK |
| DX3-F006 | #19 | [断线审视] 历史层启动与归责口径同批准层「沈逾非启动者」存在未声明冲突族（G02） | https://github.com/innuama-coder/ai-novels/issues/19 | OK |
| DX3-F007 | #20 | [断线审视] 六月写作线素材与正文对同一事件的事实互斥未收敛（K1 传输/人数/面孔/载体/地点/匹配次数） | https://github.com/innuama-coder/ai-novels/issues/20 | OK |
| DX3-F008 | #21 | [断线审视] 批准报告控制条目残留早期迭代计数（「十个环境」vs 实际 12、「六个样章片段」vs 实际 3） | https://github.com/innuama-coder/ai-novels/issues/21 | OK |
| DX3-F009 | #22 | [断线审视] 构思工程脚本路径失配扩展至样片驱动器等三处（#1 同根因、其关闭范围之外） | https://github.com/innuama-coder/ai-novels/issues/22 | OK |

回读明细（正文 SHA-256，sent＝提交体，readback＝GET 回读体）与逐条结果见文末 JSON。9/9 成功、0 失败；每条含六要素（标记/BASE/编号/责任阶段/严重度、可证伪命题、应然实然证据、与 13 条差异、建议与关闭条件、采纳边界）。

## 既有 13 条引用（DEDUP 处置索引，零评论/零关闭/零编辑）

| 既有 | 主题 | R3 处置（详见 impl-001-report.md §5） |
|---|---|---|
| #1 (C-I01) | run.py 七路径＋三测试入口 | 复核属实并精确化（L41-48/L47 失败点/f7ac2db 半改）；不重复提交；范围外同族立 DX3-F009 |
| #2 (C-I02) | 81 vs 82 技能计数 | 实测 engine/skills=82，与 ISSUE 声明一致；无新证据 |
| #3 (C-I03) | 17 素材 LLD 迁移＋R07 章节引用 | 属实；全树文字命中本不在其关闭范围，新实例归 DX3-F001 |
| #4 (C-I04) | .gitattributes engine/ 前缀 | 属实；机制独立，无新载体 |
| #5 (C-I05) | HLD-TRACE-CLOSURE P1 | 补证（06 绑定错位/10 缺行/11 handoff 失衡/01 原子复用） |
| #6 (C-I06) | v2.0/v3.0 标签混用 | 补证（gate-report:9；canonical 六项实质差） |
| #7 (C-I07) | 三个机器包基名缺失 | 佐证（conception-runs 不入库；驱动器代际差异） |
| #8 (C2-I01) | 周岚维护例外参与链 | 补证（proposal 04:21/PRD FREEZE-12/subject:42-43/brief:282/design-task-package L93,97） |
| #9 (C2-I02) | R-07 当前视听 | 补证（PRD S15-16、design:90、tech:233、digital-realm:91、正文:245/255/271、shenyu:27、声音印随） |
| #10 (C2-I03) | 终局自行关闭＋提前披露 | 补证（proposal 04:25,58、PRD 05:26-28+INFO-06、LLD K9 族、design-scenes-draft） |
| #11 (C2-I04) | 十秒沉默来源 | 补证（正文:367 安全通信记录同族） |
| #12 (C2-I05) | 郑柏舟显名 | 补证（betrayer:44-47 记录区省略 vs 正文:365 点名） |
| #13 (C2-I06) | 完整可检索记忆 | 补证（PRD S11-12、proposal 04:23/09:20/12:20、LLD K8、PRD:38,98、视网膜重建） |

## 机器可读登记

```json
{
  "schema_version": "1.0",
  "job_ref": "duanxian-audit3-impl-001",
  "base_commit": "92573f1cca40f37cee04d2beb8708ff33ba603d6",
  "definition_commit": "024ef15a201a536592162b5f8442cf6a57699a8d",
  "snapshot_sha256": "f6cc9ddf44be3ee199c7993e0a37bc56813cb6be8b5e238da35a9f6ffeeffd90",
  "existing_references": [
    {"iid": "DEDUP-01", "issue": 1, "disposition": "recheck_confirmed_precised"},
    {"iid": "DEDUP-02", "issue": 2, "disposition": "recheck_confirmed"},
    {"iid": "DEDUP-03", "issue": 3, "disposition": "recheck_confirmed_scope_respected"},
    {"iid": "DEDUP-04", "issue": 4, "disposition": "recheck_confirmed"},
    {"iid": "DEDUP-05", "issue": 5, "disposition": "evidence_added"},
    {"iid": "DEDUP-06", "issue": 6, "disposition": "evidence_added"},
    {"iid": "DEDUP-07", "issue": 7, "disposition": "corroborated"},
    {"iid": "DEDUP-08", "issue": 8, "disposition": "evidence_added"},
    {"iid": "DEDUP-09", "issue": 9, "disposition": "evidence_added"},
    {"iid": "DEDUP-10", "issue": 10, "disposition": "evidence_added"},
    {"iid": "DEDUP-11", "issue": 11, "disposition": "evidence_added"},
    {"iid": "DEDUP-12", "issue": 12, "disposition": "evidence_added"},
    {"iid": "DEDUP-13", "issue": 13, "disposition": "evidence_added"}
  ],
  "candidates": [
    {"id": "DX3-F001", "verdict": "submit", "issue": 14},
    {"id": "DX3-F002", "verdict": "submit", "issue": 15},
    {"id": "DX3-F003", "verdict": "submit", "issue": 16},
    {"id": "DX3-F004", "verdict": "submit", "issue": 17},
    {"id": "DX3-F005", "verdict": "submit", "issue": 18},
    {"id": "DX3-F006", "verdict": "submit", "issue": 19},
    {"id": "DX3-F007", "verdict": "submit", "issue": 20},
    {"id": "DX3-F008", "verdict": "submit", "issue": 21},
    {"id": "DX3-F009", "verdict": "submit", "issue": 22},
    {"id": "REG-01", "verdict": "register_only", "subject": "OPEN-01~03 映射缺表（intake L21 有正文响应）"},
    {"id": "REG-02", "verdict": "register_only", "subject": "writer-qianxu 文件名歧义（#3 迁移表已缓解）"},
    {"id": "REG-03", "verdict": "register_only", "subject": "style-reference 模仿防护声明缺口＋字符损坏"},
    {"id": "REG-04", "verdict": "register_only", "subject": "V2 报告 L1613-1646 表格截断"},
    {"id": "REG-05", "verdict": "register_only", "subject": "A2/A0 revision-037/038 时序呈现"},
    {"id": "REG-06", "verdict": "register_only", "subject": "48 小时 vs 三个月进入时序张力（可相容）"},
    {"id": "REG-07", "verdict": "register_only", "subject": "素材-正文覆盖缺口＝正常未完成创作"},
    {"id": "REG-08", "verdict": "register_only", "subject": "PRD 09 风险检查零检出＋00↔09 断链（流程观察）"},
    {"id": "REJ-01", "verdict": "rejected_after_recheck", "subject": "PRD FREEZE-05/10 与 G05/G08 冲突（亲验后判兼容）"},
    {"id": "REJ-02", "verdict": "rejected_after_recheck", "subject": "proposal 12-ending 封死未来重载（实为建议级）"}
  ],
  "created": [
    {"iid": "DX3-F001", "number": 14, "url": "https://github.com/innuama-coder/ai-novels/issues/14", "readback_ok": true, "body_sha256_sent": "5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28", "body_sha256_readback": "5fb154303e9e1d576e746c1cf2bdf0f836d4caad749a01b4fe18bb73f0cb2d28"},
    {"iid": "DX3-F002", "number": 15, "url": "https://github.com/innuama-coder/ai-novels/issues/15", "readback_ok": true, "body_sha256_sent": "7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc", "body_sha256_readback": "7581445b5ab13913ec59aa2859915cbad7f9de3a5dc5caa336a50de4787073cc"},
    {"iid": "DX3-F003", "number": 16, "url": "https://github.com/innuama-coder/ai-novels/issues/16", "readback_ok": true, "body_sha256_sent": "c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300", "body_sha256_readback": "c43c926d355ea5a4c1ce9b088cec9b3a14f4c66684baa1a0124ae7c772291300"},
    {"iid": "DX3-F004", "number": 17, "url": "https://github.com/innuama-coder/ai-novels/issues/17", "readback_ok": true, "body_sha256_sent": "ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93", "body_sha256_readback": "ddae703bfc11bf45f5631a21290430a4d9efc8507830b9c2e97e7eb6cd5e4e93"},
    {"iid": "DX3-F005", "number": 18, "url": "https://github.com/innuama-coder/ai-novels/issues/18", "readback_ok": true, "body_sha256_sent": "34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4", "body_sha256_readback": "34c9ec64c3f1aaa8d1cce96566caa4f857d5c400649826b2b415699fee6ea9b4"},
    {"iid": "DX3-F006", "number": 19, "url": "https://github.com/innuama-coder/ai-novels/issues/19", "readback_ok": true, "body_sha256_sent": "8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0", "body_sha256_readback": "8521063d9fa73ad6e338cfbcf3749da1de54dfc0dab69bc77ad5e304a88cf5d0"},
    {"iid": "DX3-F007", "number": 20, "url": "https://github.com/innuama-coder/ai-novels/issues/20", "readback_ok": true, "body_sha256_sent": "eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f", "body_sha256_readback": "eea29d09a5e19aaa994ab967e7206b98658da590c514f8920b709470543b5a9f"},
    {"iid": "DX3-F008", "number": 21, "url": "https://github.com/innuama-coder/ai-novels/issues/21", "readback_ok": true, "body_sha256_sent": "c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b", "body_sha256_readback": "c10b62c7d1933001565ee9c6676770dd2eacd9b89f04cf29d720e829a34e773b"},
    {"iid": "DX3-F009", "number": 22, "url": "https://github.com/innuama-coder/ai-novels/issues/22", "readback_ok": true, "body_sha256_sent": "186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f", "body_sha256_readback": "186d0bd68319530e46757729e7feaaac661d2b988a6284129f510435add6457f"}
  ],
  "failures": []
}
```

注：`body_sha256_sent`/`body_sha256_readback` 为提交体与 GET 回读体的 SHA-256，九条两两一致（readback_ok 全 true）。
