# HB0 executable SOP

## A. Preflight

1. Resolve the work-order file and use its parent as the sealed workspace root.
2. Validate the work order and its referenced input gate against the harness schemas.
3. Verify `stage=HB0`, exact skill/version/implementation hash, `action=execute`, `mode=forward`, empty upstreams, empty unresolved projection, null return/revision bindings, and open submission state.
4. Verify the work-order `state_before_ref`, `input_gate_ref` and every allowlist reference before reading them.
5. Verify input gate values equal the work order and revision-000 state is `initialized`, at HB0, with no accepted completion.

## B. Upstream admission

6. Resolve allowlist roles; require exactly one run request, preparation request, preparation validator, compatibility lock, baseline canonical, baseline Markdown, baseline validation, baseline manifest, and required upstream schemas.
7. Check all locked implementation/schema hashes against `preparation-compatibility-lock.json`.
8. Invoke the exact allowlisted preparation validator with the allowlisted preparation request. A nonzero code blocks; do not repair.
9. Validate `hld-run-request.json`, require project match, V1 author gate and replace policy, and ensure HLD output is disjoint from baseline/source roots.
10. Require the baseline directory to contain exactly the four upstream ready files.
11. Validate upstream manifest/validation/baseline with the locked schemas and recompute every manifest hash.

## C. Control and source closure

12. Check baseline status, project, HLD assignment, release identity and lineage.
13. Build classification and authority partitions; prove disjointness, totality and open-item subset rules.
14. Copy unresolved controls into `unresolved_register` without disposition.
15. For every control and six-domain inventory entry, resolve its root-aware source and RFC 6901 locator, recompute canonical value hash, identify the actual structural/object discriminator, and assign allowed stages strictly from the fixed matrix.
16. Deduplicate only exact identical index keys; conflicting duplicates block.

## D. Deterministic publication

17. Build `hld-control-baseline.json` and `hld-source-index.json` without story summaries or HLD decisions.
18. Write `hb0-execution.json`, deterministic validation, exact manifest and completion in a temporary package.
19. Validate schemas, package profile, manifest closure, role uniqueness and byte reproducibility.
20. Publish atomically into the work-order output directory and write one package-external `stage-result.json` with copied event/timestamp.
21. Run `validate_hb0.py` against the same sealed inputs. Any drift invalidates delivery.

## E. Branch behavior

- Source/input defect: publish only the standard blocked result package and result envelope; exit 2.
- Runtime/configuration defect before a safe result can be bound: exit 1 and preserve logs; do not claim blocked semantics.
- Ready: exit 0. The parent, not HB0, admits completion and writes revision 001.
