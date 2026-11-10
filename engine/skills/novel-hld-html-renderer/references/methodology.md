# 方法论

## 1. 渲染是保持语义的确定性投影

HH1-C 的内容权威只有 HH1-A report。Renderer 只做 `report element → DOM container → registry target` 的一对一投影；HH1-B 已回答内容是否忠实，Renderer 不重新选择结论。默认可见面只投影作者需要阅读的自然标题、故事结论、角色与地点叙述和最终决策问题；机器字段继续存在于 JSON、DOM data 属性和 registry 中。固定 DOM 顺序跟随 report 固定板块顺序，视觉布局不能改变阅读顺序。

页面不是数据字典，也不是检查清单。角色和地点字段要合成正常段落，城市、路线、普通人和季节只显示对应的 reader-story 投影。原始网络、profile、source、locator、职责字段和验证说明不得成为作者正文。最终验证器按 DOM 阅读块重新拼接跨 inline tag 文本，拒绝机器术语、流程话术、密集分号压缩和实质性重复。

## 2. 可追踪的双向映射

HRE/HVG 是报告语义元素，HUI 只是表达容器。HUI 由元素 ID、render role 和零基 ordinal 确定派生；registry 同时保存 DOM locator、回指和原元素 canonical content hash。验证器比较 report、registry 与 DOM 三个集合，防止遗漏、重复或漂移。

## 3. 离线与注入安全

所有输入都作为文本处理并按 HTML/XML context 转义；不接受 report 自带 markup。模板、CSS、renderer 受 hash 约束，输出不含脚本、外链、远程字体或可加载嵌入对象。单文件 HTML 只含内联 CSS/SVG，因此离线和打印不依赖网络状态。

## 4. 语义 HTML 优先

文档使用原生 header、nav、main、section、article、figure、table/list 和 footer；ARIA 只补足 SVG 名称/描述，不覆盖原生语义。skip link 与 fragment TOC 支持键盘；DOM 顺序就是阅读顺序，CSS 不重排。

## 5. SVG 是可替代的表达层

每个 HVG 的节点/边/点完全来自 visual model data。固定算法只计算坐标；SVG 用 title/desc 给出名字和描述，并显示自然中文文本替代，使图形不是唯一信息载体。来源绑定和内部枚举不得作为可见图例。颜色不单独编码状态，文字标签和线型同时保留区别。

## 6. reflow 与打印

页面用流式宽度、`minmax(0,1fr)`、`overflow-wrap:anywhere` 和响应式网格避免横向溢出；SVG 以 viewBox 和 `max-width:100%` 缩放。打印样式冻结页边距、颜色、分页与 URL 无关内容，不隐藏实质报告元素。

## 7. 确定性与验证分层

JSON canonical bytes、固定板块顺序、排序稳定的 attribute/registry 和固定换行保证可重现 hash。标准库验证器负责结构、集合、注入、hash 和 package profile，不判断故事含义；六维证据按 Harness `BOUNDED_EVAL_DIMENSIONS` 记录。
