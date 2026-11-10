# TASK-013：实现 H1-C 人审 HTML 生成

## 职责

实现 `engine/skills/novel-conception-review-html-generator/` 的 V2 生产能力：把已正式验收的 H1-A 组装报告确定性渲染为离线人审 HTML，验收完整呈现包，并将 H1 工作区仅从 `assembled` 推进到 `rendered`。

H1 阶段完成与 completion 归 TASK-014；本任务不得生成或声明 completion。

## 权威来源

- `engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md` §11.4、§3.8—§3.9、§14—§15、§16 item 13
- `engine/skills/novel-conception-review-html-generator/SKILL.md`
- `engine/skills/novel-conception-review-html-generator/references/v2-html-contract.md`

## 硬输入

- 已完成的 P1 包。
- H1-A 规划包、规划输入门、规划期 active return（如有）和规划所用 `initialized` 工作区。
- H1-B 片段包和片段生成所用 `planned` 工作区。
- H1-A 组装包和组装所用 `fragments_ready` 工作区。
- 当前密封的 `assembled` 工作区及 H1 coordinator。

## 交付

- `engine/skills/novel-conception-review-html-generator/scripts/run_v2.py`
- `engine/skills/novel-conception-review-html-generator/references/v2-html-contract.md`
- `engine/skills/novel-conception-review-html-generator/tests/test_v2_runtime.py`
- 必要的技能说明与本任务边界文档

## 允许范围

- 单文件 UTF-8 离线 HTML、内联 SVG、文字等价物、CSP、访问性、回流与打印。
- 正式上游链重验、当前 assembled 状态校验、TOCTOU、实现快照、manifest 和原子发布。
- coordinator 仅接受 `assembled -> rendered`。

## 禁止范围

- 修改、补写、摘要或推断小说构思内容。
- 以 NLP、关键词猜测或 P1 反向推断替代 H1-A 报告模型。
- 使用 legacy completion 或 legacy validator 作为 V2 准入依据。
- 脚本、表单、外链、下载、存储、网络、预选作者决定。
- 生成 `stage-completion.json`、推进到 `completed` 或承担 TASK-014。

## 验收

- 正式调用 H1-A `validate_assembly_package`，且失败必须向上游传播。
- 标题、五步评审路径、世界/故事线/角色/片段/决策内容完整、默认可见。
- 五类固定语义 SVG 逐值绑定图模型，并有相邻文字等价物。
- 重渲染字节一致；record、validation、manifest、实现快照和输入血缘精确。
- XSS、跨 session、上游篡改、状态跳跃、TOCTOU 和 completion 越权均被拒绝。
- 成功时 coordinator 只调用一次，目标状态仅为 `rendered`。

## 验证

```powershell
uv run --with jsonschema python -m unittest skills.novel-conception-review-html-generator.tests.test_v2_runtime
```

同时运行 legacy HTML 隔离测试、V2 静态契约测试及相关 H1-A/H1-B 集成测试。

## 停止条件

- 任一正式上游包或工作区未就绪、血缘不一致或发生变化。
- 呈现要求需要修改上游控制信息。
- 请求扩大为 H1 completion 或作者决定。

## 移交

向 TASK-014 移交已验证 H1-C package manifest 与 coordinator 返回的 `rendered` 工作区；不移交或伪造 completion。
