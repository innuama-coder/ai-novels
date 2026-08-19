# HC1 测试计划

运行：`python -m unittest discover -s skills/novel-hld-character-arc-placer/tests -p "test_*.py" -v`。

验收覆盖：合法角色弧线放置交付 ready；未经授权的新关系和越界外貌定义交付 revise；公共 HB0/HA1/HS1 输入链与所有结果封装严密绑定；闭合 canonical schema、权威分区、派生哈希、候选、投影、外部澄清引用和辅助证据均有反篡改回归；唯一方案必须给出排除证据；allowlist 攻击在读取前失败。

P/N/B 夹具由 `fixture-manifest.json` 封存。测试证明角色行动、代价与事件坐标满足确定性约束，但不替代父级/HQ1 对人物弧线感染力的语义评审。
