# HB0 methodology

## 1. Separate producer claim from consumer proof

The upstream ready baseline is a claim. HB0 independently reruns the released preparation validator, validates all four files, recomputes manifest hashes, and resolves every source locator. A stored upstream `status=pass` never substitutes for current proof.

## 2. Verify identity before meaning

Use this order:

1. work-order actor/stage/implementation identity;
2. pre-state and input-gate hashes;
3. allowlist closure and path containment;
4. preparation compatibility lock;
5. upstream validator result;
6. four-file package boundary and manifest hashes;
7. baseline schema and run/project identity;
8. control partitions, locators, value hashes and assignment;
9. deterministic wrapper outputs.

No story-valued source is read before steps 1-5 pass.

## 3. Use byte identity and canonical value identity for different risks

Manifest SHA-256 protects exact file bytes. Canonical JSON SHA-256 protects the value reached through a locator independent of harmless whitespace. Both must pass: a file may have the expected semantic value but still be an unapproved byte artifact, or may preserve its file hash while a claimed locator/value binding is wrong.

## 4. Resolve roots and locators strictly

Resolve every allowlisted path against the sealed workspace, follow filesystem resolution, and prove it remains within that root. Resolve JSON Pointer according to RFC 6901 and terminate on invalid escapes, missing members, scalar traversal or invalid array index. Never search for an equivalent value when the exact locator fails.

## 5. Preserve authority as partitions

Build four independent structures:

- mutually exclusive primary classifications: `mandatory`, `freedom`, `must_ask`, `open`;
- `source_open_items`, a subset that may overlap a primary class;
- mutually exclusive upstream authority classes;
- empty HLD ownership sets, because HB0 creates no HLD elements.

The unions must equal the control registry exactly. Any duplicate, overlap or missing member blocks.

## 6. Register unresolved; never assess it

Copy every `classification=must_ask` or `open_item=true` control into `unresolved_register`. Do not create HDD, affected obligations, disposition or questions. Later stages own stage-scoped assessment after the harness performs a purely set-based projection.

## 7. Index actual locator values

For each unique `(source_id, domain, source path, locator)`, resolve the authoritative value and verify `source_value_sha256`. Record its structural JSON type and an explicit schema discriminator (`object_type`, `kind` or `type`) only when the value supplies one. Never infer the number of story objects from the inventory array length or split nested values creatively.

## 8. Fail closed with durable evidence

Input/source defects produce a blocked package and package-external result. Runtime/configuration failures produce a runtime error result when the workspace permits it. Neither branch may contain a ready completion. The result includes facts and affected IDs, never a route or owner decision beyond the skill's own defect evidence.

## 9. Make the parent decision unambiguous

Ready binds completion, manifest and validation. Blocked binds gate data and blocked report. All condition fields are mutually exclusive, timestamps copy the work order, and the result is outside the content package. The parent can choose exactly one action without parsing logs or chat.
