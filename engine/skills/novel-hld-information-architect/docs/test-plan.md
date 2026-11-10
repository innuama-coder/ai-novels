# HI1 Test Plan

- P01: legal model produces public ready completion and parent-consumable result.
- N01: incomplete suspense terminal produces `revise/local_candidate` without completion.
- B01: prose/dialogue leakage produces revise without escaping the boundary.
- Author-required: `required_now` stops before candidate publication and produces public blocked evidence.
- Gate regressions: stale upstream manifest, extra allowlist entry, and rehashed gate drift fail before output.
- Release: full unittest discovery, public SchemaCatalog/profile/envelope checks, `py_compile`, `quick_validate`, and diff whitespace check.
