# Harness design brief

`novel-hld-autonomous` turns a released conception baseline into a verified HLD through thirteen stage owners: HB0 → HA1 → HS1 → HC1 → HI1 → HR1 → HK1 → HD1 → HQ1 → HP1 → HQ2 → HH1 → HF1. HD1 defines every chapter as a writing-ready contract before semantic review. The harness owns routing, immutable state transitions, evidence envelopes, HDD lifecycle, revision routing and author-gate transactions. Stage skills own only their named artifacts.

The portable core is runtime-neutral. Version 0.1.0 ships one Codex adapter and explicitly marks other runtimes unsupported. A stage advances only from a schema-valid work order to a schema-valid result, completion and manifest accepted into a new immutable state revision.
