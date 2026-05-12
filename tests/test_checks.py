"""
tests/test_checks.py
====================
Unit tests for all seven validation check functions.

Each test constructs a minimal DataFrame with a known number of "bad" rows,
runs the check function, and asserts on the failed count, passed count, and
pct_pass values.  Config is passed as None so each check falls back to its
hardcoded defaults — this keeps tests isolated from the YAML config file.
"""

import sys
from pathlib import Path

# Ensure project root is importable when running tests from any directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from src.checks.completeness import check_null_amounts, check_null_accounts
from src.checks.business_rules import check_no_negative_amounts, check_no_future_dates
from src.checks.referential_integrity import check_valid_status_codes
from src.checks.uniqueness import check_unique_record_ids
from src.checks.range_validation import check_amount_range


# ---------------------------------------------------------------------------
# Completeness checks
# ---------------------------------------------------------------------------

def test_check_null_amounts_basic():
    """10 rows, 2 null amounts → failed=2, pct_pass=80.0."""
    df = pd.DataFrame({
        "amount": [100.0, np.nan, 200.0, np.nan, 50.0, 75.0, 30.0, 120.0, 60.0, 90.0],
        "account_id": [f"ACC{i}" for i in range(10)],
    })
    result = check_null_amounts(df, config=None)
    assert result["failed"] == 2
    assert result["passed"] == 8
    assert result["pct_pass"] == 80.0
    assert result["severity"] == "high"
    assert result["category"] == "Completeness"


def test_check_null_amounts_all_clean():
    """No null amounts → failed=0, severity=pass."""
    df = pd.DataFrame({"amount": [10.0, 20.0, 30.0], "account_id": ["A", "B", "C"]})
    result = check_null_amounts(df, config=None)
    assert result["failed"] == 0
    assert result["severity"] == "pass"
    assert result["pct_pass"] == 100.0


def test_check_null_accounts_basic():
    """10 rows, 3 null account IDs → failed=3, pct_pass=70.0."""
    account_ids = ["ACC001", None, "ACC002", None, "ACC003", None, "ACC004", "ACC005", "ACC006", "ACC007"]
    df = pd.DataFrame({
        "account_id": account_ids,
        "amount": [float(i) for i in range(10)],
    })
    result = check_null_accounts(df, config=None)
    assert result["failed"] == 3
    assert result["passed"] == 7
    assert result["pct_pass"] == 70.0
    assert result["severity"] == "high"


def test_check_null_accounts_all_clean():
    """No null account IDs → severity=pass."""
    df = pd.DataFrame({"account_id": ["A", "B", "C"], "amount": [1.0, 2.0, 3.0]})
    result = check_null_accounts(df, config=None)
    assert result["failed"] == 0
    assert result["severity"] == "pass"


# ---------------------------------------------------------------------------
# Business rule checks
# ---------------------------------------------------------------------------

def test_check_no_negative_amounts():
    """5-row DataFrame with 1 negative amount → failed=1."""
    df = pd.DataFrame({"amount": [100.0, 200.0, -50.0, 300.0, 400.0]})
    result = check_no_negative_amounts(df, config=None)
    assert result["failed"] == 1
    assert result["passed"] == 4
    assert result["severity"] == "high"
    assert result["category"] == "Business Rule"


def test_check_no_negative_amounts_all_positive():
    """All positive amounts → failed=0, severity=pass."""
    df = pd.DataFrame({"amount": [10.0, 20.0, 30.0, 40.0]})
    result = check_no_negative_amounts(df, config=None)
    assert result["failed"] == 0
    assert result["severity"] == "pass"


def test_check_no_future_dates():
    """5 rows with 2 future dates → failed=2."""
    today = datetime.now()
    df = pd.DataFrame({
        "transaction_date": [
            today - timedelta(days=10),  # past — ok
            today + timedelta(days=400),  # future — fail
            today - timedelta(days=1),   # past — ok
            today + timedelta(days=200),  # future — fail
            today - timedelta(days=5),   # past — ok
        ]
    })
    result = check_no_future_dates(df, config=None)
    assert result["failed"] == 2
    assert result["passed"] == 3
    assert result["severity"] == "medium"


