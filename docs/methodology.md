# Validation Methodology

## Overview

This framework implements a seven-check validation suite designed around the ISO 8000 / DAMA data quality dimensions most relevant to financial transaction pipelines. Each check category maps to a well-defined data quality concern with documented enterprise precedent.

---

## 1. Validation Framework Design

### ISO 8000 Data Quality Dimensions Applied

| Dimension | ISO 8000 Term | This Framework |
|---|---|---|
| Completeness | Completeness | Null Amount Check, Null Account ID Check |
| Accuracy | Accuracy | No Negative Amount, Amount Range Check |
| Consistency | Consistency | Valid Status Code, No Future Dates |
| Timeliness | Timeliness | No Future Dates |
| Uniqueness | Uniqueness | Unique Record ID |
| Validity | Validity | Valid Status Code, Amount Range Check |

The seven checks cover the failure modes that appear most frequently in enterprise financial data pipelines according to practitioner surveys (Redman 2016; DAMA International 2017). Additional checks (cross-source referential integrity, statistical distribution drift, format regex validation) exist but were excluded from this demo to avoid over-engineering — see `docs/decision_log.md` for rationale.

---

## 2. Completeness Checks

**Metric:** Null rate (count of null values / total records).

**Acceptable threshold:** < 1% null rate per source, per field. The 1% threshold is an industry convention for financial pipeline SLAs — above 1% null rates typically trigger data quality incidents because missing values propagate into aggregation errors, reconciliation failures, and regulatory reporting gaps.

### Null Amount Check

A missing `amount` field means the transaction's monetary value is unknown. Such records cannot participate in:
- Balance sheet aggregation
- Regulatory capital calculations
- AML transaction monitoring (amount is a primary feature in AML models)

Any non-zero null count receives `severity: high`.

### Null Account ID Check

A missing `account_id` creates an orphaned transaction — a financial movement with no attributed customer. This typically indicates:
- An ETL join failure between the transaction table and the account master
- Data truncation in the source system export
- A new account type not yet registered in the account master

Any non-zero null count receives `severity: high`.

---

## 3. Business Rule Checks

Business rules encode domain-specific invariants — constraints that the business logic requires to be true, independent of the data schema.

### No Negative Amounts

**Rule:** `amount >= 0` for all records.

In this data model, financial transactions use positive amounts exclusively. Reversals are represented as separate records with `status = REVERSED` and a positive amount, not as negative values. A negative amount therefore indicates:
- A sign error during ETL (e.g., credit/debit indicator applied twice)
- A misclassified reversal that bypassed the status normalisation step
- Corruption in the source system export

Severity: `high` — negative amounts produce incorrect aggregated balances.

### No Future Dates

**Rule:** `transaction_date <= (now + tolerance_days)`.

A future-dated transaction cannot have occurred yet. Future dates indicate:
- Clock skew on the source system (source server time is ahead of UTC)
- ETL date-format parsing error (e.g., YYYYDDMM parsed as YYYYMMDD)
- Fabricated or test records that leaked into the production feed

A one-day tolerance (`future_tolerance_days: 1` in config) absorbs legitimate timezone differences and end-of-day batch timestamp rounding.

Severity: `medium` — future dates are usually data errors, not fraud, but require investigation before the record can be used in time-series analytics.

---

## 4. Referential Integrity

Referential integrity verifies that coded field values belong to an authorised enumeration. In a relational database this is enforced via foreign key constraints; in a pipeline validator it must be checked explicitly because upstream sources operate independently of the downstream schema.

### Valid Status Code Check

Authorised lifecycle states: `COMPLETED`, `PENDING`, `FAILED`, `REVERSED`.

Any value outside this set (e.g., `UNKNOWN`, `ERROR`, `NULL`, `???`) indicates:
- The upstream system introduced a new status value that the downstream schema does not recognise (undocumented API change)
- A serialisation error corrupted the enum value
- A test or debug record that was not filtered before export

In production, this check would trigger an automatic schema change review request and a temporary quarantine of affected records.

Severity: `medium` — invalid statuses prevent downstream state-machine processing but do not corrupt financial aggregations.

---

## 5. Uniqueness

### Unique Record ID Check

The `record_id` field is the natural primary key for transaction records. Duplicates within a source batch indicate:
- ETL retry loops that did not deduplicate on re-ingestion (idempotency failure)
- Parallel extraction jobs writing to the same output partition
- Source system bugs generating repeated IDs in sequential exports

