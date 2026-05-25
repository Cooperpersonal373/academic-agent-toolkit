#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from academic_agent_toolkit.cli import main
except ModuleNotFoundError as exc:
    missing = exc.name or "required dependency"
    raise SystemExit(
        "Missing runtime dependency: "
        f"{missing}. Run `uv run aat --help` from the repo root or install the package first."
    ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
