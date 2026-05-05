"""
Data Pipeline Validator
========================
Automated validation framework for multi-source data pipelines. Simulates
the type of data quality checks used in enterprise aggregation systems —
schema validation, completeness checks, referential integrity, business rule
enforcement, and anomaly flags.

Generates a synthetic multi-source dataset (50 sources, 10K+ records) then
runs a comprehensive validation suite and produces a JSON report consumed by
the dashboard.

Usage:
    python validate.py
    # Outputs: validation_report.json

No external dependencies beyond pandas and numpy.
"""

import json
import random
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

OUTPUT_PATH = "validation_report.json"

# ── Synthetic Data Generation ─────────────────────────────────────────────

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
    "ExchangeReporting_API", "ClearingHouse_Feed"
]

def generate_source_data(source_name: str, n_records: int) -> pd.DataFrame:
    base_date = datetime(2024, 1, 1)
    dates = [base_date + timedelta(days=random.randint(0, 364)) for _ in range(n_records)]

    # Introduce realistic data quality issues — varied quality per source
    tier = random.random()
    if tier > 0.8:
        issue_rate = random.uniform(0.15, 0.35)  # 20% of sources are poor quality
    elif tier > 0.5:
        issue_rate = random.uniform(0.05, 0.14)  # 30% moderate quality
    else:
        issue_rate = random.uniform(0.01, 0.04)  # 50% high quality

    account_ids = [f"ACC{random.randint(100000, 999999)}" for _ in range(n_records)]
    amounts = np.random.lognormal(mean=8.5, sigma=2.5, size=n_records).round(2)
    statuses = np.random.choice(["COMPLETED", "PENDING", "FAILED", "REVERSED"], size=n_records, p=[0.82, 0.10, 0.05, 0.03])
    source_codes = [source_name[:6].upper()] * n_records

    df = pd.DataFrame({
        "record_id": [f"{source_name[:4]}_{i:06d}" for i in range(n_records)],
        "account_id": account_ids,
        "transaction_date": dates,
        "amount": amounts,
        "status": statuses,
        "source_code": source_codes,
        "currency": np.random.choice(["USD", "EUR", "GBP", "JPY", "CAD"], size=n_records, p=[0.88, 0.05, 0.03, 0.02, 0.02]),
    })

    # Inject issues
    n_issues = int(n_records * issue_rate)
    issue_indices = random.sample(range(n_records), min(n_issues, n_records))

    issue_types = ["null_amount", "future_date", "negative_amount", "invalid_status", "missing_account", "duplicate_id", "out_of_range_amount"]
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
            df.at[idx, "amount"] = random.choice([0.0, 999999999.0, -1.0])

    return df


# ── Validation Checks ──────────────────────────────────────────────────────

VALID_STATUSES = {"COMPLETED", "PENDING", "FAILED", "REVERSED"}
VALID_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"}
MAX_DATE = datetime.now() + timedelta(days=1)
MAX_AMOUNT = 10_000_000.0

