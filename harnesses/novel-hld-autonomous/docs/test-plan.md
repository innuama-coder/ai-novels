# Harness test plan

Local bounded-skill `tests/acceptance-evidence.json` files are structural fixture anchors, not executed Agent evidence. Their truth labels are checked by the harness validator and they contribute zero Agentic qualification credit.

- Static: validate required files, exact stage order, owners, access matrix, schemas, package profiles, eval declarations and adapter mapping.
- Instance: validate concrete ready and blocked HB0 results and all referenced contract objects.
- Stage: every owner supplies positive, negative and boundary cases with a 12/12 pass bar.
- Chain: exercise normal forward execution, invalid input, ownership violation, local revision and author-return revision.
- Release: rebuild archives twice from unchanged input, validate included paths and publish checksums.

No warning, skip, manual waiver or declaration-only fixture counts as full-chain acceptance.
