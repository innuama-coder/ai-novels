# HA1 测试计划

运行：`python -m unittest discover -s skills/novel-hld-narrative-architect/tests -p "test_*.py" -v`。

验收覆盖：合法宏观叙事架构交付 ready；缺少权威转折锚点和越界场景细节交付 revise；公共 work-order、input-gate、artifactReference、manifest、completion、stage-result 全链绑定；闭合 canonical schema 拒绝多余、缺失、错误类型和错误枚举；权威分区、派生指针/值哈希、候选方案、投影、外部澄清引用和辅助证据的篡改均被拒绝；唯一方案只有在提交排除证据时可通过；allowlist 的缺失、多余、过期和漂移在读取前失败。

P/N/B 静态夹具在执行前由 `fixture-manifest.json` 封存 SHA-256。任何夹具变更必须重新封存并复跑本计划。语义质量仍由生成证据与父级/HQ1 评审，不把字段存在误当成质量证明。
