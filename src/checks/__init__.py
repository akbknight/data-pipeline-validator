"""
src/checks/__init__.py
=======================
Public API for the checks package.

All seven check functions are imported here so callers can do:

    from src.checks import ALL_CHECKS

``ALL_CHECKS`` is an ordered list of callables, each accepting
``(df: pd.DataFrame, config: dict | None)`` and returning a check result
dict.  The validator iterates this list to produce the per-source report.
"""

from .completeness import check_null_amounts, check_null_accounts
from .business_rules import check_no_negative_amounts, check_no_future_dates
from .referential_integrity import check_valid_status_codes
from .uniqueness import check_unique_record_ids
from .range_validation import check_amount_range

__all__ = [
    "check_null_amounts",
    "check_null_accounts",
    "check_no_negative_amounts",
    "check_no_future_dates",
    "check_valid_status_codes",
    "check_unique_record_ids",
    "check_amount_range",
    "ALL_CHECKS",
]

# Ordered list of all check functions.  The validator iterates this list.
# Each function signature: (df: pd.DataFrame, config: dict | None) -> dict
ALL_CHECKS = [
    check_null_amounts,
    check_null_accounts,
    check_no_negative_amounts,
    check_no_future_dates,
    check_valid_status_codes,
    check_unique_record_ids,
    check_amount_range,
]
