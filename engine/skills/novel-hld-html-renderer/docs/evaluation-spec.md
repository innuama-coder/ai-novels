# Evaluation spec

- `HH1-C-P01`：当前 fidelity pass + 合法 report，生成 exact 五文件包；report/DOM/registry 集合全等，HUI 公式、SVG accessible name、offline/print/reflow 静态门、manifest/result schema 与字节确定性全部通过。
- `HH1-C-N01`：HH1-B 不是 pass 或 report binding 漂移，输入门拒绝且不渲染。
- `HH1-C-B01`：结论含 `<script>`/属性注入、visual label 含远程 URL、或 allowlist 加入故事源；内容必须被转义且页面无执行/外部依赖，越界 allowlist 必须 fail closed。

验收维度使用 Harness 固定六维：scope fidelity、input gate obedience、output contract correctness、semantic/deterministic correctness、boundary discipline、parent consumability。三项 case、公共 schema/profile、独立 validator、quick_validate 和重复渲染 byte equality 全过才交付。
