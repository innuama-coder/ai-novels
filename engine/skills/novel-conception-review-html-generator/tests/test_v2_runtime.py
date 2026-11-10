from __future__ import annotations

import copy
import importlib
import json
import shutil
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock


H1C_MODULE = (
    "skills.novel-conception-review-html-generator.scripts.run_v2"
)
H1A_TEST_MODULE = (
    "skills.novel-conception-human-review-assembler.tests.test_v2_runtime"
)
H1B_TEST_MODULE = (
    "skills.novel-conception-fragment-writer.tests.test_v2_runtime"
)

SEMANTIC_ROLES = (
    "control_logic_chain",
    "world_environment_map",
    "storyline_architecture",
    "major_event_timeline",
    "character_relationship_network",
)
PATH_KINDS = (
    "world",
    "storylines",
    "characters",
    "fragments",
    "decision",
)


class H1CImplementationIdentityTests(unittest.TestCase):
    def test_identity_binds_reused_h1a_visible_copy_contract(self):
        h1c = importlib.import_module(H1C_MODULE)
        paths = h1c._implementation_paths()

        self.assertEqual(
            paths["h1-a-visible-copy/run_v2.py"],
            Path(h1c.h1a.__file__).resolve(),
        )
        self.assertEqual(
            paths["h1-a-visible-copy/review-plan-contract.md"],
            Path(h1c.h1a.__file__).resolve().parents[1]
            / "references"
            / "review-plan-contract.md",
        )
        self.assertTrue(
            paths["h1-a-visible-copy/review-plan-contract.md"].is_file()
        )


class _Coordinator:
    def __init__(self, *, reject: bool = False):
        self.calls: list[dict] = []
        self.reject = reject

    def accept_h1_workspace_transition(self, **kwargs):
        self.calls.append(kwargs)
        if self.reject:
            raise RuntimeError("coordinator rejected rendered transition")
        return {"state": kwargs["expected_next_state"]}


class _HtmlInspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.attrs: list[tuple[str, dict[str, str]]] = []
        self.tags: list[str] = []
        self.text: list[str] = []
        self._capture: str | None = None
        self._capture_text: list[str] = []
        self.titles: list[str] = []
        self.h1s: list[str] = []
        self._in_head = False

    def handle_starttag(self, tag, attrs):
        values = {key: value or "" for key, value in attrs}
        self.tags.append(tag)
        self.attrs.append((tag, values))
        if tag == "head":
            self._in_head = True
        if (tag == "title" and self._in_head) or tag == "h1":
            self._capture = tag
            self._capture_text = []

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == self._capture:
            value = "".join(self._capture_text).strip()
            if tag == "title":
                self.titles.append(value)
            else:
                self.h1s.append(value)
            self._capture = None
            self._capture_text = []
        if tag == "head":
            self._in_head = False

    def handle_data(self, data):
        self.text.append(data)
        if self._capture is not None:
            self._capture_text.append(data)

    @property
    def visible_text(self) -> str:
        return "\n".join(self.text)

    def attr_values(self, name: str) -> list[str]:
        return [
            attrs[name]
            for _, attrs in self.attrs
            if name in attrs
        ]


