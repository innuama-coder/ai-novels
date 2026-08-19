# HS1 design brief

## 要解决的问题

HS1 在 HA1 坐标中把全部权威故事线组织成一个可还原小说主体的多线网络。它不是“列出几条线”，而是为每个真实 storyline object 建立唯一 disposition、分段、unit/chapter placement、typed connection、汇合/分裂点和现有事件作用，使 HC1 能直接知道人物变化发生在哪条线、哪个单元和事件中。

## thinking skill 的 Agent 工作

Agent 首先只从 HB0 权威对象识别实际故事线，不能把 source index 行数当成线数。它要区分 mandatory、background、optional 和 preserved-open，逐线验证建立→发展→转折→兑现/开放结果。随后比较至少两个会改变 segment placement 或 connection function 的合法编排方案，并以因果、信息、情绪、主题、切换成本、读者定向和结局兑现为依据选择。

Agent 对已选网络的语义责任包括：主干连续；每条 placed line 有 segment；连接不是装饰线而有明确 function；optional melody 不因“丰富”被强制激活；subject reconstruction test 能用 storyline/segment/unit/event IDs 还原故事主体。`required_now` 必须在候选前阻断。

## 确定性 runtime 的责任

`scripts/run_skill.py` 验证 HS1/input gate 身份、`[HB0,HA1]` 拓扑、allowlist/HDD/evidence、稳定 HTS/HTC ID、authority/ownership 分离、register/disposition 集合一致、placed line 至少一个 segment、连接/汇合点引用完整、subject reconstruction verdict，以及 exact package/result envelope。它能发现 orphan placed line、未知 connection 和 forbidden `pov_assignment`，但不能证明 connection 在叙事上有意义、line 的情绪反差有效或主体重建真正准确；这些属于 Agent 证据与 HQ1。

## 边界

HS1 不创造新故事线事实或事件，不设计人物内在弧、POV、信息揭示、pacing、scene、dialogue 或 prose。`optional-not-activated` 是合法 disposition；不为固定线数扩写旋律线。不把后续角色/信息职责塞进 storyline 元素。

## 完成定义

P01 形成完整 connected network 和 HC1 可消费 formal result；N01 的 placed-without-segment 必须 revise，不能静默改 disposition；B01 必须同时保留 optional line 权威并拒绝 POV leakage。三个 case 的六维证据均达到 2/2 才构成当前实现验收。
