"""
src/checks/completeness.py
===========================
Completeness checks: detect missing (null) values in critical fields.

Completeness is the ISO 8000 data quality dimension that measures whether
required data is present.  For financial transaction records, both the
transaction amount and the account identifier are mandatory — a record
missing either field cannot be processed downstream and must be flagged.

Acceptable threshold: null rate < 1% per source (industry standard for
financial data pipelines).  Any null counts above zero trigger severity
"high" because missing values propagate into aggregation errors.
"""

import pandas as pd


def check_null_amounts(df: pd.DataFrame, config: dict | None = None) -> dict:
    """Check for missing (NaN) values in the ``amount`` column.

    A null amount means the transaction value is unknown and the record
    cannot participate in financial aggregations, reconciliation, or
    regulatory reporting.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame with at least an ``amount`` column.

    Returns
    -------
    dict
        Check result with keys: check, category, total, passed, failed,
        pct_pass, severity.
    """
    n = len(df)
    failed = int(df["amount"].isna().sum())
    passed = n - failed
    return {
        "check": "Null Amount Check",
        "category": "Completeness",
        "total": n,
        "passed": passed,
        "failed": failed,
        "pct_pass": round(passed / n * 100, 1),
        "severity": "high" if failed > 0 else "pass",
    }


def check_null_accounts(df: pd.DataFrame, config: dict | None = None) -> dict:
    """Check for missing (NaN) values in the ``account_id`` column.

    A null account ID creates orphaned transaction records that cannot be
    attributed to a customer.  This typically indicates an ETL join failure
    or a data truncation event in the upstream source system.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame with at least an ``account_id`` column.

    Returns
    -------
    dict
        Check result with keys: check, category, total, passed, failed,
        pct_pass, severity.
    """
    n = len(df)
    failed = int(df["account_id"].isna().sum())
    passed = n - failed
    return {
        "check": "Null Account ID Check",
        "category": "Completeness",
        "total": n,
        "passed": passed,
        "failed": failed,
        "pct_pass": round(passed / n * 100, 1),
        "severity": "high" if failed > 0 else "pass",
    }
