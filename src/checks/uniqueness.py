"""
src/checks/uniqueness.py
=========================
Uniqueness checks: detect duplicate primary key values within a source.

Uniqueness is an ISO 8000 data quality dimension that ensures each entity
is represented exactly once.  For transaction records, the ``record_id``
field is the natural primary key — duplicates indicate:

  - ETL retry loops that did not deduplicate on re-ingestion
  - Parallel extraction jobs writing the same records
  - Source system bugs that generated repeated IDs

In production, uniqueness is enforced via a database PRIMARY KEY constraint,
but pipeline validation catches duplicates before they reach the database,
enabling rejection at the ingestion boundary rather than downstream.

This check uses pandas ``Series.duplicated()`` with ``keep='first'``,
marking the second and subsequent occurrences as failed.  The total failed
count equals the number of surplus duplicate rows.
"""

import pandas as pd


def check_unique_record_ids(df: pd.DataFrame, config: dict | None = None) -> dict:
    """Check that all ``record_id`` values are unique within the source.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame with at least a ``record_id`` column.
    config : dict, optional
        Rules config dict.  Reads
        ``config["rules"]["record_ids"]["require_unique"]`` (default True).
        When False, the check is skipped and every row passes.

    Returns
    -------
    dict
        Check result dict.
    """
    n = len(df)
    require_unique = True
    if config:
        require_unique = config.get("rules", {}).get("record_ids", {}).get("require_unique", True)

    if not require_unique:
        return {
            "check": "Unique Record ID",
            "category": "Uniqueness",
            "total": n,
            "passed": n,
            "failed": 0,
            "pct_pass": 100.0,
            "severity": "pass",
        }

    failed = int(df["record_id"].duplicated().sum())
    passed = n - failed
    return {
        "check": "Unique Record ID",
        "category": "Uniqueness",
        "total": n,
        "passed": passed,
        "failed": failed,
        "pct_pass": round(passed / n * 100, 1),
        "severity": "high" if failed > 0 else "pass",
    }
