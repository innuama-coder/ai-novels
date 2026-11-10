# 研究来源（访问日期：2026-08-06）

以下 15 项均为标准组织、浏览器权威文档或安全项目的一手/权威资料；每项记录本技能实际吸收点。

1. [WHATWG HTML Living Standard — semantics](https://html.spec.whatwg.org/multipage/semantics-other.html) — 使用原生文档结构和 `nav` 表达目录，不靠纯视觉容器代替语义。
2. [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) — 落实信息关系、意义顺序、reflow、键盘、可导航、名称/角色/值等验收面。
3. [W3C ARIA in HTML](https://www.w3.org/TR/aria-in-html/) — 优先原生 HTML 语义，ARIA 只在不与强原生语义冲突时补足。
4. [W3C WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/) — 使用 banner/navigation/main/contentinfo landmark 和可访问命名关系。
5. [W3C SVG Accessibility API Mappings](https://www.w3.org/TR/svg-aam-1.0/) — SVG 以 title/desc、aria-labelledby/aria-describedby 和 graphics semantics 进入 accessibility tree。
6. [W3C SVG 2 — Document Structure](https://www.w3.org/TR/SVG/struct.html) — title/desc 作为 SVG 容器可访问名称与描述的标准组成。
7. [W3C Graphics ARIA](https://www.w3.org/TR/graphics-aria-1.0/) — 复杂图形需要明确 graphics object 语义，不暴露无意义低层 shape。
8. [W3C CSS Paged Media Level 3](https://www.w3.org/TR/css-page-3/) — 使用 `@page`、页尺寸/边距和分页规则支持打印/PDF。
9. [MDN Printing](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing) — 用 `@media print` 与 `@page` 在屏幕/打印之间保持可读布局。
10. [W3C CSS Overflow Level 3](https://www.w3.org/TR/css-overflow-3/) — 显式控制横向 overflow，长内容不应无意越出容器。
11. [W3C WCAG Technique C32](https://www.w3.org/WAI/WCAG22/Techniques/css/C32) — 320 CSS px 与 400% zoom 场景采用 source-order responsive grid，避免横向滚动和焦点顺序错位。
12. [W3C CSS Color Level 4](https://www.w3.org/TR/css-color-4/) — 不仅靠颜色表达信息，采用可读前景/背景并考虑 forced colors。
13. [OWASP Cross Site Scripting](https://owasp.org/www-community/attacks/xss/) — report 内容进入 HTML 前必须 context-safe escaping，禁止作为可执行 markup 注入。
14. [MDN SVG title](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/title) — `<title>` 作为 SVG 首子元素并提供简短可访问名称。
15. [RFC 8785 JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785) — 内容 hash 需要不变量表达和确定性键排序；本实现采用项目既有 compact sorted UTF-8 JSON 约定并明确其边界。
