# Release contract

The source tree is canonical. Version `0.1.0` is currently an `implementation-candidate`, not a semantic release candidate or a 1.0 stability claim, and supports only the Codex adapter. Claude, Gemini, OpenClaw and Hermas are explicitly unsupported until each has its own mapping, evaluation evidence and validated runtime archive.

`tools/build_release.py` must run source validation first, create one source archive and one Codex archive, validate required archive members, and write a relative-path release manifest with SHA-256 checksums. Both archives preserve repository-root layout and contain the harness plus exactly the 14 skills named by the public runtime registry; `novel-hld-writer` is forbidden. Generated archives must not contain `dist/`, absolute paths, transient caches or local run data.

The Codex archive must be extracted into an empty directory and pass `tools/post_install_validate.py` there. That validation resolves all 17 public runtime tokens and their implementation closures without using the source checkout. Promotion to `release-candidate` additionally requires the closed Agent evidence package and validator described in `agentic-qualification-contract.md`; structural checks alone cannot promote the release.