def test_check_no_future_dates_all_past():
    """All historical dates → failed=0."""
    today = datetime.now()
    df = pd.DataFrame({
        "transaction_date": [today - timedelta(days=i) for i in range(1, 6)]
    })
    result = check_no_future_dates(df, config=None)
    assert result["failed"] == 0
    assert result["severity"] == "pass"


# ---------------------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------------------

def test_check_valid_status_codes():
    """4 valid statuses + 1 invalid → failed=1."""
    df = pd.DataFrame({
        "status": ["COMPLETED", "PENDING", "FAILED", "REVERSED", "UNKNOWN"]
    })
    result = check_valid_status_codes(df, config=None)
    assert result["failed"] == 1
    assert result["passed"] == 4
    assert result["severity"] == "medium"
    assert result["category"] == "Referential Integrity"


def test_check_valid_status_codes_all_valid():
    """All valid statuses → failed=0."""
    df = pd.DataFrame({"status": ["COMPLETED", "PENDING", "FAILED", "REVERSED"]})
    result = check_valid_status_codes(df, config=None)
    assert result["failed"] == 0
    assert result["severity"] == "pass"


def test_check_valid_status_codes_uses_config():
    """Config can override the valid set."""
    df = pd.DataFrame({"status": ["COMPLETED", "CUSTOM_STATUS", "PENDING"]})
    config = {"rules": {"status_codes": {"valid_values": ["COMPLETED", "CUSTOM_STATUS", "PENDING"]}}}
    result = check_valid_status_codes(df, config=config)
    assert result["failed"] == 0


# ---------------------------------------------------------------------------
# Uniqueness
# ---------------------------------------------------------------------------

def test_check_unique_record_ids():
    """5 rows with 1 duplicate ID → failed=1."""
    df = pd.DataFrame({
        "record_id": ["REC001", "REC002", "REC001", "REC003", "REC004"]
    })
    result = check_unique_record_ids(df, config=None)
    assert result["failed"] == 1
    assert result["passed"] == 4
    assert result["severity"] == "high"
    assert result["category"] == "Uniqueness"


def test_check_unique_record_ids_all_unique():
    """All unique IDs → failed=0."""
    df = pd.DataFrame({"record_id": ["A", "B", "C", "D"]})
    result = check_unique_record_ids(df, config=None)
    assert result["failed"] == 0
    assert result["severity"] == "pass"


def test_check_unique_record_ids_multiple_dupes():
    """3 rows sharing the same ID → 2 marked as duplicates."""
    df = pd.DataFrame({
        "record_id": ["REC001", "REC001", "REC001", "REC002"]
    })
    result = check_unique_record_ids(df, config=None)
    assert result["failed"] == 2  # first occurrence kept; 2 duplicates


# ---------------------------------------------------------------------------
# Range validation
# ---------------------------------------------------------------------------

def test_check_amount_range_over_max():
    """1 amount exceeding max_value → failed=1."""
    df = pd.DataFrame({"amount": [100.0, 500.0, 10_000_001.0, 200.0, 150.0]})
    result = check_amount_range(df, config=None)
    assert result["failed"] == 1
    assert result["category"] == "Range Validation"


def test_check_amount_range_zero():
    """1 zero-value amount → failed=1 (zero not allowed by default)."""
    df = pd.DataFrame({"amount": [100.0, 0.0, 300.0]})
    result = check_amount_range(df, config=None)
    assert result["failed"] == 1
    assert result["severity"] == "low"


def test_check_amount_range_all_valid():
    """All amounts within range and non-zero → failed=0."""
    df = pd.DataFrame({"amount": [50.0, 1000.0, 9_999_999.0]})
    result = check_amount_range(df, config=None)
    assert result["failed"] == 0
    assert result["severity"] == "pass"


def test_check_amount_range_config_override():
    """Config can set a lower max_value."""
    df = pd.DataFrame({"amount": [100.0, 5001.0, 200.0]})
    config = {"rules": {"amounts": {"max_value": 5000.0, "allow_zero": False}}}
    result = check_amount_range(df, config=config)
    assert result["failed"] == 1
