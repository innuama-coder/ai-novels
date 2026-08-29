# Release Model

本仓库仅维护一份 portable source。发布构建会从该源生成 source zip 与五个 runtime zip，并生成带 SHA-256 和相对路径的 `dist/release-manifest.yaml`。运行时包只含核心、schema、validator、eval 和所选 adapter；它们不会包含调用方的代码、凭证或环境数据。

发布前运行 `python validators/validate_harness.py .`，然后运行 `python tools/build_release.py .`。结构校验与运行时 staging/zip 校验均通过后才可标记此团队定义为可分发。
