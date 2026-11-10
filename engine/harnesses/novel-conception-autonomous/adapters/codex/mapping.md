# Codex Mapping

This mapping is normative. Status is one of `native`, `prompt`, `tool`,
`manual`, or `unsupported`.

<!-- ADAPTER-MAPPING:BEGIN -->
{
  "schema_version": "2.1",
  "status_enum": ["native", "prompt", "tool", "manual", "unsupported"],
  "mappings": [
    {"id": "approved-interview-input", "status": "manual", "owner": "interview-workflow", "adapter_role": "verify-and-bind"},
    {"id": "production-run-state", "status": "native", "owner": "production-orchestrator", "adapter_role": "persist-and-report"},
    {"id": "domain-content-generation", "status": "prompt", "owner": "exact-stage-owner", "adapter_role": "dispatch-work-order"},
    {"id": "external-author-decision", "status": "manual", "owner": "external-author", "adapter_role": "verify-and-forward"},
    {"id": "terminal-compatibility", "status": "tool", "owner": "portable-runtime", "adapter_role": "legacy-api-compatibility-only"},
    {"id": "legacy-d1-r1", "status": "unsupported", "owner": "none", "adapter_role": "reject"}
  ]
}
<!-- ADAPTER-MAPPING:END -->

| Requirement ID | Status | Authority owner | Codex adapter role |
|---|---|---|---|
| `approved-interview-input` | `manual` | `interview-workflow` | `verify-and-bind` |
| `production-run-state` | `native` | `production-orchestrator` | `persist-and-report` |
| `domain-content-generation` | `prompt` | `exact-stage-owner` | `dispatch-work-order` |
| `external-author-decision` | `manual` | `external-author` | `verify-and-forward` |
| `terminal-compatibility` | `tool` | `portable-runtime` | `legacy-api-compatibility-only` |
| `legacy-d1-r1` | `unsupported` | `none` | `reject` |

Codex may author domain proposals only while acting as the exact owner named by
`dependency-spec.json`. It must never synthesize an author decision, select a
semantic fallback owner, mutate persisted run-state directly, or bypass the
current work order.
