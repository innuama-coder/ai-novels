from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from testing import duanxian_h1_plan
from testing import run_duanxian_conception_v2


class DuanxianTitleProvenanceTests(unittest.TestCase):
    def test_authoritative_title_is_duanxian_and_matches_primary_specs(self) -> None:
        self.assertEqual("断线", duanxian_h1_plan.WORK_TITLE)
        self.assertEqual("断线", run_duanxian_conception_v2.authoritative_work_title())

        metadata = json.loads(
            duanxian_h1_plan.PROJECT_DISPLAY_METADATA.read_text(encoding="utf-8")
        )
        for relative in metadata["source_documents"]:
            heading = (duanxian_h1_plan.ROOT / relative).read_text(
                encoding="utf-8"
            ).splitlines()[0]
            self.assertIn("「断线」", heading)

    def test_stale_homophone_title_is_rejected_by_source_gate(self) -> None:
        metadata = json.loads(
            duanxian_h1_plan.PROJECT_DISPLAY_METADATA.read_text(encoding="utf-8")
        )
        metadata["work_title"] = "断弦"
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "project-display-metadata.json"
            candidate.write_text(
                json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
            )
            with mock.patch.object(
                duanxian_h1_plan, "PROJECT_DISPLAY_METADATA", candidate
            ):
                with self.assertRaisesRegex(RuntimeError, "project title source drift"):
                    duanxian_h1_plan._authoritative_work_title()


if __name__ == "__main__":
    unittest.main()
