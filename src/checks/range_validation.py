"""
src/checks/range_validation.py
================================
Range validation checks: verify numeric fields fall within expected bounds.

Range validation (also called domain validation) tests whether numeric
values are plausible given the business context.  For financial transaction
amounts, the expected range is derived from the log-normal distribution
used in the synthetic data model:

  Lower bound: amount > 0  (zero-value transactions are operationally
    meaningless and typically indicate a failed amount extraction)
  Upper bound: amount <= 10,000,000 (US$10M per single transaction;
    any amount above this would be a multi-million-dollar wire that requires
    separate escalation and is unlikely to arrive via automated feed)

In production systems, the upper bound would be calibrated to the 99.9th
percentile of observed transaction amounts per source over a rolling 90-day
window to avoid false positives on legitimate large-value transactions.

The zero lower bound also acts as an implicit business rule check — a
$0 transaction is not a meaningful financial event and almost always
indicates a data extraction error.
"""

import pandas as pd


def check_amount_range(df: pd.DataFrame, config: dict | None = None) -> dict:
    """Check that ``amount`` values fall within the configured valid range.

    Failed records are those where the amount is exactly zero or exceeds
    the configured maximum value.  Negative amounts are handled separately
    by the business_rules.check_no_negative_amounts check.

    Parameters
    ----------
    df : pd.DataFrame
        Source DataFrame with at least an ``amount`` column.
    config : dict, optional
        Rules config dict.  Reads:
          ``config["rules"]["amounts"]["max_value"]`` (default 10_000_000.0)
          ``config["rules"]["amounts"]["allow_zero"]`` (default False)

    Returns
    -------
    dict
        Check result dict.
    """
    n = len(df)
    max_value = 10_000_000.0
    allow_zero = False

    if config:
        amounts_cfg = config.get("rules", {}).get("amounts", {})
        max_value = amounts_cfg.get("max_value", max_value)
        allow_zero = amounts_cfg.get("allow_zero", allow_zero)

    if allow_zero:
        failed = int((df["amount"] > max_value).sum())
    else:
        failed = int(((df["amount"] > max_value) | (df["amount"] == 0)).sum())

    passed = n - failed
    return {
        "check": "Amount Range Check",
        "category": "Range Validation",
        "total": n,
        "passed": passed,
        "failed": failed,
        "pct_pass": round(passed / n * 100, 1),
        "severity": "low" if failed > 0 else "pass",
    }
