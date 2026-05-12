# Data Dictionary

Documentation for all fields in the synthetic transaction schema and the `validation_report.json` output format.

---

## Synthetic Transaction Schema

Each source DataFrame contains the following columns:

| Column | Type | Description | Example |
|---|---|---|---|
| `record_id` | string | Unique transaction identifier; format `{source_prefix}_{6-digit-zero-padded-index}` | `CORE_000042` |
| `account_id` | string (nullable) | Customer account identifier; format `ACC{6-digit-number}`; null when missing_account issue injected | `ACC847291` |
| `transaction_date` | datetime | Date the transaction occurred; drawn from 2024-01-01 to 2024-12-31 range; may be future-dated when future_date issue injected | `2024-07-15` |
| `amount` | float64 (nullable) | Transaction amount in the source currency; log-normal distribution (mean=8.5, sigma=2.5 in log-space); null when null_amount issue injected; negative when negative_amount issue injected | `4921.50` |
| `status` | string | Transaction lifecycle status; valid values: COMPLETED, PENDING, FAILED, REVERSED; may be invalid when invalid_status issue injected | `COMPLETED` |
| `source_code` | string | 6-character uppercase prefix of the source name | `COREBA` |
| `currency` | string | ISO 4217 currency code; distribution: USD 88%, EUR 5%, GBP 3%, JPY 2%, CAD 2% | `USD` |

### Issue Injection Reference

| Issue Type | Field Affected | Injected Value |
|---|---|---|
| `null_amount` | `amount` | `NaN` |
| `future_date` | `transaction_date` | base_date + 400–730 days |
| `negative_amount` | `amount` | `-abs(original_amount)` |
| `invalid_status` | `status` | One of: UNKNOWN, ERROR, NULL, ??? |
| `missing_account` | `account_id` | `NaN` |
| `duplicate_id` | `record_id` | Copied from row 0 of same source |
| `out_of_range_amount` | `amount` | 0.0, 999999999.0, or -1.0 |

---

## validation_report.json Output Schema

### Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `generated` | string | Timestamp when the report was generated; format `YYYY-MM-DD HH:MM` |
| `elapsed_seconds` | float | Wall-clock time for the full pipeline run in seconds |
| `summary` | object | Aggregate statistics across all sources |
| `category_breakdown` | array | Issue counts by check category, sorted descending by issue count |
| `sources` | array | Per-source validation results (one object per source) |

### summary Object

| Field | Type | Description |
|---|---|---|
| `total_sources` | int | Number of sources processed |
| `total_records` | int | Total records across all sources |
| `total_issues` | int | Total failed check instances across all sources and all checks |
| `healthy` | int | Count of sources with health=healthy |
| `warning` | int | Count of sources with health=warning |
| `critical` | int | Count of sources with health=critical |
| `overall_pass_pct` | float | Global pass percentage: (total_records * n_checks - total_issues) / (total_records * n_checks) * 100 |

### category_breakdown Array Item

| Field | Type | Description |
|---|---|---|
| `category` | string | Check category name (e.g., "Completeness", "Business Rule") |
| `issues` | int | Total failed instances for this category across all sources |

### sources Array Item (per-source result)

| Field | Type | Description |
|---|---|---|
| `source` | string | Source name (e.g., "CoreBanking_API") |
| `records` | int | Number of records in this source |
| `checks` | array | Array of 7 check result objects |
| `total_issues` | int | Sum of failed counts across all 7 checks for this source |
| `overall_pass_pct` | float | (records * 7 - total_issues) / (records * 7) * 100 |
| `health` | string | Health tier: "healthy", "warning", or "critical" |

### Check Result Object (item in sources[n].checks)

| Field | Type | Description |
|---|---|---|
| `check` | string | Human-readable check name (e.g., "Null Amount Check") |
| `category` | string | ISO 8000 dimension category (e.g., "Completeness") |
| `total` | int | Total records evaluated by this check (equals source record count) |
| `passed` | int | Records that passed this check |
| `failed` | int | Records that failed this check |
| `pct_pass` | float | passed / total * 100, rounded to 1 decimal place |
| `severity` | string | "pass" if failed=0; otherwise "high", "medium", or "low" per check definition |

### Severity Reference

| Severity | Checks That Use It | Meaning |
|---|---|---|
| `high` | Null Amount, Null Account ID, No Negative Amount, Unique Record ID | Failures directly corrupt financial aggregations or create unattributed records |
| `medium` | No Future Dates, Valid Status Code | Failures affect analytics and processing but do not corrupt totals |
| `low` | Amount Range Check | Failures require human review but may be legitimate |
| `pass` | Any check | Zero failures; no issue |
