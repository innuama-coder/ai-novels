# 方法论

## 两次隔离，而不是一次自证

可消费性和忠实度是不同问题。consumer-driven contract 要先暴露消费者真正依赖的内容，因此 `consumer_test` 只看 handoff；随后由新任务把封存结果与正式 HLD 对照。分离上下文可避免“看过答案后重建”的确认偏差。

## 可消费性标准

LLD 执行者必须从每个 LWK 明确得到：工作目的、进入/退出状态、依赖、故事线/角色/场景/事件/POV/知识边界、必须保留的控制信息、允许细化的空间、禁止事项和验收锚点。还必须逐章得到章名、该章要讲清的核心内容、主要/辅助/背景/开放故事线，以及章末发生的变化。只要仍需猜测章节用途、故事线归属，或会改变故事主体的内容，就不得 pass。

章节设计必须完整覆盖架构中的全部章节，并与工作单元和故事线放置一致；同时不得越界到分场、对白、感官细节和具体叙述视角。前者缺失属于不可消费，后者过度规定会剥夺详细设计应有的空间，两者都不能通过。

## 忠实度标准

以稳定 ID 建立双向追溯：每个 source LWR 恰好映射到 LWK，每个 LWK 只来自声明的 LWR。逐项核对 obligation 与分类，特别寻找四类漂移：遗漏、擅自增强、弱化、重新分类。数量相等不能代替对象级证据。

## 证据标准

结构正确由 schema 证明；内容结论必须由已签名文件中的对象 ID 与 JSON Pointer 证明。六个维度必须都有对象级证据：provenance、semantic_fit、instructional_quality、structure、consistency、boundary。

## 来源与封存

任务输入、actual reads、canonical source artifacts、manifest 和 stage result 形成连续 provenance 链。封存以相对仓库路径与内容共同计算 implementation digest，避免同名文件替换、闭包遗漏或路径顺序漂移。

## 缺陷归属

HQ2 自己的候选结构、引用或判断错误是 `reviewer_local`；handoff 不能被消费或 HP1 与 handoff 实质漂移是 `upstream_content`；确需作者裁决或外部事实才分别标记 `author_required`、`reality_dependency`。HQ2 只分类与举证，不代替责任方修正。
