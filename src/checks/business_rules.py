"""
src/checks/business_rules.py
=============================
Business rule checks: domain-specific invariants for financial transactions.

Business rules enforce the semantic correctness of data values according to
the operational rules of the business domain.  For financial transaction
pipelines two invariants are universal:

1. Non-negative amounts — legitimate financial debits and credits are
   represented as positive values; a negative amount in this schema indicates
   either a sign error during ingestion or a misclassified reversal that
   should carry status=REVERSED with a positive amount.

2. Historical dates — transaction_date must not be in the future beyond a
   configurable tolerance (default: 1 day to absorb timezone drift).
   Future-dated transactions indicate clock skew on the source system, ETL
   date-format parsing errors, or fabricated records.
"""

from datetime import datetime, timedelta

import pandas as pd


def check_no_negative_amounts(df: pd.DataFrame, config: dict | None = None) -> dict:
    """Check that no transaction amounts are negative.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame with at least an ``amount`` column.
    config : dict, optional
        Rules config dict.  If provided, reads
        ``config["rules"]["amounts"]["allow_negative"]`` (default False).
        Pass ``None`` to use hardcoded defaults.

    Returns
    -------
    dict
        Check result dict.
    """
    n = len(df)
    allow_negative = False
    if config:
        allow_negative = config.get("rules", {}).get("amounts", {}).get("allow_negative", False)

    if allow_negative:
        # If the config explicitly allows negatives, every row passes
        return {
            "check": "No Negative Amount",
            "category": "Business Rule",
            "total": n,
            "passed": n,
            "failed": 0,
            "pct_pass": 100.0,
            "severity": "pass",
        }

    failed = int((df["amount"] < 0).sum())
    passed = n - failed
    return {
        "check": "No Negative Amount",
        "category": "Business Rule",
        "total": n,
        "passed": passed,
        "failed": failed,
        "pct_pass": round(passed / n * 100, 1),
        "severity": "high" if failed > 0 else "pass",
    }


def check_no_future_dates(df: pd.DataFrame, config: dict | None = None) -> dict:
    """Check that transaction_date values are not in the future.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame with at least a ``transaction_date`` column.
    config : dict, optional
        Rules config dict.  Reads
        ``config["rules"]["dates"]["future_tolerance_days"]`` (default 1).

    Returns
    -------
    dict
        Check result dict.
    """
    n = len(df)
    tolerance_days = 1
    if config:
        tolerance_days = config.get("rules", {}).get("dates", {}).get("future_tolerance_days", 1)

    max_date = datetime.now() + timedelta(days=tolerance_days)
    failed = int((df["transaction_date"] > max_date).sum())
    passed = n - failed
    return {
        "check": "No Future Dates",
        "category": "Business Rule",
        "total": n,
        "passed": passed,
        "failed": failed,
        "pct_pass": round(passed / n * 100, 1),
        "severity": "medium" if failed > 0 else "pass",
    }
