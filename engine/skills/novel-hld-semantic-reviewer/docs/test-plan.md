# HQ1 测试计划

运行：

```powershell
python -m unittest discover -s skills/novel-hld-semantic-reviewer/tests -p "test_*.py" -v
```

覆盖：真实 HB0–HK1 public ready 链；全部 canonical HLD 对象；六域、四跨域、八挑战；重复运行确定性；local revise 不发布 canonical；upstream/author/reality blocked；禁止 HQ1 输出最终路由；actual-read 缺失/多读；来源和上游 manifest/main/completion/validation 篡改；closed schema 的额外/缺失/类型/枚举错误；allowlist 缺失/多余；实现 hash 覆盖运行时与语义 schema；pass claim 不能扩大一手覆盖且必须与原检查证据完全一致；P/N/B 静态夹具防重封装。
