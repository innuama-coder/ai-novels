# TASK-013 Prompt

## 执行目标

完成 H1-C V2：把 H1-A 已验收的 `human-review-report.json` 确定性渲染为离线、可访问、可打印的单文件 HTML；完整验收呈现包后，只将 H1 工作区从 `assembled` 推进到 `rendered`。

## 范围

允许：

- HTML/SVG 忠实投影、文字等价物、安全、访问性、回流、打印。
- 正式上游链重验、状态与血缘校验、TOCTOU、实现快照、manifest、原子发布。
- 一次 `assembled -> rendered` coordinator 转换。

禁止：

- 改写、补充、摘要或推断构思内容。
- 从 P1 反向生成页面内容，或以 NLP/关键词猜测关系。
- 使用 legacy completion 作为 V2 依据。
- 脚本、表单、外链、网络、存储、下载和作者决定预选。
- 生成 H1 completion、推进到 `completed` 或执行 TASK-014。

## 验收

- 正式调用 H1-A 组装包验证器并传递失败。
- 标题与唯一 H1 精确一致，五步路径和五部分默认可见。
- 五类语义图形、全部图值、方向、来源和相邻文字等价物完整。
- 输出确定、离线、安全、可访问、可回流、可打印。
- 包、记录、manifest、实现快照、输入血缘和状态转换精确。

## 验证

```powershell
uv run --with jsonschema python -m unittest skills.novel-conception-review-html-generator.tests.test_v2_runtime
```

并执行 legacy 隔离测试、V2 静态契约及 H1-A/H1-B 相关集成。

## 决策原则

V2 契约优先。输入、状态、来源或边界不满足时必须失败关闭；不得以视觉修补掩盖内容或血缘问题。
