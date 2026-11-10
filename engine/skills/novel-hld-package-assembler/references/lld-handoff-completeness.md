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

The handoff also carries one `chapter_designs[]` entry for every HA1 chapter
shell. Each entry preserves the shell ID, the independent HS1 design ID, chapter
number and work-unit binding, a readable working title, the chapter's core
content, its chapter-end change, and the primary/supporting/background/open
storyline roles. HP1 rejects missing, duplicate, reordered, cross-unit, or
storyline-inconsistent chapter designs. LLD may design scenes and prose inside
these boundaries; it may not invent what the chapter is for.
