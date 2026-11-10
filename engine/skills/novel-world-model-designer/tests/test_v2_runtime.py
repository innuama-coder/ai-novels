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
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime"
)
s1 = importlib.import_module(
    "skills.novel-storyline-architecture-designer.scripts.run_v2"
)
s1_test = importlib.import_module(
    "skills.novel-storyline-architecture-designer.tests.test_v2_runtime"
)
w1 = importlib.import_module(
    "skills.novel-world-model-designer.scripts.run_v2"
)
baseline_test = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_baseline"
)


class W1ImplementationDependencyRegistryTests(unittest.TestCase):
    def test_registry_binds_w1_and_excludes_later_stage_schemas(self) -> None:
        identities = set(w1._implementation_paths())
        self.assertIn("skill/run_v2.py", identities)
        self.assertIn("schemas/world-model.schema.json", identities)
        self.assertIn("schemas/canonical-common.schema.json", identities)
        self.assertIn("runtime/stage_implementation_identity.py", identities)
        self.assertNotIn("runtime/baseline.py", identities)
        self.assertNotIn("schemas/storyline-architecture.schema.json", identities)
        self.assertFalse(any(identity.startswith("upstream/") for identity in identities))
        self.assertNotIn("schemas/environment-system.schema.json", identities)
        self.assertNotIn("schemas/event-timeline.schema.json", identities)
        self.assertNotIn("runtime/b0_completion.py", identities)


