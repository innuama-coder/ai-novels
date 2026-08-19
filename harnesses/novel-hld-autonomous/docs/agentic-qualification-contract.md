# Agentic qualification contract

This contract separates **structural implementation acceptance** from **semantic agentic qualification**. Unit tests, schema validation, synthetic canonical drafts and fixture declarations may prove deterministic mechanics; none of them proves that a fresh Agent can perform the reasoning owned by a skill.

Files named `tests/acceptance-evidence.json` inside bounded skills are retained as structural fixture anchors only. They must declare `evidence_class: structural-fixture-anchor`, `agentic_qualification: not-run`, `qualification_credit: false`, and `reviewer_role: implementation-test-author`; the harness validator rejects semantic-pass or independent-review claims in those files.

## Required evidence

A semantically qualified release must provide one `agentic-acceptance.json` plus its closed evidence directory. The acceptance must include:

1. all 42 bounded-skill P/N/B cases, executed by fresh producer tasks;
2. all five full-chain P/N/B/R cases, executed through the public Codex operation path;
3. an end-to-end reference run for project `duanxian`, from the accepted baseline through HF1 and author decision;
4. independent semantic reviews by task identities different from the producer identities;
5. immutable file references and SHA-256 digests for fixtures, prompts, instructions, transcripts, products, deterministic validations and reviews;
6. one runtime task receipt for every producer and reviewer, with unique task/context identities and an exact transcript binding;
7. one detached RSA-PKCS#1 v1.5/SHA-256 attestation from the trusted qualification controller. The signature covers the acceptance payload, which transitively covers every referenced receipt and artifact.

The producer receives only the declared allowlist and must not receive expected answers or earlier conclusions. The reviewer receives the product, the scoring contract and source authority needed to judge it, but not a prewritten score. A bounded case passes only when all six dimensions score 2/2 and there is no blocker. A harness case passes only when all seven dimensions are present, total at least 12/14, and there is no blocker.

## Fixture lifecycle

Case files and `declaration-only` fixture descriptors are test specifications, not execution evidence. Before an execution, the operator must materialize a complete fixture directory, write a manifest containing every allowed input path and SHA-256, and seal it before the producer starts. Outputs and transcripts must be written outside the sealed input directory. Any changed digest invalidates the result.

## Qualification and release

The trust anchor lives outside the evidence directory at `references/qualification-trust-anchor.json`. Its default `unconfigured` state is deliberate: no packaged test key is allowed to authorize release promotion. A qualification operator must install a reviewed public key, set the anchor to `configured`, and retain the private signing key outside the repository.

The `duanxian` reference run is role-typed rather than a bag of files. Baseline, HP1 package, HQ2 acceptance, HH1 manifest/report/render registry, HTML, author decision and HF1 completion must be distinct artifacts; the validator checks their schemas and their run, revision and digest bindings.

Run:

`python harnesses/novel-hld-autonomous/tools/validate_agentic_acceptance.py <acceptance.json> --trust-anchor harnesses/novel-hld-autonomous/references/qualification-trust-anchor.json`

The validator is fail-closed: it checks the exact case closure, controller-signed runtime receipts, independent task/context identities, context-isolation declarations, dimension bars, referenced file hashes, validation/review verdicts and the schema-bound complete `duanxian` reference run. Merely inventing IDs, transcripts or JSON files cannot pass without the external controller signature. Only a passing acceptance permits `status: release-candidate`. Without it, the package may be an `implementation-candidate`, but must not claim semantic or full-chain qualification.
