"""
Data Pipeline Validator — root compatibility shim
==================================================
This file is kept at the project root so that existing invocations of
``python validate.py`` continue to work without modification.

The actual implementation now lives in the ``src/`` package:
  src/data/generator.py       — synthetic data generation
  src/checks/                 — 7 validation check modules
  src/pipeline/validator.py   — per-source validation orchestrator
  src/pipeline/runner.py      — full pipeline loop and JSON output
  src/cli/run.py              — primary entry point

Configuration is read from configs/validation/rules.yaml.

Usage:
    python validate.py          # backwards-compatible (same as before)
    python -m src.cli.run       # preferred entry point

No external dependencies beyond pandas, numpy, and pyyaml.
"""

import sys
from pathlib import Path

# Ensure project root is importable as a package root
_root = Path(__file__).parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.pipeline.runner import run_pipeline

if __name__ == "__main__":
    run_pipeline()
