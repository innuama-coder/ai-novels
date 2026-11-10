import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))
import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import copy
import importlib
import json
import shutil
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


p1 = importlib.import_module(
    "skills.novel-conception-deliverable-assembler.scripts.run_v2"
)


class _Runtime:
    def validate(self, instance, schema_name):
        return None


class _Coordinator:
    def __init__(self, gate=None):
        self.calls = []
        self.gate = gate

    def build_input_gate(
        self,
        target_stage,
        gate_path,
        *,
        active_return_request=None,
    ):
        return self.gate

    def accept_stage_completion(self, **kwargs):
        self.calls.append(kwargs)
        return {"accepted": True}


class P1RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.runtime = p1.rt.ContractRuntime()

    def tearDown(self):
        self.temporary.cleanup()

    def _write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            p1.rt.canonical_json(value), encoding="utf-8", newline=""
        )

    def _reference(self, path, root):
        return p1.rt.artifact_reference(path, root=root)

    def _packages(
        self,
        *,
        q1_verdict="ready",
        input_name="inputs",
        story_value="exact story value",
    ):
        roots = {}
        models = {}
        for stage in p1.STAGES:
            root = self.root / input_name / stage
            root.mkdir(parents=True)
            roots[stage] = root
        design_artifacts = []
        for index, domain in enumerate(
            ("I0", "I1", "I2", "I3", "I4", "I5")
        ):
            path = roots["B0"] / "design" / f"{domain}.json"
            self._write(
                path,
                {
                    "domain": domain,
                    "control": f"author value {index}",
                },
            )
            design_artifacts.append(
                {
                    "domain": domain,
                    "artifact": self._reference(path, roots["B0"]),
                }
            )
        models["B0"] = {
            "schema_version": "2.0",
            "stage": "B0",
            "run_id": "RUN-1",
            "status": "ready",
            "design_artifacts": design_artifacts,
            "control_registry": [
                {
                    "id": "INT-1",
                    "hardness": "author_locked",
                },
                {
                    "id": "WLD-FREE",
                    "hardness": "downstream_freedom",
                },
                {
                    "id": "INT-OPEN",
                    "hardness": "author_open",
                },
            ],
            "open_items": ["INT-OPEN"],
        }
        for stage in p1._MODEL_STAGES:
            models[stage] = {
                "schema_version": "2.0",
                "stage": stage,
                "run_id": "RUN-1",
                "status": "ready",
                "objects": [
                    {
                        "id": f"{stage}-OBJECT-1",
                        "meaning": f"{stage} {story_value}",
                    },
                    {
                        "id": "SLC-SHARED-1",
                        "meaning": f"{stage} shared occurrence",
                    },
                ],
                "authority_partition": {
                    "author_locked": [],
                    "autonomous_owned": (
                        ["CHR-DEV-1"] if stage == "C1" else []
                    ),
                    "downstream_freedom": (
                        ["WLD-FREE"]
                        if stage == "W1"
                        else (["DEV-1"] if stage == "C1" else [])
                    ),
                    "author_open": (
                        ["INT-OPEN"] if stage == "W1" else []
                    ),
                },
                "open_items": (
                    [
                        {
                            "id": "OPEN-INT-1",
                            "question": "Which author-owned value applies?",
                            "source_ids": ["INT-OPEN"],
                            "status": "author_open",
                        }
                    ]
                    if stage == "W1"
                    else []
                ),
            }
        models["C1"]["profiles"] = [{"id": "CHR-DEV-1"}]
        models["C1"]["development_freedoms"] = [
            {
                "id": "DEV-1",
                "subject_ids": ["CHR-DEV-1"],
                "scope": "Scene-level character realization.",
                "allowed_variations": ["Vary gesture and phrasing."],
                "forbidden_changes": ["Do not change the character objective."],
                "acceptance_checks": ["The objective remains recognizable."],
                "source_ids": ["INT-1"],
            }
        ]
        quality_objects = p1._expected_quality_objects(models)
        models["Q1"] = {
            "schema_version": "2.0",
            "skill": "novel-conception-reviewer",
            "stage": "Q1",
            "run_id": "RUN-1",
            "status": q1_verdict,
            "verdict": q1_verdict,
            "findings": [],
            "quality_coverage": {
                "coverage_basis": p1.QUALITY_COVERAGE_BASIS,
                "required_objects": quality_objects,
                "covered_objects": [
                    {
                        **item,
                        "handoff_check_ids": ["CHK-HANDOFF-TRACE"],
                    }
                    for item in quality_objects
                ],
                "unresolved_blocking_quality_record_ids": [],
                "result": "complete",
            },
            "return_request": (
                None
                if q1_verdict == "ready"
                else {"path": "return-request.json", "sha256": "1" * 64}
            ),
        }
        for stage, model in models.items():
            self._write(
                roots[stage] / p1.CANONICAL_NAMES[stage], model
            )
            self._write(
                roots[stage] / "validation.json",
                {"stage": stage, "verdict": "ready"},
            )
            manifest_files = [
                self._reference(path, roots[stage])
                for path in sorted(
                    roots[stage].rglob("*"),
                    key=lambda item: item.as_posix(),
                )
                if path.is_file()
            ]
            self._write(
                roots[stage] / "package-manifest.json",
                {
                    "schema_version": "2.0",
                    "run_id": "RUN-1",
                    "stage": stage,
                    "verdict": "ready",
                    "files": manifest_files,
                },
            )
            self._write(
                roots[stage] / "stage-completion.json",
                {
                    "schema_version": "2.0",
                    "run_id": "RUN-1",
                    "stage": stage,
                    "status": "ready",
                    "manifest": {
                        "path": f"{stage}/package-manifest.json",
                        "sha256": p1.rt.sha256_file(
                            roots[stage] / "package-manifest.json"
                        ),
                    },
                    "validation": {
                        "path": f"{stage}/validation.json",
                        "sha256": p1.rt.sha256_file(
                            roots[stage] / "validation.json"
                        ),
                    },
                },
            )
        refs = {
            stage: {
                "stage": stage,
                "path": f"{stage}/stage-completion.json",
                "sha256": p1.rt.sha256_file(
                    roots[stage] / "stage-completion.json"
                ),
            }
            for stage in p1.STAGES
        }
        self._active_refs = refs
        self._write(
            roots["Q1"] / "input-gate.json",
            {
                "target_stage": "Q1",
                "active_return": None,
                "return_binding": None,
                "upstream_completions": [
                    refs[stage]
                    for stage in ("S1", "W1", "E1", "T1", "C1")
                ],
            },
        )
        q1_manifest = self._read(roots["Q1"] / "package-manifest.json")
        q1_manifest["files"].append(
            self._reference(
                roots["Q1"] / "input-gate.json", roots["Q1"]
            )
        )
        self._write(
            roots["Q1"] / "package-manifest.json", q1_manifest
        )
        self._refresh_input_manifest(roots["Q1"])
        return roots, refs

    def _read(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def _gate(self, refs, **updates):
        data = {
            "schema_version": "2.0",
            "run_id": "RUN-1",
            "target_stage": "P1",
            "entry_mode": "forward",
            "run_state": {
                "path": "state/revision-007.json",
                "sha256": "7" * 64,
            },
            "baseline_completion": refs["B0"],
            "upstream_completions": [
                refs[stage] for stage in p1.UPSTREAM_STAGES
            ],
            "active_return": None,
            "return_binding": None,
        }
        data.update(updates)
        return p1.rt.SealedDocument(
            data=data,
            reference={
                "path": "P1/input-gate.json",
                "sha256": p1.rt.canonical_sha256(data),
            },
        )

    def _run(
        self,
        roots,
        gate,
        *,
        output_name="P1",
        logical_package_path="P1",
        next_state_path="state/revision-008.json",
        active_return_request=None,
        coordinator=None,
    ):
        coordinator = coordinator or _Coordinator(gate)
        if isinstance(coordinator, _Coordinator):
            coordinator.gate = gate
        arguments = {
            "baseline_package": roots["B0"],
            "storyline_package": roots["S1"],
            "world_package": roots["W1"],
            "environment_package": roots["E1"],
            "event_package": roots["T1"],
            "character_package": roots["C1"],
            "review_package": roots["Q1"],
        }
        validators = {
            stage: (lambda root, runtime=None: {"verdict": "ready"})
            for stage in p1.STAGES
        }
        with mock.patch.object(
            p1, "_validator", side_effect=lambda stage: validators[stage]
        ):
            receipt = p1.run_p1(
                self.root / output_name,
                coordinator=coordinator,
                input_gate=gate,
                logical_package_path=logical_package_path,
                next_state_path=next_state_path,
                active_return_request=active_return_request,
                runtime=self.runtime,
                **arguments,
            )
        return receipt, coordinator

    def _validate(self, package_root):
        validators = {
            stage: (lambda root, runtime=None: {"verdict": "ready"})
            for stage in p1.STAGES
        }
        with mock.patch.object(
            p1, "_validator", side_effect=lambda stage: validators[stage]
        ):
            return p1.validate_p1_package(
                package_root, runtime=self.runtime
            )

    def _reseal_manifest_and_completion(self, package_root):
        manifest_path = package_root / "package-manifest.json"
        completion_path = package_root / "stage-completion.json"
        manifest = self._read(manifest_path)
        files = [
            self._reference(path, package_root)
            for path in sorted(
                package_root.rglob("*"), key=lambda item: item.as_posix()
            )
            if path.is_file()
            and path.name not in {
                "package-manifest.json",
                "stage-completion.json",
            }
        ]
        by_path = {item["path"]: item for item in files}
        manifest["files"] = files
        manifest["artifact_roles"] = {
            role: by_path[reference["path"]]
            for role, reference in manifest["artifact_roles"].items()
        }
        manifest["validation"] = by_path["validation.json"]
        manifest["implementation"] = [
            by_path[reference["path"]]
            for reference in manifest["implementation"]
        ]
        self._write(manifest_path, manifest)
        completion = self._read(completion_path)
        completion["manifest"]["sha256"] = p1.rt.sha256_file(manifest_path)
        self._write(completion_path, completion)

    def _refresh_input_manifest(self, package_root):
        manifest_path = package_root / "package-manifest.json"
        manifest = self._read(manifest_path)
        manifest["files"] = [
            self._reference(path, package_root)
            for path in sorted(
                package_root.rglob("*"), key=lambda item: item.as_posix()
            )
            if path.is_file()
            and path.name not in {
                "package-manifest.json",
                "stage-completion.json",
            }
        ]
        self._write(manifest_path, manifest)
        completion_path = package_root / "stage-completion.json"
        completion = self._read(completion_path)
        completion["manifest"]["sha256"] = p1.rt.sha256_file(manifest_path)
        self._write(completion_path, completion)
        stage = completion["stage"]
        if hasattr(self, "_active_refs"):
            self._active_refs[stage]["sha256"] = p1.rt.sha256_file(
                completion_path
            )
        if stage != "Q1" and hasattr(self, "_active_refs"):
            q1_root = package_root.parent / "Q1"
            q1_gate_path = q1_root / "input-gate.json"
            if q1_gate_path.is_file():
                q1_gate = self._read(q1_gate_path)
                q1_gate["upstream_completions"] = [
                    self._active_refs[item]
                    for item in ("S1", "W1", "E1", "T1", "C1")
                ]
                self._write(q1_gate_path, q1_gate)
                self._refresh_input_manifest(q1_root)

    def _refresh_q1_quality_coverage(self, roots):
        models = {
            stage: self._read(
                roots[stage] / p1.CANONICAL_NAMES[stage]
            )
            for stage in ("S1", "T1")
        }
        expected = p1._expected_quality_objects(models)
        review_path = roots["Q1"] / p1.CANONICAL_NAMES["Q1"]
        review = self._read(review_path)
        review["quality_coverage"] = {
            "coverage_basis": p1.QUALITY_COVERAGE_BASIS,
            "required_objects": expected,
            "covered_objects": [
                {
                    **item,
                    "handoff_check_ids": ["CHK-HANDOFF-TRACE"],
                }
                for item in expected
            ],
            "unresolved_blocking_quality_record_ids": [],
            "result": "complete",
        }
        self._write(review_path, review)
        self._refresh_input_manifest(roots["Q1"])

    def _return_binding(self, *, resume_stage="P1", resume_point="P1"):
        request = {
            "path": "returns/RET-P1-1/return-request.json",
            "sha256": "9" * 64,
        }
        return request, {
            "return_id": "RET-P1-1",
            "return_kind": "local_revision",
            "return_request": request,
            "calculated_owner": "P1",
            "resume_stage": resume_stage,
            "resume_point": resume_point,
        }

    def _real_coordinator_through_q1(self, refs):
        initialized = p1.rt.AutonomousCoordinator.initialize(
            run_id="RUN-1",
            source_interview_state={
                "path": "interview/run-state.json",
                "sha256": "1" * 64,
            },
            state_path="state/revision-000.json",
            runtime=self.runtime,
        )
        state = initialized.state
        state["revision"] = 7
        state["current_stage_completions"] = {
            stage: copy.deepcopy(refs[stage])
            for stage in ("B0", "S1", "W1", "E1", "T1", "C1", "Q1")
        }
        state["previous_state"] = {
            "path": "state/revision-006.json",
            "sha256": "6" * 64,
        }
        sealed = p1.rt.seal_document(state, "state/revision-007.json")
        return p1.rt.AutonomousCoordinator.from_snapshot(
            sealed.data,
            sealed.reference,
            runtime=self.runtime,
        )

    def test_forward_gate_and_ready_q1_build_completion(self):
        roots, refs = self._packages()
        receipt, coordinator = self._run(roots, self._gate(refs))
        self.assertFalse(receipt.replayed)
        self.assertTrue(
            (receipt.package_root / "stage-completion.json").is_file()
        )
        self.assertEqual(receipt.conception_package["stage"], "P1")
        self.assertEqual(len(coordinator.calls), 1)
        self.assertEqual(
            self._validate(receipt.package_root)["verdict"],
            "ready",
        )

    def test_formal_logical_package_path_is_exactly_p1(self):
        roots, refs = self._packages()
        gate = self._gate(refs)
        coordinator = _Coordinator(gate)
        with self.assertRaisesRegex(p1.P1Error, "P1_PATH_INVALID"):
            self._run(
                roots,
                gate,
                logical_package_path="packages/P1",
                coordinator=coordinator,
            )
        self.assertFalse((self.root / "P1").exists())
        self.assertEqual([], coordinator.calls)

    def test_same_inputs_are_byte_deterministic(self):
        roots, refs = self._packages()
        first, _ = self._run(roots, self._gate(refs), output_name="P1-A")
        second, _ = self._run(roots, self._gate(refs), output_name="P1-B")
        first_files = {
            path.relative_to(first.package_root).as_posix(): path.read_bytes()
            for path in first.package_root.rglob("*")
            if path.is_file()
        }
        second_files = {
            path.relative_to(second.package_root).as_posix(): path.read_bytes()
            for path in second.package_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(first_files, second_files)

    def test_valid_p1_return_resolution_is_bound_to_completion(self):
        roots, refs = self._packages()
        request, binding = self._return_binding()
        gate = self._gate(
            refs,
            entry_mode="return_resolution",
            active_return=request,
            return_binding=binding,
        )
        receipt, coordinator = self._run(
            roots,
            gate,
            active_return_request=p1.rt.SealedDocument(
                data={"return_id": "RET-P1-1"},
                reference=request,
            ),
        )
        self.assertEqual(receipt.completion.data["return_binding"], binding)
        self.assertEqual(
            coordinator.calls[0]["active_return_request"].reference,
            request,
        )
        self.assertEqual(
            self._validate(receipt.package_root)["verdict"],
            "ready",
        )

    def test_non_p1_return_resolution_is_rejected(self):
        roots, refs = self._packages()
        request, binding = self._return_binding(
            resume_stage="Q1", resume_point="Q1"
        )
        gate = self._gate(
            refs,
            entry_mode="return_resolution",
            active_return=request,
            return_binding=binding,
        )
        with self.assertRaisesRegex(p1.P1Error, "P1_GATE_INVALID"):
            self._run(roots, gate)
        self.assertFalse((self.root / "P1").exists())

    def test_lossless_materialization_and_cross_stage_occurrences(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        output = receipt.package_root
        self.assertEqual(
            (output / "author-control-baseline.json").read_bytes(),
            (
                roots["B0"] / p1.CANONICAL_NAMES["B0"]
            ).read_bytes(),
        )
        for stage in p1._MODEL_STAGES:
            self.assertEqual(
                (
                    output
                    / "canonical-models"
                    / p1.CANONICAL_NAMES[stage]
                ).read_bytes(),
                (roots[stage] / p1.CANONICAL_NAMES[stage]).read_bytes(),
            )
        self.assertEqual(
            (
                output / "review" / p1.CANONICAL_NAMES["Q1"]
            ).read_bytes(),
            (roots["Q1"] / p1.CANONICAL_NAMES["Q1"]).read_bytes(),
        )
        design_index = self._read(
            output / "authoritative-design-index.json"
        )
        self.assertEqual(len(design_index["artifacts"]), 6)
        for item in design_index["artifacts"]:
            source = p1.rt.verify_artifact_reference(
                item["baseline_artifact"], root=roots["B0"]
            )
            target = p1.rt.verify_artifact_reference(
                item["materialized"], root=output
            )
            self.assertEqual(target.read_bytes(), source.read_bytes())
        index = self._read(output / "cross-model-index.json")
        self.assertNotIn(
            "run_id",
            {item["field"] for item in index["references"]},
        )
        shared = [
            item
            for item in index["definitions"]
            if item["id"] == "SLC-SHARED-1"
        ]
        self.assertEqual(
            [item["stage"] for item in shared],
            sorted(p1._MODEL_STAGES),
        )

    def _add_slot_reference_fixture(
        self,
        roots,
        *,
        include_resolution,
        include_generic_shadow=False,
    ):
        slot_id = "SLOT-LEAD"
        event_id = "EV-SLOT-USE"
        demand_id = "CHD-SLOT-USE"
        character_id = "CHR-SLOT-LEAD"

        s1_path = roots["S1"] / p1.CANONICAL_NAMES["S1"]
        s1 = self._read(s1_path)
        s1["objects"].append(
            {
                "id": demand_id,
                "actor_slot_ids": [slot_id],
            }
        )
        if include_generic_shadow:
            s1["objects"].append(
                {
                    "id": slot_id,
                    "meaning": "A generic ID object is not a slot resolution.",
                }
            )
        self._write(s1_path, s1)
        self._refresh_input_manifest(roots["S1"])

        t1_path = roots["T1"] / p1.CANONICAL_NAMES["T1"]
        t1 = self._read(t1_path)
        t1["objects"].append(
            {
                "id": event_id,
                "participant_slot_ids": [slot_id],
                "initiator_slot_id": slot_id,
                "counter_slot_ids": [],
            }
        )
        self._write(t1_path, t1)
        self._refresh_input_manifest(roots["T1"])

        c1_path = roots["C1"] / p1.CANONICAL_NAMES["C1"]
        c1 = self._read(c1_path)
        c1.setdefault("profiles", []).append({"id": character_id})
        if include_resolution:
            c1["slot_resolution"] = [
                {
                    "slot_id": slot_id,
                    "character_id": character_id,
                    "demand_ids": [demand_id],
                    "event_ids": [event_id],
                    "rationale": "The named character resolves the required slot.",
                }
            ]
        self._write(c1_path, c1)
        self._refresh_input_manifest(roots["C1"])
        self._refresh_q1_quality_coverage(roots)
        return slot_id

    def test_c1_slot_resolution_is_the_typed_slot_definition(self):
        roots, refs = self._packages()
        slot_id = self._add_slot_reference_fixture(
            roots,
            include_resolution=True,
        )

        receipt, _ = self._run(roots, self._gate(refs))
        index = self._read(receipt.package_root / "cross-model-index.json")
        definitions = [
            item for item in index["definitions"] if item["id"] == slot_id
        ]
        resolution = self._read(
            roots["C1"] / p1.CANONICAL_NAMES["C1"]
        )["slot_resolution"][0]
        self.assertEqual(
            definitions,
            [
                {
                    "id": slot_id,
                    "stage": "C1",
                    "json_pointer": "/slot_resolution/0",
                    "kind": "slot_resolution",
                    "value_sha256": p1.rt.canonical_sha256(resolution),
                }
            ],
        )
        slot_references = [
            item
            for item in index["references"]
            if item["target_id"] == slot_id
        ]
        self.assertTrue(slot_references)
        self.assertNotIn(
            "/slot_resolution/0/slot_id",
            {item["json_pointer"] for item in slot_references},
        )
        expected_occurrences = [
            {
                key: value
                for key, value in definitions[0].items()
                if key != "id"
            }
        ]
        self.assertTrue(
            all(
                item["target_occurrences"] == expected_occurrences
                for item in slot_references
            )
        )

    def test_generic_slot_id_shadow_cannot_satisfy_slot_reference(self):
        roots, refs = self._packages()
        self._add_slot_reference_fixture(
            roots,
            include_resolution=False,
            include_generic_shadow=True,
        )

        with self.assertRaisesRegex(
            p1.P1Error,
            "P1_CROSS_REFERENCE_UNRESOLVED",
        ):
            self._run(roots, self._gate(refs))
        self.assertFalse((self.root / "P1").exists())

    def test_slot_reference_ignores_generic_shadow_when_typed_target_exists(self):
        roots, refs = self._packages()
        slot_id = self._add_slot_reference_fixture(
            roots,
            include_resolution=True,
            include_generic_shadow=True,
        )

        receipt, _ = self._run(roots, self._gate(refs))
        index = self._read(receipt.package_root / "cross-model-index.json")
        slot_references = [
            item
            for item in index["references"]
            if item["target_id"] == slot_id
        ]
        self.assertTrue(slot_references)
        self.assertTrue(
            all(
                item["target_occurrences"]
                == [
                    {
                        "stage": "C1",
                        "json_pointer": "/slot_resolution/0",
                        "kind": "slot_resolution",
                        "value_sha256": p1.rt.canonical_sha256(
                            self._read(
                                roots["C1"] / p1.CANONICAL_NAMES["C1"]
                            )["slot_resolution"][0]
                        ),
                    }
                ]
                for item in slot_references
            )
        )

    def test_path_handoff_manifest_and_authority_bindings_are_exact(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        output = receipt.package_root
        package = self._read(output / "novel-conception-package.json")
        handoff = self._read(output / "development-handoff.json")
        manifest = self._read(output / "package-manifest.json")
        self.assertEqual(
            package["development_handoff"],
            {"path": "development-handoff.json"},
        )
        self.assertEqual(
            handoff["conception_package"],
            self._reference(
                output / "novel-conception-package.json", output
            ),
        )
        self.assertEqual(
            handoff["mandatory_controls"], ["CHR-DEV-1", "INT-1"]
        )
        self.assertEqual(
            handoff["development_freedoms"], ["DEV-1"]
        )
        self.assertEqual(handoff["must_ask"], ["INT-OPEN"])
        self.assertEqual(handoff["open_items"], ["INT-OPEN"])
        self.assertEqual(
            manifest["artifact_roles"]["conception_package"],
            self._reference(
                output / "novel-conception-package.json", output
            ),
        )
        self.assertEqual(
            manifest["artifact_roles"]["development_handoff"],
            self._reference(output / "development-handoff.json", output),
        )

    def test_handoff_projects_only_terminal_c1_development_freedoms(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        package = self._read(
            receipt.package_root / "novel-conception-package.json"
        )
        handoff = self._read(
            receipt.package_root / "development-handoff.json"
        )
        self.assertEqual(
            package["authority_partition"]["downstream_freedom"],
            ["DEV-1", "WLD-FREE"],
        )
        self.assertEqual(handoff["development_freedoms"], ["DEV-1"])

    def test_dev_references_resolve_to_typed_character_targets(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        index = self._read(receipt.package_root / "cross-model-index.json")
        dev_definitions = [
            item for item in index["definitions"] if item["id"] == "DEV-1"
        ]
        self.assertEqual(len(dev_definitions), 1)
        self.assertEqual(dev_definitions[0]["stage"], "C1")
        self.assertEqual(
            dev_definitions[0]["json_pointer"], "/development_freedoms/0"
        )
        references = [
            item
            for item in index["references"]
            if item["json_pointer"]
            == "/development_freedoms/0/subject_ids/0"
        ]
        self.assertEqual(
            references[0]["target_occurrences"],
            [
                {
                    "stage": "C1",
                    "json_pointer": "/profiles/0",
                    "kind": "profiles",
                    "value_sha256": p1.rt.canonical_sha256(
                        {"id": "CHR-DEV-1"}
                    ),
                }
            ],
        )

    def test_dev_reference_ignores_generic_shadow_when_typed_target_exists(self):
        roots, refs = self._packages()
        s1_path = roots["S1"] / p1.CANONICAL_NAMES["S1"]
        s1 = self._read(s1_path)
        s1["objects"].append(
            {"id": "DEV-1", "meaning": "generic shadow"}
        )
        s1["objects"].append(
            {
                "id": "S1-DEV-CONSUMER",
                "development_freedom_ids": ["DEV-1"],
            }
        )
        self._write(s1_path, s1)
        self._refresh_input_manifest(roots["S1"])
        self._refresh_q1_quality_coverage(roots)
        receipt, _ = self._run(roots, self._gate(refs))
        index = self._read(receipt.package_root / "cross-model-index.json")
        dev_references = [
            item
            for item in index["references"]
            if item["target_id"] == "DEV-1"
        ]
        self.assertTrue(dev_references)
        self.assertTrue(
            all(
                [
                    (
                        target["stage"],
                        target["json_pointer"],
                        target["kind"],
                    )
                    for target in item["target_occurrences"]
                ]
                == [("C1", "/development_freedoms/0", "development_freedoms")]
                for item in dev_references
            )
        )

    def test_source_id_pattern_accepts_dev_and_rejects_unknown_prefix(self):
        self.assertIsNotNone(p1._SOURCE_ID.fullmatch("DEV-SCENE-001"))
        self.assertIsNone(p1._SOURCE_ID.fullmatch("FREEDOM-SCENE-001"))

    def test_generic_dev_shadow_cannot_satisfy_typed_dev_definition(self):
        roots, refs = self._packages()
        c1_path = roots["C1"] / p1.CANONICAL_NAMES["C1"]
        c1 = self._read(c1_path)
        c1["development_freedoms"] = []
        c1["objects"].append(
            {"id": "DEV-1", "meaning": "generic shadow"}
        )
        self._write(c1_path, c1)
        self._refresh_input_manifest(roots["C1"])
        with self.assertRaisesRegex(
            p1.P1Error,
            "P1_CROSS_REFERENCE_UNRESOLVED|P1_TERMINAL_FREEDOM_INVALID",
        ):
            self._run(roots, self._gate(refs))

    def test_dev_subject_must_be_a_c1_profile(self):
        roots, refs = self._packages()
        c1_path = roots["C1"] / p1.CANONICAL_NAMES["C1"]
        c1 = self._read(c1_path)
        c1["profiles"] = []
        c1["objects"].append({"id": "CHR-DEV-1"})
        self._write(c1_path, c1)
        self._refresh_input_manifest(roots["C1"])
        with self.assertRaisesRegex(
            p1.P1Error, "P1_DEV_REFERENCE_INVALID"
        ):
            self._run(roots, self._gate(refs))

    def test_dev_source_must_resolve_in_current_package(self):
        roots, refs = self._packages()
        c1_path = roots["C1"] / p1.CANONICAL_NAMES["C1"]
        c1 = self._read(c1_path)
        c1["development_freedoms"][0]["source_ids"] = ["INT-MISSING"]
        self._write(c1_path, c1)
        self._refresh_input_manifest(roots["C1"])
        with self.assertRaisesRegex(
            p1.P1Error,
            "P1_CROSS_REFERENCE_UNRESOLVED|P1_DEV_REFERENCE_INVALID",
        ):
            self._run(roots, self._gate(refs))

    def test_terminal_dev_must_match_c1_downstream_partition(self):
        roots, refs = self._packages()
        c1_path = roots["C1"] / p1.CANONICAL_NAMES["C1"]
        c1 = self._read(c1_path)
        c1["authority_partition"]["downstream_freedom"] = []
        self._write(c1_path, c1)
        self._refresh_input_manifest(roots["C1"])
        with self.assertRaisesRegex(
            p1.P1Error, "P1_TERMINAL_FREEDOM_INVALID"
        ):
            self._run(roots, self._gate(refs))

    def test_old_c1_without_development_freedoms_fails_closed(self):
        roots, refs = self._packages()
        c1_path = roots["C1"] / p1.CANONICAL_NAMES["C1"]
        c1 = self._read(c1_path)
        del c1["development_freedoms"]
        c1["authority_partition"]["downstream_freedom"] = ["CHR-DEV-1"]
        self._write(c1_path, c1)
        self._refresh_input_manifest(roots["C1"])
        with self.assertRaisesRegex(
            p1.P1Error,
            "P1_AUTHORITY_CONFLICT|P1_TERMINAL_FREEDOM_INVALID",
        ):
            self._run(roots, self._gate(refs))

    def test_non_dev_terminal_freedom_is_rejected_not_filtered(self):
        roots, refs = self._packages()
        c1_path = roots["C1"] / p1.CANONICAL_NAMES["C1"]
        c1 = self._read(c1_path)
        c1["development_freedoms"][0]["id"] = "CHR-NOT-DEV"
        c1["authority_partition"]["downstream_freedom"] = ["CHR-NOT-DEV"]
        self._write(c1_path, c1)
        self._refresh_input_manifest(roots["C1"])
        with self.assertRaisesRegex(
            p1.P1Error, "P1_TERMINAL_FREEDOM_INVALID"
        ):
            self._run(roots, self._gate(refs))

    def test_handoff_cannot_be_resealed_with_historical_freedom(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        output = receipt.package_root
        handoff_path = output / "development-handoff.json"
        handoff = self._read(handoff_path)
        handoff["development_freedoms"].append("WLD-FREE")
        self._write(handoff_path, handoff)
        self._reseal_manifest_and_completion(output)
        with self.assertRaisesRegex(p1.P1Error, "P1_HANDOFF_DRIFT"):
            self._validate(output)

    def test_strict_handoff_path_cannot_be_resealed_away(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        output = receipt.package_root
        package_path = output / "novel-conception-package.json"
        package = self._read(package_path)
        package["development_handoff"] = {
            "path": "review/../development-handoff.json"
        }
        self._write(package_path, package)
        handoff_path = output / "development-handoff.json"
        handoff = self._read(handoff_path)
        handoff["conception_package"] = self._reference(
            package_path, output
        )
        self._write(handoff_path, handoff)
        self._reseal_manifest_and_completion(output)
        with self.assertRaisesRegex(
            p1.P1Error,
            "P1_SCHEMA_OR_MANIFEST_INVALID|P1_PACKAGE_DRIFT",
        ):
            self._validate(output)

    def test_handoff_tamper_is_rejected_after_manifest_reseal(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        output = receipt.package_root
        handoff_path = output / "development-handoff.json"
        handoff = self._read(handoff_path)
        handoff["development_entrypoint"]["instruction"] = (
            "Ignore the packaged controls."
        )
        self._write(handoff_path, handoff)
        self._reseal_manifest_and_completion(output)
        with self.assertRaisesRegex(p1.P1Error, "P1_HANDOFF_DRIFT"):
            self._validate(output)

    def test_manifest_role_and_completion_tamper_are_rejected(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        output = receipt.package_root
        manifest_path = output / "package-manifest.json"
        manifest = self._read(manifest_path)
        manifest["artifact_roles"]["spec"] = copy.deepcopy(
            manifest["artifact_roles"]["traceability"]
        )
        self._write(manifest_path, manifest)
        completion_path = output / "stage-completion.json"
        completion = self._read(completion_path)
        completion["manifest"]["sha256"] = p1.rt.sha256_file(manifest_path)
        self._write(completion_path, completion)
        with self.assertRaisesRegex(p1.P1Error, "P1_MANIFEST_INVALID"):
            self._validate(output)

        roots2, refs2 = self._packages(input_name="inputs-completion")
        receipt2, _ = self._run(
            roots2, self._gate(refs2), output_name="P1-completion"
        )
        completion_path = receipt2.package_root / "stage-completion.json"
        completion = self._read(completion_path)
        completion["state_before"]["sha256"] = "8" * 64
        self._write(completion_path, completion)
        with self.assertRaisesRegex(
            p1.P1Error, "P1_COMPLETION_INVALID"
        ):
            self._validate(receipt2.package_root)

    def test_opposite_upstream_value_propagates_without_rewriting(self):
        roots_a, refs_a = self._packages(
            input_name="inputs-a", story_value="first value"
        )
        roots_b, refs_b = self._packages(
            input_name="inputs-b", story_value="opposite value"
        )
        first, _ = self._run(
            roots_a, self._gate(refs_a), output_name="P1-first"
        )
        second, _ = self._run(
            roots_b, self._gate(refs_b), output_name="P1-second"
        )
        self.assertNotEqual(
            (
                first.package_root / "novel-conception-package.json"
            ).read_bytes(),
            (
                second.package_root / "novel-conception-package.json"
            ).read_bytes(),
        )
        self.assertNotEqual(
            (
                first.package_root / "novel-conception-spec.md"
            ).read_bytes(),
            (
                second.package_root / "novel-conception-spec.md"
            ).read_bytes(),
        )
        self.assertEqual(
            (
                second.package_root
                / "canonical-models"
                / p1.CANONICAL_NAMES["S1"]
            ).read_bytes(),
            (
                roots_b["S1"] / p1.CANONICAL_NAMES["S1"]
            ).read_bytes(),
        )

    def test_authority_id_cannot_cross_partition_classes(self):
        roots, refs = self._packages()
        w1_path = roots["W1"] / p1.CANONICAL_NAMES["W1"]
        w1 = self._read(w1_path)
        w1["authority_partition"]["downstream_freedom"].append("INT-1")
        self._write(w1_path, w1)
        self._refresh_input_manifest(roots["W1"])
        with self.assertRaisesRegex(
            p1.P1Error, "P1_AUTHORITY_CONFLICT"
        ):
            self._run(roots, self._gate(refs))
        self.assertFalse((self.root / "P1").exists())

    def test_author_open_control_requires_open_item_source_coverage(self):
        roots, refs = self._packages()
        w1_path = roots["W1"] / p1.CANONICAL_NAMES["W1"]
        w1 = self._read(w1_path)
        w1["open_items"][0]["source_ids"] = ["WLD-FREE"]
        self._write(w1_path, w1)
        self._refresh_input_manifest(roots["W1"])
        with self.assertRaisesRegex(
            p1.P1Error, "P1_OPEN_ITEM_COVERAGE_MISSING"
        ):
            self._run(roots, self._gate(refs))
        self.assertFalse((self.root / "P1").exists())

    def test_source_change_after_freeze_is_rejected(self):
        roots, refs = self._packages()
        original_copy = p1._copy_exact
        changed = False

        def copy_then_change(source, target):
            nonlocal changed
            original_copy(source, target)
            if not changed:
                changed = True
                source_path = (
                    roots["S1"] / p1.CANONICAL_NAMES["S1"]
                )
                source_path.write_bytes(source_path.read_bytes() + b" ")

        validators = {
            stage: (lambda root, runtime=None: {"verdict": "ready"})
            for stage in p1.STAGES
        }
        with mock.patch.object(
            p1, "_validator", side_effect=lambda stage: validators[stage]
        ), mock.patch.object(p1, "_copy_exact", side_effect=copy_then_change):
            with self.assertRaisesRegex(
                p1.P1Error, "P1_INPUT_MUTATED|P1_CANONICAL_DRIFT"
            ):
                p1.run_p1(
                    self.root / "P1",
                    baseline_package=roots["B0"],
                    storyline_package=roots["S1"],
                    world_package=roots["W1"],
                    environment_package=roots["E1"],
                    event_package=roots["T1"],
                    character_package=roots["C1"],
                    review_package=roots["Q1"],
                    coordinator=_Coordinator(self._gate(refs)),
                    input_gate=self._gate(refs),
                    next_state_path="state/revision-008.json",
                    runtime=self.runtime,
                )
        self.assertFalse((self.root / "P1").exists())

    def test_return_body_must_match_gate_reference_and_return_id(self):
        roots, refs = self._packages()
        request, binding = self._return_binding()
        gate = self._gate(
            refs,
            entry_mode="return_resolution",
            active_return=request,
            return_binding=binding,
        )
        mismatched = p1.rt.SealedDocument(
            data={"return_id": "RET-P1-WRONG"},
            reference=request,
        )
        with self.assertRaisesRegex(p1.P1Error, "P1_GATE_INVALID"):
            self._run(
                roots,
                gate,
                active_return_request=mismatched,
            )
        self.assertFalse((self.root / "P1").exists())

    def test_unresolved_story_reference_is_rejected(self):
        roots, refs = self._packages()
        s1_path = roots["S1"] / p1.CANONICAL_NAMES["S1"]
        s1 = self._read(s1_path)
        s1["objects"].append(
            {
                "id": "SLC-UNRESOLVED-1",
                "trigger_id": "EV-MISSING",
            }
        )
        self._write(s1_path, s1)
        self._refresh_input_manifest(roots["S1"])
        self._refresh_q1_quality_coverage(roots)
        with self.assertRaisesRegex(
            p1.P1Error, "P1_CROSS_REFERENCE_UNRESOLVED"
        ):
            self._run(roots, self._gate(refs))
        self.assertFalse((self.root / "P1").exists())

    def test_resealed_legacy_stage_snapshot_is_rejected(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        output = receipt.package_root
        self._write(
            output / "source-packages" / "D1" / "legacy.json",
            {"legacy": True},
        )
        self._reseal_manifest_and_completion(output)
        with self.assertRaisesRegex(
            p1.P1Error, "P1_SOURCE_SNAPSHOT_BOUNDARY_INVALID"
        ):
            self._validate(output)

    def test_resealed_source_snapshot_root_file_is_rejected(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        output = receipt.package_root
        self._write(
            output / "source-packages" / "rogue.json",
            {"rogue": True},
        )
        self._reseal_manifest_and_completion(output)
        with self.assertRaisesRegex(
            p1.P1Error, "P1_SOURCE_SNAPSHOT_BOUNDARY_INVALID"
        ):
            self._validate(output)

    def test_resealed_missing_stage_snapshot_is_rejected(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        output = receipt.package_root
        shutil.rmtree(output / "source-packages" / "C1")
        self._reseal_manifest_and_completion(output)
        with self.assertRaisesRegex(
            p1.P1Error, "P1_SOURCE_SNAPSHOT_BOUNDARY_INVALID"
        ):
            self._validate(output)

    def test_resealed_multiple_unknown_stage_snapshots_are_rejected(self):
        roots, refs = self._packages()
        receipt, _ = self._run(roots, self._gate(refs))
        output = receipt.package_root
        self._write(
            output / "source-packages" / "R1" / "legacy.json",
            {"legacy": "R1"},
        )
        self._write(
            output / "source-packages" / "X1" / "unknown.json",
            {"legacy": "X1"},
        )
        self._reseal_manifest_and_completion(output)
        with self.assertRaisesRegex(
            p1.P1Error, "P1_SOURCE_SNAPSHOT_BOUNDARY_INVALID"
        ):
            self._validate(output)

    def test_publish_race_does_not_call_coordinator(self):
        roots, refs = self._packages()
        coordinator = _Coordinator()
        destination = self.root / "P1"
        original_replace = Path.replace

        def replace_after_race(source, target):
            Path(target).mkdir(parents=True, exist_ok=False)
            return original_replace(source, target)

        with mock.patch.object(Path, "replace", new=replace_after_race):
            with self.assertRaisesRegex(
                p1.P1Error,
                "P1_SOURCE_SNAPSHOT_BOUNDARY_INVALID",
            ):
                self._run(
                    roots,
                    self._gate(refs),
                    coordinator=coordinator,
                )
        self.assertEqual(coordinator.calls, [])
        self.assertTrue(destination.is_dir())
        self.assertFalse((destination / "stage-completion.json").exists())

    def test_exact_valid_publish_race_winner_is_recovered(self):
        roots, refs = self._packages()
        gate = self._gate(refs)
        coordinator = _Coordinator(gate)
        destination = self.root / "P1"
        winner_bytes = None

        def replace_after_exact_winner(source, target):
            nonlocal winner_bytes
            shutil.copytree(source, target)
            winner_bytes = {
                path.relative_to(target).as_posix(): path.read_bytes()
                for path in Path(target).rglob("*")
                if path.is_file()
            }
            raise FileExistsError("exact concurrent winner")

        with mock.patch.object(
            Path, "replace", new=replace_after_exact_winner
        ):
            receipt, _ = self._run(
                roots,
                gate,
                coordinator=coordinator,
            )
        after = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        self.assertTrue(receipt.replayed)
        self.assertEqual(winner_bytes, after)
        self.assertEqual(1, len(coordinator.calls))
        self.assertEqual(
            receipt.completion,
            coordinator.calls[0]["completion"],
        )

    def test_current_gate_preserves_typed_coordinator_error(self):
        class RaisingCoordinator:
            def build_input_gate(self, *args, **kwargs):
                raise p1.rt.CoordinatorError(
                    "COORD_ILLEGAL_STAGE_TRANSITION",
                    "P1 is not currently admissible",
                )

            def accept_stage_completion(self, **kwargs):
                raise AssertionError("must not accept")

        roots, refs = self._packages()
        with self.assertRaises(p1.rt.CoordinatorError) as caught:
            self._run(
                roots,
                self._gate(refs),
                coordinator=RaisingCoordinator(),
            )
        self.assertEqual(
            "COORD_ILLEGAL_STAGE_TRANSITION",
            caught.exception.code,
        )
        self.assertFalse((self.root / "P1").exists())

    def test_current_gate_wraps_malformed_coordinator_interface(self):
        class MalformedCoordinator:
            def build_input_gate(self, *args, **kwargs):
                return {"not": "a sealed document"}

            def accept_stage_completion(self, **kwargs):
                raise AssertionError("must not accept")

        roots, refs = self._packages()
        with self.assertRaises(p1.P1Error) as caught:
            self._run(
                roots,
                self._gate(refs),
                coordinator=MalformedCoordinator(),
            )
        self.assertEqual("P1_GATE_INVALID", caught.exception.code)
        self.assertFalse((self.root / "P1").exists())

    def test_coordinator_rejection_leaves_valid_unreferenced_package(self):
        class RejectingCoordinator:
            def __init__(self, gate):
                self.calls = []
                self.gate = gate

            def build_input_gate(
                self,
                target_stage,
                gate_path,
                *,
                active_return_request=None,
            ):
                return self.gate

            def accept_stage_completion(self, **kwargs):
                self.calls.append(kwargs)
                raise RuntimeError("coordinator rejected completion")

        roots, refs = self._packages()
        gate = self._gate(refs)
        coordinator = RejectingCoordinator(gate)
        destination = self.root / "P1"
        with self.assertRaisesRegex(
            RuntimeError, "coordinator rejected completion"
        ):
            self._run(
                roots,
                gate,
                coordinator=coordinator,
            )
        self.assertEqual(len(coordinator.calls), 1)
        self.assertTrue((destination / "stage-completion.json").is_file())
        self.assertEqual(
            self._validate(destination)["verdict"],
            "ready",
        )
        before = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        recovery = _Coordinator(gate)
        receipt, _ = self._run(
            roots,
            gate,
            coordinator=recovery,
        )
        after = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        self.assertTrue(receipt.replayed)
        self.assertEqual(before, after)
        self.assertEqual(len(recovery.calls), 1)
        self.assertEqual(
            receipt.completion,
            recovery.calls[0]["completion"],
        )

    def test_existing_p1_with_other_gate_is_rejected_without_overwrite(self):
        roots, refs = self._packages()
        original_gate = self._gate(refs)
        receipt, _ = self._run(roots, original_gate)
        destination = receipt.package_root
        before = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        other_gate = self._gate(
            refs,
            run_state={
                "path": "state/revision-008.json",
                "sha256": "8" * 64,
            },
        )
        coordinator = _Coordinator(other_gate)
        with self.assertRaisesRegex(
            p1.P1Error, "P1_RECOVERY_GATE_MISMATCH"
        ):
            self._run(
                roots,
                other_gate,
                coordinator=coordinator,
            )
        after = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual([], coordinator.calls)

    def test_existing_p1_with_changed_source_is_rejected_without_overwrite(self):
        roots, refs = self._packages()
        gate = self._gate(refs)
        receipt, _ = self._run(roots, gate)
        destination = receipt.package_root
        before = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        s1_path = roots["S1"] / p1.CANONICAL_NAMES["S1"]
        s1 = self._read(s1_path)
        s1["objects"][0]["meaning"] = "changed after orphan publication"
        self._write(s1_path, s1)
        self._refresh_input_manifest(roots["S1"])
        coordinator = _Coordinator(gate)
        with self.assertRaisesRegex(
            p1.P1Error, "P1_RECOVERY_SOURCE_MISMATCH"
        ):
            self._run(roots, gate, coordinator=coordinator)
        after = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual([], coordinator.calls)

    def test_existing_p1_with_noncanonical_completion_is_rejected(self):
        roots, refs = self._packages()
        gate = self._gate(refs)
        receipt, _ = self._run(roots, gate)
        completion_path = receipt.package_root / "stage-completion.json"
        completion = self._read(completion_path)
        completion_path.write_text(
            json.dumps(completion, indent=2),
            encoding="utf-8",
            newline="",
        )
        coordinator = _Coordinator(gate)
        with self.assertRaisesRegex(
            p1.P1Error, "P1_COMPLETION_INVALID"
        ):
            self._run(roots, gate, coordinator=coordinator)
        self.assertEqual([], coordinator.calls)

    def test_existing_p1_with_stale_implementation_is_rejected(self):
        roots, refs = self._packages()
        gate = self._gate(refs)
        self._run(roots, gate)
        stale = dict(p1._implementation_paths())
        alternate = self.root / "alternate-run-v2.py"
        alternate.write_text("# stale implementation\n", encoding="utf-8")
        stale["skill/run_v2.py"] = alternate
        coordinator = _Coordinator(gate)
        with mock.patch.object(
            p1, "_implementation_paths", return_value=stale
        ):
            with self.assertRaisesRegex(
                p1.P1Error, "P1_IMPLEMENTATION_STALE"
            ):
                self._run(roots, gate, coordinator=coordinator)
        self.assertEqual([], coordinator.calls)

    def test_recovery_detects_destination_toctou_before_accept(self):
        roots, refs = self._packages()
        gate = self._gate(refs)
        receipt, _ = self._run(roots, gate)
        destination = receipt.package_root
        manifest_path = (destination / "package-manifest.json").resolve()
        original_read = p1._read
        manifest_reads = 0

        def mutate_after_final_manifest_read(path, code):
            nonlocal manifest_reads
            value = original_read(path, code)
            if Path(path).resolve() == manifest_path:
                manifest_reads += 1
                if manifest_reads == 2:
                    (destination / "late-race.txt").write_text(
                        "race", encoding="utf-8"
                    )
            return value

        coordinator = _Coordinator(gate)
        with mock.patch.object(
            p1, "_read", side_effect=mutate_after_final_manifest_read
        ):
            with self.assertRaisesRegex(
                p1.P1Error, "P1_RECOVERY_OUTPUT_MUTATED"
            ):
                self._run(roots, gate, coordinator=coordinator)
        self.assertEqual(2, manifest_reads)
        self.assertEqual([], coordinator.calls)

    def test_recovery_detects_input_toctou_before_accept(self):
        roots, refs = self._packages()
        gate = self._gate(refs)
        receipt, _ = self._run(roots, gate)
        destination = receipt.package_root
        manifest_path = (destination / "package-manifest.json").resolve()
        original_read = p1._read
        manifest_reads = 0

        def mutate_input_after_final_manifest_read(path, code):
            nonlocal manifest_reads
            value = original_read(path, code)
            if Path(path).resolve() == manifest_path:
                manifest_reads += 1
                if manifest_reads == 2:
                    with (
                        roots["S1"] / p1.CANONICAL_NAMES["S1"]
                    ).open("ab") as stream:
                        stream.write(b" ")
            return value

        coordinator = _Coordinator(gate)
        with mock.patch.object(
            p1, "_read", side_effect=mutate_input_after_final_manifest_read
        ):
            with self.assertRaisesRegex(
                p1.P1Error, "P1_INPUT_MUTATED"
            ):
                self._run(roots, gate, coordinator=coordinator)
        self.assertEqual(2, manifest_reads)
        self.assertEqual([], coordinator.calls)

    def test_return_resolution_orphan_recovers_exact_package(self):
        class RejectingCoordinator(_Coordinator):
            def accept_stage_completion(self, **kwargs):
                self.calls.append(kwargs)
                raise RuntimeError("return transition rejected")

        roots, refs = self._packages()
        request, binding = self._return_binding()
        gate = self._gate(
            refs,
            entry_mode="return_resolution",
            active_return=request,
            return_binding=binding,
        )
        active = p1.rt.SealedDocument(
            data={"return_id": "RET-P1-1"},
            reference=request,
        )
        with self.assertRaisesRegex(
            RuntimeError, "return transition rejected"
        ):
            self._run(
                roots,
                gate,
                active_return_request=active,
                coordinator=RejectingCoordinator(gate),
            )
        destination = self.root / "P1"
        before = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        coordinator = _Coordinator(gate)
        receipt, _ = self._run(
            roots,
            gate,
            active_return_request=active,
            coordinator=coordinator,
        )
        after = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        self.assertTrue(receipt.replayed)
        self.assertEqual(before, after)
        self.assertEqual(1, len(coordinator.calls))
        self.assertEqual(
            request,
            coordinator.calls[0]["active_return_request"].reference,
        )

    def test_real_coordinator_orphan_accept_and_persistent_replay(self):
        class RejectingCoordinator(_Coordinator):
            def accept_stage_completion(self, **kwargs):
                self.calls.append(kwargs)
                raise RuntimeError("leave ordinary orphan")

        roots, refs = self._packages()
        coordinator = self._real_coordinator_through_q1(refs)
        gate = coordinator.build_input_gate("P1", "P1/input-gate.json")
        with self.assertRaisesRegex(RuntimeError, "leave ordinary orphan"):
            self._run(
                roots,
                gate,
                coordinator=RejectingCoordinator(gate),
            )
        destination = self.root / "P1"
        before = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        first, _ = self._run(
            roots,
            gate,
            coordinator=coordinator,
        )
        self.assertTrue(first.replayed)
        self.assertFalse(first.transition.replayed)
        self.assertEqual(
            first.completion.reference,
            coordinator.state["current_stage_completions"]["P1"],
        )

        successor = p1.rt.AutonomousCoordinator.from_snapshot(
            first.transition.snapshot,
            first.transition.reference,
            runtime=self.runtime,
        )
        second, _ = self._run(
            roots,
            gate,
            coordinator=successor,
        )
        after = {
            path.relative_to(destination).as_posix(): path.read_bytes()
            for path in destination.rglob("*")
            if path.is_file()
        }
        self.assertTrue(second.replayed)
        self.assertTrue(second.transition.replayed)
        self.assertEqual(before, after)
        self.assertEqual(first.completion, second.completion)

    def test_real_coordinator_return_resolution_is_one_shot(self):
        class RejectingCoordinator(_Coordinator):
            def accept_stage_completion(self, **kwargs):
                self.calls.append(kwargs)
                raise RuntimeError("leave return orphan")

        roots, refs = self._packages()
        coordinator = self._real_coordinator_through_q1(refs)
        request_data = p1.rt.route_return(
            run_id="RUN-1",
            return_id="RET-P1-REAL",
            origin_kind="stage",
            origin_stage="P1",
            issue_kind="package_assembly",
            problem="P1 package requires a local revision",
            evidence_ids=["P1-EVIDENCE-1"],
            violated_contract="P1 package contract",
            required_revision="Reassemble the exact P1 package.",
            author_decision=None,
            has_current_author_decision=False,
            has_current_conception_completion=False,
            runtime=self.runtime,
        )
        active = p1.rt.seal_document(
            request_data,
            "returns/RET-P1-REAL/return-request.json",
        )
        coordinator.apply_return_request(
            request=active,
            next_state_path="state/revision-008.json",
        )
        gate = coordinator.build_input_gate(
            "P1",
            "P1/input-gate.json",
            active_return_request=active,
        )
        with self.assertRaisesRegex(RuntimeError, "leave return orphan"):
            self._run(
                roots,
                gate,
                next_state_path="state/revision-009.json",
                active_return_request=active,
                coordinator=RejectingCoordinator(gate),
            )
        first, _ = self._run(
            roots,
            gate,
            next_state_path="state/revision-009.json",
            active_return_request=active,
            coordinator=coordinator,
        )
        self.assertTrue(first.replayed)
        self.assertFalse(first.transition.replayed)
        successor = p1.rt.AutonomousCoordinator.from_snapshot(
            first.transition.snapshot,
            first.transition.reference,
            runtime=self.runtime,
        )
        with self.assertRaises(p1.rt.CoordinatorError) as caught:
            self._run(
                roots,
                gate,
                next_state_path="state/revision-009.json",
                active_return_request=active,
                coordinator=successor,
            )
        self.assertEqual(
            "COORD_RETURN_ALREADY_RESOLVED",
            caught.exception.code,
        )

    def test_nonready_q1_is_a_hard_gate(self):
        roots, refs = self._packages(q1_verdict="revise")
        with self.assertRaisesRegex(p1.P1Error, "P1_Q1_NOT_READY"):
            self._run(roots, self._gate(refs))

    def test_q1_partial_quality_coverage_is_a_hard_gate(self):
        roots, refs = self._packages()
        review_path = roots["Q1"] / p1.CANONICAL_NAMES["Q1"]
        review = self._read(review_path)
        review["quality_coverage"]["covered_objects"].pop()
        self._write(review_path, review)
        self._refresh_input_manifest(roots["Q1"])
        with self.assertRaisesRegex(
            p1.P1Error, "P1_Q1_QUALITY_COVERAGE_INVALID"
        ):
            self._run(roots, self._gate(refs))

    def test_q1_unresolved_quality_record_is_a_hard_gate(self):
        roots, refs = self._packages()
        review_path = roots["Q1"] / p1.CANONICAL_NAMES["Q1"]
        review = self._read(review_path)
        review["quality_coverage"][
            "unresolved_blocking_quality_record_ids"
        ] = ["CHK-HANDOFF-CAUSAL"]
        review["quality_coverage"]["result"] = "incomplete"
        self._write(review_path, review)
        self._refresh_input_manifest(roots["Q1"])
        with self.assertRaisesRegex(
            p1.P1Error, "P1_Q1_QUALITY_COVERAGE_INVALID"
        ):
            self._run(roots, self._gate(refs))
        self.assertFalse((self.root / "P1").exists())

    def test_gate_requires_exact_order_through_q1(self):
        roots, refs = self._packages()
        wrong = [refs[stage] for stage in p1.UPSTREAM_STAGES]
        wrong[0], wrong[1] = wrong[1], wrong[0]
        with self.assertRaisesRegex(p1.P1Error, "P1_GATE_INVALID"):
            self._run(
                roots,
                self._gate(refs, upstream_completions=wrong),
            )
        self.assertFalse((self.root / "P1").exists())

    def test_extra_upstream_root_file_is_rejected(self):
        roots, refs = self._packages()
        (roots["S1"] / "smuggled-chat.txt").write_text(
            "legacy answer", encoding="utf-8"
        )
        with self.assertRaisesRegex(
            p1.P1Error, "P1_S1_PACKAGE_BOUNDARY_INVALID"
        ):
            self._run(roots, self._gate(refs))
        self.assertFalse((self.root / "P1").exists())


if __name__ == "__main__":
    unittest.main()
