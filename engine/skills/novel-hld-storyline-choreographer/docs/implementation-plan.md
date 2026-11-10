# HS1 implementation plan and realized design

## 1. 上游坐标准入（已实现）

Runtime/skill contract 固定 HS1 owner、`[HB0,HA1]` 顺序、HA1 registered role、allowlist 和 HDD 前置。HS1 不能绕过 completion 直接使用旧坐标，也不能读取质量域、聊天或呈现稿。

## 2. Agent 编排算法（已实现为指令与 evidence contract）

Agent 从 authority object values 建立 semantic register，逐线测试建立/发展/转折/兑现，再比较实际改变 placement/connection 的候选。选择后投影 segments、unit matrix、typed connections、convergence/split、event placement 和唯一 activation disposition，最后执行 removal/duplication/disconnection/starvation/overinflation/premature-resolution attacks，并形成 subject reconstruction。

五份 generation evidence 将 dependency、obligation、option、projection 和 adversarial review 分开，避免 runtime 根据字段数量伪造“编排完成”。

## 3. 确定性验证与封装（已实现）

公共 runtime 验证 work order/input gate/read/evidence/authority/IDs/package。HS1 分支额外验证 register ID 唯一、activation disposition 对 register 全覆盖且仅四种值、每条 placed line 在 segments 中出现、convergence/split 引用已知 connection、subject reconstruction verdict=pass。Forbidden key walker 拒绝 POV、pacing、inner arc、scene/prose 等越界。

合法候选生成 exact ready package；orphan、边界或 malformed candidate 生成 revise/local_candidate；`required_now` 在候选前生成 blocked/author_required。脚本不选 storyline、不解释 connection、不写 router/run-state。

## 4. 验收实现（已完成）

P01 测 connected ready；N01 注入第二 placed line 无 segment；B01 注入 `pov_assignment`。Fixture manifest 保护 sealed hash；acceptance evidence 将自动 set/reference 检查和语义 line-motion/ownership 依据分开。

## 5. 保留的系统边界

人物选择与关系变化交给 HC1，POV/knowledge/reveal 交给 HI1，节奏交给 HR1，场景功能交给 HK1。未来若需要更多旋律线，应由权威输入提供或保持 optional/open，不能修改 runtime 让 HS1 自动发明。