class H1CHtmlRuntimeTests(unittest.TestCase):
    """Exercise the real H1-A/B/C chain behind one isolated P1 boundary.

    Building and revalidating B0 through P1 is the autonomous workflow E2E
    suite's responsibility.  This suite replaces only that formal P1
    validator boundary; all H1 controlled workspaces, packages, validators,
    and the ContractRuntime remain production implementations.
    """

    @classmethod
    def setUpClass(cls):
        cls.h1c = importlib.import_module(H1C_MODULE)
        cls.h1a_tests = importlib.import_module(H1A_TEST_MODULE)
        cls.h1b_tests = importlib.import_module(H1B_TEST_MODULE)
        cls.runtime = cls.h1c.rt.ContractRuntime()
        cls._build_formal_chain()

    @classmethod
    def tearDownClass(cls):
        for case in reversed(cls._kept_h1a_cases):
            cls._original_h1a_teardown(case)
        cls._h1b_driver.tearDown()

    @classmethod
    def _build_formal_chain(cls):
        """Retain the upstream suite's real formal integration products.

        The upstream integration constructs controlled H1-A plan evidence,
        controlled H1-B phase evidence, and H1-A assembly with the production
        ContractRuntime. Capturing its assembly call avoids a second, drifting
        model of those contracts.
        """

        driver = cls.h1b_tests.H1BRuntimeTests(
            methodName=(
                "test_real_h1a_plan_h1b_and_h1a_assembly_integration"
            )
        )
        driver.setUp()
        cls._h1b_driver = driver
        cls._kept_h1a_cases = []
        captured: dict[str, object] = {}

        case_class = cls.h1a_tests.H1APlanSkeletonTests
        original_setup = case_class.setUp
        original_teardown = case_class.tearDown
        original_assemble = cls.h1c.h1a.run_assemble
        cls._original_h1a_teardown = original_teardown

        def retaining_setup(case):
            original_setup(case)
            cls._kept_h1a_cases.append(case)

        def capture_assemble(*args, **kwargs):
            receipt = original_assemble(*args, **kwargs)
            captured["assembly_kwargs"] = copy.copy(kwargs)
            captured["assembly_receipt"] = receipt
            return receipt

        try:
            with mock.patch.object(
                case_class, "setUp", retaining_setup
            ), mock.patch.object(
                case_class, "tearDown", lambda _case: None
            ), mock.patch.object(
                cls.h1c.h1a,
                "run_assemble",
                side_effect=capture_assemble,
            ):
                driver.test_real_h1a_plan_h1b_and_h1a_assembly_integration()
        except Exception:
            for case in reversed(cls._kept_h1a_cases):
                original_teardown(case)
            driver.tearDown()
            raise

        assembly_kwargs = captured["assembly_kwargs"]
        assembly_receipt = captured["assembly_receipt"]
        ready_workspace = assembly_kwargs["workspace_state"]
        assembly_manifest = {
            "path": "H1/assembly/package-manifest.json",
            "sha256": cls.h1c.rt.sha256_file(
                assembly_receipt.package_root / "package-manifest.json"
            ),
        }
        assembled_data = {
            "schema_version": "2.0",
            "run_id": ready_workspace.data["run_id"],
            "stage": "H1",
            "session_id": ready_workspace.data["session_id"],
            "state": "assembled",
            "p1_completion": copy.deepcopy(
                ready_workspace.data["p1_completion"]
            ),
            "previous_state_sha256": ready_workspace.reference["sha256"],
            "artifacts": {
                **copy.deepcopy(ready_workspace.data["artifacts"]),
                "assembly_manifest": assembly_manifest,
            },
        }
        assembled_workspace = cls.h1c.rt.SealedDocument(
            data=assembled_data,
            reference={
                "path": "H1/assembled-workspace-state.json",
                "sha256": cls.h1c.rt.canonical_sha256(assembled_data),
            },
        )
        cls.chain = {
            "p1_package": assembly_kwargs["p1_package"],
            "plan_package": assembly_kwargs["plan_package"],
            "plan_input_gate": assembly_kwargs["plan_input_gate"],
            "plan_workspace_state": assembly_kwargs[
                "plan_workspace_state"
            ],
            "fragment_package": assembly_kwargs["fragment_package"],
            "fragment_workspace_state": assembly_kwargs[
                "fragment_workspace_state"
            ],
            "assembly_package": assembly_receipt.package_root,
            "assembly_workspace_state": ready_workspace,
            "workspace_state": assembled_workspace,
            "runtime": cls.runtime,
        }
        cls.report = json.loads(
            (
                assembly_receipt.package_root
                / "human-review-report.json"
            ).read_text(encoding="utf-8")
        )

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def _run(self, name: str = "html-package", coordinator=None):
        coordinator = coordinator or _Coordinator()
        output = self.root / name
        with mock.patch.object(
            self.h1c.h1a.p1_runtime,
            "validate_p1_package",
            side_effect=self._accept_isolated_p1_boundary,
        ):
            receipt = self.h1c.run(
                output,
                coordinator=coordinator,
                **self.chain,
            )
        return output, receipt, coordinator

    def _validate(self, output: Path):
        with mock.patch.object(
            self.h1c.h1a.p1_runtime,
            "validate_p1_package",
            side_effect=self._accept_isolated_p1_boundary,
        ):
            return self.h1c.validate_html_package(
                output,
                **self.chain,
            )

    @classmethod
    def _accept_isolated_p1_boundary(cls, package_root, *, runtime):
        if not isinstance(runtime, cls.h1c.rt.ContractRuntime):
            raise AssertionError("P1 boundary did not receive ContractRuntime")
        root = Path(package_root).resolve()
        if root != Path(cls.chain["p1_package"]).resolve():
            raise AssertionError("P1 boundary received an unexpected package")
        if not (root / "novel-conception-package.json").is_file():
            raise AssertionError("P1 canonical package is missing")
        if not (root / "stage-completion.json").is_file():
            raise AssertionError("P1 completion is missing")
        return {"verdict": "ready"}

    def test_real_chain_renders_and_transitions_exactly_once(self):
        with mock.patch.object(
            self.h1c.h1a,
            "validate_assembly_package",
            wraps=self.h1c.h1a.validate_assembly_package,
        ) as assembly_validator:
            output, receipt, coordinator = self._run()

        self.assertGreaterEqual(assembly_validator.call_count, 1)
        self.assertTrue((output / "human-review-report.html").is_file())
        self.assertTrue((output / "render-record.json").is_file())
        self.assertTrue((output / "validation.json").is_file())
        self.assertTrue((output / "package-manifest.json").is_file())
        self.assertFalse((output / "stage-completion.json").exists())
        self.assertFalse((output / "h1-completion.json").exists())
        self.assertEqual(len(coordinator.calls), 1)
        call = coordinator.calls[0]
        self.assertIs(
            call["current_workspace"], self.chain["workspace_state"]
        )
        self.assertEqual(call["expected_next_state"], "rendered")
        self.assertEqual(receipt.transition["state"], "rendered")
        self.assertEqual(self._validate(output)["verdict"], "ready")

    def test_p1_formal_boundary_failure_is_propagated_before_publish(self):
        output = self.root / "p1-boundary-rejected"
        with mock.patch.object(
            self.h1c.h1a.p1_runtime,
            "validate_p1_package",
            side_effect=RuntimeError(
                "P1_PACKAGE_BOUNDARY_INVALID: injected boundary failure"
            ),
        ), self.assertRaisesRegex(
            self.h1c.H1CError,
            "H1C_UPSTREAM_INVALID.*H1A_P1_INVALID.*"
            "P1_PACKAGE_BOUNDARY_INVALID",
        ):
            self.h1c.run(
                output,
                coordinator=_Coordinator(),
                **self.chain,
            )
        self.assertFalse(output.exists())

    def test_gate_workspace_and_active_return_lineage_are_exact(self):
        self.assertEqual(
            [
                self.chain["plan_workspace_state"].data["state"],
                self.chain["fragment_workspace_state"].data["state"],
                self.chain["assembly_workspace_state"].data["state"],
                self.chain["workspace_state"].data["state"],
            ],
            ["initialized", "planned", "fragments_ready", "assembled"],
        )
        self.assertEqual(
            self.chain["plan_workspace_state"].data["p1_completion"],
            self.chain["plan_input_gate"].data["upstream_completions"][0],
        )
        self.assertIsNone(self.chain["plan_input_gate"].data["active_return"])
        self.assertIsNone(
            self.chain["plan_input_gate"].data["return_binding"]
        )

        forged_data = {
            "schema_version": "2.0",
            "run_id": self.chain["workspace_state"].data["run_id"],
            "return_id": "RET-FORGED-H1",
        }
        forged_return = self.h1c.rt.SealedDocument(
            data=forged_data,
            reference={
                "path": "returns/RET-FORGED-H1/return-request.json",
                "sha256": self.h1c.rt.canonical_sha256(forged_data),
            },
        )
        args = {
            **self.chain,
            "plan_active_return_request": forged_return,
        }
        output = self.root / "forged-active-return"
        with mock.patch.object(
            self.h1c.h1a.p1_runtime,
            "validate_p1_package",
            side_effect=self._accept_isolated_p1_boundary,
        ), self.assertRaisesRegex(
            self.h1c.H1CError,
            "H1C_UPSTREAM_INVALID",
        ):
            self.h1c.run(
                output,
                coordinator=_Coordinator(),
                **args,
            )
        self.assertFalse(output.exists())

    def test_input_toctou_is_rejected_before_atomic_publish(self):
        assembly_copy = self.root / "assembly-toctou"
        shutil.copytree(self.chain["assembly_package"], assembly_copy)
        args = {**self.chain, "assembly_package": assembly_copy}
        real_render = self.h1c.render_html

        def render_then_mutate(report):
            document = real_render(report)
            report_path = assembly_copy / "human-review-report.json"
            report_path.write_bytes(report_path.read_bytes() + b" ")
            return document

        output = self.root / "toctou-output"
        with mock.patch.object(
            self.h1c.h1a.p1_runtime,
            "validate_p1_package",
            side_effect=self._accept_isolated_p1_boundary,
        ), mock.patch.object(
            self.h1c,
            "render_html",
            side_effect=render_then_mutate,
        ), self.assertRaisesRegex(
            self.h1c.H1CError,
            "H1C_INPUT_MUTATED|H1C_UPSTREAM_INVALID",
        ):
            self.h1c.run(
                output,
                coordinator=_Coordinator(),
                **args,
            )
        self.assertFalse(output.exists())

    def test_coordinator_rejection_keeps_valid_atomic_package_unreferenced(self):
        output = self.root / "coordinator-rejected"
        coordinator = _Coordinator(reject=True)
        with mock.patch.object(
            self.h1c.h1a.p1_runtime,
            "validate_p1_package",
            side_effect=self._accept_isolated_p1_boundary,
        ), self.assertRaisesRegex(
            RuntimeError,
            "coordinator rejected rendered transition",
        ):
            self.h1c.run(
                output,
                coordinator=coordinator,
                **self.chain,
            )
        self.assertEqual(len(coordinator.calls), 1)
        self.assertTrue((output / "package-manifest.json").is_file())
        self.assertEqual(self._validate(output)["verdict"], "ready")

    def test_render_is_byte_deterministic_and_tamper_evident(self):
        first, _, _ = self._run("first")
        second, _, _ = self._run("second")
        first_bytes = (first / "human-review-report.html").read_bytes()
        second_bytes = (second / "human-review-report.html").read_bytes()
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(
            first_bytes.decode("utf-8"),
            self.h1c.render_html(self.report),
        )

        path = first / "human-review-report.html"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                self.report["title"], "tampered title", 1
            ),
            encoding="utf-8",
            newline="",
        )
        with self.assertRaises(Exception):
            self._validate(first)

    def test_title_four_dimension_navigation_and_editorial_content_are_visible(self):
        output, _, _ = self._run()
        document = (
            output / "human-review-report.html"
        ).read_text(encoding="utf-8")
        inspector = _HtmlInspector()
        inspector.feed(document)
        inspector.close()

        self.assertEqual(inspector.titles, [self.report["title"]])
        self.assertEqual(inspector.h1s, [self.report["title"]])
        self.assertEqual(
            inspector.attr_values("data-path-id"),
            [item["id"] for item in self.report["review_path"][:4]],
        )
        self.assertEqual(
            inspector.attr_values("data-path-kind"),
            list(PATH_KINDS[:4]),
        )
        ids = set(inspector.attr_values("id"))
        self.assertTrue(
            {
                "section-world",
                "section-storylines",
                "section-characters",
                "section-fragments",
                "section-decision",
            }
            <= ids
        )
        visible = inspector.visible_text
        normalized_visible = self._normalized_text(visible)
        for collection in (
            self.report["world"]["systems"],
            self.report["world"]["environments"],
            self.report["world"]["event_conditions"],
            self.report["storylines"]["lines"],
            self.report["storylines"]["connections"],
            self.report["storylines"]["major_events"],
            self.report["characters"]["core_characters"],
            self.report["characters"]["supporting_characters"],
            self.report["characters"]["relationship_networks"],
            self.report["characters"]["role_coverage"],
        ):
            for item in collection:
                for key in ("title", "definition"):
                    for value in self._leaf_strings(item[key]):
                        self.assertIn(value, visible)
        element_ids = inspector.attr_values("data-element-id")
        for item in self.report["fragments"]:
            self.assertIn(item["id"], element_ids)
            self.assertIn(item["title"], visible)
            self.assertIn(self._normalized_text(item["text"]), normalized_visible)
        self.assertIn(self.report["decision_prompts"][0]["question"], visible)
        for forbidden in (
            "Full P1 evidence", "Decision controls", "来源覆盖",
            "controls=", "sha256=", "run=",
        ):
            self.assertNotIn(forbidden, document)

    def test_story_rhythm_scalar_and_module_are_rendered_once(self):
        report = copy.deepcopy(self.report)
        rhythm_item = next(
            item
            for collection in (
                report["storylines"]["lines"],
                report["storylines"]["connections"],
                report["storylines"]["major_events"],
            )
            for item in collection
            if item["definition"] != report["storylines"]["story_subject"]
        )
        rhythm = "悬念从追查真相转向一次无法委托的生命选择。"
        rhythm_item["definition"] = rhythm
        report["storylines"]["suspense_conflict_rhythm"] = rhythm

        document = self.h1c.render_html(report)

        self.assertEqual(1, document.count(rhythm))
        self.assertIn(rhythm_item["title"], document)
        self.h1c.validate_html_document(document, report)

    def test_first_screen_world_and_story_scalars_are_rendered_once(self):
        document = self.h1c.render_html(self.report)
        world_definition = self.report["world"]["definition"]
        story_subject = self.report["storylines"]["story_subject"]
        world_item = next(
            item
            for key in ("systems", "environments", "event_conditions")
            for item in self.report["world"][key]
            if item["definition"] == world_definition
        )
        story_item = next(
            item
            for key in ("lines", "connections", "major_events")
            for item in self.report["storylines"][key]
            if item["definition"] == story_subject
        )
        logic_item = next(
            item
            for key in ("systems", "environments", "event_conditions")
            for item in self.report["world"][key]
            if item["definition"] == self.report["world"]["operating_logic"]
        )

        self.assertEqual(
            1, document.count(f'<p class="promise">{world_definition}</p>')
        )
        self.assertEqual(1, document.count(f'<p class="pitch">{story_subject}</p>'))
        self.assertNotIn(f'<p class="lead">{world_definition}</p>', document)
        self.assertNotIn(f'<p class="lead">{story_subject}</p>', document)
        self.assertNotIn(f'<p>{world_definition}</p></article>', document)
        self.assertNotIn(f'<p>{story_subject}</p></article>', document)
        self.assertIn(world_item["title"], document)
        self.assertIn(story_item["title"], document)
        self.assertIn(f'data-element-id="{world_item["id"]}"', document)
        self.assertIn(f'data-element-id="{story_item["id"]}"', document)
        self.assertIn(logic_item["title"], document)
        self.assertIn(logic_item["responsibility"], document)
        self.assertIn(f'data-element-id="{logic_item["id"]}"', document)
        self.h1c.validate_html_document(document, self.report)

    def test_world_scalar_module_mapping_is_exact(self):
        for mutation in ("missing", "multiple"):
            with self.subTest(mutation=mutation):
                report = copy.deepcopy(self.report)
                operating_logic = report["world"]["operating_logic"]
                modules = [
                    item
                    for key in ("systems", "environments", "event_conditions")
                    for item in report["world"][key]
                ]
                match = next(
                    item for item in modules if item["definition"] == operating_logic
                )
                if mutation == "missing":
                    match["definition"] = "另一套不会匹配运行规则的说明。"
                else:
                    duplicate = next(item for item in modules if item is not match)
                    duplicate["definition"] = operating_logic

                with self.assertRaisesRegex(
                    ValueError, "H1C_HTML_PROJECTION_INVALID"
                ):
                    self.h1c.render_html(report)

    def test_story_and_character_constraints_are_module_backed_once(self):
        document = self.h1c.render_html(self.report)
        inspector = _HtmlInspector()
        inspector.feed(document)
        inspector.close()
        blocks = [value.strip() for value in inspector.text if value.strip()]

        for section, collections in (
            ("storylines", ("lines", "connections", "major_events")),
            (
                "characters",
                (
                    "core_characters",
                    "supporting_characters",
                    "relationship_networks",
                    "role_coverage",
                ),
            ),
        ):
            modules = [
                item for key in collections for item in self.report[section][key]
            ]
            for value in self.report[section]["constraints"]:
                matches = [item for item in modules if item["definition"] == value]
                self.assertEqual(1, len(matches))
                self.assertEqual(1, blocks.count(value))
                self.assertIn(matches[0]["title"], blocks)
                self.assertIn(
                    f'data-element-id="{matches[0]["id"]}"', document
                )
        self.h1c.validate_html_document(document, self.report)

    def test_review_path_visible_ids_are_byte_and_data_traceable(self):
        baseline = self.h1c.render_html(self.report)
        changed = copy.deepcopy(self.report)
        step = changed["review_path"][0]
        step["visible_element_ids"] = list(
            reversed(step["visible_element_ids"])
        )
        self.runtime.validate(
            changed, "human-review-report.schema.json"
        )

        document = self.h1c.render_html(changed)
        self.assertNotEqual(document.encode("utf-8"), baseline.encode("utf-8"))
        self.h1c.validate_html_document(document, changed)
        inspector = _HtmlInspector()
        inspector.feed(document)
        inspector.close()
        anchor = next(
            attrs
            for tag, attrs in inspector.attrs
            if tag == "a"
            and attrs.get("data-path-id") == step["id"]
        )
        self.assertEqual(
            json.loads(anchor["data-visible-element-ids"]),
            step["visible_element_ids"],
        )

    def test_visual_text_module_is_byte_and_data_traceable(self):
        baseline = self.h1c.render_html(self.report)
        changed = copy.deepcopy(self.report)
        visual = next(
            item
            for item in changed["visual_models"]
            if item["section_id"] == "SEC-WORLD"
        )
        legal_world_modules = [
            item["id"]
            for key in ("systems", "environments", "event_conditions")
            for item in changed["world"][key]
        ]
        replacement = next(
            item
            for item in legal_world_modules
            if item != visual["text_equivalent_module_id"]
        )
        visual["text_equivalent_module_id"] = replacement
        self.runtime.validate(
            changed, "human-review-report.schema.json"
        )

        document = self.h1c.render_html(changed)
        self.assertNotEqual(document.encode("utf-8"), baseline.encode("utf-8"))
        self.h1c.validate_html_document(document, changed)
        inspector = _HtmlInspector()
        inspector.feed(document)
        inspector.close()
        bound = [
            (tag, attrs)
            for tag, attrs in inspector.attrs
            if attrs.get("data-visual-id") == visual["id"]
            and (
                tag in {"figure", "svg"}
                or "visual-text-equivalent"
                in attrs.get("class", "").split()
            )
        ]
        self.assertEqual(
            [attrs["data-text-equivalent-module-id"] for _, attrs in bound],
            [replacement, replacement, replacement],
        )

    def test_five_svg_models_preserve_graph_and_text_equivalents(self):
        output, _, _ = self._run()
        document = (
            output / "human-review-report.html"
        ).read_text(encoding="utf-8")
        inspector = _HtmlInspector()
        inspector.feed(document)
        inspector.close()

        page_visuals = [
            visual
            for section_id in (
                "SEC-WORLD",
                "SEC-STORYLINES",
                "SEC-CHARACTERS",
            )
            for visual in self.report["visual_models"]
            if visual["section_id"] == section_id
        ]
        self.assertEqual(
            [
                attrs["data-semantic-role"]
                for tag, attrs in inspector.attrs
                if tag == "svg" and "data-semantic-role" in attrs
            ],
            [item["semantic_role"] for item in page_visuals],
        )
        self.assertEqual(
            [
                attrs["data-visual-id"]
                for tag, attrs in inspector.attrs
                if tag == "svg" and "data-visual-id" in attrs
            ],
            [item["id"] for item in page_visuals],
        )
        self.assertEqual(
            [
                attrs["data-node-id"]
                for tag, attrs in inspector.attrs
                if tag == "g" and "data-node-id" in attrs
            ],
            [
                node["id"]
                for visual in page_visuals
                for node in visual["nodes"]
            ],
        )
        self.assertEqual(
            [
                attrs["data-edge-id"]
                for tag, attrs in inspector.attrs
                if tag == "g" and "data-edge-id" in attrs
            ],
            [
                edge["id"]
                for visual in page_visuals
                for edge in visual["edges"]
            ],
        )
        self.assertEqual(
            [
                attrs["data-group-id"]
                for tag, attrs in inspector.attrs
                if tag == "g"
                and "data-group-id" in attrs
                and "data-node-id" not in attrs
                and "data-edge-id" not in attrs
            ],
            [
                group["id"]
                for visual in page_visuals
                for group in visual["groups"]
            ],
        )
        svg_attrs = [
            attrs
            for tag, attrs in inspector.attrs
            if tag == "svg"
            and "semantic-visual" in attrs.get("class", "").split()
        ]
        self.assertEqual(len(svg_attrs), 5)
        self.assertTrue(
            all(
                item.get("role") == "img"
                and item.get("aria-labelledby")
                for item in svg_attrs
            )
        )
        text_equivalent_blocks = [
            attrs
            for _, attrs in inspector.attrs
            if "visual-text-equivalent"
            in attrs.get("class", "").split()
        ]
        self.assertEqual(len(text_equivalent_blocks), 5)
        for visual in self.report["visual_models"]:
            for item in (
                *visual["groups"],
                *visual["nodes"],
                *visual["edges"],
            ):
                self.assertIn(item["summary"], document)
        timeline = next(
            item
            for item in self.report["visual_models"]
            if item["semantic_role"] == "major_event_timeline"
        )
        self.assertTrue(timeline["groups"])
        self.assertTrue(
            all(
                node["lane"]
                and node["temporal_label"]
                and isinstance(node["order"], int)
                for node in timeline["nodes"]
            )
        )

    def test_security_csp_xss_and_no_decision_side_effects(self):
        report = copy.deepcopy(self.report)
        report["title"] = (
            '《</script><img src="https://bad.invalid" '
            'onerror="steal()">》'
        )
        report["fragments"][0]["text"] = (
            '<svg onload="steal()"><a href="javascript:steal()">x</a>'
        )
        document = self.h1c.render_html(report)
        self.h1c.validate_html_document(document, report)
        inspector = _HtmlInspector()
        inspector.feed(document)
        inspector.close()

        self.assertNotIn("img", inspector.tags)
        self.assertNotIn("form", inspector.tags)
        self.assertNotIn("button", inspector.tags)
        self.assertNotIn("iframe", inspector.tags)
        self.assertNotIn("object", inspector.tags)
        executable_scripts = [
            attrs
            for tag, attrs in inspector.attrs
            if tag == "script"
            and attrs.get("type") != "application/json"
        ]
        self.assertFalse(executable_scripts)
        for _, attrs in inspector.attrs:
            self.assertFalse(
                any(name.lower().startswith("on") for name in attrs)
            )
            self.assertNotIn("checked", attrs)
            self.assertNotIn("selected", attrs)
            for name in (
                "href",
                "src",
                "action",
                "formaction",
                "xlink:href",
            ):
                value = attrs.get(name, "").lower().strip()
                self.assertFalse(
                    value.startswith(("http:", "https:", "//", "javascript:"))
                )
        self.assertNotIn("navigator.clipboard", document)
        self.assertNotIn("localStorage", document)
        self.assertNotIn("sessionStorage", document)
        self.assertNotIn("URL.createObjectURL", document)
        self.assertNotIn("download=", document)

    def test_public_validator_rejects_url_and_resource_loading_attacks(self):
        document = self.h1c.render_html(self.report)
        self.h1c.validate_html_document(document, self.report)
        inspector = _HtmlInspector()
        inspector.feed(document)
        inspector.close()
        target_ids = set(inspector.attr_values("id"))
        allowed_hrefs = [
            attrs["href"]
            for tag, attrs in inspector.attrs
            if tag == "a" and "href" in attrs
        ]
        self.assertEqual(
            allowed_hrefs,
            [
                "#main-content",
                *[
                    f'#section-{item["kind"]}'
                    for item in self.report["review_path"][:4]
                ],
            ],
        )
        self.assertTrue(
            all(href.removeprefix("#") in target_ids for href in allowed_hrefs)
        )

        injections = {
            "download": document.replace(
                '<a href="#section-world"',
                '<a download="report.html" href="#section-world"',
                1,
            ),
            "meta-refresh": document.replace(
                "</head>",
                '<meta http-equiv="refresh" '
                'content="0;url=https://bad.invalid/"></head>',
                1,
            ),
            "external-xlink": document.replace(
                "</body>",
                '<svg><use xlink:href="https://bad.invalid/a.svg#x">'
                "</use></svg></body>",
                1,
            ),
            "fragment-xlink": document.replace(
                "</body>",
                '<svg><use xlink:href="#main-content"></use></svg></body>',
                1,
            ),
            "external-href": document.replace(
                'href="#section-world"',
                'href="https://bad.invalid/"',
                1,
            ),
        }
        for attribute in (
            "src",
            "action",
            "formaction",
            "poster",
            "data",
            "cite",
            "background",
        ):
            injections[attribute] = document.replace(
                "<body>",
                f'<body {attribute}="https://bad.invalid/resource">',
                1,
            )
        for name, attacked in injections.items():
            with self.subTest(attack=name), self.assertRaisesRegex(
                self.h1c.H1CError,
                "H1C_HTML_SECURITY_INVALID",
            ):
                self.h1c.validate_html_document(attacked, self.report)

    def test_accessibility_responsive_print_and_nonstructured_fail_closed(self):
        output, _, _ = self._run()
        document = (
            output / "human-review-report.html"
        ).read_text(encoding="utf-8")
        inspector = _HtmlInspector()
        inspector.feed(document)
        inspector.close()
        html_attrs = next(
            attrs for tag, attrs in inspector.attrs if tag == "html"
        )
        self.assertEqual(html_attrs.get("lang"), "zh-CN")
        self.assertEqual(
            html_attrs.get("data-render-contract"),
            self.h1c.DOM_CONTRACT,
        )
        self.assertTrue(
            {"header", "nav", "main", "footer"} <= set(inspector.tags)
        )
        self.assertIn("@media(max-width:640px)", document)
        self.assertIn("@media print", document)
        self.assertIn(":focus-visible", document)
        self.assertIn("overflow-x", document)

        malformed = copy.deepcopy(self.report)
        del malformed["visual_models"]
        with self.assertRaises(Exception):
            self.h1c.render_html(malformed)
        with self.assertRaises(Exception):
            self.h1c.validate_html_document(
                "<!doctype html><title>x</title>", malformed
            )

    def test_cross_state_and_upstream_tamper_are_rejected_before_publish(self):
        bad_data = copy.deepcopy(self.chain["workspace_state"].data)
        bad_data["session_id"] = "OTHER-SESSION"
        bad_workspace = self.h1c.rt.SealedDocument(
            data=bad_data,
            reference={
                "path": "H1/other-assembled-workspace.json",
                "sha256": self.h1c.rt.canonical_sha256(bad_data),
            },
        )
        args = {**self.chain, "workspace_state": bad_workspace}
        output = self.root / "wrong-session"
        with self.assertRaises(Exception):
            self.h1c.run(
                output, coordinator=_Coordinator(), **args
            )
        self.assertFalse(output.exists())

        assembly_copy = self.root / "tampered-assembly"
        shutil.copytree(self.chain["assembly_package"], assembly_copy)
        report_path = assembly_copy / "human-review-report.json"
        report_path.write_text(
            report_path.read_text(encoding="utf-8") + " ",
            encoding="utf-8",
            newline="",
        )
        args = {**self.chain, "assembly_package": assembly_copy}
        output = self.root / "tampered-output"
        with self.assertRaises(Exception):
            self.h1c.run(
                output, coordinator=_Coordinator(), **args
            )
        self.assertFalse(output.exists())

    @classmethod
    def _leaf_strings(cls, value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for item in value.values():
                yield from cls._leaf_strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from cls._leaf_strings(item)

    @staticmethod
    def _normalized_text(value: str) -> str:
        return " ".join(value.split())


if __name__ == "__main__":
    unittest.main()
