# Exploratory Data Analysis

Characterisation of the synthetic dataset produced by the default configuration (`configs/validation/rules.yaml`, seed=42).

---

## Dataset Overview

| Property | Value |
|---|---|
| Sources | 15 (first 15 of 50 named sources) |
| Total records | ~12,000 (exact count varies slightly by seed; typical: 11,800–12,200) |
| Records per source | 400–1,200 (uniform random, seed=42) |
| Date range | 2024-01-01 to 2024-12-31 (plus future-dated outliers) |
| Currencies | USD (88%), EUR (5%), GBP (3%), JPY (2%), CAD (2%) |

---

## Source List (Default 15)

| # | Source | Category |
|---|---|---|
| 1 | CoreBanking_API | Core banking transaction feed |
| 2 | CRM_Export | Customer relationship management batch export |
| 3 | LoanServicing_DB | Loan servicing database extract |
| 4 | CardTrans_Stream | Card transaction real-time stream |
| 5 | AML_Feed | Anti-money laundering monitoring feed |
| 6 | FraudAlert_API | Fraud detection alert stream |
| 7 | CreditBureau_Pull | Credit bureau inquiry log |
| 8 | ACH_Processor | ACH payment processor log |
| 9 | WireTransfer_Log | Wire transfer audit log |
| 10 | Compliance_Registry | Compliance event registry |
| 11 | Collections_API | Collections workflow API |
| 12 | CustomerPortal_Events | Customer portal event log |
| 13 | ThirdPartyRisk_Feed | Third-party risk assessment feed |
| 14 | RegulatoryReport_DB | Regulatory reporting database extract |
| 15 | BranchOps_Export | Branch operations batch export |

---

## Amount Distribution

The `amount` field follows a log-normal distribution with parameters mean=8.5, sigma=2.5 (in log-space):

| Statistic | Value |
|---|---|
| Median | ~$4,915 (= exp(8.5)) |
| Mean | ~$65,659 (log-normal mean = exp(μ + σ²/2)) |
| Mode | ~$340 (log-normal mode = exp(μ - σ²)) |
| 25th percentile | ~$500 |
| 75th percentile | ~$48,000 |
| 99th percentile | ~$1,800,000 |
| Maximum (pre-injection) | Can exceed $10M due to heavy tail |

This heavy right tail is why the range validation upper bound ($10M) catches a non-trivial number of records even in clean sources.

---

## Quality Tier Distribution

With seed=42 and 15 sources, the tiered quality model produces approximately:

| Tier | Sources | Issue Rate Range | Approx. Source Count |
|---|---|---|---|
| High quality (tier <= 0.5) | 7–8 sources | 1–4% | ~50% |
| Moderate quality (0.5 < tier <= 0.8) | 4–5 sources | 5–14% | ~30% |
| Poor quality (tier > 0.8) | 2–3 sources | 15–35% | ~20% |

The tiering is random (bounded by seed), so exact source assignments vary. With seed=42, typically 10 sources are healthy, 3 are warning, and 2 are critical.

---

## Typical Issue Rates by Category

Averaged across all 15 sources under default configuration:

| Check Category | Typical Issue Rate | Notes |
|---|---|---|
| Completeness (amounts) | 2–8% of affected sources | Null amounts concentrated in poor-tier sources |
| Completeness (accounts) | 2–8% of affected sources | Correlated with null amounts (same issue injection) |
| Business Rule (negative) | 2–8% of affected sources | Negative and zero amounts overlap with range failures |
| Business Rule (future date) | 2–8% of affected sources | Only future dates 400+ days out are injected |
| Referential Integrity | 2–8% of affected sources | Invalid status codes from 4 possible bad values |
| Uniqueness | 2–8% of affected sources | Duplicates: row i copies record_id from row 0 |
| Range Validation | 3–10% of affected sources | Catches both zero and >$10M amounts |

The range validation check tends to have slightly higher failure rates because it catches both the `out_of_range_amount` injection ($0, $999M, -$1) and the natural tail of the log-normal distribution that exceeds $10M in high-sigma draws.

---

## Status Distribution

Before issue injection:

| Status | Probability | Description |
|---|---|---|
| COMPLETED | 82% | Transaction fully settled |
| PENDING | 10% | Awaiting clearing |
| FAILED | 5% | Transaction rejected |
| REVERSED | 3% | Funds returned |

After injection, a small fraction of records receive invalid statuses (UNKNOWN, ERROR, NULL, ???), typically 1–4 records per source in poor-quality sources.

---

## Health Distribution (seed=42, n=15 sources)

Typical output:

| Health | Count | Percentage |
|---|---|---|
| healthy | 10 | 67% |
| warning | 3 | 20% |
| critical | 2 | 13% |

This distribution reflects the tiered quality model: the majority of sources are well-governed, producing a realistic enterprise environment where most data is acceptable but a meaningful minority requires attention.
