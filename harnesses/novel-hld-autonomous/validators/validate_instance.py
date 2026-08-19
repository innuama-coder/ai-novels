#!/usr/bin/env python3
"""Validate one JSON artifact against the portable schema catalog."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.canonical import read_json  # noqa: E402
from runtime.schema_catalog import SchemaCatalog  # noqa: E402


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schema")
    parser.add_argument("instance", type=Path)
    args = parser.parse_args()
    try:
        catalog = SchemaCatalog(ROOT / "schemas")
        catalog.validate(read_json(args.instance.resolve(strict=True)), args.schema)
    except Exception as error:
        print(json.dumps({"status": "fail", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "pass", "schema": args.schema, "instance": str(args.instance)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