In production, uniqueness is enforced at the database layer via `PRIMARY KEY` constraints. Pipeline validation catches duplicates before they reach the database, enabling rejection at the ingestion boundary.

**Detection method:** `pandas.Series.duplicated(keep='first')` — the first occurrence is treated as the canonical record; all subsequent occurrences are marked as failed.

Severity: `high` — duplicates cause double-counting in aggregations, inflated transaction counts in regulatory reports, and potential double-payment scenarios.

---

## 6. Range Validation

### Amount Range Check

**Rule:** `0 < amount <= max_value` (default max: $10,000,000 USD).

**Lower bound derivation:** Zero-value transactions are operationally meaningless. A $0 amount almost always indicates a failed amount extraction where the field defaulted to zero rather than null. Using 0 as a sentinel value (instead of null) is a common anti-pattern in legacy financial systems.

**Upper bound derivation:** The upper bound of $10M per transaction is derived from the expected distribution of transaction amounts in the covered source categories (core banking, ACH, wire transfers). The log-normal distribution used in data generation (mean=8.5, sigma=2.5 in log-space) has a 99.9th percentile of approximately $5.8M. The $10M cap adds headroom for legitimate large-value transactions while flagging implausibly large values for human review.

In production, the upper bound would be calibrated dynamically to the 99.9th percentile of observed amounts per source over a rolling 90-day window.

Severity: `low` — out-of-range amounts require review but may be legitimate; they do not necessarily invalidate the record.

---

## 7. Health Scoring

### Three-Tier Classification

Health classification uses the **overall pass percentage** across all checks and all records for a source:

```
overall_pass_pct = (total_records * n_checks - total_issues) / (total_records * n_checks) * 100
```

| Tier | Threshold | Action |
|---|---|---|
| healthy | >= 99.0% | Automated processing proceeds without intervention |
| warning | >= 97.5% | Alert raised; data team reviews before end-of-day batch |
| critical | < 97.5% | Pipeline processing halted; incident response triggered |

**Rationale for 99.0% healthy threshold:**

99% data completeness/validity is a common SLA floor for financial data pipelines. Below 99%, downstream systems begin to exhibit measurable reconciliation drift — for example, a 1% null rate in a $1B daily transaction feed leaves $10M unattributed per day.

**Rationale for 97.5% warning threshold:**

The 1.5 percentage-point gap between warning and healthy provides an early-warning window. A source trending from 99% toward 97.5% signals a deteriorating upstream data quality condition before it reaches the severity level that would halt processing.

**Rationale for < 97.5% critical threshold:**

Below 97.5%, the volume of bad records is sufficient to materially corrupt downstream aggregations and regulatory reports. Automated processing should stop; the incident response runbook should be triggered.

---

## 8. Synthetic Data Model

### Why Log-Normal for Transaction Amounts

Financial transaction amounts follow a log-normal distribution because the underlying process is multiplicative rather than additive:
- Retail purchases cluster around small amounts (tens to hundreds of dollars)
- Business payments span orders of magnitude (thousands to millions)
- The log-normal's heavy right tail captures the occasional very large transaction without requiring a different distribution family

The specific parameters (mean=8.5, sigma=2.5 in log-space) produce a distribution with:
- Median: exp(8.5) ≈ $4,915
- Mean: exp(8.5 + 2.5²/2) ≈ $65,659 (pulled right by the heavy tail)
- 99th percentile: approximately $1.8M
- This is consistent with the observed distribution in enterprise banking transaction feeds

### Tiered Quality Model

Three quality tiers simulate the realistic distribution of data quality across enterprise sources:

| Tier | Sources | Issue Rate | Rationale |
|---|---|---|---|
| Poor (top 20%) | Legacy feeds, batch exports | 15–35% | Older systems with no data contracts; manual extraction processes |
| Moderate (middle 30%) | Partially-migrated systems | 5–14% | Systems mid-migration with inconsistent validation |
| High (bottom 50%) | Modern API feeds | 1–4% | Well-governed sources with client-side validation |

This distribution reflects the observation (from practitioner experience and DAMA surveys) that data quality in enterprise environments follows a power-law-like pattern: a majority of sources are well-governed, but a minority of legacy sources produce a disproportionate share of issues.
