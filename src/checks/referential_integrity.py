"""
src/checks/referential_integrity.py
=====================================
Referential integrity checks: validate values against known reference sets.

Referential integrity verifies that coded values in a dataset belong to an
authorised enumeration.  In relational databases this is enforced via foreign
key constraints; in pipeline validation it must be checked explicitly because
upstream sources are not bound by the downstream schema.

Status code lifecycle:
    COMPLETED → terminal state; funds settled.
    PENDING   → in-flight; awaiting clearing.
    FAILED    → terminal state; transaction rejected.
    REVERSED  → terminal state; funds returned.

Any value outside this set (e.g. "UNKNOWN", "ERROR", "NULL") indicates the
upstream system introduced a new status that the downstream schema does not
recognise, or that a serialisation error corrupted the field.

Currency codes:
    ISO 4217 subset in scope: USD, EUR, GBP, JPY, CAD, AUD, CHF.
    Values outside this set may indicate a data-entry error or an
    unsupported currency that needs manual review.
"""

import pandas as pd

# Default reference sets (overridden by config when provided)
_DEFAULT_VALID_STATUSES = {"COMPLETED", "PENDING", "FAILED", "REVERSED"}
_DEFAULT_VALID_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"}


def check_valid_status_codes(df: pd.DataFrame, config: dict | None = None) -> dict:
    """Check that all ``status`` values belong to the authorised enumeration.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame with at least a ``status`` column.
    config : dict, optional
        Rules config dict.  Reads
        ``config["rules"]["status_codes"]["valid_values"]``.

    Returns
    -------
    dict
        Check result dict.
    """
    n = len(df)
    if config:
        valid = set(config.get("rules", {}).get("status_codes", {}).get("valid_values", list(_DEFAULT_VALID_STATUSES)))
    else:
        valid = _DEFAULT_VALID_STATUSES

    failed = int((~df["status"].isin(valid)).sum())
    passed = n - failed
    return {
        "check": "Valid Status Code",
        "category": "Referential Integrity",
        "total": n,
        "passed": passed,
        "failed": failed,
        "pct_pass": round(passed / n * 100, 1),
        "severity": "medium" if failed > 0 else "pass",
    }
