"""
tests/test_validator.py
========================
Integration tests for ``validate_source()``.

These tests exercise the full validation orchestration path: check functions
are invoked via ``ALL_CHECKS``, results are aggregated, and a health
classification is produced.  A clean DataFrame — no nulls, valid statuses,
unique IDs, in-range amounts, historical dates — should always produce
health="healthy".
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from src.pipeline.validator import validate_source


def _clean_df(n: int = 100) -> pd.DataFrame:
    """Return a fully clean synthetic DataFrame with no injected issues."""
    today = datetime.now()
    return pd.DataFrame({
        "record_id": [f"TEST_{i:06d}" for i in range(n)],
        "account_id": [f"ACC{100000 + i}" for i in range(n)],
        "transaction_date": [today - timedelta(days=(i % 30) + 1) for i in range(n)],
        "amount": [float(100 + i * 10) for i in range(n)],   # all positive, in-range
        "status": ["COMPLETED"] * (n // 2) + ["PENDING"] * (n - n // 2),
        "source_code": ["TEST01"] * n,
        "currency": ["USD"] * n,
    })


class TestValidateSourceCleanData:
    """validate_source() with a perfectly clean DataFrame."""

    def test_health_is_healthy(self):
        """A clean DataFrame should receive health=healthy."""
        df = _clean_df(100)
        result = validate_source("TEST_SOURCE", df)
        assert result["health"] == "healthy"

    def test_total_issues_is_zero(self):
        """A clean DataFrame should produce zero total issues."""
        df = _clean_df(100)
        result = validate_source("TEST_SOURCE", df)
        assert result["total_issues"] == 0

    def test_overall_pass_pct_is_100(self):
        """A clean DataFrame should score 100.0% overall pass."""
        df = _clean_df(100)
        result = validate_source("TEST_SOURCE", df)
        assert result["overall_pass_pct"] == 100.0

    def test_result_has_required_keys(self):
        """Result dict must contain all expected keys."""
        df = _clean_df(50)
        result = validate_source("TEST_SOURCE", df)
        for key in ("source", "records", "checks", "total_issues", "overall_pass_pct", "health"):
            assert key in result, f"Missing key: {key}"

    def test_seven_checks_returned(self):
        """Result must contain exactly 7 check results."""
        df = _clean_df(50)
        result = validate_source("TEST_SOURCE", df)
        assert len(result["checks"]) == 7

    def test_source_name_preserved(self):
        """Source name must pass through to the result."""
        df = _clean_df(10)
        result = validate_source("MY_FEED", df)
        assert result["source"] == "MY_FEED"

    def test_record_count_preserved(self):
        """Record count must match the DataFrame length."""
        df = _clean_df(75)
        result = validate_source("TEST_SOURCE", df)
        assert result["records"] == 75


class TestValidateSourceWithIssues:
    """validate_source() correctly downgrades health when issues exist."""

    def test_null_amounts_increase_issue_count(self):
        """Introducing null amounts should raise total_issues."""
        df = _clean_df(100)
        df.loc[0:4, "amount"] = np.nan   # 5 null amounts
        result = validate_source("TEST_SOURCE", df)
        assert result["total_issues"] >= 5

    def test_critical_health_on_many_issues(self):
        """Heavy issue injection should produce health=critical."""
        df = _clean_df(100)
        # Inject issues across many rows to force overall pass < 97.5%
        df.loc[:30, "amount"] = np.nan          # 31 null amounts
        df.loc[31:60, "account_id"] = np.nan    # 30 null accounts
        df.loc[61:80, "status"] = "INVALID"     # 20 bad statuses
        result = validate_source("BAD_SOURCE", df)
        assert result["health"] == "critical"

    def test_check_categories_present(self):
        """All expected categories appear in checks list."""
        df = _clean_df(50)
        result = validate_source("TEST_SOURCE", df)
        categories = {c["category"] for c in result["checks"]}
        expected = {
            "Completeness", "Business Rule",
            "Referential Integrity", "Uniqueness", "Range Validation",
        }
        assert expected.issubset(categories)
