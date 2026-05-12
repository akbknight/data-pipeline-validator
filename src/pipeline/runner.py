"""
src/pipeline/runner.py
=======================
Full-pipeline orchestrator.

Reads simulation parameters from the config, generates synthetic data for
each source, delegates per-source validation to ``validate_source``,
aggregates statistics, and writes the JSON report consumed by the dashboard.
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from src.data.generator import generate_source_data, SOURCE_NAMES
from src.pipeline.validator import validate_source

# Project root is three levels up from this file
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "configs" / "validation" / "rules.yaml"


def _load_config() -> dict[str, Any]:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    return {}


def run_pipeline() -> None:
    """Execute the full validation pipeline and write the JSON report.

    Reads simulation parameters (n_sources, record counts, seed) from
    ``configs/validation/rules.yaml``.  For each source: generates synthetic
    data, validates it, and collects results.  Writes the aggregated report
    to the configured output path (default: ``validation_report.json``).
    """
    config = _load_config()
    sim = config.get("simulation", {})
    output_path = _PROJECT_ROOT / config.get("output", {}).get("path", "validation_report.json")

    n_sources = int(sim.get("n_sources", 15))
    min_records = int(sim.get("min_records_per_source", 400))
    max_records = int(sim.get("max_records_per_source", 1200))
    seed = int(sim.get("seed", 42))

    random.seed(seed)

    demo_sources = SOURCE_NAMES[:n_sources]
    records_per_source = [random.randint(min_records, max_records) for _ in demo_sources]

    print("Data Pipeline Validator")
    print("=" * 24)
    print(f"Processing {len(demo_sources)} sources ({sum(records_per_source):,} total records)...")

    all_results: list[dict[str, Any]] = []
    total_records = 0
    start = time.time()

    for i, (source, n_records) in enumerate(zip(demo_sources, records_per_source), 1):
        df = generate_source_data(source, n_records)
        result = validate_source(source, df)
        all_results.append(result)
        total_records += n_records

        h = result["health"]
        icon = "OK" if h == "healthy" else "!!" if h == "warning" else "XX"
        print(
            f"  [{i:02d}] {source:<30} {icon} {h:8s} "
            f"{result['overall_pass_pct']:5.1f}% ({result['total_issues']} issues)"
        )

    elapsed = round(time.time() - start, 2)

    # ── Aggregate statistics ──────────────────────────────────────────────
    total_issues = sum(r["total_issues"] for r in all_results)
    healthy = sum(1 for r in all_results if r["health"] == "healthy")
    warning = sum(1 for r in all_results if r["health"] == "warning")
    critical = sum(1 for r in all_results if r["health"] == "critical")

    category_issues: dict[str, int] = {}
    for r in all_results:
        for c in r["checks"]:
            cat = c["category"]
            category_issues[cat] = category_issues.get(cat, 0) + c["failed"]

    n_checks = len(all_results[0]["checks"]) if all_results else 7

    output: dict[str, Any] = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "elapsed_seconds": elapsed,
        "summary": {
            "total_sources": len(demo_sources),
            "total_records": total_records,
            "total_issues": total_issues,
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "overall_pass_pct": round(
                (total_records * n_checks - total_issues) / (total_records * n_checks) * 100, 2
            ),
        },
        "category_breakdown": [
            {"category": k, "issues": v}
            for k, v in sorted(category_issues.items(), key=lambda x: -x[1])
        ],
        "sources": all_results,
    }

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, default=str)

    print(
        f"\nSummary: {total_records:,} records · {total_issues} issues · "
        f"{healthy} healthy / {warning} warning / {critical} critical"
    )
    print(f"Completed in {elapsed}s · Saved: {output_path}")
