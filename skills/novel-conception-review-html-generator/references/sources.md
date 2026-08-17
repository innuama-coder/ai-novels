# 方法论与最佳实践来源

研究日期：2026-07-26。以下来源用于形成通用页面契约，不包含任何特定小说内容。

1. [W3C WAI：Page Structure Tutorial](https://www.w3.org/WAI/tutorials/page-structure/)  
   用途：语义页面结构、逻辑标题和快速定位。
2. [W3C WAI：Page Sections](https://www.w3.org/WAI/tutorials/page-structure/sections/)  
   用途：header、nav、main、section、footer 与区域标注。
3. [W3C WAI：Content Structure](https://www.w3.org/WAI/tutorials/page-structure/content/)  
   用途：用文章、列表、描述列表表达真实信息关系。
4. [W3C WAI：Labeling Controls](https://www.w3.org/WAI/tutorials/forms/labels/)  
   用途：显式关联表单标签与控件。
5. [WCAG 2.2：Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum)  
   用途：正文与功能色保持可辨对比。
6. [WCAG 2.2：Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html)  
   用途：类别和状态不得只依赖颜色。
7. [WCAG 2.2：Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)  
   用途：320 CSS px 下正文单向滚动和单列重排。
8. [WCAG 2.2：Keyboard](https://www.w3.org/WAI/WCAG22/Understanding/keyboard.html)  
   用途：全部交互无需鼠标。
9. [WCAG 2.2：Focus Visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html)  
   用途：提供清楚的键盘焦点。
10. [WCAG 2.2：Bypass Blocks](https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks.html)  
    用途：提供跳到主要内容的机制。
11. [WCAG 2.2：Headings and Labels](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html)  
    用途：标题和标签准确描述用途。
12. [USWDS：Typography](https://designsystem.digital.gov/components/typography/)  
    用途：16px 基准、45–90 字符行长、约 66 字符目标和长文行高。
13. [USWDS：Design principles](https://designsystem.digital.gov/design-principles/)  
    用途：从真实用户需要出发、可达性、信任与一致性。
14. [GOV.UK：Government Design Principles](https://www.gov.uk/guidance/government-design-principles)  
    用途：从用户需要出发、做少、把复杂工作变简单、持续迭代。
15. [Datawrapper：Accessible charts, maps and tables](https://www.datawrapper.de/academy/how-we-make-sure-our-charts-maps-and-tables-are-accessible)  
    用途：视觉数据提供文字等价信息，不排除辅助技术用户。
16. [MDN：Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)  
    用途：限制静态页面可加载和可执行的资源。
17. [MDN：Printing](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Printing)  
    用途：用 print media 与 `@page` 提供纸面/PDF 评审。
18. [MDN：prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion)  
    用途：尊重减少非必要动态的系统偏好。
19. [OWASP：Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)  
    用途：按 HTML 上下文编码不可信文本，避免危险 sink 和事件处理器。

## 形成的 SOP 要点

- 固定目标和版式，避免每次临场设计造成审阅漂移。
- 默认完整显示决定所需内容，只折叠机器追溯。
- 图形表达关系，文字保留完整事实。
- 严格语义 HTML、标题、label、skip link 与键盘焦点。
- 以 320px 重排、打印和减少动态作为硬测试面。
- 对所有上游文本转义；不依赖网络；CSP 作为附加防线。
- 不预选作者结论；本地导出只产生非权威草稿。
- 以哈希、嵌入 JSON 相等和确定性重渲染完成交付验收。
