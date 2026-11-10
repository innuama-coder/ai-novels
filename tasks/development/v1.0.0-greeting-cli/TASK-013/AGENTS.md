# TASK-013 AGENTS.md

## 当前任务

实现并验收 H1-C V2 离线人审 HTML 生成器。

## 阅读顺序

1. `docs/ai-novel-workflow/conception-autonomous-workflow-v2.md` §11.4、§3.8—§3.9、§14—§15、§16 item 13
2. `skills/novel-conception-review-html-generator/SKILL.md`
3. `skills/novel-conception-review-html-generator/references/v2-html-contract.md`

## 工作边界

- 输入事实源只允许使用已验收 H1-A 报告。
- 必须调用正式 H1-A 组装验证器，不得 mock、复制或缩写生产验证。
- 页面只做确定性呈现，不改写、不补写、不推断、不摘要。
- 必须保持离线、无脚本、无表单、无外链、无作者决定副作用。
- 只允许 `assembled -> rendered`；H1 completion 与 `completed` 归 TASK-014。
- legacy 代码和测试必须隔离，不得成为 V2 准入或完成依据。

## 验证

```powershell
uv run --with jsonschema python -m unittest skills.novel-conception-review-html-generator.tests.test_v2_runtime
```

还必须运行 legacy HTML 隔离测试、V2 静态契约和相关 H1-A/H1-B 集成测试。

## 移交

移交生产文件、独立测试证据、文件 SHA、已验证 H1-C manifest 和 `rendered` 转换证据。不得宣称 root acceptance 或 H1 completion。
