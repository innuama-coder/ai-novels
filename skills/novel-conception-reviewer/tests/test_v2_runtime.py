"""Q1 V2 runtime tests.

The Agent fixtures in this module simulate distinct controlled contexts by
patching environment identities.  They are test-only evidence and do not make
same-thread production execution acceptable.
"""

from __future__ import annotations

import copy
import importlib
import inspect
import json
import os
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


q1 = importlib.import_module(
    "skills.novel-conception-reviewer.scripts.run_v2"
)


class Q1InterfaceAndIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _identity(self, task: str, thread: str):
        return mock.patch.dict(
            os.environ,
            {
                "CODEX_TASK_ID": task,
                "CODEX_THREAD_ID": thread,
                "Q1_TEST_AGENT_FIXTURE": "1",
            },
            clear=False,
        )

    def test_public_state_machine_api_has_no_identity_override(self):
        expected = {
            "start_q1_controller",
            "start_semantic_review",
            "submit_semantic_phase",
            "start_handoff_review",
            "seal_handoff_review",
            "import_sealed_handoff",
            "submit_final_review",
            "validate_q1_package",
            "run_q1",
        }
        self.assertTrue(expected <= set(q1.__all__))
        for name in expected:
            parameters = inspect.signature(getattr(q1, name)).parameters
            self.assertNotIn("task_id", parameters, name)
            self.assertNotIn("thread_id", parameters, name)

    def test_identity_requires_task_and_thread_from_environment(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_CONTROLLED_IDENTITY_REQUIRED"
            ):
                q1._identity()
        with mock.patch.dict(
            os.environ, {"CODEX_TASK_ID": "semantic-task"}, clear=True
        ):
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_CONTROLLED_IDENTITY_REQUIRED"
            ):
                q1._identity()

    def test_handoff_materialization_is_an_exact_physical_allowlist(self):
        sources: dict[str, Path] = {}
        for stage, names in {
            "B0": ("author-control-baseline.json", "package-manifest.json"),
            "S1": ("storyline-architecture.json", "package-manifest.json"),
            "W1": ("world-model.json", "package-manifest.json"),
            "E1": ("environment-system.json", "package-manifest.json"),
            "T1": ("event-timeline.json", "package-manifest.json"),
            "C1": ("character-system.json", "package-manifest.json"),
        }.items():
            for name in names:
                source = self.root / "source" / stage / name
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text(f"{stage}:{name}", encoding="utf-8")
                sources[f"{stage}/{name}"] = source
        workspace = self.root / "handoff"
        inventory = q1.materialize_exact_allowlist(
            workspace, files=sources
        )
        actual = {
            path.relative_to(workspace).as_posix()
            for path in (workspace / "inputs").rglob("*")
            if path.is_file()
        }
        self.assertEqual(
            actual,
            {f"inputs/{logical}" for logical in sources},
        )
        self.assertEqual(
            {item["path"] for item in inventory},
            actual,
        )
        self.assertFalse(
            any(
                forbidden in path
                for path in actual
                for forbidden in (
                    "stage-completion",
                    "validation",
                    "generation-evidence",
                    "chat",
                    "interview",
                    "semantic",
                    "expected",
                )
            )
        )

    def test_allowlist_rejects_path_escape_and_existing_workspace(self):
        source = self.root / "source.json"
        source.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(q1.Q1Error, "Q1_PATH_INVALID"):
            q1.materialize_exact_allowlist(
                self.root / "escape",
                files={"../source.json": source},
            )
        workspace = self.root / "existing"
        workspace.mkdir()
        with self.assertRaisesRegex(q1.Q1Error, "Q1_WORKSPACE_EXISTS"):
            q1.materialize_exact_allowlist(
                workspace,
                files={"B0/author-control-baseline.json": source},
            )

    def test_semantic_api_cannot_submit_controller_owned_phase4(self):
        with self._identity("semantic-task", "semantic-thread"):
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_SEMANTIC_PHASE_FORBIDDEN"
            ):
                q1.submit_semantic_phase(
                    self.root / "controller",
                    self.root / "semantic",
                    phase=q1.HANDOFF_PHASE,
                    payload={"forged": True},
                )

    def _q1_source_packages(self):
        roots = {}
        names = q1.STAGE_CANONICAL
        models = {
            "B0": {
                "run_id": "RUN-1",
                "control_registry": [
                    {
                        "id": "INT-1",
                        "meaning": "author subject control",
                        "links": ["SL-1"],
                    }
                ],
            },
            "S1": {
                "run_id": "RUN-1",
                "objects": [
                    {
                        "id": "SL-1",
                        "meaning": "main storyline",
                        "links": ["EV-1", "WF-1"],
                    }
                ],
            },
            "W1": {
                "run_id": "RUN-1",
                "objects": [
                    {
                        "id": "WF-1",
                        "meaning": "world rule",
                        "links": ["EV-1", "ENV-1"],
                    }
                ],
            },
            "E1": {
                "run_id": "RUN-1",
                "objects": [
                    {
                        "id": "ENV-1",
                        "meaning": "event environment",
                        "links": ["EV-1", "WF-1"],
                    }
                ],
            },
            "T1": {
                "run_id": "RUN-1",
                "objects": [
                    {
                        "id": "EV-1",
                        "meaning": "causal event",
                        "links": ["SL-1", "ENV-1", "CHR-1", "WF-1"],
                    }
                ],
            },
            "C1": {
                "run_id": "RUN-1",
                "objects": [
                    {
                        "id": "CHR-1",
                        "meaning": "choosing character",
                        "links": ["EV-1"],
                    }
                ],
            },
        }
        for stage, canonical in names.items():
            root = self.root / "packages" / stage
            root.mkdir(parents=True, exist_ok=True)
            (root / canonical).write_text(
                json.dumps(models[stage], ensure_ascii=False),
                encoding="utf-8",
            )
            (root / "package-manifest.json").write_text(
                f"{stage}:manifest", encoding="utf-8"
            )
            roots[stage] = root
        return roots

    def _handoff_controller(self, packages):
        controller = self.root / "controller"
        controller.mkdir()
        implementation_identity = q1._implementation_identity()
        sources = q1._handoff_allowlist(
            baseline_package=packages["B0"],
            storyline_package=packages["S1"],
            world_package=packages["W1"],
            environment_package=packages["E1"],
            event_package=packages["T1"],
            character_package=packages["C1"],
        )
        state = {
            "schema_version": "2.0",
            "run_id": "RUN-1",
            "revision": 0,
            "status": "semantic_p1_p3_complete",
            "previous_state_sha256": None,
            "input_gate": {"path": "Q1/input-gate.json", "sha256": "0" * 64},
            "semantic_identity": {
                "task_id": "semantic-task",
                "thread_id": "semantic-thread",
            },
            "semantic_session_id": "SEM-1",
            "completed_phases": list(q1.SEMANTIC_PHASES),
            "generation_identities": [
                {
                    "task_id": f"{stage}-task",
                    "thread_id": f"{stage}-thread",
                }
                for stage in q1.UPSTREAM_STAGES
            ],
            "handoff_source_inventory": [
                {"path": name, "sha256": q1._sha256_file(path)}
                for name, path in sorted(sources.items())
            ],
            "implementation_identity": implementation_identity,
        }
        q1._write(
            controller / "state" / "revision-000.json",
            state,
        )
        q1._write(
            controller / "frozen-inputs.json",
            {
                "package_roots": {
                    stage: str(root.resolve())
                    for stage, root in packages.items()
                },
                "source_inventory": q1._source_inventory(packages),
                "implementation_identity": implementation_identity,
            },
        )
        return controller

    def _handoff_payload(self, session, handoff):
        index = q1._handoff_object_index(handoff)
        checks = [
            self._check("HANDOFF-SUBJECT", "story_subject"),
            self._check("HANDOFF-TRACE", "storyline_trace"),
            self._check("HANDOFF-EVENT", "event_conditions"),
            self._check("HANDOFF-CHOICE", "character_choices"),
            self._check("HANDOFF-FREEDOM", "development_freedoms"),
            self._check("CHK-HANDOFF-CHRONOLOGY", "chronology_reconstruction"),
            self._check("CHK-HANDOFF-CAUSAL", "causal_precondition_trace"),
            self._check("CHK-HANDOFF-INFORMATION", "information_release_trace"),
            self._check("CHK-HANDOFF-AUTHOR", "author_control_trace"),
        ]
        specifications = [
            (["INT-1"], "story-subject", "reconstruct-subject", None),
            (
                ["SL-1", "EV-1"],
                "storyline-event-trace",
                "trace-development",
                "EV-1",
            ),
            (
                ["WF-1", "EV-1"],
                "event-condition",
                "locate-preconditions",
                "EV-1",
            ),
            (
                ["EV-1", "CHR-1"],
                "character-choice",
                "explain-choice",
                "CHR-1",
            ),
            (
                ["INT-1"],
                "development-boundary",
                "locate-freedom",
                None,
            ),
            (
                ["SL-1", "EV-1"],
                "chronology-reconstruction",
                "reconstruct-chronology",
                "EV-1",
            ),
            (
                ["SL-1", "EV-1"],
                "causal-precondition",
                "trace-preconditions",
                "EV-1",
            ),
            (
                ["SL-1", "EV-1"],
                "information-release",
                "trace-information-release",
                "EV-1",
            ),
            (
                ["INT-1", "SL-1", "EV-1"],
                "author-control",
                "trace-author-control",
                "SL-1",
            ),
        ]
        bindings = [
            self._bind_check(
                check,
                index,
                evidence_ids=evidence_ids,
                predicate=predicate,
                operator=operator,
                target_id=target_id,
            )
            for check, (evidence_ids, predicate, operator, target_id)
            in zip(checks, specifications)
        ]
        evidence_ids = list(
            dict.fromkeys(
                evidence_id
                for check in checks
                for evidence_id in check["evidence_ids"]
            )
        )
        return {
            "development_usability_test": {
                "id": "HANDOFF-1",
                "tested_tasks": list(q1.HANDOFF_TASKS),
                "evidence_ids": evidence_ids,
                "conclusion": (
                    "The package supports all nine tasks with projected "
                    "story values."
                ),
                "result": "pass",
            },
            "read_set": [item["path"] for item in session["allowlist"]],
            "responses": {
                "story_subject": "subject restatement",
                "storyline_trace": "trace through stable IDs",
                "event_conditions": "preconditions and consequences",
                "character_choices": "motivation, information and cost",
                "development_freedoms": "declared downstream freedoms",
                "chronology_reconstruction": "ordered world-time reconstruction",
                "causal_precondition_trace": "precondition-to-consequence trace",
                "information_release_trace": "knowledge and disclosure trace",
                "author_control_trace": "author control and freedom trace",
            },
            "handoff_checks": checks,
            "assertion_bindings": bindings,
        }

    def test_start_handoff_seals_exact_twelve_file_projection(self):
        packages = self._q1_source_packages()
        controller = self._handoff_controller(packages)
        workspace = self.root / "handoff"
        with self._identity("handoff-task", "handoff-thread"):
            session = q1.start_handoff_review(
                controller,
                workspace,
                baseline_package=packages["B0"],
                storyline_package=packages["S1"],
                world_package=packages["W1"],
                environment_package=packages["E1"],
                event_package=packages["T1"],
                character_package=packages["C1"],
            )
        actual = {
            path.relative_to(workspace).as_posix()
            for path in (workspace / "inputs").rglob("*")
            if path.is_file()
        }
        self.assertEqual(len(actual), 12)
        self.assertEqual(
            actual,
            {item["path"] for item in session["allowlist"]},
        )
        self.assertEqual(session["identity"]["task_id"], "handoff-task")

    def test_start_handoff_rejects_identity_overlap(self):
        packages = self._q1_source_packages()
        controller = self._handoff_controller(packages)
        with self._identity("semantic-task", "fresh-thread"):
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_HANDOFF_NOT_ISOLATED"
            ):
                q1.start_handoff_review(
                    controller,
                    self.root / "handoff",
                    baseline_package=packages["B0"],
                    storyline_package=packages["S1"],
                    world_package=packages["W1"],
                    environment_package=packages["E1"],
                    event_package=packages["T1"],
                    character_package=packages["C1"],
                )

    def test_sealed_handoff_is_imported_one_way_as_phase4(self):
        packages = self._q1_source_packages()
        controller = self._handoff_controller(packages)
        handoff = self.root / "handoff"
        semantic = self.root / "semantic"
        semantic.mkdir()
        q1._write(
            semantic / "generation-session.json",
            {
                "session_id": "SEM-1",
                "identity": {
                    "task_id": "semantic-task",
                    "thread_id": "semantic-thread",
                },
            },
        )
        for index, phase in enumerate(q1.SEMANTIC_PHASES, 1):
            q1._write(
                semantic / "generation-evidence" / f"{index:02d}-{phase}.json",
                {"phase": phase},
            )
        with self._identity("handoff-task", "handoff-thread"):
            session = q1.start_handoff_review(
                controller,
                handoff,
                baseline_package=packages["B0"],
                storyline_package=packages["S1"],
                world_package=packages["W1"],
                environment_package=packages["E1"],
                event_package=packages["T1"],
                character_package=packages["C1"],
            )
            q1.seal_handoff_review(
                controller,
                handoff,
                payload=self._handoff_payload(session, handoff),
            )
        with self._identity("semantic-task", "semantic-thread"):
            reference = q1.import_sealed_handoff(
                controller, semantic, handoff
            )
        self.assertEqual(
            reference["path"],
            "generation-evidence/04-development-handoff-test.json",
        )
        self.assertFalse((semantic / "inputs").exists())
        self.assertEqual(
            q1._latest_state(controller)["status"],
            "handoff_imported",
        )

    def test_handoff_seal_rejects_extra_physical_input(self):
        packages = self._q1_source_packages()
        controller = self._handoff_controller(packages)
        handoff = self.root / "handoff"
        with self._identity("handoff-task", "handoff-thread"):
            session = q1.start_handoff_review(
                controller,
                handoff,
                baseline_package=packages["B0"],
                storyline_package=packages["S1"],
                world_package=packages["W1"],
                environment_package=packages["E1"],
                event_package=packages["T1"],
                character_package=packages["C1"],
            )
            (handoff / "inputs/expected-answer.json").write_text(
                "{}", encoding="utf-8"
            )
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_HANDOFF_ALLOWLIST_MISMATCH"
            ):
                q1.seal_handoff_review(
                    controller,
                    handoff,
                    payload=self._handoff_payload(session, handoff),
                )

    def test_handoff_hash_and_read_set_attacks_are_rejected(self):
        packages = self._q1_source_packages()
        controller = self._handoff_controller(packages)
        handoff = self.root / "handoff"
        with self._identity("handoff-task", "handoff-thread"):
            session = q1.start_handoff_review(
                controller,
                handoff,
                baseline_package=packages["B0"],
                storyline_package=packages["S1"],
                world_package=packages["W1"],
                environment_package=packages["E1"],
                event_package=packages["T1"],
                character_package=packages["C1"],
            )
            first = handoff / session["allowlist"][0]["path"]
            original = first.read_bytes()
            first.write_bytes(original + b"tamper")
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_HANDOFF_ALLOWLIST_MISMATCH"
            ):
                q1.seal_handoff_review(
                    controller,
                    handoff,
                    payload=self._handoff_payload(session, handoff),
                )
            first.write_bytes(original)
            payload = self._handoff_payload(session, handoff)
            payload["read_set"] = payload["read_set"][:-1]
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_HANDOFF_READ_SET_INVALID"
            ):
                q1.seal_handoff_review(
                    controller,
                    handoff,
                    payload=payload,
                )

    def test_controller_freezes_gate_sources_and_generation_identities(self):
        packages = self._q1_source_packages()
        gate = types.SimpleNamespace(
            data={"run_state": {"path": "state.json", "sha256": "1" * 64}},
            reference={"path": "Q1/input-gate.json", "sha256": "2" * 64},
        )
        inventory = q1._source_inventory(packages)
        validated = {
            "run_id": "RUN-1",
            "baseline_completion": {
                "stage": "B0",
                "path": "B0/stage-completion.json",
                "sha256": "3" * 64,
            },
            "upstream_completions": [
                {
                    "stage": stage,
                    "path": f"{stage}/stage-completion.json",
                    "sha256": str(index) * 64,
                }
                for index, stage in enumerate(q1.UPSTREAM_STAGES, 4)
            ],
            "generation_identities": [
                {
                    "task_id": f"{stage}-task",
                    "thread_id": f"{stage}-thread",
                }
                for stage in q1.UPSTREAM_STAGES
            ],
            "source_inventory": inventory,
        }
        with (
            self._identity("controller-task", "controller-thread"),
            mock.patch.object(
                q1, "_revalidate_inputs", return_value=validated
            ),
        ):
            frozen = q1.start_q1_controller(
                self.root / "controller",
                baseline_package=packages["B0"],
                storyline_package=packages["S1"],
                world_package=packages["W1"],
                environment_package=packages["E1"],
                event_package=packages["T1"],
                character_package=packages["C1"],
                input_gate=gate,
            )
        self.assertEqual(len(frozen["handoff_source_inventory"]), 12)
        self.assertEqual(
            frozen["implementation_identity"], q1._implementation_identity()
        )
        self.assertEqual(
            q1._latest_state(self.root / "controller")["status"],
            "inputs_frozen",
        )

    def test_semantic_start_rejects_generation_identity_overlap(self):
        packages = self._q1_source_packages()
        gate = types.SimpleNamespace(
            data={"run_state": {"path": "state.json", "sha256": "1" * 64}},
            reference={"path": "Q1/input-gate.json", "sha256": "2" * 64},
        )
        inventory = q1._source_inventory(packages)
        validated = {
            "run_id": "RUN-1",
            "baseline_completion": {},
            "upstream_completions": [],
            "generation_identities": [
                {
                    "task_id": f"{stage}-task",
                    "thread_id": f"{stage}-thread",
                }
                for stage in q1.UPSTREAM_STAGES
            ],
            "source_inventory": inventory,
        }
        with (
            self._identity("controller-task", "controller-thread"),
            mock.patch.object(
                q1, "_revalidate_inputs", return_value=validated
            ),
        ):
            q1.start_q1_controller(
                self.root / "controller",
                baseline_package=packages["B0"],
                storyline_package=packages["S1"],
                world_package=packages["W1"],
                environment_package=packages["E1"],
                event_package=packages["T1"],
                character_package=packages["C1"],
                input_gate=gate,
            )
        with (
            self._identity("S1-task", "fresh-thread"),
            mock.patch.object(
                q1, "_revalidate_inputs", return_value=validated
            ),
        ):
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_SEMANTIC_NOT_ISOLATED"
            ):
                q1.start_semantic_review(
                    self.root / "controller",
                    self.root / "semantic",
                    baseline_package=packages["B0"],
                    storyline_package=packages["S1"],
                    world_package=packages["W1"],
                    environment_package=packages["E1"],
                    event_package=packages["T1"],
                    character_package=packages["C1"],
                    input_gate=gate,
                )

    def _active_semantic(self):
        controller = self.root / "controller"
        semantic = self.root / "semantic"
        controller.mkdir()
        semantic.mkdir()
        packages = self._q1_source_packages()
        identity = {
            "task_id": "semantic-task",
            "thread_id": "semantic-thread",
        }
        implementation_identity = q1._implementation_identity()
        state = {
            "schema_version": "2.0",
            "run_id": "RUN-1",
            "revision": 0,
            "status": "semantic_running",
            "previous_state_sha256": None,
            "input_gate": {
                "path": "Q1/input-gate.json",
                "sha256": "1" * 64,
            },
            "semantic_identity": identity,
            "semantic_session_id": "SEM-1",
            "completed_phases": [],
            "implementation_identity": implementation_identity,
        }
        q1._write(controller / "state" / "revision-000.json", state)
        q1._write(
            controller / "frozen-inputs.json",
            {
                "package_roots": {
                    stage: str(root.resolve())
                    for stage, root in packages.items()
                },
                "source_inventory": q1._source_inventory(packages),
                "implementation_identity": implementation_identity,
            },
        )
        q1._write(
            semantic / "generation-session.json",
            {
                "schema_version": "2.0",
                "run_id": "RUN-1",
                "stage": "Q1",
                "role": "semantic-reviewer",
                "session_id": "SEM-1",
                "identity": identity,
                "input_gate": state["input_gate"],
                "source_inventory": [
                    {"path": "S1/model.json", "sha256": "2" * 64}
                ],
            },
        )
        return controller, semantic

    def _check(self, identifier, scope):
        return {
            "id": identifier,
            "scope": scope,
            "checked_contract": "contract",
            "method": "trace concrete story evidence",
            "evidence_ids": [f"{scope}-OBJECT-1"],
            "conclusion": f"story-specific conclusion for {identifier}",
            "result": "pass",
        }

    def _story_index(self, packages):
        output = {}
        for stage, canonical in q1.STAGE_CANONICAL.items():
            q1._index_objects(
                q1._read(packages[stage] / canonical, "test"),
                stage=stage,
                output=output,
            )
        return output

    def test_story_index_allows_cross_stage_ids_and_rejects_same_stage(self):
        index = {}
        identifiers = {
            "B0": "CHR-001",
            "S1": "SL-001",
            "W1": "WF-001",
            "E1": "ENV-001",
            "T1": "EV-001",
            "C1": "CHR-001",
        }
        for stage, identifier in identifiers.items():
            q1._index_objects(
                {
                    "objects": [
                        {
                            "id": identifier,
                            "meaning": f"{stage} distinct meaning",
                        }
                    ]
                },
                stage=stage,
                output=index,
            )
        self.assertNotEqual(
            index[("B0", "CHR-001")]["value_sha256"],
            index[("C1", "CHR-001")]["value_sha256"],
        )
        plan = {
            "object_fingerprints": [
                {
                    "id": identifier,
                    "stage": stage,
                    "value_sha256": index[
                        (stage, identifier)
                    ]["value_sha256"],
                }
                for stage, identifier in identifiers.items()
            ]
        }
        q1._validate_plan_fingerprints(plan, index)

        with self.assertRaisesRegex(
            q1.Q1Error, "Q1_STORY_OBJECT_AMBIGUOUS"
        ):
            q1._index_objects(
                {
                    "objects": [
                        {"id": "SL-DUP", "meaning": "first"},
                        {"id": "SL-DUP", "meaning": "second"},
                    ]
                },
                stage="S1",
                output={},
            )

    def test_review_plan_cannot_sample_away_s1_or_t1_objects(self):
        packages = self._q1_source_packages()
        index = self._story_index(packages)
        q1._index_objects(
            {
                "objects": [
                    {
                        "id": "SL-SECOND",
                        "meaning": "second required storyline object",
                    }
                ]
            },
            stage="S1",
            output=index,
        )
        with self.assertRaisesRegex(
            q1.Q1Error, "Q1_REVIEW_PLAN_BINDING_INVALID"
        ):
            q1._validate_plan_fingerprints(
                {"object_fingerprints": self._plan_fingerprints(index)},
                index,
            )

    def test_quality_trace_tasks_must_cover_every_s1_t1_object(self):
        packages = self._q1_source_packages()
        index = self._story_index(packages)
        q1._index_objects(
            {
                "objects": [
                    {
                        "id": "EV-SECOND",
                        "meaning": "second required timeline realization",
                    }
                ]
            },
            stage="T1",
            output=index,
        )
        payload = {
            "assertion_bindings": [
                {
                    "check_id": "CHK-HANDOFF-CHRONOLOGY",
                    "scope": "chronology_reconstruction",
                    "evidence_objects": [
                        {
                            "stage": "S1",
                            "id": "SL-1",
                            "value_sha256": index[("S1", "SL-1")][
                                "value_sha256"
                            ],
                        },
                        {
                            "stage": "T1",
                            "id": "EV-1",
                            "value_sha256": index[("T1", "EV-1")][
                                "value_sha256"
                            ],
                        },
                    ],
                }
            ]
        }
        with self.assertRaisesRegex(
            q1.Q1Error, "Q1_QUALITY_COVERAGE_INCOMPLETE"
        ):
            q1._validate_quality_trace_coverage(payload, index)

    def test_dev_objects_are_c1_owned_development_freedoms(self):
        self.assertEqual(q1._OWNER_PREFIXES["DEV-"], "C1")
        self.assertEqual(
            q1._object_kind("C1", "DEV-SCENE-001"),
            "development-freedom",
        )
        self.assertEqual(
            q1._owner_for_finding(
                {
                    "id": "FND-DEV-001",
                    "affected_ids": ["DEV-SCENE-001"],
                    "evidence_ids": [],
                },
                author_ids=set(),
            ),
            ("C1", "C1"),
        )

    def _plan_fingerprints(self, index):
        return [
            {
                "id": next(
                    record["id"]
                    for record in index.values()
                    if record["stage"] == stage
                ),
                "stage": stage,
                "value_sha256": next(
                    record["value_sha256"]
                    for record in index.values()
                    if record["stage"] == stage
                ),
            }
            for stage in q1.STAGE_CANONICAL
        ]

    def _record_for_id(self, index, identifier, stage=None):
        matches = [
            record
            for record in index.values()
            if record["id"] == identifier
            and (stage is None or record["stage"] == stage)
        ]
        self.assertEqual(
            len(matches),
            1,
            f"test fixture must select one {(stage, identifier)} object",
        )
        return matches[0]

    def _bind_check(
        self,
        check,
        index,
        *,
        evidence_ids,
        predicate,
        operator,
        target_id=None,
    ):
        check["evidence_ids"] = list(evidence_ids)
        selected = []
        for position, identifier in enumerate(evidence_ids):
            record = self._record_for_id(index, identifier)
            paths = ["/meaning"]
            if position == 0 and target_id is not None:
                paths.append("/links")
            selected.append(
                {
                    "id": identifier,
                    "stage": record["stage"],
                    "kind": record["kind"],
                    "value_sha256": record["value_sha256"],
                    "projections": [
                        {
                            "path": path,
                            "value_sha256": q1._canonical_sha256(
                                q1._pointer_value(record["value"], path)
                            ),
                        }
                        for path in paths
                    ],
                }
            )
        check["conclusion"] = (
            f"{check['id']}: "
            f"{self._record_for_id(index, evidence_ids[0])['value']['meaning']}"
        )
        binding = {
            "check_id": check["id"],
            "scope": check["scope"],
            "evidence_objects": selected,
            "assertion": {
                "predicate": predicate,
                "subject_id": evidence_ids[0],
                "target_id": target_id,
                "challenge_operator": operator,
                "result": check["result"],
            },
        }
        digest = q1._canonical_sha256(binding)
        binding["assertion_sha256"] = digest
        check["method"] = f"story-assertion:{digest}"
        return binding

    def _bind_semantic_payload(self, payload, index, phase):
        bindings = []
        if phase == "domain-challenges":
            stage_ids = {
                record["stage"]: record["id"]
                for record in index.values()
            }
            for check in payload["domain_reviews"]:
                bindings.append(
                    self._bind_check(
                        check,
                        index,
                        evidence_ids=[stage_ids[check["scope"]]],
                        predicate="domain-contract",
                        operator="challenge-domain",
                    )
                )
            bindings.extend(
                [
                    self._bind_check(
                        payload["reality_claim_review"][0],
                        index,
                        evidence_ids=["WF-1"],
                        predicate="reality-claim",
                        operator="verify-reality",
                    ),
                    self._bind_check(
                        payload["coverage_recalculation"][0],
                        index,
                        evidence_ids=["SL-1", "EV-1"],
                        predicate="covers",
                        operator="recompute-coverage",
                        target_id="EV-1",
                    ),
                    self._bind_check(
                        payload["causal_challenges"][0],
                        index,
                        evidence_ids=["EV-1", "CHR-1"],
                        predicate="causal-dependency",
                        operator="break-cause",
                        target_id="CHR-1",
                    ),
                    self._bind_check(
                        payload["easy_solution_challenges"][0],
                        index,
                        evidence_ids=["EV-1", "WF-1"],
                        predicate="counterfactual-pressure",
                        operator="remove-convenience",
                        target_id="WF-1",
                    ),
                ]
            )
        else:
            bindings.extend(
                [
                    self._bind_check(
                        payload["cross_domain_checks"][0],
                        index,
                        evidence_ids=["SL-1", "EV-1"],
                        predicate="cross-domain-reference",
                        operator="compare-domains",
                        target_id="EV-1",
                    ),
                    self._bind_check(
                        payload["consistency_matrix"][0],
                        index,
                        evidence_ids=["WF-1", "EV-1"],
                        predicate="consistent-with",
                        operator="compare-semantics",
                        target_id="EV-1",
                    ),
                ]
            )
        payload["assertion_bindings"] = bindings
        return payload

    def test_semantic_phases_form_forward_hash_chain(self):
        controller, semantic = self._active_semantic()
        frozen = q1._read(controller / "frozen-inputs.json", "test")
        object_index = q1._story_object_index(frozen)
        payloads = {
            "review-plan": {
                "review_plan": {
                    "domain_scopes": list(q1.UPSTREAM_STAGES),
                    "cross_domain_dimensions": ["coverage", "causality"],
                    "evidence_strategy": "cite stable story object IDs",
                    "challenge_strategy": "try counterexamples",
                    "object_fingerprints": self._plan_fingerprints(
                        object_index
                    ),
                }
            },
            "domain-challenges": {
                "domain_reviews": [
                    self._check(f"CHK-{stage}", stage)
                    for stage in q1.UPSTREAM_STAGES
                ],
                "reality_claim_review": [
                    self._check("CHK-REALITY", "reality")
                ],
                "coverage_recalculation": [
                    self._check("CHK-COVERAGE", "coverage")
                ],
                "causal_challenges": [
                    self._check("CHK-CAUSE", "causality")
                ],
                "easy_solution_challenges": [
                    self._check("CHK-EASY", "easy-solution")
                ],
            },
            "cross-domain-challenges": {
                "cross_domain_checks": [
                    self._check("CHK-CROSS", "cross-domain")
                ],
                "consistency_matrix": [
                    self._check("CHK-CONSISTENCY", "consistency")
                ],
            },
        }
        self._bind_semantic_payload(
            payloads["domain-challenges"],
            object_index,
            "domain-challenges",
        )
        self._bind_semantic_payload(
            payloads["cross-domain-challenges"],
            object_index,
            "cross-domain-challenges",
        )
        references = []
        with self._identity("semantic-task", "semantic-thread"):
            for phase in q1.SEMANTIC_PHASES:
                references.append(
                    q1.submit_semantic_phase(
                        controller,
                        semantic,
                        phase=phase,
                        payload=payloads[phase],
                    )
                )
        self.assertEqual(
            q1._latest_state(controller)["status"],
            "semantic_p1_p3_complete",
        )
        second = q1._read(
            semantic / "generation-evidence/02-domain-challenges.json",
            "test",
        )
        self.assertEqual(
            second["previous_evidence_sha256"],
            references[0]["sha256"],
        )

    def test_semantic_phase_order_and_identity_are_hard_gates(self):
        controller, semantic = self._active_semantic()
        payload = {
            "cross_domain_checks": [
                self._check("CHK-CROSS", "cross-domain")
            ],
            "consistency_matrix": [
                self._check("CHK-CONSISTENCY", "consistency")
            ],
        }
        with self._identity("semantic-task", "semantic-thread"):
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_SEMANTIC_PHASE_ORDER_INVALID"
            ):
                q1.submit_semantic_phase(
                    controller,
                    semantic,
                    phase="cross-domain-challenges",
                    payload=payload,
                )
        with self._identity("forged-task", "forged-thread"):
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_SEMANTIC_IDENTITY_MISMATCH"
            ):
                q1.submit_semantic_phase(
                    controller,
                    semantic,
                    phase="review-plan",
                    payload={
                        "review_plan": {
                            "domain_scopes": list(q1.UPSTREAM_STAGES),
                            "cross_domain_dimensions": ["coverage"],
                            "evidence_strategy": "IDs",
                            "challenge_strategy": "counterexamples",
                        }
                    },
                )

    def _active_final_review(self):
        controller = self.root / "controller-final"
        semantic = self.root / "semantic-final"
        controller.mkdir()
        semantic.mkdir()
        packages = self._q1_source_packages()
        object_index = self._story_index(packages)
        identity = {
            "task_id": "semantic-task",
            "thread_id": "semantic-thread",
        }
        handoff_identity = {
            "task_id": "handoff-task",
            "thread_id": "handoff-thread",
        }
        implementation_identity = q1._implementation_identity()
        gate_data = {
            "run_state": {
                "path": "run-state.json",
                "sha256": "7" * 64,
            },
            "upstream_completions": [
                {
                    "stage": stage,
                    "path": f"{stage}/stage-completion.json",
                    "sha256": str(index) * 64,
                }
                for index, stage in enumerate(q1.UPSTREAM_STAGES, 1)
            ],
            "return_binding": None,
        }
        input_gate = {
            "path": "Q1/input-gate.json",
            "sha256": q1._canonical_sha256(gate_data),
        }
        allowlist = [
            {"path": f"inputs/file-{index}.json", "sha256": str(index) * 64}
            for index in range(1, 7)
        ]
        handoff_path = (
            semantic / "sealed-handoff/handoff-test-evidence.json"
        )
        handoff_test = {
            "id": "HANDOFF-1",
            "tested_tasks": list(q1.HANDOFF_TASKS),
            "evidence_ids": ["SL-1", "EV-1"],
            "conclusion": "usable",
            "result": "pass",
        }
        trace_checks = [
            self._check("CHK-HANDOFF-CHRONOLOGY", "chronology_reconstruction"),
            self._check("CHK-HANDOFF-CAUSAL", "causal_precondition_trace"),
            self._check("CHK-HANDOFF-INFORMATION", "information_release_trace"),
            self._check("CHK-HANDOFF-AUTHOR", "author_control_trace"),
        ]
        trace_specs = [
            ("chronology-reconstruction", "reconstruct-chronology"),
            ("causal-precondition", "trace-preconditions"),
            ("information-release", "trace-information-release"),
            ("author-control", "trace-author-control"),
        ]
        trace_bindings = [
            self._bind_check(
                check,
                object_index,
                evidence_ids=["SL-1", "EV-1"],
                predicate=predicate,
                operator=operator,
                target_id="EV-1",
            )
            for check, (predicate, operator) in zip(
                trace_checks, trace_specs
            )
        ]
        handoff_payload = {
            "development_usability_test": handoff_test,
            "handoff_checks": trace_checks,
            "assertion_bindings": trace_bindings,
        }
        q1._write(
            handoff_path,
            {"payload": handoff_payload},
        )
        handoff_ref = q1._artifact_reference(handoff_path, root=semantic)
        q1._write(
            semantic / "sealed-handoff/handoff-execution-record.json",
            {
                "operation": "independent-development-handoff-test",
                "identity": handoff_identity,
                "allowlist": allowlist,
                "read_set": [item["path"] for item in allowlist],
                "output": {
                    "path": "handoff-test-evidence.json",
                    "sha256": handoff_ref["sha256"],
                },
            },
        )
        state = {
            "schema_version": "2.0",
            "run_id": "RUN-1",
            "revision": 0,
            "status": "handoff_imported",
            "previous_state_sha256": None,
            "input_gate": input_gate,
            "semantic_identity": identity,
            "semantic_session_id": "SEM-1",
            "handoff_identity": handoff_identity,
            "handoff_allowlist": allowlist,
            "completed_phases": [
                *q1.SEMANTIC_PHASES,
                q1.HANDOFF_PHASE,
            ],
            "imported_handoff": {"evidence": handoff_ref},
            "implementation_identity": implementation_identity,
        }
        q1._write(controller / "state/revision-000.json", state)
        q1._write(
            controller / "frozen-inputs.json",
            {
                "package_roots": {
                    stage: str(root.resolve())
                    for stage, root in packages.items()
                },
                "source_inventory": q1._source_inventory(packages),
                "implementation_identity": implementation_identity,
            },
        )
        q1._write(
            semantic / "generation-session.json",
            {
                "schema_version": "2.0",
                "run_id": "RUN-1",
                "stage": "Q1",
                "role": "semantic-reviewer",
                "session_id": "SEM-1",
                "identity": identity,
            },
        )
        p2 = {
            "domain_reviews": [
                self._check(f"CHK-{stage}", stage)
                for stage in q1.UPSTREAM_STAGES
            ],
            "reality_claim_review": [
                self._check("CHK-REALITY", "reality")
            ],
            "coverage_recalculation": [
                self._check("CHK-COVERAGE", "coverage")
            ],
            "causal_challenges": [
                self._check("CHK-CAUSE", "causality")
            ],
            "easy_solution_challenges": [
                self._check("CHK-EASY", "easy")
            ],
        }
        p3 = {
            "cross_domain_checks": [
                self._check("CHK-CROSS", "cross")
            ],
            "consistency_matrix": [
                self._check("CHK-CONSISTENCY", "consistency")
            ],
        }
        p1 = {
            "review_plan": {
                "domain_scopes": list(q1.UPSTREAM_STAGES),
                "cross_domain_dimensions": ["coverage"],
                "evidence_strategy": "IDs",
                "challenge_strategy": "counterexamples",
                "object_fingerprints": self._plan_fingerprints(
                    object_index
                ),
            }
        }
        self._bind_semantic_payload(
            p2, object_index, "domain-challenges"
        )
        self._bind_semantic_payload(
            p3, object_index, "cross-domain-challenges"
        )
        previous = None
        for index, phase, payload in (
            (1, "review-plan", p1),
            (2, "domain-challenges", p2),
            (3, "cross-domain-challenges", p3),
        ):
            path = (
                semantic
                / "generation-evidence"
                / f"{index:02d}-{phase}.json"
            )
            q1._write(
                path,
                {
                    "phase": phase,
                    "sequence": index,
                    "previous_evidence_sha256": previous,
                    "payload": payload,
                    "payload_sha256": q1._canonical_sha256(payload),
                },
            )
            previous = q1._sha256_file(path)
        phase4_path = (
            semantic
            / "generation-evidence/04-development-handoff-test.json"
        )
        q1._write(
            phase4_path,
            {
                "phase": q1.HANDOFF_PHASE,
                "sequence": 4,
                "previous_evidence_sha256": previous,
            },
        )
        review = {
            "schema_version": "2.0",
            "skill": "novel-conception-reviewer",
            "stage": "Q1",
            "run_id": "RUN-1",
            "status": "ready",
            "input_gate": input_gate,
            **{
                key: value
                for key, value in p2.items()
                if key != "assertion_bindings"
            },
            **{
                key: value
                for key, value in p3.items()
                if key != "assertion_bindings"
            },
            "development_usability_test": handoff_test,
            "handoff_test_evidence": handoff_ref,
            "task_isolation": {
                "semantic_task_id": "semantic-task",
                "handoff_task_id": "handoff-task",
                "handoff_allowlist": allowlist,
                "forbidden_reads": list(q1.FORBIDDEN_HANDOFF_READS),
            },
            "findings": [
                {
                    "id": "FND-NOTE-1",
                    "severity": "note",
                    "problem": "non-blocking observation",
                    "evidence_ids": ["SL-1"],
                    "affected_ids": ["SL-1"],
                    "violated_contract": "none",
                    "calculated_owner": "S1",
                    "required_revision": "none",
                    "minimum_rerun": "S1",
                }
            ],
            "return_request": None,
            "verdict": "ready",
        }
        review["quality_coverage"] = q1._quality_coverage_certificate(
            object_index=object_index,
            handoff_payload=handoff_payload,
            semantic_payloads=(p2, p3),
            findings=review["findings"],
        )
        known = {
            "SL-1",
            *[
                evidence_id
                for check in [*p2["domain_reviews"], *[
                    p2["reality_claim_review"][0],
                    p2["coverage_recalculation"][0],
                    p2["causal_challenges"][0],
                    p2["easy_solution_challenges"][0],
                    p3["cross_domain_checks"][0],
                    p3["consistency_matrix"][0],
                ]]
                for evidence_id in check["evidence_ids"]
            ],
        }
        return controller, semantic, review, known

    def test_final_ready_review_seals_only_agent_authored_model(self):
        controller, semantic, review, known = self._active_final_review()

        class Runtime:
            def validate(self, instance, schema_name):
                self.instance = instance

        with (
            self._identity("semantic-task", "semantic-thread"),
            mock.patch.object(q1, "_known_story_ids", return_value=known),
            mock.patch.object(q1, "_author_control_ids", return_value=set()),
            mock.patch.object(
                q1, "_validate_frozen_source_inventory", return_value={}
            ),
        ):
            reference = q1.submit_final_review(
                controller, semantic, review=review, runtime=Runtime()
            )
        self.assertEqual(reference["path"], "conception-review.json")
        self.assertEqual(
            q1._latest_state(controller)["status"], "final_sealed"
        )

    def test_final_review_rejects_forged_finding_owner(self):
        controller, semantic, review, known = self._active_final_review()
        review["findings"][0]["calculated_owner"] = "W1"

        class Runtime:
            def validate(self, instance, schema_name):
                pass

        with (
            self._identity("semantic-task", "semantic-thread"),
            mock.patch.object(q1, "_known_story_ids", return_value=known),
            mock.patch.object(q1, "_author_control_ids", return_value=set()),
            mock.patch.object(
                q1, "_validate_frozen_source_inventory", return_value={}
            ),
        ):
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_FINDING_OWNER_INVALID"
            ):
                q1.submit_final_review(
                    controller, semantic, review=review, runtime=Runtime()
                )

    def test_final_review_rejects_generic_non_story_evidence(self):
        controller, semantic = self._active_semantic()
        frozen = q1._read(controller / "frozen-inputs.json", "test")
        object_index = q1._story_object_index(frozen)
        plan = {
            "review_plan": {
                "domain_scopes": list(q1.UPSTREAM_STAGES),
                "cross_domain_dimensions": ["coverage"],
                "evidence_strategy": "stable story object IDs",
                "challenge_strategy": "counterexamples",
                "object_fingerprints": self._plan_fingerprints(
                    object_index
                ),
            }
        }
        domain = {
            "domain_reviews": [
                self._check(f"CHK-{stage}", stage)
                for stage in q1.UPSTREAM_STAGES
            ],
            "reality_claim_review": [
                self._check("CHK-REALITY", "reality")
            ],
            "coverage_recalculation": [
                self._check("CHK-COVERAGE", "coverage")
            ],
            "causal_challenges": [
                self._check("CHK-CAUSE", "causality")
            ],
            "easy_solution_challenges": [
                self._check("CHK-EASY", "easy")
            ],
        }
        self._bind_semantic_payload(
            domain, object_index, "domain-challenges"
        )
        for index, checks in enumerate(
            [
                domain["domain_reviews"],
                domain["reality_claim_review"],
                domain["coverage_recalculation"],
                domain["causal_challenges"],
                domain["easy_solution_challenges"],
            ]
        ):
            for offset, check in enumerate(checks):
                check["conclusion"] = (
                    f"All required fields exist {index}-{offset}"
                )
        with self._identity("semantic-task", "semantic-thread"):
            q1.submit_semantic_phase(
                controller,
                semantic,
                phase="review-plan",
                payload=plan,
            )
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_GENERIC_SEMANTIC_EVIDENCE"
            ):
                q1.submit_semantic_phase(
                    controller,
                    semantic,
                    phase="domain-challenges",
                    payload=domain,
                )

    def test_opposite_upstream_semantics_require_new_agent_bindings(self):
        packages = self._q1_source_packages()
        index_a = self._story_index(packages)

        def agent_payloads(index):
            plan = {
                "domain_scopes": list(q1.UPSTREAM_STAGES),
                "cross_domain_dimensions": ["coverage"],
                "evidence_strategy": "project current story values",
                "challenge_strategy": "challenge current relations",
                "object_fingerprints": self._plan_fingerprints(index),
            }
            domain = {
                "domain_reviews": [
                    self._check(f"CHK-{stage}", stage)
                    for stage in q1.UPSTREAM_STAGES
                ],
                "reality_claim_review": [
                    self._check("CHK-REALITY", "reality")
                ],
                "coverage_recalculation": [
                    self._check("CHK-COVERAGE", "coverage")
                ],
                "causal_challenges": [
                    self._check("CHK-CAUSE", "causality")
                ],
                "easy_solution_challenges": [
                    self._check("CHK-EASY", "easy")
                ],
            }
            cross = {
                "cross_domain_checks": [
                    self._check("CHK-CROSS", "cross")
                ],
                "consistency_matrix": [
                    self._check("CHK-CONSISTENCY", "consistency")
                ],
            }
            self._bind_semantic_payload(
                domain, index, "domain-challenges"
            )
            self._bind_semantic_payload(
                cross, index, "cross-domain-challenges"
            )
            handoff_check = self._check(
                "HANDOFF-TRACE", "storyline_trace"
            )
            handoff_binding = self._bind_check(
                handoff_check,
                index,
                evidence_ids=["SL-1", "EV-1"],
                predicate="storyline-event-trace",
                operator="trace-development",
                target_id="EV-1",
            )
            handoff = {
                "handoff_checks": [handoff_check],
                "assertion_bindings": [handoff_binding],
            }
            return plan, domain, cross, handoff

        plan_a, domain_a, cross_a, handoff_a = agent_payloads(index_a)
        storyline_path = (
            packages["S1"] / q1.STAGE_CANONICAL["S1"]
        )
        storyline = q1._read(storyline_path, "test")
        storyline["objects"][0]["meaning"] = (
            "opposite storyline: the crisis is deliberately preserved"
        )
        q1._write(storyline_path, storyline)
        index_b = self._story_index(packages)
        plan_b, domain_b, cross_b, handoff_b = agent_payloads(index_b)

        self.assertNotEqual(
            plan_a["object_fingerprints"],
            plan_b["object_fingerprints"],
        )
        self.assertNotEqual(
            domain_a["assertion_bindings"],
            domain_b["assertion_bindings"],
        )
        self.assertNotEqual(
            cross_a["assertion_bindings"],
            cross_b["assertion_bindings"],
        )
        self.assertNotEqual(
            handoff_a["assertion_bindings"],
            handoff_b["assertion_bindings"],
        )
        with self.assertRaisesRegex(
            q1.Q1Error, "Q1_REVIEW_PLAN_BINDING_INVALID"
        ):
            q1._validate_plan_fingerprints(plan_a, index_b)
        for payload, phase in (
            (domain_a, "domain-challenges"),
            (cross_a, "cross-domain-challenges"),
            (handoff_a, "handoff"),
        ):
            with self.assertRaisesRegex(
                q1.Q1Error, "Q1_ASSERTION_BINDING_INVALID"
            ):
                q1._validate_assertion_bindings(
                    payload,
                    object_index=index_b,
                    phase=phase,
                )

    def test_run_q1_ready_builds_exact_package_and_completion(self):
        controller, semantic, review, known = self._active_final_review()

        class Runtime:
            def validate(self, instance, schema_name):
                pass

        runtime = Runtime()
        with (
            self._identity("semantic-task", "semantic-thread"),
            mock.patch.object(q1, "_known_story_ids", return_value=known),
            mock.patch.object(q1, "_author_control_ids", return_value=set()),
            mock.patch.object(
                q1, "_validate_frozen_source_inventory", return_value={}
            ),
        ):
            q1.submit_final_review(
                controller, semantic, review=review, runtime=runtime
            )
        packages = self._q1_source_packages()
        gate = types.SimpleNamespace(
            data={
                "run_state": {
                    "path": "run-state.json",
                    "sha256": "7" * 64,
                },
                "upstream_completions": [
                    {
                        "stage": stage,
                        "path": f"{stage}/stage-completion.json",
                        "sha256": str(index) * 64,
                    }
                    for index, stage in enumerate(q1.UPSTREAM_STAGES, 1)
                ],
                "return_binding": None,
            },
            reference=review["input_gate"],
        )
        frozen = q1._read(
            controller / "frozen-inputs.json", "test"
        )
        frozen["package_roots"] = {
            stage: str(root.resolve()) for stage, root in packages.items()
        }
        frozen["source_inventory"] = q1._source_inventory(packages)
        frozen["input_gate"] = gate.reference
        q1._write(controller / "frozen-inputs.json", frozen)

        class RuntimeModule:
            @staticmethod
            def seal_stage_document(data, stage, path):
                return types.SimpleNamespace(
                    data=dict(data),
                    reference={
                        "stage": stage,
                        "path": path,
                        "sha256": q1._canonical_sha256(data),
                    },
                )

        class Coordinator:
            def accept_stage_completion(self, **kwargs):
                return types.SimpleNamespace(snapshot={"revision": 1})

        real_import = q1.importlib.import_module

        def import_side_effect(name):
            if name == "harnesses.novel-conception-autonomous.runtime":
                return RuntimeModule
            return real_import(name)

        output = self.root / "Q1"
        with (
            self._identity("semantic-task", "semantic-thread"),
            mock.patch.object(
                q1.importlib,
                "import_module",
                side_effect=import_side_effect,
            ),
        ):
            receipt = q1.run_q1(
                output,
                baseline_package=packages["B0"],
                storyline_package=packages["S1"],
                world_package=packages["W1"],
                environment_package=packages["E1"],
                event_package=packages["T1"],
                character_package=packages["C1"],
                coordinator=Coordinator(),
                input_gate=gate,
                controller_workspace=controller,
                semantic_workspace=semantic,
                handoff_workspace=self.root / "unused-handoff",
                next_state_path="state-1.json",
                runtime=runtime,
            )
        self.assertEqual(receipt.verdict, "ready")
        self.assertTrue((output / "stage-completion.json").is_file())
        self.assertFalse((output / "return-request.json").exists())
        self.assertEqual(
            q1.validate_q1_package(output, runtime=runtime)["verdict"],
            "ready",
        )
        execution = q1._read(output / "execution-record.json", "test")
        original_execution = copy.deepcopy(execution)
        execution["implementation_identity"]["canonical_digest"] = "0" * 64
        q1._write(output / "execution-record.json", execution)
        with self.assertRaisesRegex(q1.Q1Error, "Q1_IMPLEMENTATION_STALE"):
            q1.validate_q1_package(output, runtime=runtime)
        q1._write(output / "execution-record.json", original_execution)
        execution = copy.deepcopy(original_execution)
        execution["implementation_catalog"].append(
            copy.deepcopy(execution["implementation_catalog"][0])
        )
        execution["implementation"].append(
            copy.deepcopy(execution["implementation"][0])
        )
        q1._write(output / "execution-record.json", execution)
        with self.assertRaisesRegex(q1.Q1Error, "Q1_IMPLEMENTATION_STALE"):
            q1.validate_q1_package(output, runtime=runtime)
        q1._write(output / "execution-record.json", original_execution)
        completion = q1._read(output / "stage-completion.json", "test")
        original_completion = dict(completion)
        completion["state_before"] = {
            "path": "run-state.json",
            "sha256": "0" * 64,
        }
        q1._write(output / "stage-completion.json", completion)
        with self.assertRaisesRegex(
            q1.Q1Error, "Q1_COMPLETION_INVALID"
        ):
            q1.validate_q1_package(output, runtime=runtime)
        q1._write(output / "stage-completion.json", original_completion)
        manifest = q1._read(output / "package-manifest.json", "test")
        manifest["files"][0]["sha256"] = "0" * 64
        q1._write(output / "package-manifest.json", manifest)
        with self.assertRaisesRegex(q1.Q1Error, "Q1_MANIFEST_INVALID"):
            q1.validate_q1_package(output, runtime=runtime)

    def test_run_q1_revise_builds_return_bundle_without_completion(self):
        controller, semantic, review, known = self._active_final_review()
        finding = review["findings"][0]
        finding["severity"] = "revise"
        finding["problem"] = "storyline causal link is incomplete"
        finding["required_revision"] = "repair SL-1 causal transition"
        review["status"] = "revise"
        review["verdict"] = "revise"
        review["return_request"] = {"finding_id": finding["id"]}
        review["quality_coverage"][
            "unresolved_blocking_quality_record_ids"
        ] = [finding["id"]]
        review["quality_coverage"]["result"] = "incomplete"

        class Runtime:
            def validate(self, instance, schema_name):
                pass

        class RuntimeModule:
            @staticmethod
            def route_return(**kwargs):
                return {
                    "schema_version": "2.0",
                    "run_id": kwargs["run_id"],
                    "return_id": kwargs["return_id"],
                    "return_kind": "local_revision",
                    "origin_kind": "stage",
                    "origin_stage": "Q1",
                    "author_decision": None,
                    "problem": kwargs["problem"],
                    "evidence_ids": kwargs["evidence_ids"],
                    "violated_contract": kwargs["violated_contract"],
                    "calculated_owner": "S1",
                    "owner_basis": "§14.1 rule=storyline",
                    "required_revision": kwargs["required_revision"],
                    "target_stage": "S1",
                    "resume_stage": "S1",
                    "resume_point": "S1",
                    "invalidated_stages": [
                        "S1",
                        "W1",
                        "E1",
                        "T1",
                        "C1",
                        "Q1",
                        "P1",
                        "H1",
                    ],
                    "invalidated_h1_artifacts": [
                        "plan",
                        "fragments",
                        "assembly",
                        "html",
                        "completion",
                    ],
                    "invalidate_author_decision": False,
                    "invalidate_conception_completion": False,
                    "status": "active",
                }

            @staticmethod
            def seal_document(data, path):
                return types.SimpleNamespace(
                    data=dict(data),
                    reference={
                        "path": path,
                        "sha256": q1._canonical_sha256(data),
                    },
                )

        runtime = Runtime()
        real_import = q1.importlib.import_module

        def import_side_effect(name):
            if name == "harnesses.novel-conception-autonomous.runtime":
                return RuntimeModule
            return real_import(name)

        with (
            self._identity("semantic-task", "semantic-thread"),
            mock.patch.object(q1, "_known_story_ids", return_value=known),
            mock.patch.object(q1, "_author_control_ids", return_value=set()),
            mock.patch.object(
                q1, "_validate_frozen_source_inventory", return_value={}
            ),
            mock.patch.object(
                q1.importlib,
                "import_module",
                side_effect=import_side_effect,
            ),
        ):
            q1.submit_final_review(
                controller, semantic, review=review, runtime=runtime
            )
        packages = self._q1_source_packages()
        gate = types.SimpleNamespace(
            data={
                "run_state": {
                    "path": "run-state.json",
                    "sha256": "7" * 64,
                },
                "upstream_completions": [
                    {
                        "stage": stage,
                        "path": f"{stage}/stage-completion.json",
                        "sha256": str(index) * 64,
                    }
                    for index, stage in enumerate(q1.UPSTREAM_STAGES, 1)
                ],
                "return_binding": None,
            },
            reference=review["input_gate"],
        )
        frozen = q1._read(controller / "frozen-inputs.json", "test")
        frozen["package_roots"] = {
            stage: str(root.resolve()) for stage, root in packages.items()
        }
        frozen["source_inventory"] = q1._source_inventory(packages)
        frozen["input_gate"] = gate.reference
        q1._write(controller / "frozen-inputs.json", frozen)

        class Coordinator:
            def apply_return_request(self, **kwargs):
                return types.SimpleNamespace(
                    snapshot={
                        "revision": 1,
                        "status": "revise",
                        "active_return": {
                            "path": "Q1/return-request.json",
                            "sha256": "9" * 64,
                        },
                    }
                )

        output = self.root / "Q1-return"
        with (
            self._identity("semantic-task", "semantic-thread"),
            mock.patch.object(
                q1.importlib,
                "import_module",
                side_effect=import_side_effect,
            ),
        ):
            receipt = q1.run_q1(
                output,
                baseline_package=packages["B0"],
                storyline_package=packages["S1"],
                world_package=packages["W1"],
                environment_package=packages["E1"],
                event_package=packages["T1"],
                character_package=packages["C1"],
                coordinator=Coordinator(),
                input_gate=gate,
                controller_workspace=controller,
                semantic_workspace=semantic,
                handoff_workspace=self.root / "unused-handoff",
                next_state_path="state-1.json",
                runtime=runtime,
            )
        self.assertEqual(receipt.verdict, "revise")
        self.assertTrue((output / "return-request.json").is_file())
        self.assertTrue((output / "next-run-state.json").is_file())
        self.assertFalse((output / "stage-completion.json").exists())
        self.assertFalse((output / "package-manifest.json").exists())


