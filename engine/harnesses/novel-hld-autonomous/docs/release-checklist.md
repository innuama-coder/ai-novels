# Harness implementation and release checklist

- [x] Portable core topology and ownership contracts agree.
- [x] Schemas compile and static validator reports zero errors.
- [x] Ready and blocked HB0 concrete instances validate.
- [x] Codex adapter maps all portable behaviors and unsupported runtimes are explicit.
- [x] Release builder produces source and Codex archives with SHA-256 metadata.
- [x] All 14 registered stage skills have P/N/B specifications and their deterministic implementation checks pass.
- [x] Runtime manifest, Codex operation contract and post-install checks are packaged.
- [ ] Fresh Agents execute all 42 bounded-skill P/N/B cases with independent semantic review.
- [ ] Fresh Agents execute the five full-chain P/N/B/R cases from materialized, sealed fixtures.
- [ ] The complete `duanxian` reference run passes HQ1, HQ2, human review and author decision without semantic drift.
- [ ] A passing `agentic-acceptance.json` promotes the manifest to `release-candidate`.

Machine-readable structural evidence: `releases/0.1.0-acceptance.json`. It intentionally records `agentic_qualification: not-run`; declaration-only fixtures and synthetic drafts are not execution evidence. A structural archive is valid only when its own post-install validation passes from an empty directory. Semantic release additionally requires `docs/agentic-qualification-contract.md`.
