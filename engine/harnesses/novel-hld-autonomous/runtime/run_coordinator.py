#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
if str(REPO) not in sys.path:sys.path.insert(0,str(REPO))
from runtime.coordinator import _main
if __name__=="__main__":raise SystemExit(_main())