def agent_world_proposal(
    *,
    run_id: str,
    gate_reference: dict[str, str],
    source_artifacts: list[dict[str, str]],
    baseline: dict[str, object],
    storyline: dict[str, object],
) -> dict[str, object]:
    """A test Agent's authored world model; production never synthesizes it."""

    requirements = copy.deepcopy(storyline["world_requirements"])
    lines = {item["id"]: item for item in storyline["storylines"]}
    decisions = []
    facts = []
    history = []
    institutions = []
    systems = []
    resource_flows = []
    authority_flows = []
    information_flows = []
    conflicts = []
    support = []
    environment_demands = []
    derivations = []
    owned_ids = []
    all_markers = " | ".join(item["responsibility"] for item in requirements)

    for index, requirement in enumerate(requirements, 1):
        line_id = next(item for item in requirement["source_ids"] if item in lines)
        line = lines[line_id]
        marker = requirement["responsibility"]
        decision_id = f"DEC-W1-{index:03d}"
        fact_id = f"WF-RULE-{index:03d}"
        history_id = f"HIS-{index:03d}"
        institution_id = f"INST-{index:03d}"
        system_id = f"WS-{index:03d}"
        resource_id = f"RF-{index:03d}"
        authority_id = f"AF-{index:03d}"
        information_id = f"IF-{index:03d}"
        conflict_id = f"WRC-{index:03d}"
        support_id = f"COV-W1-{index:03d}"
        environment_id = f"END-W1-{index:03d}"

        decisions.append(
            {
                "id": decision_id,
                "gap": f"Choose world pressure for {requirement['id']}: {marker}",
                "options": [
                    f"Use a costly regulated system for {marker}.",
                    f"Use an unrestricted system for {marker}.",
                ],
                "selection": f"Use a costly regulated system for {marker}.",
                "owner": "W1",
                "authority_basis": f"W1 owns world realization of {requirement['id']}.",
                "compatibility": f"Preserves the S1 responsibility: {marker}",
                "impact_ids": [fact_id, system_id],
                "cost": f"The rule makes {marker} possible but never free.",
                "reversibility": "costly",
                "downstream_freedom": "E1 may choose concrete places within the rule.",
                "projection_ids": [fact_id, system_id],
            }
        )
        fact = {
            "id": fact_id,
            "kind": "rule",
            "statement": f"The world permits and pressures this obligation: {marker}",
            "applies_to_ids": [line_id],
            "constraints": [
                f"Scope: applies wherever {marker} must be realized.",
                f"Exception: no actor may bypass the rule merely to achieve {marker}.",
                f"Cost: using the capability consumes scarce capacity for {marker}.",
                f"Constraint: authority must be verified before pursuing {marker}.",
            ],
            "consequences": [
                f"Success leaves an observable cost while supporting {marker}.",
                f"Failure blocks or worsens {marker}.",
            ],
            "source_ids": [requirement["id"], decision_id],
        }
        facts.append(fact)
        history.append(
            {
                "id": history_id,
                "origin": f"Earlier misuse created regulation around {marker}.",
                "current_pressure": f"Institutions now ration access needed for {marker}.",
                "storyline_ids": [line_id],
                "constraints": [f"Past damage cannot be erased to simplify {marker}."],
            }
        )
        institutions.append(
            {
                "id": institution_id,
                "responsibility": f"Govern the capability required by {marker}.",
                "authority": [f"Authorize bounded access for {marker}."],
                "resources": [f"Maintain scarce capacity used by {marker}."],
                "constraints": [f"Must record every authorization affecting {marker}."],
                "failure_modes": [f"Delay or capture can prevent {marker}."],
                "storyline_ids": [line_id],
                "source_requirement_ids": [requirement["id"]],
                "world_position": f"A bounded governing body for {requirement['id']}.",
                "interests": [f"Preserve accountable capability for {requirement['id']}."],
                "dependencies": [fact_id],
                "conflicts": [f"Urgency competes with safeguards for {requirement['id']}."],
                "intervention_scope": f"May govern access but may not choose downstream realization for {requirement['id']}.",
            }
        )
        system = {
            "id": system_id,
            "input_conditions": [
                f"A verified request exists for {marker}.",
                f"The originating storyline is in state: {line['start_state']}",
            ],
            "actor_slot_ids": copy.deepcopy(line["actor_slot_ids"]),
            "resources": [f"Scarce capacity allocated to {marker}."],
            "authorities": [f"Recorded permission governing {marker}."],
            "transformation_rules": [
                f"Scope: transform only verified inputs related to {marker}.",
                f"Exception: refuse inputs that would bypass the conflict in {marker}.",
            ],
            "observable_outputs": [f"An auditable output advances or blocks {marker}."],
            "costs": [f"Capacity and trust are spent whenever {marker} proceeds."],
            "limits": [f"No operation may remove the core pressure in {marker}."],
            "failure_modes": [f"Denial, delay, or corrupted input can defeat {marker}."],
            "state_changes": [
                f"The world moves from latent capacity to accountable consequence for {marker}."
            ],
            "storyline_ids": [line_id],
            "source_requirement_ids": [requirement["id"]],
        }
        systems.append(system)
        resource_flows.append(
            {
                "id": resource_id,
                "from_id": system_id,
                "to_id": institution_id,
                "relation": f"accounts for capacity used by {marker}",
                "mechanism": f"usage ledger for {marker}",
                "constraints": [f"No unrecorded resource transfer for {marker}."],
            }
        )
        authority_flows.append(
            {
                "id": authority_id,
                "from_id": institution_id,
                "to_id": system_id,
                "relation": f"grants bounded permission for {marker}",
                "mechanism": f"revocable authorization for {marker}",
                "constraints": [f"Permission cannot erase the cost of {marker}."],
            }
        )
        information_flows.append(
            {
                "id": information_id,
                "from_id": system_id,
                "to_id": institution_id,
                "relation": f"reports observable consequences of {marker}",
                "mechanism": f"auditable report for {marker}",
                "constraints": [f"Visibility remains bounded while preserving {marker}."],
            }
        )
        conflicts.append(
            {
                "id": conflict_id,
                "rule_ids": [fact_id, system_id],
                "tension": f"Capability and restriction pull against each other in {marker}.",
                "resolution_rule": f"Cost and authorization remain active whichever side wins {marker}.",
                "storyline_ids": [line_id],
            }
        )
        realization_ids = [fact_id, system_id, history_id, institution_id]
        claim_coverage = [
            {
                "source_pointer": "/required_capability",
                "source_sha256": runtime.canonical_sha256(requirement["required_capability"]),
                "realization_id": system_id,
                "realization_pointer": f"/systems/{index - 1}/observable_outputs/0",
                "disposition": "realized",
                "rationale": f"The system output operationalizes the required capability for {requirement['id']}.",
            },
            *[
                {
                    "source_pointer": f"/constraints/{claim_index}",
                    "source_sha256": runtime.canonical_sha256(claim),
                    "realization_id": fact_id,
                    "realization_pointer": f"/world_facts/{index - 1}/constraints/{claim_index % len(fact['constraints'])}",
                    "disposition": "constrained",
                    "rationale": f"The sourced rule constrains claim {claim_index} without copying it as proof.",
                }
                for claim_index, claim in enumerate(requirement["constraints"])
            ],
            *[
                {
                    "source_pointer": f"/acceptance_checks/{claim_index}",
                    "source_sha256": runtime.canonical_sha256(claim),
                    "realization_id": system_id,
                    "realization_pointer": f"/systems/{index - 1}/state_changes/0",
                    "disposition": "tested",
                    "rationale": f"The observable state transition gives acceptance claim {claim_index} a test target.",
                }
                for claim_index, claim in enumerate(requirement["acceptance_checks"])
            ],
            {
                "source_pointer": "/downstream_freedom",
                "source_sha256": runtime.canonical_sha256(requirement["downstream_freedom"]),
                "realization_id": institution_id,
                "realization_pointer": f"/institutions/{index - 1}/intervention_scope",
                "disposition": "deferred_to_downstream",
                "rationale": "The institution boundary preserves downstream freedom without selecting an environment.",
            },
        ]
        support_record = {
            "id": support_id,
            "source_ids": [requirement["id"]],
            "realization_ids": realization_ids,
            "status": "covered",
            "evidence": f"Structured claim coverage binds {requirement['id']} to its rule and system.",
            "claim_coverage": claim_coverage,
        }
        support.append(support_record)
        environment_demands.append(
            {
                "id": environment_id,
                "target_stage": "E1",
                "responsibility": f"Provide concrete carrying conditions for {marker}.",
                "source_ids": [requirement["id"], *realization_ids],
                "required_capability": f"Expose access, cost, limits, and failure for {marker}.",
                "constraints": [
                    f"Do not bypass {fact_id} while carrying {marker}.",
                    f"Make {system_id} inputs and outputs observable for {marker}.",
                ],
                "acceptance_checks": [
                    f"A concrete environment can carry success and failure for {marker}.",
                    f"The environment cites the exact W1 support set for {marker}.",
                ],
                "downstream_freedom": "E1 chooses topology and functional zones.",
                "environment_dimensions": {
                    "macro_geography": [f"Expose broad-scale consequence conditions for {requirement['id']}."],
                    "institution_facility": [f"Expose institutional access conditions for {requirement['id']}."],
                    "spatial_relations": [f"Expose source-to-receiver adjacency for {requirement['id']}."],
                    "plot_carriers": [f"Expose success and failure carriers for {requirement['id']}."],
                },
            }
        )
        derivations.extend(
            [
                {
                    "id": f"DRV-W1-RULE-{index:03d}",
                    "value_sha256": runtime.canonical_sha256(fact),
                    "source_ids": [requirement["id"]],
                    "decision_ids": [decision_id],
                    "projection_ids": [fact_id],
                },
                {
                    "id": f"DRV-W1-SYSTEM-{index:03d}",
                    "value_sha256": runtime.canonical_sha256(system),
                    "source_ids": [requirement["id"]],
                    "decision_ids": [decision_id],
                    "projection_ids": [system_id],
                },
                {
                    "id": f"DRV-W1-SUPPORT-{index:03d}",
                    "value_sha256": runtime.canonical_sha256(support_record),
                    "source_ids": [requirement["id"]],
                    "decision_ids": [decision_id],
                    "projection_ids": [support_id],
                },
            ]
        )
        owned_ids.extend(
            [
                decision_id,
                fact_id,
                history_id,
                institution_id,
                system_id,
                resource_id,
                authority_id,
                information_id,
                conflict_id,
                support_id,
            ]
        )

    reality_claims = []
    for index, dependency in enumerate(baseline["fact_dependencies"], 1):
        handling = {
            "adopted": "adopted",
            "open": "preserve_open",
            "not_applicable": "fiction_boundary",
        }[dependency["status"]]
        details = dependency["claim"]
        if dependency["status"] == "adopted":
            details += (
                f" Allowed use: {dependency['allowed_use']}."
                f" Fiction boundary: {dependency['fiction_boundary']}."
            )
        claim_id = f"WF-REALITY-{index:03d}"
        reality_claims.append(
            {
                "id": claim_id,
                "fact_dependency_id": dependency["id"],
                "handling": handling,
                "claim": details,
            }
        )
        owned_ids.append(claim_id)

    facets = {
        name: [
            {
                "claim": f"{name} domain carries traceable world constraints.",
                "requirement_ids": [item["id"] for item in requirements],
                "rule_ids": [item["id"] for item in facts if item["kind"] == "rule"],
            }
        ]
        for name in (
            "physical",
            "technology",
            "social",
            "political",
            "economic",
            "legal_and_ethical",
            "information",
            "historical",
        )
    }
    locked = [
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_locked"
    ]
    author_open_controls = [
        item
        for item in baseline["control_registry"]
        if item["hardness"] == "author_open"
    ]
    model = {
        "schema_version": w1.CURRENT_MODEL_SCHEMA_VERSION,
        "skill": "novel-world-model-designer",
        "stage": "W1",
        "run_id": run_id,
        "status": "ready",
        "contract_revision": w1.CURRENT_CONTRACT_REVISION,
        "input_gate": copy.deepcopy(gate_reference),
        "source_artifacts": copy.deepcopy(source_artifacts),
        "authority_partition": {
            "author_locked": locked,
            "autonomous_owned": owned_ids,
            "downstream_freedom": [item["id"] for item in environment_demands],
            "author_open": [item["id"] for item in author_open_controls],
        },
        "design_decisions": decisions,
        "derivation_claims": derivations,
        "storyline_requirements": requirements,
        "world_definition": {
            "premise": f"One regulated world carries all approved obligations: {all_markers}",
            "scope": f"The designed world covers only story-relevant operations: {all_markers}",
            "period": f"A period shaped by accumulated institutional pressure: {all_markers}",
            "reality_relation": f"Reality claims are bounded by B0 while fiction carries: {all_markers}",
            "operating_logic": f"Capability always meets authority, scarcity, and failure: {all_markers}",
            "boundaries": [
                f"No convenient world mechanism may bypass: {all_markers}",
                "Concrete environments, events, and character profiles remain downstream.",
            ],
            "story_relevance": f"Every rule exists to carry an S1 obligation: {all_markers}",
        },
        "world_facts": facts,
        "reality_claims": reality_claims,
        "world_facets": facets,
        "history_pressures": history,
        "institutions": institutions,
        "systems": systems,
        "resource_flows": resource_flows,
        "authority_flows": authority_flows,
        "information_flows": information_flows,
        "rule_conflict_matrix": conflicts,
        "storyline_support_ledger": support,
        "environment_demands": environment_demands,
        "open_items": [
            {
                "id": f"OPEN-W1-{index:03d}",
                "question": f"Preserve author-open control {item['id']}.",
                "source_ids": [item["id"]],
                "status": "author_open",
            }
            for index, item in enumerate(author_open_controls, 1)
        ],
    }
    return model


