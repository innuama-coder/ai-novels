# TASK-015 CLAUDE.md

## Karpathy Context Engineering

Keep the current task source-backed and auditable.

## Required Reading

- docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §2, §13-§16
- docs/ai-novel-workflow/conception-orchestration.md

## Current task

组装自主构思主 Harness、适配器与发布验证。固定入口为 rendered H1 →
formal H1 completion → external author decision → approved-only final。

## Constraints

- 不复制领域逻辑到 orchestration
- 不保留 D1/R1 作为 V2 成功路径
- 不以文档声明替代可运行调用
- 不 patch H1 validators；不得由 Agent 生成作者决定
- revise/rejected 永不发布 final completion

## Verification

- uv run --offline --with-requirements harnesses/novel-conception-autonomous/requirements.txt python harnesses/novel-conception-autonomous/validators/validate_harness.py
- 运行全体单元/契约测试并检查发布包清单

## Final Response

Provide paths, acceptance evidence, Verification results, blockers, and Handoff artifacts.
