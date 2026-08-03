"""PyInstaller entry point for Audio Track Studio."""

import os
import sys
from pathlib import Path

from desktop.launcher import run, run_smoke_test

if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        report = os.getenv("ATS_SMOKE_REPORT", "").strip()
        raise SystemExit(run_smoke_test(Path(report) if report else None))
    raise SystemExit(run())
