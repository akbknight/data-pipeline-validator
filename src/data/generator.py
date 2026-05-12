"""
src/data/generator.py
=====================
Synthetic financial transaction data generator.

Synthetic Data Model
--------------------
This module simulates realistic financial transaction data from 50 named
enterprise-style data sources (core banking, AML, wire transfers, etc.).

Amount distribution:
    Transaction amounts follow a log-normal distribution with mean=8.5 and
    sigma=2.5 (parameterized in log-space). This models the multiplicative
    growth process inherent in financial transactions — most transactions are
    small, but a heavy right tail captures occasional large-value transfers.
    Mean transaction amount is approximately exp(8.5) ≈ $4,915; the long
    tail extends into millions.

Tiered quality model:
    Each source is assigned a random quality tier at generation time:
      - Top 20% of sources (tier > 0.8): poor quality, issue_rate 15–35%
        (simulates a legacy or poorly-maintained upstream feed)
      - Middle 30% of sources (0.5 < tier ≤ 0.8): moderate quality,
        issue_rate 5–14% (common in partially-migrated systems)
      - Bottom 50% of sources (tier ≤ 0.5): high quality, issue_rate 1–4%
        (modern, well-governed sources)

Issue injection:
    Seven failure modes are injected at random into issue-rate-determined
    record counts:
      1. null_amount          — missing transaction value (NaN)
      2. future_date          — transaction_date set 400–730 days in future
      3. negative_amount      — sign-flipped (absolute) amount
      4. invalid_status       — status set to undocumented value
      5. missing_account      — account_id set to NaN
      6. duplicate_id         — record_id copied from row 0
      7. out_of_range_amount  — amount set to $0, $999,999,999, or −$1
"""

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Source catalogue — 50 enterprise-style financial data source names
# ---------------------------------------------------------------------------

SOURCE_NAMES = [
    "CoreBanking_API", "CRM_Export", "LoanServicing_DB", "CardTrans_Stream",
    "AML_Feed", "FraudAlert_API", "CreditBureau_Pull", "ACH_Processor",
    "WireTransfer_Log", "Compliance_Registry", "Collections_API",
    "CustomerPortal_Events", "ThirdPartyRisk_Feed", "RegulatoryReport_DB",
    "BranchOps_Export", "MortgageServicing", "AutoLoan_API", "StudentLoan_DB",
    "InvestmentAccts_Feed", "TrustDept_Export", "InsuranceLinks_API",
    "PayrollDeposit_Stream", "CheckProcessing_Log", "SafeDeposit_DB",
    "MerchantProcessing_API", "ForexDesk_Feed", "TreasuryOps_Export",
    "RiskMgmt_DB", "CybersecEvents_Stream", "OperationalLoss_API",
    "VendorPayments_Export", "EmployeeExpense_DB", "FacilitiesOps_API",
    "MarketData_Feed", "PortfolioRisk_DB", "HedgingOps_Export",
    "TradingDesk_Stream", "SettlementOps_API", "CustodyServices_DB",
    "PrimeServices_Export", "CorpAction_Feed", "DividendProcessing_API",
    "TaxReporting_DB", "KYC_Repository", "SAR_Database",
    "LitigationMgmt_DB", "InsiderTrading_Monitor", "BsaCsa_Export",
    "ExchangeReporting_API", "ClearingHouse_Feed",
]


def generate_source_data(source_name: str, n_records: int) -> pd.DataFrame:
    """Generate a synthetic financial transaction DataFrame for one source.

    Parameters
    ----------
    source_name : str
        Identifier for the upstream data source (e.g. "CoreBanking_API").
        Used to populate the ``source_code`` column and prefix ``record_id``
        values.
    n_records : int
        Number of transaction rows to generate before issue injection.

    Returns
    -------
    pd.DataFrame
        Columns: record_id, account_id, transaction_date, amount, status,
        source_code, currency.  Some rows will contain injected quality
        issues according to the tiered quality model described in the module
        docstring.
    """
    base_date = datetime(2024, 1, 1)
    dates = [base_date + timedelta(days=random.randint(0, 364)) for _ in range(n_records)]

    # Tiered quality model — determines fraction of rows that receive issues
    tier = random.random()
    if tier > 0.8:
        issue_rate = random.uniform(0.15, 0.35)   # poor-quality source
    elif tier > 0.5:
        issue_rate = random.uniform(0.05, 0.14)   # moderate-quality source
    else:
        issue_rate = random.uniform(0.01, 0.04)   # high-quality source

    account_ids = [f"ACC{random.randint(100000, 999999)}" for _ in range(n_records)]

    # Log-normal amount distribution — mean=8.5, sigma=2.5 in log-space
    amounts = np.random.lognormal(mean=8.5, sigma=2.5, size=n_records).round(2)

    statuses = np.random.choice(
        ["COMPLETED", "PENDING", "FAILED", "REVERSED"],
        size=n_records,
        p=[0.82, 0.10, 0.05, 0.03],
    )
    source_codes = [source_name[:6].upper()] * n_records

    df = pd.DataFrame({
        "record_id": [f"{source_name[:4]}_{i:06d}" for i in range(n_records)],
        "account_id": account_ids,
        "transaction_date": dates,
        "amount": amounts,
        "status": statuses,
        "source_code": source_codes,
        "currency": np.random.choice(
            ["USD", "EUR", "GBP", "JPY", "CAD"],
            size=n_records,
            p=[0.88, 0.05, 0.03, 0.02, 0.02],
        ),
    })

    # ── Issue injection ───────────────────────────────────────────────────
    n_issues = int(n_records * issue_rate)
    issue_indices = random.sample(range(n_records), min(n_issues, n_records))

    issue_types = [
        "null_amount",
        "future_date",
        "negative_amount",
        "invalid_status",
        "missing_account",
        "duplicate_id",
        "out_of_range_amount",
    ]

    for idx in issue_indices:
        issue = random.choice(issue_types)
        if issue == "null_amount":
            df.at[idx, "amount"] = np.nan
        elif issue == "future_date":
            df.at[idx, "transaction_date"] = base_date + timedelta(days=random.randint(400, 730))
        elif issue == "negative_amount":
            df.at[idx, "amount"] = -abs(df.at[idx, "amount"])
        elif issue == "invalid_status":
            df.at[idx, "status"] = random.choice(["UNKNOWN", "ERROR", "NULL", "???"])
        elif issue == "missing_account":
            df.at[idx, "account_id"] = np.nan
        elif issue == "duplicate_id":
            if idx > 0:
                df.at[idx, "record_id"] = df.at[0, "record_id"]
        elif issue == "out_of_range_amount":
            df.at[idx, "amount"] = random.choice([0.0, 999_999_999.0, -1.0])

    return df
