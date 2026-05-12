# Data Pipeline Validator

Automated validation framework for multi-source financial data pipelines. Simulates the quality control layer of an enterprise data aggregation system — the kind of infrastructure that processes records from dozens of upstream sources and enforces data contracts before downstream consumption.

**Live demo:** [akbknight.github.io/data-pipeline-validator](https://akbknight.github.io/data-pipeline-validator/)

---

## What It Validates

The validator ingests a synthetic multi-source dataset (15 sources, 12,000+ records) and runs 7 validation checks per source:

| Check | Category | Catches |
|---|---|---|
| Null Amount | Completeness | Missing transaction values |
| Null Account ID | Completeness | Orphaned records with no customer attribution |
| No Negative Amount | Business Rule | Sign errors, misclassified reversals |
| No Future Dates | Business Rule | Clock skew, ETL date-format parsing errors |
| Valid Status Code | Referential Integrity | Undocumented status values from upstream API changes |
| Unique Record ID | Uniqueness | Duplicate ingestion from ETL retry loops |
| Amount Range Check | Range Validation | $0 extractions and $10M+ outliers requiring manual review |

Each source receives a health classification based on its overall pass rate:

| Health | Threshold | Action |
|---|---|---|
| healthy | >= 99.0% | Automated processing proceeds |
| warning | >= 97.5% | Alert raised; data team reviews before batch close |
| critical | < 97.5% | Pipeline halted; incident response triggered |

---

## Quick Start

```bash
git clone https://github.com/akbknight/data-pipeline-validator.git
cd data-pipeline-validator

pip install -r requirements.txt

# Run the full validation pipeline
python validate.py
# Outputs: validation_report.json

# Or use the modular entry point
python -m src.cli.run

# Run tests
python -m pytest tests/ -v

# Open index.html in a browser to view the dashboard
```

---

## Sample Output

```
Data Pipeline Validator
========================
Processing 15 sources (12,012 total records)...
  [01] CoreBanking_API                OK healthy   99.6% (28 issues)
  [02] CRM_Export                     !! warning   98.6% (50 issues)
  [09] WireTransfer_Log               !! warning   98.3% (134 issues)
  [11] Collections_API                XX critical  97.4% (199 issues)
  [15] BranchOps_Export               XX critical  97.1% (203 issues)

Summary: 12,012 records · 899 issues · 10 healthy / 3 warning / 2 critical
```

---

## Configuration

All validation rules, health thresholds, and simulation parameters are controlled by `configs/validation/rules.yaml` — no code changes required to adjust rule parameters.

```yaml
rules:
  amounts:
    allow_negative: false
    max_value: 10000000.0
    allow_zero: false

  status_codes:
    valid_values: [COMPLETED, PENDING, FAILED, REVERSED]

thresholds:
  health_healthy: 99.0
  health_warning: 97.5

simulation:
  n_sources: 15
  seed: 42
```

See `configs/validation/rules.yaml` for the full configuration reference.

---

## Project Structure

```
data-pipeline-validator/
├── validate.py                  # Root entry point (backwards-compatible shim)
├── validation_report.json       # Pre-computed pipeline output
├── index.html                   # Interactive dashboard (Chart.js)
├── configs/
│   └── validation/rules.yaml   # All rule parameters and thresholds
├── src/
│   ├── data/generator.py        # Synthetic financial data generation
│   ├── checks/                  # 7 validation check modules
│   ├── pipeline/validator.py    # Per-source validation orchestrator
│   ├── pipeline/runner.py       # Full pipeline loop and JSON output
│   └── cli/run.py               # CLI entry point
├── tests/
│   ├── test_checks.py           # Unit tests (18 tests across all 7 checks)
│   └── test_validator.py        # Integration tests for validate_source()
├── docs/
│   ├── methodology.md           # ISO 8000 dimensions and check rationale
│   ├── architecture.md          # Data flow and module dependency diagram
│   ├── decision_log.md          # Key design decisions with rationale
│   └── data_dictionary.md       # Field documentation for all schemas
└── reports/
    ├── research_notes.md        # DAMA data quality dimensions, references
    ├── eda.md                   # Synthetic dataset characterisation
    └── results.md               # Validation results interpretation
```

---

## Check Category Descriptions

**Completeness** (ISO 8000 dimension: Completeness)
Detects missing values in mandatory fields. Both `amount` and `account_id` are required for every transaction record. Null rate > 0% triggers severity high.

**Business Rule** (ISO 8000 dimension: Accuracy / Consistency)
Enforces domain-specific invariants: transaction amounts must be non-negative (reversals use `status=REVERSED` with a positive amount); transaction dates must not be in the future beyond a configurable tolerance window.

**Referential Integrity** (ISO 8000 dimension: Validity)
Validates enumerated field values against authorised sets. Status codes (`COMPLETED`, `PENDING`, `FAILED`, `REVERSED`) and currency codes (`USD`, `EUR`, `GBP`, `JPY`, `CAD`, `AUD`, `CHF`) must belong to the defined reference set.

**Uniqueness** (ISO 8000 dimension: Uniqueness)
Detects duplicate `record_id` values within each source batch. Duplicates indicate ETL idempotency failures or parallel extraction collisions.

**Range Validation** (ISO 8000 dimension: Accuracy)
Verifies that `amount` values fall within the expected range: > $0 and <= $10M per transaction. Zero values indicate extraction failures; values above $10M require manual review.

---

## Data Model

The synthetic dataset models financial transaction records from 15 of 50 named enterprise-style sources (core banking, AML, wire transfers, card processing, regulatory reporting, etc.).

Each transaction record contains:

| Field | Description |
|---|---|
| `record_id` | Unique transaction identifier |
| `account_id` | Customer account identifier |
| `transaction_date` | Date of transaction (2024 calendar year) |
| `amount` | Transaction amount — log-normal distribution (mean≈$4,915, heavy right tail to ~$1.8M at 99th pct) |
| `status` | Lifecycle status (COMPLETED 82%, PENDING 10%, FAILED 5%, REVERSED 3%) |
| `source_code` | 6-character source identifier |
| `currency` | ISO 4217 currency code (USD 88%, EUR 5%, GBP 3%, JPY 2%, CAD 2%) |

Issue injection uses a tiered quality model: 50% of sources are high-quality (1–4% issue rate), 30% moderate (5–14%), and 20% poor (15–35%) — simulating realistic enterprise data quality distribution.

See `docs/data_dictionary.md` for the full field reference and `docs/methodology.md` for the synthetic data model rationale.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data generation | Python, NumPy (log-normal distribution), pandas |
| Validation engine | pandas-based rule assertions, pyyaml config |
| Testing | pytest (28 tests) |
| Dashboard | Chart.js 4, HTML/CSS/JS |
| Deployment | GitHub Pages |
| Package metadata | PEP 517 (pyproject.toml) |

---

## Methodology

The validation framework is designed around the ISO 8000 / DAMA data quality dimensions most relevant to financial transaction pipelines. See `docs/methodology.md` for detailed coverage of:

- How each of the 7 checks maps to ISO 8000 data quality dimensions
- Why log-normal distribution is appropriate for financial transaction amounts
- Health scoring threshold derivation and industry SLA alignment
- Tiered quality model design

---

## Why This Project

This project mirrors the data quality infrastructure built for enterprise financial clients — specifically the validation layer of a platform aggregating data from 3,000+ sources for Capital One, where automated validation checks reduced manual review overhead and cut legal notification processing time by 50%.

The real system used SQL assertions, Python validators, and custom business rule engines. This demo reconstructs the validation logic with synthetic data at a smaller scale, demonstrating the same categories of quality checks.

---

## Author

**Akshay Kumar**
[linkedin.com/in/akshaykumardl](https://www.linkedin.com/in/akshaykumardl/) | [akbknight.github.io](https://akbknight.github.io)
