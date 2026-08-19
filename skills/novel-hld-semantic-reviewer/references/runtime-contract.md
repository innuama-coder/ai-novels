# HQ1 输入、输出与运行契约

## 调度器入口

协调器必须读取 `runtime-contract.json.public_entrypoint`，不得猜测脚本名。当前唯一入口是：

```powershell
python skills/novel-hld-semantic-reviewer/scripts/run_skill.py <work-order.json> <draft-directory>
```

`implementation_closure.ordered_files` 是实现 hash 的完整有序闭包；算法为 `sha256-basename-nul-content-nul-v1`。入口、契约、canonical schema、六个上游 canonical schema、共享设计运行时和 HQ1 运行时全部纳入 hash。

## 输入

精确上游顺序为 `[HB0, HA1, HS1, HC1, HI1, HR1, HK1]`。work order、input gate、run state、ArtifactReference 顺序、run/revision、manifest/completion/validation/main hash 和 package profile 必须全部通过公共 SchemaCatalog 与 envelope 校验。

语义读取集合必须精确等于：source index 中授权 HQ1 的原始值，以及 HB0 与 HA1–HK1 的 main、manifest、completion、deterministic validation。generation evidence、execution、自评、草案和后续阶段文件都不在读取闭包内。

## Agent 草稿

- `canonical.json`：符合 `hq1-semantic-review.schema.json` 的闭合审查。
- `review-session.json`：符合公共 `hq1-review-session.schema.json`，记录独立任务身份和精确实际读取集合。

## 结果

- `ready`：发布 HQ1 公共 ready profile、completion 和外置 `stage-result.json`。
- `revise/local_candidate`：仅审查草稿或证据错误；不发布 canonical。
- `blocked/upstream_defect`：生产阶段 canonical 必须修正。
- `blocked/author_required`：需要作者作出当前必需决定。
- `blocked/reality_dependency`：需要外部事实或专业核验。
- 输入准入失败返回 3，且不发布结果包。

blocked 结果只携带 finding IDs、affected IDs 与原因。owner、target skill、reopen point 和 invalidated suffix 由 Router 根据注册表计算。

## 原子性

运行时只在同级 staging 目录组装结果；closed-schema、manifest、completion 和 result 全部复验后才重命名发布。任何失败都不得留下可误认成 ready 的 canonical。
