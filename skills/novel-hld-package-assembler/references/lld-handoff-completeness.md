# LLD handoff completeness

The LLD handoff carries more than the storylines already named by HK1 work units.
It contains the complete HS1 storyline inventory with one disposition per stable
storyline ID. `placed` and `background-carried` lines must map to at least one LLD
work unit; `optional-not-activated` and `preserved-open` lines keep their IDs with
an explicit absence reason and no false placement.

Each LLD work unit also receives a relative elapsed-time window derived from HR1.
HP1 rejects missing time bands, missing background-story carriers, extra storylines,
or any mismatch between HS1 unit placement and HK1 storyline references. HQ2 tests
against this complete inventory, including preserved-open identities, rather than
reconstructing the expected set from the possibly incomplete work units themselves.