class W1RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.shared_temporary = tempfile.TemporaryDirectory()
        cls.shared = Path(cls.shared_temporary.name)
        cls.sources = baseline_test.SourceFixture(cls.shared / "sources")
        coordinator = runtime.AutonomousCoordinator.initialize(
            run_id=cls.sources.run_id,
            source_interview_state={
                "path": "interview/interview-state.json",
                "sha256": runtime.sha256_file(cls.sources.state),
            },
            state_path="state/revision-000.json",
        )
        b0_gate = coordinator.build_input_gate("B0", "B0/input-gate.json")
        cls.shared_b0 = cls.shared / "run" / "B0"
        runtime.build_baseline_package(
            **cls.sources.build_args(cls.shared_b0, b0_gate)
        )
        runtime.complete_b0(
            cls.shared_b0,
            coordinator=coordinator,
            input_gate=b0_gate,
            logical_package_path="workspaces/B0-attempt-01/package",
            next_state_path="state/revision-001.json",
        )
        s1_gate = coordinator.build_input_gate("S1", "S1/input-gate.json")
        cls.shared_s1 = cls.shared / "run" / "S1"
        s1_workspace = cls.shared / "workspace" / "S1"
        baseline = json.loads(
            (cls.shared_b0 / "author-control-baseline.json").read_text(
                encoding="utf-8"
            )
        )
        controls = s1._controls(cls.shared_b0, baseline)
        source_artifacts = [
            {
                "path": f"sources/B0/{name}",
                "sha256": runtime.sha256_file(cls.shared_b0 / name),
            }
            for name in (
                "author-control-baseline.json",
                "package-manifest.json",
                "stage-completion.json",
            )
        ]
        s1_proposal = s1_test.agent_proposal(
            run_id=cls.sources.run_id,
            gate_reference=s1_gate.reference,
            source_artifacts=source_artifacts,
            controls=controls,
        )
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-shared-s1"}, clear=False
        ):
            s1.start_s1_session(
                s1_workspace,
                baseline_package=cls.shared_b0,
                input_gate=s1_gate,
            )
            for phase in s1.PHASES:
                payload = (
                    {"model": s1_proposal}
                    if phase == "final-storyline-model"
                    else {
                        field: s1_proposal[field]
                        for field in s1.PHASE_FIELDS[phase]
                    }
                )
                if phase == "line-design":
                    request = s1.start_s1_line_claim_review(
                        s1_workspace,
                        baseline_package=cls.shared_b0,
                        input_gate=s1_gate,
                        payload=payload,
                    )
                    review = {
                        "claim_verdicts": [
                            {
                                "claim_id": claim_id,
                                "verdict": "pass",
                                "rationale": "Fixture claim matches its declared source authority.",
                            }
                            for claim_id in request["claim_ids"]
                        ],
                        "source_sequence_verdicts": [
                            {
                                "realization_id": item["id"],
                                "source_unit_id": item["source_unit_id"],
                                "verdict": "pass",
                                "rationale": "Fixture realization preserves its declared ordered source.",
                            }
                            for item in request["candidate"]["source_sequence_realizations"]
                        ],
                    }
                    with mock.patch.dict(
                        os.environ,
                        {"CODEX_THREAD_ID": "thread-shared-s1-line-review"},
                        clear=False,
                    ):
                        s1.submit_s1_line_claim_review(
                            s1_workspace,
                            candidate_sha256=request["candidate_sha256"],
                            review=review,
                        )
                if phase == "topology-and-consistency":
                    request = s1.start_s1_topology_semantic_review(
                        s1_workspace,
                        baseline_package=cls.shared_b0,
                        input_gate=s1_gate,
                        payload=payload,
                    )
                    with mock.patch.dict(
                        os.environ,
                        {"CODEX_THREAD_ID": "thread-shared-s1-topology-review"},
                        clear=False,
                    ):
                        s1.submit_s1_topology_semantic_review(
                            s1_workspace,
                            candidate_sha256=request["candidate_sha256"],
                            verdicts=s1_test.passing_topology_verdicts(request),
                        )
                s1.submit_s1_phase(
                    s1_workspace,
                    baseline_package=cls.shared_b0,
                    input_gate=s1_gate,
                    phase=phase,
                    payload=payload,
                )
            s1.run_s1(
                cls.shared_s1,
                baseline_package=cls.shared_b0,
                coordinator=coordinator,
                input_gate=s1_gate,
                controlled_workspace=s1_workspace,
                logical_package_path="S1/attempt-03",
                next_state_path="state/revision-002.json",
            )
        cls.coordinator_state = coordinator.state
        cls.coordinator_reference = coordinator.state_reference

    @classmethod
    def tearDownClass(cls) -> None:
        cls.shared_temporary.cleanup()

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.b0 = self.work / "run" / "B0"
        self.s1 = self.work / "run" / "S1"
        shutil.copytree(self.shared_b0, self.b0)
        shutil.copytree(self.shared_s1, self.s1)
        self.coordinator = runtime.AutonomousCoordinator.from_snapshot(
            self.coordinator_state,
            self.coordinator_reference,
        )
        self.gate = self.coordinator.build_input_gate(
            "W1", "W1/input-gate.json"
        )
        self.package = self.work / "run" / "W1"
        self.workspace = self.work / "workspace" / "W1"
        self.baseline = json.loads(
            (self.b0 / "author-control-baseline.json").read_text(encoding="utf-8")
        )
        self.storyline = json.loads(
            (self.s1 / "storyline-architecture.json").read_text(encoding="utf-8")
        )
        source_artifacts = [
            *[
                {
                    "path": f"sources/B0/{name}",
                    "sha256": runtime.sha256_file(self.b0 / name),
                }
                for name in (
                    "author-control-baseline.json",
                    "package-manifest.json",
                    "stage-completion.json",
                )
            ],
            *[
                {
                    "path": f"sources/S1/{name}",
                    "sha256": runtime.sha256_file(self.s1 / name),
                }
                for name in (
                    "storyline-architecture.json",
                    "package-manifest.json",
                    "stage-completion.json",
                )
            ],
        ]
        self.proposal = agent_world_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=source_artifacts,
            baseline=self.baseline,
            storyline=self.storyline,
        )
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-w1"}, clear=False
        ):
            w1.start_w1_session(
                self.workspace,
                baseline_package=self.b0,
                storyline_package=self.s1,
                input_gate=self.gate,
            )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_w1(self) -> w1.W1RunReceipt:
        self._seal_all_phases()
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-w1"}, clear=False
        ):
            return w1.run_w1(
                self.package,
                baseline_package=self.b0,
                storyline_package=self.s1,
                coordinator=self.coordinator,
                input_gate=self.gate,
                controlled_workspace=self.workspace,
                logical_package_path="W1",
                next_state_path="state/revision-003.json",
            )

    def _seal_all_phases(self) -> None:
        evidence = self.workspace / "generation-evidence"
        for phase in w1.PHASES:
            ordinal = w1.PHASES.index(phase) + 1
            if (evidence / f"{ordinal:02d}-{phase}.json").exists():
                continue
            self._submit_phase(
                self.workspace,
                phase,
                self._phase_payload(phase),
            )

    def _validate(self, model: dict[str, object]) -> None:
        w1._validate_model(
            model,
            self.baseline,
            self.storyline,
            w1._controls(self.b0, self.baseline),
            runtime.ContractRuntime(),
            expected_gate=self.gate.reference,
            expected_sources=self.proposal["source_artifacts"],
        )

    def _phase_payload(
        self, phase: str, proposal: dict[str, object] | None = None
    ) -> dict[str, object]:
        value = proposal or self.proposal
        return (
            {"model": copy.deepcopy(value)}
            if phase == "final-world-model"
            else {
                field: copy.deepcopy(value[field])
                for field in w1.PHASE_FIELDS[phase]
            }
        )

    def _fresh_workspace(self, name: str) -> Path:
        workspace = self.work / "phase-tests" / name
        workspace.mkdir(parents=True)
        shutil.copyfile(
            self.workspace / "generation-session.json",
            workspace / "generation-session.json",
        )
        return workspace

    def _submit_phase(
        self, workspace: Path, phase: str, payload: dict[str, object]
    ) -> dict[str, str]:
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-w1"}, clear=False
        ):
            return w1.submit_w1_phase(
                workspace,
                baseline_package=self.b0,
                storyline_package=self.s1,
                input_gate=self.gate,
                phase=phase,
                payload=payload,
            )

    def _submit_valid_before(self, workspace: Path, target_phase: str) -> None:
        for phase in w1.PHASES[: w1.PHASES.index(target_phase)]:
            self._submit_phase(workspace, phase, self._phase_payload(phase))

    def _legacy_model(self) -> dict[str, object]:
        model = copy.deepcopy(self.proposal)
        model.pop("contract_revision")
        model["schema_version"] = w1.LEGACY_MODEL_SCHEMA_VERSION
        markers = " | ".join(
            item["responsibility"] for item in model["storyline_requirements"]
        )
        model["world_facets"] = {
            name: [f"Legacy {name} participation: {markers}"]
            for name in model["world_facets"]
        }
        for institution in model["institutions"]:
            for field in (
                "source_requirement_ids",
                "world_position",
                "interests",
                "dependencies",
                "conflicts",
                "intervention_scope",
            ):
                institution.pop(field)
        for system in model["systems"]:
            system.pop("source_requirement_ids")
        requirements = {
            item["id"]: item for item in model["storyline_requirements"]
        }
        for support in model["storyline_support_ledger"]:
            support.pop("claim_coverage")
            support["evidence"] = (
                requirements[support["source_ids"][0]]["responsibility"]
                + " is carried by its legacy realization set."
            )
        model["derivation_claims"] = [
            item
            for item in model["derivation_claims"]
            if not item["id"].startswith("DRV-W1-SUPPORT-")
        ]
        systems = {item["id"]: item for item in model["systems"]}
        for claim in model["derivation_claims"]:
            projection_id = claim["projection_ids"][0]
            if projection_id in systems:
                claim["value_sha256"] = runtime.canonical_sha256(
                    systems[projection_id]
                )
        for demand in model["environment_demands"]:
            demand.pop("environment_dimensions")
        return model

    def test_each_current_phase_rejects_bad_payload_before_evidence(self) -> None:
        cases = []
        bad_p1 = self._phase_payload("requirement-projection")
        bad_p1["storyline_requirements"].pop()
        cases.append(("requirement-projection", bad_p1))

        bad_p2 = self._phase_payload("world-rules-and-history")
        bad_p2["world_facts"] = [
            item
            for item in bad_p2["world_facts"]
            if self.proposal["storyline_requirements"][-1]["id"]
            not in item["source_ids"]
        ]
        cases.append(("world-rules-and-history", bad_p2))

        bad_p3 = self._phase_payload("systems-and-flows")
        bad_p3["systems"][0].pop("source_requirement_ids")
        cases.append(("systems-and-flows", bad_p3))

        bad_p4 = self._phase_payload("cross-line-world-test")
        bad_p4["storyline_support_ledger"][0].pop("claim_coverage")
        cases.append(("cross-line-world-test", bad_p4))

        for phase, payload in cases:
            with self.subTest(phase=phase):
                workspace = self._fresh_workspace(phase)
                self._submit_valid_before(workspace, phase)
                prior = {
                    path.name: runtime.sha256_file(path)
                    for path in (workspace / "generation-evidence").glob("*.json")
                } if (workspace / "generation-evidence").exists() else {}
                with self.assertRaises(w1.W1Error):
                    self._submit_phase(workspace, phase, payload)
                target = workspace / "generation-evidence" / (
                    f"{w1.PHASES.index(phase) + 1:02d}-{phase}.json"
                )
                self.assertFalse(target.exists())
                self.assertEqual(
                    prior,
                    {
                        path.name: runtime.sha256_file(path)
                        for path in (workspace / "generation-evidence").glob("*.json")
                    } if (workspace / "generation-evidence").exists() else {},
                )

    def test_phase5_requires_exact_sealed_phase_projections_before_evidence(self) -> None:
        workspace = self._fresh_workspace("phase5-projection")
        self._submit_valid_before(workspace, "final-world-model")
        bad = copy.deepcopy(self.proposal)
        bad["systems"][0]["limits"].append("A post-seal mutation.")
        with self.assertRaisesRegex(w1.W1Error, "W1_PHASE_PROJECTION_MISMATCH"):
            self._submit_phase(workspace, "final-world-model", {"model": bad})
        self.assertFalse(
            (workspace / "generation-evidence/05-final-world-model.json").exists()
        )

    def test_structured_claim_coverage_accepts_paraphrase_without_responsibility_copy(self) -> None:
        storyline = copy.deepcopy(self.storyline)
        model = copy.deepcopy(self.proposal)
        replacement = "A newly worded responsibility that is absent from every realization body."
        storyline["world_requirements"][0]["responsibility"] = replacement
        model["storyline_requirements"][0]["responsibility"] = replacement
        self.assertNotIn(
            replacement,
            runtime.canonical_json(
                [
                    *model["world_facts"],
                    *model["institutions"],
                    *model["systems"],
                ]
            ),
        )
        w1._validate_model(
            model,
            self.baseline,
            storyline,
            w1._controls(self.b0, self.baseline),
            runtime.ContractRuntime(),
            expected_gate=self.gate.reference,
            expected_sources=self.proposal["source_artifacts"],
        )

    def test_claim_coverage_mutants_are_rejected(self) -> None:
        cases = []
        missing = copy.deepcopy(self.proposal)
        missing["storyline_support_ledger"][0]["claim_coverage"].pop()
        cases.append(("missing", missing, "W1_SUPPORT_CLAIM_COVERAGE_MISMATCH"))
        pointer = copy.deepcopy(self.proposal)
        pointer["storyline_support_ledger"][0]["claim_coverage"][0]["source_pointer"] = "/missing"
        cases.append(("source-pointer", pointer, "W1_SUPPORT_CLAIM_COVERAGE_MISMATCH"))
        digest = copy.deepcopy(self.proposal)
        digest["storyline_support_ledger"][0]["claim_coverage"][0]["source_sha256"] = "0" * 64
        cases.append(("hash", digest, "W1_SUPPORT_SOURCE_HASH_MISMATCH"))
        realization = copy.deepcopy(self.proposal)
        realization["storyline_support_ledger"][0]["claim_coverage"][0]["realization_id"] = realization["systems"][1]["id"]
        cases.append(("realization", realization, "W1_SUPPORT_REALIZATION_MISMATCH"))
        realization_pointer = copy.deepcopy(self.proposal)
        realization_pointer["storyline_support_ledger"][0]["claim_coverage"][0]["realization_pointer"] = "/systems/1/observable_outputs/0"
        cases.append(("realization-pointer", realization_pointer, "W1_SUPPORT_REALIZATION_POINTER_INVALID"))
        for name, model, code in cases:
            with self.subTest(name=name):
                with self.assertRaises(w1.W1Error) as caught:
                    self._validate(model)
                self.assertEqual(code, caught.exception.code)

        wrong_disposition = {
            "realized": "tested",
            "constrained": "realized",
            "tested": "constrained",
            "deferred_to_downstream": "realized",
        }
        for index, coverage in enumerate(
            self.proposal["storyline_support_ledger"][0]["claim_coverage"]
        ):
            with self.subTest(disposition_pointer=coverage["source_pointer"]):
                model = copy.deepcopy(self.proposal)
                model["storyline_support_ledger"][0]["claim_coverage"][index][
                    "disposition"
                ] = wrong_disposition[coverage["disposition"]]
                with self.assertRaisesRegex(
                    w1.W1Error, "W1_SUPPORT_DISPOSITION_MISMATCH"
                ):
                    self._validate(model)

    def test_responsibility_copy_without_claim_coverage_is_rejected(self) -> None:
        model = copy.deepcopy(self.proposal)
        support = model["storyline_support_ledger"][0]
        support["evidence"] = model["storyline_requirements"][0]["responsibility"]
        support.pop("claim_coverage")
        with self.assertRaisesRegex(
            w1.W1Error, "W1_SUPPORT_CLAIM_COVERAGE_MISSING"
        ):
            self._validate(model)

    def test_current_structure_and_environment_dimension_mutants_are_rejected(self) -> None:
        for field in (
            "world_position",
            "interests",
            "dependencies",
            "conflicts",
            "intervention_scope",
            "source_requirement_ids",
        ):
            with self.subTest(institution_field=field):
                institution = copy.deepcopy(self.proposal)
                institution["institutions"][0].pop(field)
                with self.assertRaisesRegex(
                    w1.W1Error, "W1_MODEL_SCHEMA_INVALID"
                ):
                    self._validate(institution)
        for dimension in (
            "macro_geography",
            "institution_facility",
            "spatial_relations",
            "plot_carriers",
        ):
            with self.subTest(environment_dimension=dimension):
                demand = copy.deepcopy(self.proposal)
                demand["environment_demands"][0]["environment_dimensions"].pop(
                    dimension
                )
                with self.assertRaisesRegex(
                    w1.W1Error, "W1_MODEL_SCHEMA_INVALID"
                ):
                    self._validate(demand)

        dependency_only = copy.deepcopy(self.proposal)
        dependency_only["institutions"][0]["conflicts"] = []
        self._validate(dependency_only)

        conflict_only = copy.deepcopy(self.proposal)
        conflict_only["institutions"][0]["dependencies"] = []
        self._validate(conflict_only)

        no_relation = copy.deepcopy(self.proposal)
        no_relation["institutions"][0]["dependencies"] = []
        no_relation["institutions"][0]["conflicts"] = []
        with self.assertRaisesRegex(w1.W1Error, "W1_MODEL_SCHEMA_INVALID"):
            self._validate(no_relation)

    def test_global_id_collision_and_flow_ownership_rules(self) -> None:
        collision = copy.deepcopy(self.proposal)
        collision["reality_claims"][0]["id"] = collision["world_facts"][0]["id"]
        with self.assertRaisesRegex(w1.W1Error, "W1_GLOBAL_ID_COLLISION"):
            self._validate(collision)

        resource = copy.deepcopy(self.proposal)
        target = resource["resource_flows"][0]["to_id"]
        resource["resource_flows"].append(
            {
                "id": "RF-MULTI-SOURCE",
                "from_id": resource["institutions"][1]["id"],
                "to_id": target,
                "relation": "supplies a second independent resource",
                "mechanism": "separate bounded allocation",
                "constraints": ["The second input grants no authority."],
            }
        )
        resource["authority_partition"]["autonomous_owned"].append("RF-MULTI-SOURCE")
        self._validate(resource)

        authority = copy.deepcopy(self.proposal)
        authority["authority_flows"][1]["to_id"] = authority["authority_flows"][0]["to_id"]
        with self.assertRaisesRegex(w1.W1Error, "W1_DOUBLE_OWNERSHIP"):
            self._validate(authority)

        duplicate_edge = copy.deepcopy(self.proposal)
        clone = copy.deepcopy(duplicate_edge["information_flows"][0])
        clone["id"] = "IF-DUPLICATE-EDGE"
        duplicate_edge["information_flows"].append(clone)
        duplicate_edge["authority_partition"]["autonomous_owned"].append(
            clone["id"]
        )
        with self.assertRaisesRegex(w1.W1Error, "W1_FLOW_DUPLICATE_EDGE"):
            self._validate(duplicate_edge)

    def test_derivation_and_author_open_implementation_are_rejected(self) -> None:
        derivation = copy.deepcopy(self.proposal)
        derivation["derivation_claims"] = [
            item
            for item in derivation["derivation_claims"]
            if item["projection_ids"] != [derivation["storyline_support_ledger"][0]["id"]]
        ]
        with self.assertRaisesRegex(w1.W1Error, "W1_DERIVATION_INCOMPLETE"):
            self._validate(derivation)
        implemented = copy.deepcopy(self.proposal)
        implemented["design_decisions"][0]["impact_ids"].append(
            implemented["authority_partition"]["author_open"][0]
        )
        with self.assertRaisesRegex(w1.W1Error, "W1_AUTHOR_OPEN_IMPLEMENTED"):
            self._validate(implemented)

        rule_source = copy.deepcopy(self.proposal)
        rule_source["world_facts"][0]["source_ids"].append(
            rule_source["authority_partition"]["author_open"][0]
        )
        with self.assertRaisesRegex(w1.W1Error, "W1_AUTHOR_OPEN_IMPLEMENTED"):
            self._validate(rule_source)

        derivation_source = copy.deepcopy(self.proposal)
        derivation_source["derivation_claims"][0]["source_ids"].append(
            derivation_source["authority_partition"]["author_open"][0]
        )
        with self.assertRaisesRegex(w1.W1Error, "W1_AUTHOR_OPEN_IMPLEMENTED"):
            self._validate(derivation_source)

    def test_legacy_contract_remains_readable_and_unknown_revision_is_rejected(self) -> None:
        self._validate(self._legacy_model())
        current_as_20 = copy.deepcopy(self.proposal)
        current_as_20["schema_version"] = w1.LEGACY_MODEL_SCHEMA_VERSION
        with self.assertRaisesRegex(w1.W1Error, "W1_CURRENT_SCHEMA_VERSION_INVALID"):
            self._validate(current_as_20)
        legacy_as_21 = self._legacy_model()
        legacy_as_21["schema_version"] = w1.CURRENT_MODEL_SCHEMA_VERSION
        with self.assertRaisesRegex(w1.W1Error, "W1_LEGACY_SCHEMA_VERSION_INVALID"):
            self._validate(legacy_as_21)
        unknown = copy.deepcopy(self.proposal)
        unknown["contract_revision"] = "future-unknown"
        with self.assertRaisesRegex(w1.W1Error, "W1_CONTRACT_REVISION_UNSUPPORTED"):
            self._validate(unknown)

    def test_trusted_existing_legacy_package_is_readable(self) -> None:
        legacy = (
            w1._REPO
            / "projects"
            / "duanxian"
            / "conception-runs"
            / "duanxian-conception-v2-20260803-04"
            / "W1"
        )
        self.assertEqual("ready", w1.validate_w1_package(legacy)["verdict"])

    def test_current_package_cannot_be_disguised_by_deleting_revision(self) -> None:
        self.run_w1()
        self._disguise_current_package_as_legacy()
        with self.assertRaises(w1.W1Error) as caught:
            w1.validate_w1_package(self.package)
        self.assertEqual("W1_LEGACY_PROVENANCE_UNTRUSTED", caught.exception.code)

    def test_phase2_duplicate_reality_dependency_fails_before_evidence(self) -> None:
        workspace = self._fresh_workspace("phase2-duplicate-dependency")
        self._submit_phase(
            workspace,
            "requirement-projection",
            self._phase_payload("requirement-projection"),
        )
        phase1 = workspace / "generation-evidence/01-requirement-projection.json"
        phase1_sha = runtime.sha256_file(phase1)
        payload = self._phase_payload("world-rules-and-history")
        duplicate = copy.deepcopy(payload["reality_claims"][0])
        duplicate["id"] = "WF-REALITY-DUPLICATE"
        payload["reality_claims"].append(duplicate)
        with self.assertRaisesRegex(w1.W1Error, "W1_REALITY_CLAIM_MISMATCH"):
            self._submit_phase(
                workspace,
                "world-rules-and-history",
                payload,
            )
        self.assertEqual(phase1_sha, runtime.sha256_file(phase1))
        self.assertFalse(
            (workspace / "generation-evidence/02-world-rules-and-history.json").exists()
        )

    def test_run17_style_evidence_geo_confirmation_chain_is_valid(self) -> None:
        model = copy.deepcopy(self.proposal)
        stop, geo, c10 = model["systems"][3:6]
        stop["observable_outputs"].append("Evidence@7 complete stop result.")
        geo["input_conditions"].append("Evidence@7 already exists; C10 is not an input.")
        geo["observable_outputs"].append("Geo@5 completes before C10.")
        c10["input_conditions"].append("Existing Evidence@7 and existing Geo@5 are read-only inputs.")
        c10["observable_outputs"].append("C10 confirms but does not produce either result.")
        extra = [
            {
                "id": "SLC-EVIDENCE-STOP-GEO",
                "from_id": stop["id"],
                "to_id": geo["id"],
                "relation": "carries completed Evidence@7 to the unique Geo@5 producer",
                "mechanism": "direct completed-result notification",
                "constraints": ["C10 is not an input, trigger, prerequisite, or owner."],
            },
            {
                "id": "IF-GEO-C10-CONFIRM",
                "from_id": geo["id"],
                "to_id": c10["id"],
                "relation": "carries existing Geo@5 to its confirmation-only consumer",
                "mechanism": "read-only result handoff",
                "constraints": ["The receiver cannot create or modify Geo@5."],
            },
        ]
        model["information_flows"].extend(extra)
        model["authority_partition"]["autonomous_owned"].extend(
            item["id"] for item in extra
        )
        for system in (stop, geo, c10):
            claim = next(
                item
                for item in model["derivation_claims"]
                if item["projection_ids"] == [system["id"]]
            )
            claim["value_sha256"] = runtime.canonical_sha256(system)
        self._validate(model)

    def test_authority_partition_rejects_overlap_before_deep_validation(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["authority_partition"]["downstream_freedom"].append(
            model["authority_partition"]["autonomous_owned"][0]
        )
        with self.assertRaisesRegex(
            w1.W1Error, "W1_AUTHORITY_PARTITION_OVERLAP"
        ):
            self._validate(model)

    def test_authority_partition_requires_all_four_exact_sets(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["authority_partition"]["autonomous_owned"].pop()
        with self.assertRaisesRegex(
            w1.W1Error, "W1_AUTHORITY_PARTITION_MISMATCH"
        ):
            self._validate(model)

    def test_ready_world_model_covers_every_storyline_and_advances(self) -> None:
        receipt = self.run_w1()
        model = receipt.model
        requirement_ids = {item["id"] for item in model["storyline_requirements"]}
        self.assertEqual(
            requirement_ids,
            {
                item["source_ids"][0]
                for item in model["storyline_support_ledger"]
            },
        )
        self.assertEqual(
            requirement_ids,
            {
                next(
                    source
                    for source in item["source_ids"]
                    if source in requirement_ids
                )
                for item in model["environment_demands"]
            },
        )
        self.assertTrue(
            all(
                all(
                    any(tag in value for value in item["constraints"])
                    for tag in w1._RULE_TAGS
                )
                for item in model["world_facts"]
                if item["kind"] == "rule"
            )
        )
        self.assertEqual("W1", receipt.completion.data["stage"])
        self.assertEqual(3, receipt.transition.snapshot["revision"])
        self.assertEqual(
            "ready", w1.validate_w1_package(self.package)["verdict"]
        )

    @unittest.skipUnless(os.name == "nt", "Windows path-length regression")
    def test_long_final_path_with_s1_review_directories_publishes(self) -> None:
        relative_paths = [
            Path("sources") / "B0" / path.relative_to(self.b0)
            for path in self.b0.rglob("*")
            if path.is_file()
        ]
        relative_paths.extend(
            Path("sources") / "S1" / path.relative_to(self.s1)
            for path in self.s1.rglob("*")
            if path.is_file()
        )
        relative_paths.extend(
            Path("generation-evidence") / path.name
            for path in (self.workspace / "generation-evidence").rglob("*")
            if path.is_file()
        )
        relative_paths.extend(
            Path("implementation") / identity
            for identity in w1._implementation_paths()
        )
        relative_paths.extend(
            Path(name)
            for name in (
                "input-gate.json",
                "world-model.json",
                "generation-evidence-index.json",
                "generation-session.json",
                "execution-record.json",
                "world-preview.md",
                "validation.json",
                "package-manifest.json",
                "stage-completion.json",
            )
        )
        longest_relative = max(len(os.fspath(path)) for path in relative_paths)
        base = self.work / "long-package-root"
        # The final tree remains below MAX_PATH. The old
        # .<destination>.<random>/package staging shape would not.
        padding = 246 - len(os.fspath(base)) - 10 - longest_relative
        self.assertGreaterEqual(padding, 8)
        self.assertLessEqual(padding, 240)
        destination = base / ("x" * padding) / "package"
        parent_length = len(os.fspath(destination.parent))
        old_deepest = (
            parent_length
            + 1
            + len(".package.")
            + 8
            + 1
            + len("package")
            + 1
            + longest_relative
        )
        new_deepest = (
            parent_length
            + 1
            + len(".w1-")
            + 8
            + 1
            + longest_relative
        )
        self.assertGreater(old_deepest, 259)
        self.assertLess(new_deepest, 260)

        self._seal_all_phases()
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-w1"}, clear=False
        ):
            receipt = w1.run_w1(
                destination,
                baseline_package=self.b0,
                storyline_package=self.s1,
                coordinator=self.coordinator,
                input_gate=self.gate,
                controlled_workspace=self.workspace,
                logical_package_path="W1/long-path",
                next_state_path="state/revision-003.json",
            )

        self.assertEqual(destination.resolve(), receipt.package_root)
        self.assertEqual("ready", w1.validate_w1_package(destination)["verdict"])
        self.assertEqual([], list(destination.parent.glob(".w1-*")))

    def test_staging_copy_failure_cleans_short_atomic_directory(self) -> None:
        self._seal_all_phases()
        with mock.patch.object(
            w1.shutil, "copytree", side_effect=OSError("injected copy failure")
        ):
            with self.assertRaises(OSError):
                with mock.patch.dict(
                    os.environ,
                    {"CODEX_THREAD_ID": "thread-generic-w1"},
                    clear=False,
                ):
                    w1.run_w1(
                        self.package,
                        baseline_package=self.b0,
                        storyline_package=self.s1,
                        coordinator=self.coordinator,
                        input_gate=self.gate,
                        controlled_workspace=self.workspace,
                        logical_package_path="W1",
                        next_state_path="state/revision-003.json",
                    )

        self.assertFalse(self.package.exists())
        self.assertEqual([], list(self.package.parent.glob(".w1-*")))
        self.assertEqual(2, self.coordinator.state["revision"])

    def test_late_output_conflict_is_preserved_and_staging_is_cleaned(self) -> None:
        marker = self.package / "owner.txt"

        def create_conflict(**_: object) -> object:
            self.package.mkdir(parents=True)
            marker.write_text("preexisting owner", encoding="utf-8")
            return mock.sentinel.transition

        self._seal_all_phases()
        with mock.patch.object(
            self.coordinator,
            "accept_stage_completion",
            side_effect=create_conflict,
        ):
            with self.assertRaises(w1.W1Error) as caught:
                with mock.patch.dict(
                    os.environ,
                    {"CODEX_THREAD_ID": "thread-generic-w1"},
                    clear=False,
                ):
                    w1.run_w1(
                        self.package,
                        baseline_package=self.b0,
                        storyline_package=self.s1,
                        coordinator=self.coordinator,
                        input_gate=self.gate,
                        controlled_workspace=self.workspace,
                        logical_package_path="W1",
                        next_state_path="state/revision-003.json",
                    )

        self.assertEqual("W1_OUTPUT_EXISTS", caught.exception.code)
        self.assertEqual("preexisting owner", marker.read_text(encoding="utf-8"))
        self.assertEqual([], list(self.package.parent.glob(".w1-*")))
        self.assertEqual(2, self.coordinator.state["revision"])

    def test_opposite_s1_values_change_every_agent_phase_payload(self) -> None:
        left_storyline = copy.deepcopy(self.storyline)
        right_storyline = copy.deepcopy(self.storyline)
        left_storyline["world_requirements"][0]["responsibility"] = (
            "The world must keep the protected subject present."
        )
        right_storyline["world_requirements"][0]["responsibility"] = (
            "The world must force the protected subject to leave."
        )
        sources = copy.deepcopy(self.proposal["source_artifacts"])
        left = agent_world_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=sources,
            baseline=self.baseline,
            storyline=left_storyline,
        )
        right = agent_world_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=sources,
            baseline=self.baseline,
            storyline=right_storyline,
        )
        for phase in w1.PHASES:
            left_payload = (
                {"model": left}
                if phase == "final-world-model"
                else {field: left[field] for field in w1.PHASE_FIELDS[phase]}
            )
            right_payload = (
                {"model": right}
                if phase == "final-world-model"
                else {field: right[field] for field in w1.PHASE_FIELDS[phase]}
            )
            self.assertNotEqual(
                runtime.canonical_sha256(left_payload),
                runtime.canonical_sha256(right_payload),
                phase,
            )

    def test_resealed_rule_coverage_deletion_is_rejected(self) -> None:
        self.run_w1()
        model = self._read_model()
        model["storyline_support_ledger"][0]["realization_ids"] = [
            item
            for item in model["storyline_support_ledger"][0]["realization_ids"]
            if not item.startswith("WF-RULE-")
        ]
        self._reseal_model(model)
        with self.assertRaises(w1.W1Error) as caught:
            w1.validate_w1_package(self.package)
        self.assertEqual("W1_SUPPORT_COVERAGE_MISMATCH", caught.exception.code)

    def test_resealed_forged_gate_is_rejected(self) -> None:
        self.run_w1()
        model = self._read_model()
        model["input_gate"]["sha256"] = "0" * 64
        self._reseal_model(model, input_gate=model["input_gate"])
        with self.assertRaises(w1.W1Error) as caught:
            w1.validate_w1_package(self.package)
        self.assertEqual("W1_GATE_REFERENCE_MISMATCH", caught.exception.code)

    def test_missing_completion_is_not_ready(self) -> None:
        self.run_w1()
        (self.package / "stage-completion.json").unlink()
        with self.assertRaises(w1.W1Error) as caught:
            w1.validate_w1_package(self.package)
        self.assertEqual("W1_COMPLETION_MISSING", caught.exception.code)

    def test_downstream_artifact_is_a_boundary_violation(self) -> None:
        self.run_w1()
        forbidden = self.package / "environment-system.json"
        forbidden.write_text("{}", encoding="utf-8")
        with self.assertRaises(w1.W1Error) as caught:
            w1.validate_w1_package(self.package)
        self.assertEqual("W1_BOUNDARY_VIOLATION", caught.exception.code)

    def test_semantic_shells_are_rejected_after_reseal(self) -> None:
        self.run_w1()
        cases = []

        empty_actor = self._read_model()
        empty_actor["systems"][0]["actor_slot_ids"] = []
        cases.append(("empty-actor", empty_actor, "W1_ACTOR_SLOT_DANGLING"))

        dangling_fact = self._read_model()
        dangling_fact["world_facts"].append(
            {
                "id": "WF-UNSOURCED",
                "kind": "condition",
                "statement": "An unsupported condition.",
                "applies_to_ids": ["SL-UNKNOWN"],
                "constraints": ["Unsupported."],
                "consequences": ["Unsupported."],
                "source_ids": ["WR-UNKNOWN"],
            }
        )
        dangling_fact["authority_partition"]["autonomous_owned"].append(
            "WF-UNSOURCED"
        )
        cases.append(("dangling-fact", dangling_fact, "W1_SOURCE_ID_DANGLING"))

        placeholder_facets = self._read_model()
        placeholder_facets["world_facets"] = {
            name: ["placeholder"]
            for name in placeholder_facets["world_facets"]
        }
        cases.append(
            ("placeholder-facets", placeholder_facets, "W1_FACET_UNBOUND")
        )

        for name, model, expected_code in cases:
            with self.subTest(name=name):
                mutant = self.work / "mutants" / name
                shutil.copytree(self.package, mutant)
                self._reseal_model(model, package=mutant)
                with self.assertRaises(w1.W1Error) as caught:
                    w1.validate_w1_package(mutant)
                self.assertEqual(expected_code, caught.exception.code)

    def test_missing_controlled_thread_is_blocked(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(w1.W1Error) as caught:
                w1.run_w1(
                    self.package,
                    baseline_package=self.b0,
                    storyline_package=self.s1,
                    coordinator=self.coordinator,
                    input_gate=self.gate,
                    controlled_workspace=self.workspace,
                    logical_package_path="W1",
                    next_state_path="state/revision-003.json",
                )
        self.assertEqual("W1_THREAD_REQUIRED", caught.exception.code)
        self.assertFalse(self.package.exists())

    def test_gate_authoritative_rebuilt_upstream_paths_run_and_validate(self) -> None:
        session = json.loads(
            (self.workspace / "generation-session.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            "workspaces/B0-attempt-01/package/stage-completion.json",
            session["baseline_completion"]["path"],
        )
        self.assertEqual(
            "S1/attempt-03/stage-completion.json",
            session["upstream_completions"][0]["path"],
        )
        self.run_w1()
        self.assertEqual("ready", w1.validate_w1_package(self.package)["verdict"])

    def test_foreign_rebuilt_b0_path_is_rejected_before_workspace_write(self) -> None:
        data = copy.deepcopy(self.gate.data)
        data["baseline_completion"]["path"] = (
            "workspaces/foreign/package/stage-completion.json"
        )
        forged = runtime.seal_document(data, self.gate.reference["path"])
        workspace = self.work / "foreign-b0-workspace"
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-foreign-b0"}, clear=False
        ):
            with self.assertRaises(w1.W1Error) as caught:
                w1.start_w1_session(
                    workspace,
                    baseline_package=self.b0,
                    storyline_package=self.s1,
                    input_gate=forged,
                )
        self.assertEqual("W1_B0_INVALID", caught.exception.code)
        self.assertFalse(workspace.exists())

    def test_stale_rebuilt_s1_hash_is_rejected_before_workspace_write(self) -> None:
        data = copy.deepcopy(self.gate.data)
        data["upstream_completions"][0]["sha256"] = "f" * 64
        forged = runtime.seal_document(data, self.gate.reference["path"])
        workspace = self.work / "stale-s1-workspace"
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-stale-s1"}, clear=False
        ):
            with self.assertRaises(w1.W1Error) as caught:
                w1.start_w1_session(
                    workspace,
                    baseline_package=self.b0,
                    storyline_package=self.s1,
                    input_gate=forged,
                )
        self.assertEqual("W1_S1_INVALID", caught.exception.code)
        self.assertFalse(workspace.exists())

    def test_tampered_rebuilt_b0_completion_is_rejected_before_workspace_write(
        self,
    ) -> None:
        completion_path = self.b0 / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["run_id"] = "foreign-run"
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8", newline=""
        )
        workspace = self.work / "tampered-b0-workspace"
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-tampered-b0"}, clear=False
        ):
            with self.assertRaises(w1.W1Error) as caught:
                w1.start_w1_session(
                    workspace,
                    baseline_package=self.b0,
                    storyline_package=self.s1,
                    input_gate=self.gate,
                )
        self.assertEqual("W1_B0_INVALID", caught.exception.code)
        self.assertFalse(workspace.exists())

    def _read_model(self) -> dict[str, object]:
        return json.loads(
            (self.package / "world-model.json").read_text(encoding="utf-8")
        )

    def _disguise_current_package_as_legacy(self) -> None:
        model = self._read_model()
        model["schema_version"] = w1.LEGACY_MODEL_SCHEMA_VERSION
        model.pop("contract_revision")
        (self.package / "world-model.json").write_text(
            runtime.canonical_json(model), encoding="utf-8"
        )

        session_path = self.package / "generation-session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session.pop("contract_revision")
        session_path.write_text(runtime.canonical_json(session), encoding="utf-8")

        previous = None
        evidence_paths = []
        for index, phase in enumerate(w1.PHASES, 1):
            path = self.package / "generation-evidence" / f"{index:02d}-{phase}.json"
            evidence = json.loads(path.read_text(encoding="utf-8"))
            evidence.pop("contract_revision")
            evidence["previous_evidence_sha256"] = previous
            if phase == "final-world-model":
                evidence["payload"]["model"] = copy.deepcopy(model)
            evidence["payload_sha256"] = runtime.canonical_sha256(
                evidence["payload"]
            )
            path.write_text(runtime.canonical_json(evidence), encoding="utf-8")
            previous = runtime.sha256_file(path)
            evidence_paths.append(path)

        index_path = self.package / "generation-evidence-index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["evidence"] = [
            runtime.artifact_reference(path, root=self.package)
            for path in evidence_paths
        ]
        index_path.write_text(runtime.canonical_json(index), encoding="utf-8")

        execution_path = self.package / "execution-record.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["output_sha256"] = runtime.canonical_sha256(model)
        execution_path.write_text(
            runtime.canonical_json(execution), encoding="utf-8"
        )

        manifest_path = self.package / "package-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"] = [
            runtime.artifact_reference(self.package / item["path"], root=self.package)
            for item in manifest["files"]
        ]
        manifest["artifact_roles"] = {
            role: runtime.artifact_reference(
                self.package / reference["path"], root=self.package
            )
            for role, reference in manifest["artifact_roles"].items()
        }
        manifest_path.write_text(runtime.canonical_json(manifest), encoding="utf-8")

        completion_path = self.package / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["manifest"]["sha256"] = runtime.sha256_file(manifest_path)
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )

    def _reseal_model(
        self,
        model: dict[str, object],
        *,
        input_gate: dict[str, str] | None = None,
        package: Path | None = None,
    ) -> None:
        root = package or self.package
        model_path = root / "world-model.json"
        model_path.write_text(runtime.canonical_json(model), encoding="utf-8")
        execution_path = root / "execution-record.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["output_sha256"] = runtime.canonical_sha256(model)
        if input_gate is not None:
            execution["input_gate"] = copy.deepcopy(input_gate)
        execution_path.write_text(
            runtime.canonical_json(execution), encoding="utf-8"
        )
        manifest_path = root / "package-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        replacements = {
            "world-model.json": runtime.artifact_reference(
                model_path, root=root
            ),
            "execution-record.json": runtime.artifact_reference(
                execution_path, root=root
            ),
        }
        manifest["files"] = [
            replacements.get(item["path"], item) for item in manifest["files"]
        ]
        manifest["artifact_roles"]["canonical"] = replacements["world-model.json"]
        manifest["artifact_roles"]["execution_record"] = replacements[
            "execution-record.json"
        ]
        manifest_path.write_text(
            runtime.canonical_json(manifest), encoding="utf-8"
        )
        completion_path = root / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["manifest"]["sha256"] = runtime.sha256_file(manifest_path)
        if input_gate is not None:
            completion["input_gate"] = copy.deepcopy(input_gate)
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )


if __name__ == "__main__":
    unittest.main()
