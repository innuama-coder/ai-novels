# TASK-003: 实现 B0 基线封装、事实门与完成判定

## 目标

实现 B0 基线封装、事实门与完成判定，并以可运行制品、自动验证和可追溯 handoff 作为完成证据。

## 来源

- engine/docs/ai-novel-workflow/conception-autonomous-workflow-v2.md §3.7, §3.3-§3.6, §13-§15, §16 item 3

## 输入

- 冻结的 source interview run-state
- I0–I5 六个 ready completion 及其六份 canonical 设计原文
- V1 completion 及其绑定的 fact-dependency-register
- V2 completion 与当前、唯一、绑定本次 V2 的 approved 作者记录
- TASK-001/002 正式运行时

## 交付

- harnesses/novel-conception-autonomous/runtime/baseline.py
- harnesses/novel-conception-autonomous/runtime/b0_completion.py
- harnesses/novel-conception-autonomous/tests/test_baseline.py

## Allowed scope

- 无损封装 B0，按原文稳定 control ID 建立锁定项/开放项/证据锚点，执行事实门、manifest 与 completion

## Forbidden scope

- 不补写故事内容
- 不把访谈推断升级为锁定事实
- 不发明原文不存在的 control ID、fact adoption 或批准记录
- 不允许仅凭文件存在判完成

## Acceptance

- 每个锁定事实可追溯到批准来源
- 冲突事实、缺失证据和未批准简报均硬阻断
- B0 completion 同时校验语义状态、制品、hash、manifest 和 run-state

## Verification

- python -m unittest harnesses.novel-conception-autonomous.tests.test_baseline
- 用批准、未批准、冲突、篡改四组 fixture 验证

## Stop conditions

- 缺少已批准访谈制品或无法确定来源优先级
- 缺少 fact-dependency-register、原文稳定 control ID 或结构性事实仍未采用
- 事实门发现需作者裁决的实质冲突

## Handoff

- 向 S1 提供唯一合法 B0 输入包与完成收据
