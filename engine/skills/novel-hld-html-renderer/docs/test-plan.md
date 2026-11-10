# Test plan

1. 用合法 report/fidelity 运行两次隔离 workspace，比较 HTML、registry、execution、validation 字节完全相同。
2. 检查每个 HRE/HVG 恰好一个 HUI；公式、DOM locator、data 回指、content hash 全正确。
3. 检查标题、范围、版本、状态、目录、作者说明、landmark、skip link、SVG title/desc/text fallback。
4. 植入 script/attribute/URL 文本，确认仅作为转义文本呈现且无 script/外部请求面。
5. 将 fidelity 设为 fail 或篡改 report_ref，确认在输出目录创建前 fail closed。
6. 向 allowlist 加入故事源，确认输入门拒绝。
7. 用公共 Harness SchemaCatalog/profile/manifest/envelope 重验 ready 包；用独立 validator 重验 sealed package。
8. 检查五份 lifecycle docs、15 sources、三项 eval/fixtures 和六维 acceptance evidence。
