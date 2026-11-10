# TASK-014：实现 H1 完成、作者决定与最终构思完成

## 目标

实现 H1 顶层完成、外部作者决定三分支和唯一开发准入，保持所有包、状态与哈希属于同一当前 run。

## 权威输入

- `engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md` §12–§15、§16 第 14 项。
- `contracts/autonomous-v2` 中的 stage completion、author decision、return request、run-state、workspace、manifest、development handoff 与 conception completion schema。
- 当前 P1 completion、rendered H1 workspace、H1-A/B/C 正式包和 autonomous run-state。

## 交付

- `runtime/h1_completion.py`
- `runtime/author_decision.py`
- `runtime/final_completion.py`
- coordinator 与 return router 的最小状态转换支持
- 独立测试角色维护的 `tests/test_final_completion.py`

## 职责与边界

- H1 completion 只把同 session 的 rendered H1 正式链提升为唯一顶层 H1 completion。
- 作者决定只接受调用方提供的外部 sealed `approved / revise / rejected` 事件，不生成、默认或解释作者意图。
- `revise` 只生成确定性 author-origin return；跨 owner 或跨恢复点必须拆分。
- `approved` 才可生成最终 completion 并把 development status 推进为 ready。
- `rejected` 终止当前 run；不得生成 return、最终 completion 或开发准入。
- 不改写 P1/H1 内容，不让 HTML 技能承担作者决定或 H1 completion。

## 硬验收

- 所有正式输入通过 schema、文件哈希、manifest、run/session/current 与拓扑重验。
- 使用 staging、自验、输入 TOCTOU 复查、原子发布、目的地复验、coordinator 接受的固定顺序。
- coordinator 拒绝时，已发布包只能保留为 valid non-current orphan。
- 精确重放幂等；同键异体冲突；active/stale/cross-run 全部 fail closed。
- 最终 completion 精确绑定 B0、S1、W1、E1、T1、C1、Q1、P1、H1 九个当前 completion、当前批准、P1/H1 HTML 与 development handoff。

## 验证

```text
python -m unittest harnesses.novel-conception-autonomous.tests.test_final_completion
python -m unittest harnesses.novel-conception-autonomous.tests.test_contract_runtime harnesses.novel-conception-autonomous.tests.test_coordinator
```

本任务开发完成不等于验收；独立测试与 root 验收通过后才能移交 TASK-015。
