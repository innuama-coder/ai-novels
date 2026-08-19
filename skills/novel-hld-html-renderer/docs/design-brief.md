# Design brief

HH1-C 是无语义裁决权的 script skill。它只在 HH1-B pass 且绑定当前 HH1-A report hash 后，将 report 元素一对一投影为离线 HTML/SVG 和 HUI registry。HRE/HVG 保留语义所有权；HUI 只拥有 DOM 表达。成功意味着内容集合无损、registry/DOM 全等、离线/可访问/打印/常见视口静态门通过、输出字节可重现，并只产生 composite_internal result。

关键风险为：Renderer 越权改写内容、从故事源补答案、HTML injection、外部依赖、HUI 漂移、图形无文本替代、视觉顺序与 DOM 顺序不一致、HH1-C 越权发布 completion。设计以严 allowlist、fidelity hash binding、HTML escaping、固定模板/资产 hash、一对一 registry 和 exact internal profile控制。
