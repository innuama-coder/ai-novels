#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from render_validation import validate_package


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a sealed HH1-C render package")
    parser.add_argument("package_directory", type=Path)
    args = parser.parse_args()
    errors = validate_package(args.package_directory.resolve())
    if errors:
        for error in errors:
            print(error)
        return 2
    print("HH1-C render package is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
