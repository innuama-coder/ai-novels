# Development Process

1. Run the source validator.
2. Run all fixture evaluations, including negative and provenance boundary cases.
3. Build runtime release packages only after source validation passes.
4. Review the semantic rubric; record its verdict in a handoff packet.

Changes to stage ownership, schema or gates require a new harness version and
must update the affected leaf-skill integrations.