def validate_source(source_name: str, df: pd.DataFrame) -> dict:
    n = len(df)
    checks = []

    # 1. Completeness: null amounts
    null_amounts = df["amount"].isna().sum()
    checks.append({
        "check": "Null Amount Check",
        "category": "Completeness",
        "total": n,
        "passed": int(n - null_amounts),
        "failed": int(null_amounts),
        "pct_pass": round((n - null_amounts) / n * 100, 1),
        "severity": "high" if null_amounts > 0 else "pass",
    })

    # 2. Completeness: null account IDs
    null_accounts = df["account_id"].isna().sum()
    checks.append({
        "check": "Null Account ID Check",
        "category": "Completeness",
        "total": n,
        "passed": int(n - null_accounts),
        "failed": int(null_accounts),
        "pct_pass": round((n - null_accounts) / n * 100, 1),
        "severity": "high" if null_accounts > 0 else "pass",
    })

    # 3. Business rule: no negative amounts
    neg_amounts = (df["amount"] < 0).sum()
    checks.append({
        "check": "No Negative Amount",
        "category": "Business Rule",
        "total": n,
        "passed": int(n - neg_amounts),
        "failed": int(neg_amounts),
        "pct_pass": round((n - neg_amounts) / n * 100, 1),
        "severity": "high" if neg_amounts > 0 else "pass",
    })

    # 4. Business rule: future dates
    future_dates = (df["transaction_date"] > MAX_DATE).sum()
    checks.append({
        "check": "No Future Dates",
        "category": "Business Rule",
        "total": n,
        "passed": int(n - future_dates),
        "failed": int(future_dates),
        "pct_pass": round((n - future_dates) / n * 100, 1),
        "severity": "medium" if future_dates > 0 else "pass",
    })

    # 5. Referential integrity: valid status codes
    invalid_status = (~df["status"].isin(VALID_STATUSES)).sum()
    checks.append({
        "check": "Valid Status Code",
        "category": "Referential Integrity",
        "total": n,
        "passed": int(n - invalid_status),
        "failed": int(invalid_status),
        "pct_pass": round((n - invalid_status) / n * 100, 1),
        "severity": "medium" if invalid_status > 0 else "pass",
    })

    # 6. Uniqueness: duplicate record IDs
    dupes = df["record_id"].duplicated().sum()
    checks.append({
        "check": "Unique Record ID",
        "category": "Uniqueness",
        "total": n,
        "passed": int(n - dupes),
        "failed": int(dupes),
        "pct_pass": round((n - dupes) / n * 100, 1),
        "severity": "high" if dupes > 0 else "pass",
    })

    # 7. Range check: amount reasonable
    range_fail = ((df["amount"] > MAX_AMOUNT) | (df["amount"] == 0)).sum()
    checks.append({
        "check": "Amount Range Check",
        "category": "Range Validation",
        "total": n,
        "passed": int(n - range_fail),
        "failed": int(range_fail),
        "pct_pass": round((n - range_fail) / n * 100, 1),
        "severity": "low" if range_fail > 0 else "pass",
    })

    total_issues = sum(c["failed"] for c in checks)
    overall_pass = round((n * len(checks) - total_issues) / (n * len(checks)) * 100, 1)
    health = "healthy" if overall_pass >= 99.0 else "warning" if overall_pass >= 97.5 else "critical"

    return {
        "source": source_name,
        "records": n,
        "checks": checks,
        "total_issues": total_issues,
        "overall_pass_pct": overall_pass,
        "health": health,
    }


# ── Pipeline Execution ─────────────────────────────────────────────────────

def main():
    print("Data Pipeline Validator")
    print("=" * 24)
    start = time.time()

    # Sample 15 sources for demo (would be 50+ in production)
    demo_sources = SOURCE_NAMES[:15]
    records_per_source = [random.randint(400, 1200) for _ in demo_sources]

    print(f"Processing {len(demo_sources)} sources ({sum(records_per_source):,} total records)...")

    all_results = []
    total_records = 0

    for i, (source, n_records) in enumerate(zip(demo_sources, records_per_source), 1):
        df = generate_source_data(source, n_records)
        result = validate_source(source, df)
        all_results.append(result)
        total_records += n_records
        h = result["health"]
        icon = "OK" if h == "healthy" else "!!" if h == "warning" else "XX"
        print(f"  [{i:02d}] {source:<30} {icon} {h:8s} {result['overall_pass_pct']:5.1f}% ({result['total_issues']} issues)")

    elapsed = round(time.time() - start, 2)

    # Aggregate stats
    total_issues = sum(r["total_issues"] for r in all_results)
    healthy = sum(1 for r in all_results if r["health"] == "healthy")
    warning = sum(1 for r in all_results if r["health"] == "warning")
    critical = sum(1 for r in all_results if r["health"] == "critical")

    # Category breakdown
    category_issues: dict[str, int] = {}
    for r in all_results:
        for c in r["checks"]:
            cat = c["category"]
            category_issues[cat] = category_issues.get(cat, 0) + c["failed"]

    output = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "elapsed_seconds": elapsed,
        "summary": {
            "total_sources": len(demo_sources),
            "total_records": total_records,
            "total_issues": total_issues,
            "healthy": healthy,
            "warning": warning,
            "critical": critical,
            "overall_pass_pct": round((total_records * 7 - total_issues) / (total_records * 7) * 100, 2),
        },
        "category_breakdown": [{"category": k, "issues": v} for k, v in sorted(category_issues.items(), key=lambda x: -x[1])],
        "sources": all_results,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nSummary: {total_records:,} records · {total_issues} issues · {healthy} healthy / {warning} warning / {critical} critical")
    print(f"Completed in {elapsed}s · Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
