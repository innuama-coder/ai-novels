# HS1 测试计划

运行：`python -m unittest discover -s skills/novel-hld-storyline-choreographer/tests -p "test_*.py" -v`。

验收覆盖：合法多线编排交付 ready；孤立故事线和越界 POV 分配交付 revise；公共 HB0/HA1 输入链、manifest、completion、stage-result 全链绑定；闭合 canonical schema 和闭合生成证据拒绝多余、缺失、错误类型与错误枚举；权威分区、派生哈希、候选、投影、外部澄清绑定和辅助交付篡改均被拒绝；唯一方案必须具有排除证据；allowlist 攻击在读取前失败。

静态 P/N/B 夹具由 `fixture-manifest.json` 的 SHA-256 封存。测试只确定契约与边界，故事线连接是否有叙事价值仍由证据和父级/HQ1 评审。
