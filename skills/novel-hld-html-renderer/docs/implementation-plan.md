# Implementation plan

1. 冻结 catalog 15、2.4-B、2.16、HUI/HRE/HVG 和公共 Harness envelope。
2. 研究 HTML/SVG accessibility、reflow、print、overflow、escaping 与 deterministic hashing。
3. 冻结 report/registry schema、模板、CSS 和 HUI 派生规则。
4. 实现 gate：current upstream、strict allowlist、fidelity pass/report hash、renderer snapshot binding。
5. 实现标准库 HTML escape、固定 DOM、内联 SVG/文本替代、registry、execution、validation、manifest/internal result。
6. 实现独立 package validator，覆盖集合全等、外链/危险元素、SVG、print/reflow 与 exact profile。
7. 运行 P01/N01/B01、重复字节对比、Harness schema/profile 和 skill validator。
