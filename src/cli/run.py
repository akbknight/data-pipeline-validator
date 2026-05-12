"""
src/cli/run.py
==============
Command-line entry point for the data pipeline validator.

Usage
-----
    # From project root:
    python -m src.cli.run

    # Or via the root shim (backwards-compatible):
    python validate.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a module
_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.pipeline.runner import run_pipeline


def main() -> None:
    """Entry point: parse minimal CLI args and launch the pipeline."""
    # Future: argparse for --config, --output, --sources flags
    run_pipeline()


if __name__ == "__main__":
    main()
