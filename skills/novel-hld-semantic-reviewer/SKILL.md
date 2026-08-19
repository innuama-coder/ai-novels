---
name: novel-hld-semantic-reviewer
description: 独立审查小说 HLD 的完整性、一致性、因果与现实可行性。仅在 novel-hld-autonomous 的 HQ1 阶段使用；读取 HB0 与 HA1–HK1 已验收公共包，输出证据绑定的审查结论，不修改上游 HLD，也不决定返工路由。
---

# 小说 HLD 独立语义审查

开始前完整阅读：

- [运行契约](references/runtime-contract.md)
- [执行 SOP](references/sop.md)
- [审查方法](references/methodology.md)
- [语义量表](references/semantic-rubric.md)

方法依据见 [研究来源](references/sources.md)。

## 唯一职责

独立重读 HB0 与 HA1–HK1 的正式交付，判断这套 HLD 是否完整、自洽、可信、可开发，并形成 `hld-semantic-review.json`。本技能验证设计，不替生产技能重写设计。

## 硬边界

- 只读取 work order 和 input gate 明确授权且 hash 匹配的文件。
- 不读取生产 Agent 的思考过程、generation evidence、自评、聊天记录、HP1/HQ2、LLD 或人审材料。
- finding 只记录缺陷来源、受影响对象、违反契约和修正条件；不得填写 owner、target skill、reopen stage 或失效后缀。最终路由属于 Router。
- 不因个人偏好、市场判断或固定三幕/五幕模板判失败。
- `required_now` 必须在 verdict 前阻断；存在 actionable finding 时不得 ready。

## Agent 草稿

在独立草稿目录生成：

```text
canonical.json
review-session.json
```

随后调用机器入口：

```powershell
python skills/novel-hld-semantic-reviewer/scripts/run_skill.py <work-order.json> <draft-directory>
```

退出码：`0=ready`，`2=revise 或 blocked`，`3=输入准入失败且不产生可提交结果`。

## Ready 条件

- 六个生产阶段的全部 canonical HLD 对象都有可解析到原值的证据。
- 六个领域检查、四个跨域检查、八类反证挑战均闭合。
- quality HDD 与 work order projection 精确一致，且不存在 required-now 项。
- findings 为空；每个适用检查都有独立 pass claim。
- review task 与所有 producer task 身份隔离，实际语义读取集合与授权闭包完全一致。