class Q1ProductionAcceptanceOutline(unittest.TestCase):
    def _run_case(self, name):
        case = Q1InterfaceAndIsolationTests(name)
        result = unittest.TestResult()
        case.run(result)
        if result.errors or result.failures:
            details = "\n".join(
                message for _, message in [*result.errors, *result.failures]
            )
            self.fail(details)

    def test_ready_dual_context_happy_path(self):
        self._run_case(
            "test_sealed_handoff_is_imported_one_way_as_phase4"
        )
        self._run_case(
            "test_run_q1_ready_builds_exact_package_and_completion"
        )

    def test_revise_routes_without_ready_completion(self):
        self._run_case(
            "test_run_q1_revise_builds_return_bundle_without_completion"
        )

    def test_same_context_and_upstream_generation_identity_are_rejected(self):
        self._run_case("test_start_handoff_rejects_identity_overlap")
        self._run_case(
            "test_semantic_start_rejects_generation_identity_overlap"
        )

    def test_handoff_extra_file_hash_and_read_set_attacks_are_rejected(self):
        self._run_case("test_handoff_seal_rejects_extra_physical_input")
        self._run_case(
            "test_handoff_hash_and_read_set_attacks_are_rejected"
        )

    def test_generic_semantic_evidence_and_forged_owner_are_rejected(self):
        self._run_case(
            "test_final_review_rejects_generic_non_story_evidence"
        )
        self._run_case("test_final_review_rejects_forged_finding_owner")

    def test_package_and_completion_tampering_are_rejected(self):
        self._run_case(
            "test_run_q1_ready_builds_exact_package_and_completion"
        )


if __name__ == "__main__":
    unittest.main()
