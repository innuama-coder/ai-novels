from __future__ import annotations

import copy
import importlib
import unittest


p1 = importlib.import_module(
    "skills.novel-conception-deliverable-assembler.scripts.run_v2"
)


class P1OpenItemProjectionTests(unittest.TestCase):
    @staticmethod
    def _fixture():
        source_ids = ["CAU-OPEN", "INT-OPEN", "NAR-OPEN"]
        baseline = {
            "control_registry": [
                {"id": source_id, "hardness": "author_open"}
                for source_id in source_ids
            ],
            "open_items": source_ids,
        }
        models = {
            stage: {
                "authority_partition": {
                    name: [] for name in p1._PARTITIONS
                },
                "open_items": [],
            }
            for stage in (*p1._MODEL_STAGES, "Q1")
        }
        for index, source_id in enumerate(source_ids):
            identifier = f"OPEN-{source_id}"
            models["S1"]["open_items"].append(
                {
                    "id": identifier,
                    "question": f"Author question {index}",
                    "source_ids": [source_id],
                    "status": "author_open",
                }
            )
            models["T1"]["open_items"].append(
                {
                    "id": identifier,
                    "question": "Preserved author-open item.",
                    "source_ids": [source_id],
                    "status": "author_open",
                }
            )
        for stage in ("W1", "E1", "C1"):
            for index, source_id in enumerate(source_ids):
                models[stage]["open_items"].append(
                    {
                        "id": f"OPEN-{stage}-{index}",
                        "question": f"{stage} local question {index}",
                        "source_ids": [source_id],
                        "status": "author_open",
                    }
                )
        quality = []
        for stage, classification in (
            ("S1", "s1_obligation"),
            ("T1", "t1_realization"),
        ):
            for body in models[stage]["open_items"]:
                quality.append(
                    {
                        "stage": stage,
                        "classification": classification,
                        "id": body["id"],
                        "value_sha256": p1.rt.canonical_sha256(body),
                    }
                )
        models["Q1"]["quality_coverage"] = {
            "required_objects": copy.deepcopy(quality),
            "covered_objects": [
                {**item, "handoff_check_ids": ["CHK-TRACE"]}
                for item in quality
            ],
        }
        return baseline, models

    def test_current_shape_merges_only_three_s1_t1_pairs(self):
        baseline, models = self._fixture()
        models_before = copy.deepcopy(models)
        input_count = sum(
            len(models[stage]["open_items"]) for stage in p1._MODEL_STAGES
        )
        _, output = p1._authority_and_open(baseline, models)
        self.assertEqual(models_before, models)
        self.assertEqual(15, input_count)
        self.assertEqual(12, len(output))
        self.assertEqual(
            sorted(item["id"] for item in output),
            [item["id"] for item in output],
        )
        for s1 in models["S1"]["open_items"]:
            self.assertEqual(
                s1,
                next(item for item in output if item["id"] == s1["id"]),
            )
        self.assertEqual(
            set(baseline["open_items"]),
            {source for item in output for source in item["source_ids"]},
        )

    def test_projection_mutants_fail_closed(self):
        def source_mismatch(baseline, models):
            models["T1"]["open_items"][0]["source_ids"] = ["INT-OPEN"]

        def status(baseline, models):
            models["S1"]["open_items"][0]["status"] = "resolved"

        def question(baseline, models):
            models["T1"]["open_items"][0]["question"] = "Approximate."

        def q1_missing(baseline, models):
            models["Q1"]["quality_coverage"]["covered_objects"] = [
                item
                for item in models["Q1"]["quality_coverage"]["covered_objects"]
                if not (item["stage"] == "T1" and item["id"] == "OPEN-CAU-OPEN")
            ]

        def q1_hash(baseline, models):
            models["Q1"]["quality_coverage"]["required_objects"][0][
                "value_sha256"
            ] = "0" * 64

        def third_stage(baseline, models):
            models["W1"]["open_items"][0]["id"] = "OPEN-CAU-OPEN"

        def same_stage(baseline, models):
            models["S1"]["open_items"].append(
                copy.deepcopy(models["S1"]["open_items"][0])
            )

        def b0_hardness(baseline, models):
            baseline["control_registry"][0]["hardness"] = "author_locked"

        def s1_stale(baseline, models):
            models["S1"]["open_items"][0]["question"] = "Stale after Q1."

        mutations = {
            "source": source_mismatch,
            "status": status,
            "question": question,
            "q1_missing": q1_missing,
            "q1_hash": q1_hash,
            "third": third_stage,
            "same_stage": same_stage,
            "b0_hardness": b0_hardness,
            "s1_stale": s1_stale,
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                baseline, models = self._fixture()
                mutation(baseline, models)
                with self.assertRaises(p1.P1Error):
                    p1._authority_and_open(baseline, models)


if __name__ == "__main__":
    unittest.main()
