"""
src/pipeline/validator.py
==========================
Per-source validation orchestrator.

Loads configuration from ``configs/validation/rules.yaml`` (resolved
relative to the project root), applies all seven check functions, and
returns a standardised result dict consumed by the runner and the
JSON report.

Health scoring
--------------
Health tier thresholds are read from the config:
  healthy  : overall_pass_pct >= thresholds.health_healthy  (default 99.0)
  warning  : overall_pass_pct >= thresholds.health_warning  (default 97.5)
  critical : overall_pass_pct <  thresholds.health_warning

These thresholds align with typical SLA definitions for financial data
pipelines: 99% clean data is the minimum acceptable for automated
processing; 97.5% triggers an alert; below that triggers incident response.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.checks import ALL_CHECKS

# ---------------------------------------------------------------------------
# Config loading (cached at module level; safe for single-process use)
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "validation" / "rules.yaml"
_config_cache: dict[str, Any] | None = None


def _load_config() -> dict[str, Any]:
    """Load and cache the validation rules YAML config."""
    global _config_cache
    if _config_cache is None:
        if _CONFIG_PATH.exists():
            with open(_CONFIG_PATH, "r", encoding="utf-8") as fh:
                _config_cache = yaml.safe_load(fh)
        else:
            # Fallback to empty config so hardcoded defaults in each check apply
            _config_cache = {}
    return _config_cache


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_source(source_name: str, df: pd.DataFrame) -> dict[str, Any]:
    """Run all validation checks against a single source DataFrame.

    Reads health thresholds and rule parameters from
    ``configs/validation/rules.yaml``.  Applies each function in
    ``src.checks.ALL_CHECKS`` to ``df`` and aggregates results into a
    standardised result dict.

    Parameters
    ----------
    source_name : str
        Human-readable label for this data source (used in the report).
    df : pd.DataFrame
        Fully-loaded source DataFrame.  Must contain columns: record_id,
        account_id, transaction_date, amount, status, source_code, currency.

    Returns
    -------
    dict
        Keys: source, records, checks (list of check result dicts),
        total_issues, overall_pass_pct, health.
    """
    config = _load_config()
    thresholds = config.get("thresholds", {})
    healthy_threshold = float(thresholds.get("health_healthy", 99.0))
    warning_threshold = float(thresholds.get("health_warning", 97.5))

    n = len(df)
    checks = [check_fn(df, config) for check_fn in ALL_CHECKS]

    total_issues = sum(c["failed"] for c in checks)
    n_checks = len(checks)
    overall_pass = round((n * n_checks - total_issues) / (n * n_checks) * 100, 1)

    if overall_pass >= healthy_threshold:
        health = "healthy"
    elif overall_pass >= warning_threshold:
        health = "warning"
    else:
        health = "critical"

    return {
        "source": source_name,
        "records": n,
        "checks": checks,
        "total_issues": total_issues,
        "overall_pass_pct": overall_pass,
        "health": health,
    }
