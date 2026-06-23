#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
POC_DIR = PROJECT_ROOT / "python-poc"
if str(POC_DIR) not in sys.path:
    sys.path.insert(0, str(POC_DIR))

from runner import main as run_poc


def main() -> None:
    run_poc(sys.argv[1:])


if __name__ == "__main__":
    main()
