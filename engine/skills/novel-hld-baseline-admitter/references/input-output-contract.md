# HB0 input and output contract

## Input

The sole CLI input is a path to the harness-issued `work-order.json`. All artifacts are relative to the sealed workspace root and appear in the work-order/input-gate allowlist with exact SHA-256.

Required allowlist roles are:

`hld_run_request`, `preparation_request`, `preparation_validator`, `preparation_runtime`, `preparation_compatibility_lock`, `development_baseline`, `development_baseline_markdown`, `baseline_validation`, `baseline_manifest`, `development_baseline_schema`, `baseline_validation_schema`, `baseline_manifest_schema`, `preparation_request_schema`, `upstream_release_lock`, `harness_run_request_schema`, `harness_input_gate_schema`, `harness_work_order_schema`, `harness_run_state_schema`, `harness_package_manifest_schema`, `harness_stage_completion_schema`, `harness_stage_result_schema`, `harness_control_baseline_schema`, `harness_source_index_schema`, `harness_hb0_validation_schema`, and `harness_hb0_execution_schema`. `preparation_validator` and `preparation_runtime` must be staged as sibling files so the sealed upstream validator can import its exact hash-bound runtime dependency.

No role may repeat. Besides the fixed roles above, HB0 accepts only the generated lineage roles `source::<root>::<path>` and `upstream::<root>::<path>` that are explicitly present in both the work-order and input-gate allowlists. Every such role is derived from a baseline source reference and is hash-bound; arbitrary extra roles are rejected.

## Control baseline

`hld-control-baseline.json` contains source baseline identity/release/lineage, deterministic admission verdicts, the exact four-layer authority partition, a lossless control registry, unresolved register, HLD assignment, change policy, prohibitions and the source-access policy version. HLD ownership sets are empty.

## Source index

Each entry contains `source_id`, `domain`, `object_type`, optional explicit discriminator, source role/path/hash, locator, canonical value hash and fixed allowed stages. Index identity is `(source_id, domain, source.path, locator)`; conflicting duplicates block.

## Package and result

The ready content package has the exact six-file profile declared in `SKILL.md`. `stage-result.json` is its package-external parent-consumption envelope. A blocked result package has exactly four files and no completion. All JSON objects are closed by schema and deterministically serialized as sorted compact UTF-8 with a final LF.

## Parent-consumption rule

The harness validates the result envelope, manifest, validation and completion. On ready it may create revision 001 and issue HA1. On blocked it routes by blocker evidence. It must never inspect stdout to decide the next stage.
