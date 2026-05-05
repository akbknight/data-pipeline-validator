# Data Pipeline Validator

Automated validation framework for multi-source data pipelines. Simulates the quality control layer of an enterprise data aggregation system — the kind of infrastructure that processes records from dozens of upstream sources and enforces data contracts before downstream consumption.

Live dashboard: [akbknight.github.io/data-pipeline-validator](https://akbknight.github.io/data-pipeline-validator/)

## What it does

The validator ingests a synthetic multi-source dataset (15 sources, 12,000+ records) and runs 7 validation checks per source in parallel:

| Check | Category | Catches |
|---|---|---|
| Null Amount | Completeness | Missing transaction values |
| Null Account ID | Completeness | Orphaned records |
| No Negative Amount | Business Rule | Sign errors, reversals misclassified |
| No Future Dates | Business Rule | Clock skew, ETL date errors |
| Valid Status Code | Referential Integrity | Undocumented status values from upstream |
| Unique Record ID | Uniqueness | Duplicate ingestion, ETL retry loops |
| Amount Range Check | Range Validation | $0 and $10M+ outliers needing review |

Each source receives a health score and classification: **healthy** (≥99%), **warning** (97.5–99%), or **critical** (<97.5%).

## Sample results

```
CoreBanking_API      OK healthy   99.6%   30 issues
CRM_Export           !! warning   98.6%   51 issues
WireTransfer_Log     !! warning   98.3%  134 issues
Collections_API      XX critical  97.2%  200 issues
BranchOps_Export     XX critical  97.7%  120 issues
```

**15 sources · 12,012 records · 898 total issues · 10 healthy / 3 warning / 2 critical**

## Why it matters

This project mirrors the data quality infrastructure I built for enterprise financial clients at AIS InfoSource — specifically the validation layer of a platform aggregating data from 3,000+ sources for Capital One, where automated validation checks reduced manual review overhead and cut legal notification processing time by 50%.

The real system used a combination of SQL assertions, Python validators, and custom business rule engines. This demo reconstructs the validation logic with synthetic data, showing the same categories of quality checks at a smaller scale.

## How to run

```bash
git clone https://github.com/akbknight/data-pipeline-validator.git
cd data-pipeline-validator

pip install pandas numpy

# Generate a fresh synthetic dataset and run validation
python validate.py
# Outputs: validation_report.json

# Open index.html in a browser
# Dashboard reads embedded data — no server required
```

## Tech stack

| Layer | Technology |
|---|---|
| Data generation | Python, NumPy, pandas |
| Validation engine | pandas-based rule assertions |
| Dashboard | Chart.js 4, HTML/CSS/JS |
| Deployment | GitHub Pages |

## Skills demonstrated

- **Data quality engineering:** Schema, completeness, referential integrity, and business rule checks
- **Pipeline architecture:** Multi-source ingestion pattern with per-source health scoring
- **Statistical monitoring:** Threshold-based alerting, issue rate tracking
- **Data visualization:** Interactive source health table, category breakdown chart, expandable check details

## Author

**Akshay Kumar**  
[linkedin.com/in/akshaykumardl](https://www.linkedin.com/in/akshaykumardl/)
