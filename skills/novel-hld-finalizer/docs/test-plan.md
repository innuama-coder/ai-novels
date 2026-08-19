# Test plan

## Automated

- Use bundled Python by absolute path with no installed dependency.
- Reject third-party imports through AST inspection.
- Validate strict schemas and `additionalProperties:false`.
- Tamper each critical hash and assert no completion.
- Reject an empty/fake content manifest, a manifest that omits validation/canonical, a completion whose manifest binding is stale, and changed canonical member bytes. The manifest must exclude itself and `stage-completion.json`; the completion must bind the finished manifest.
- Reject absent HQ2 HP1/handoff bindings and invalid, out-of-range, or wrong-value RFC6901 author locators.
- Compare two approved executions byte-for-byte.
- Assert revise target arrays are byte-equivalent JSON values to the author event.
- Assert rejected emits `blocked/author_rejected` and no completion.
- Assert no package contains run-state, return request, revision plan, or LLD content.

## Release

All tests, compilation, skill structure, and six-dimension evidence pass. Approved-only completion and non-approved absence are hard gates.
