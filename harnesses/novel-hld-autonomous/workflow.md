# Novel HLD Autonomous Workflow

## Fixed topology

```text
request -> revision-000 -> HB0 -> HA1 -> HS1 -> HC1 -> HI1 -> HR1
        -> HK1 -> HQ1 -> HP1 -> HQ2(consumer,fidelity,publisher)
        -> HH1(A,B,C,publisher) -> author gate -> HF1 -> lld_ready
```

HA1 through HK1 are sequential. HQ2 and HH1 are composite stages whose internal results can be consumed only by their deterministic publisher. Only the publisher emits a top-level result. The router is the only parent consumer and the only component that writes a successor run state.

## Stage input rule

Each work order binds one sealed `input-gate.json`, one pre-state, a strictly ordered upstream-completion list, exact owner identity and implementation hash, a read allowlist, an unresolved projection, and optional revision bindings. Skills may not discover inputs or read chat history.

| Stage | Ordered upstream completions |
| --- | --- |
| HB0 | `[]` |
| HA1 | `[HB0]` |
| HS1 | `[HB0,HA1]` |
| HC1 | `[HB0,HA1,HS1]` |
| HI1 | `[HB0,HA1,HS1,HC1]` |
| HR1 | `[HB0,HA1,HS1,HC1,HI1]` |
| HK1 | `[HB0,HA1,HS1,HC1,HI1,HR1]` |
| HQ1 | `[HB0,HA1,HS1,HC1,HI1,HR1,HK1]` |
| HP1 | `[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HQ1]` |
| HQ2 | `[HB0,HP1]` |
| HH1 | `[HB0,HP1,HQ2]` |
| HF1 | `[HB0,HA1,HS1,HC1,HI1,HR1,HK1,HQ1,HP1,HQ2,HH1]` |

## Result routing

- `ready`: validate the ready package profile and completion, then advance.
- `revise/local_candidate`: create an immutable revision plan and activate its earliest group.
- `revise/external_author_request`: allowed only for HF1; create a plan from the sealed final author event.
- `blocked/author_required`: create an author-question transaction.
- `blocked/reality_dependency`: terminate this run and create a conception reentry request.
- `blocked/upstream_defect`: derive owner by stable affected IDs and create a revision plan.
- `blocked/author_rejected`: terminate without HLD completion.
- `runtime_error`: keep the previous current state and preserve evidence.

## Decision-dependency protocol

HB0 only registers unresolved controls. The harness projects every non-quality unresolved source to every HA1-HK1 stage authorized by the source matrix, and every quality unresolved source only to HQ1. The recipient creates `HDD-<stage>-<source_id>` before candidates or verdicts. `required_now` stops the work order before candidate generation. HQ1 checks coverage; HP1 may only aggregate proven dispositions.

## Revision protocol

The router creates one immutable `revision-plan.json`. Every source finding or author target becomes its own group; groups are ordered by stage topology and original source order, never semantically merged. Mutable status is append-only in `revision-plan-state/revision-NNN.json`. One group is active; all others remain pending. If an upstream revision removes or changes a later target, mark that group `superseded` and use `revision_retarget`; do not edit the plan or silently resolve it.

## Composite publication

HQ2 and HH1 publishers only revalidate identities, hashes, bindings and fixed file profiles. On the first non-ready internal task, later tasks are not issued. The publisher byte-copies the first non-ready internal package and result into a top-level non-ready package and result. It does not fabricate missing tasks or findings.

## Author gate

The external gate binds the current HP1, HQ2, HH1 and HTML hashes. `approved` permits HF1 validation; `revise` is losslessly projected by HF1 and routed through the revision-plan protocol; `rejected` terminates the run. Final author decisions never answer a mid-run must-ask.
