# SOP

1. 验证 work order/input gate、HB0→HP1→HQ2 completion、state 与 implementation hash。
2. 验证 allowlist 只含 report、fidelity 与固定渲染资产；校验全部文件 hash。
3. 验证 HH1-A report schema、HRE/HVG ID 唯一和 source binding；验证 HH1-B pass 精确绑定当前 report hash。
4. 按固定章节顺序遍历，不摘要、不重排；为每元素派生唯一 HUI 和 canonical content hash。
5. HRE 渲染为带 conclusion/question/source/locator 的语义 article；HVG 用固定坐标算法渲染 SVG，并输出 title/desc 和可见文本替代。
6. 组装准确标题、范围、版本、状态、目录、作者决定说明、landmark、skip link 与内联 CSS。
7. 生成 registry；比较 report 元素、DOM target、DOM 回指、registry 四个集合全等。
8. 检查无 script/外链/远程资源/危险元素；检查 reflow/print/keyboard 所需静态规则与 SVG accessible name。
9. 写 render-execution、validation、manifest 和包外 composite_internal result；不得写 completion。
10. 以独立 validator 重验 sealed package；任一本地渲染缺陷返回 revise，不以删内容通过。
