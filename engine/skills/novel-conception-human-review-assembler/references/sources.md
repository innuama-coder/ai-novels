# 方法论与最佳实践来源

以下来源用于设计通用的人审信息架构，不用于提供任何具体小说事实。

1. [W3C — Clear and Understandable Content](https://www.w3.org/WAI/WCAG2/supplemental/objectives/o3-clear-content/)  
   使用短句、短块、明确词汇、留白和长内容摘要，支撑十分钟快速理解。
2. [W3C — Headings](https://www.w3.org/WAI/tutorials/page-structure/headings/)  
   标题应准确表达分区关系，帮助扫读和辅助技术导航。
3. [W3C — Writing for Web Accessibility](https://www.w3.org/WAI/tips/writing/)  
   清晰标题、简明语言和有意义链接应在内容模型阶段确定，而非交给视觉层补救。
4. [GOV.UK — Government Design Principles](https://www.gov.uk/guidance/government-design-principles)  
   从用户需要开始、少做但做好、用数据迭代，支撑以“作者要作什么决定”为起点。
5. [GOV.UK Publishing — Identify user needs](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/plan-manage-content/identify-user-needs/)  
   内容应解决明确任务，避免把组织内部材料原样暴露给用户。
6. [Department for Education — Plain language](https://design.education.gov.uk/content-design/plain-language)  
   使用具体、直接、可操作的语言，避免抽象术语和不必要背景。
7. [Department for Education — Plain language standard](https://standards.education.gov.uk/standard/plain-language)  
   将清晰表达作为可检查的标准，而非文风偏好。
8. [Cumberland Council — Plain English](https://www.cumberland.gov.uk/design-and-content-guidelines/content-design-style-and-patterns/writing-users/plain-english)  
   重要信息前置、适应扫读，支撑“快速定向 → 三域 → 片段 → 决定”的顺序。
9. [Home Office Design System — Headings](https://design.homeoffice.gov.uk/accessibility/page-structure/headings)  
   标题层级表达结构而非视觉大小，后续 HTML 不得破坏内容层级。
10. [GOV.UK — Publishing accessible documents](https://www.gov.uk/guidance/publishing-accessible-documents)  
    可访问性应从内容和文档结构开始，不应只靠最终格式修补。
11. [Datawrapper — Accessible charts, maps and tables](https://www.datawrapper.de/academy/how-we-make-sure-our-charts-maps-and-tables-are-accessible)  
    图形需要清楚标题、文本等价信息和不依赖颜色的编码；因此本技能输出可读的语义节点与边。
12. [Datawrapper — Annotate tab](https://www.datawrapper.de/academy/annotate-tab)  
    标题、说明与注释应解释图中真正需要注意的关系，而不是重复图形。
13. [Schröder et al. — Data Storytelling: A Systematic Literature Review](https://arxiv.org/abs/2312.01164)  
    叙事、视觉和数据需要协同；报告同时提供短文本、结构化图形语义和时间推进。
14. [Shao et al. — Data Storytelling in Data Visualisation](https://arxiv.org/abs/2402.12634)  
    视觉叙事的顺序和注释影响理解，因此时间线必须显式呈现压力、选择和后果。
15. [Character-Oriented Design for Visual Data Storytelling](https://arxiv.org/abs/2308.07557)  
    角色化组织能增强叙事理解，支撑以人物目标、行为和关系变化组织角色板块。
16. [Brysbaert — How many words do we read per minute?](https://biblio.ugent.be/publication/8647789)  
    阅读速度随文本类型和语言变化；本技能因此把速率作为可校准参数，而不宣称统一的人类读速。
17. [Interaction Design Foundation — Progressive Disclosure](https://www.interaction-design.org/literature/topics/progressive-disclosure)  
    先呈现完成主要任务所需的信息，再提供细节；关键审批信息不能被折叠隐藏。
18. [Interaction Design Foundation — Task Load](https://www.interaction-design.org/literature/topics/task-load)  
    通过减少不必要选择、记忆负担和重复降低任务负荷。
19. [Nielsen Norman Group — Information Foraging](https://media.nngroup.com/media/articles/attachments/InformationForaging_SizeA4.pdf)  
    用户会追随信息气味并权衡寻找成本；每个板块必须有明确问题、短标题和结论方向。

## 方法边界

- 上述来源支持信息架构、可访问性、可视叙事和阅读预算方法。
- 它们不定义小说必须采用某种题材、结构或角色模型。
- 默认阅读速率只是本技能的可调设计假设，必须通过真实作者测试校准。
