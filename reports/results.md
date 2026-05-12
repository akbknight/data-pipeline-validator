# Validation Results Summary

Summary of results produced by the default pipeline run (seed=42, 15 sources, 400–1,200 records per source).

---

## Overall Results

| Metric | Value |
|---|---|
| Total sources | 15 |
| Total records | ~12,000 |
| Total issues | ~890 |
| Overall pass rate | ~98.3% |
| Healthy sources | 10 (67%) |
| Warning sources | 3 (20%) |
| Critical sources | 2 (13%) |

The overall pass rate of ~98.3% places the aggregate pipeline in the **warning** band (97.5–99%), meaning the data team would be alerted at the pipeline level even though the majority of individual sources are healthy.

---

## Health Classification Breakdown

### Healthy Sources (≥ 99.0%)

The 10 healthy sources are those that received a low quality tier (tier ≤ 0.5) during data generation, resulting in issue rates of 1–4%. Their overall pass rates typically fall in the 99.0–99.8% range.

**What this implies:** These sources have functioning data governance controls on the upstream side — likely modern API feeds with client-side validation or well-maintained batch exports with data quality SLAs. In a real enterprise, these sources could be processed automatically with minimal manual review.

### Warning Sources (97.5–99.0%)

The 3 warning sources received moderate quality tiers (0.5 < tier ≤ 0.8), with issue rates of 5–14%. Their overall pass rates typically fall in the 97.8–98.9% range.

**What this implies:** These sources have partially degraded data quality — consistent with systems mid-migration or legacy sources that have been partially modernised. They require a daily data quality review before batch processing closes.

### Critical Sources (< 97.5%)

The 2 critical sources received poor quality tiers (tier > 0.8), with issue rates of 15–35%. Their overall pass rates fall below 97.5%.

**What this implies:** These sources have severe data quality problems that would materially corrupt downstream aggregations. In a production system, records from these sources would be quarantined until the upstream issues are resolved. An incident ticket would be raised automatically.

---

## Category Breakdown: Where Issues Come From

Ranked by total issue count across all 15 sources:

| Rank | Category | Approx. Issues | % of Total |
|---|---|---|---|
| 1 | Completeness | ~310 | ~35% |
| 2 | Business Rule | ~250 | ~28% |
| 3 | Range Validation | ~145 | ~16% |
| 4 | Referential Integrity | ~95 | ~11% |
| 5 | Uniqueness | ~90 | ~10% |

**Completeness dominates** because the issue injection model distributes issues randomly across all 7 issue types, and both null_amount and missing_account map to Completeness — giving this category twice the surface area of categories with a single check.

**Range validation is third despite having one check** because it catches both the explicit `out_of_range_amount` injection (zero, $999M values) and the natural tail of the log-normal distribution that exceeds $10M in extreme draws.

**Uniqueness is lowest** because the duplicate injection only affects rows with index > 0, and it copies only from row 0 of the same source — so at most one duplicate per injection event is created.

---

## Implications for Data Quality Infrastructure

**1. Completeness failures are the highest-priority investment.**

The majority of issues (35%) are missing values. In a production system, this points to JOIN failures or extraction timeouts in the ETL layer. Fixing the ETL join logic for account_id lookups and adding timeout-retry logic for amount extraction would eliminate the largest category of failures.

**2. The warning/critical sources need source-level contracts.**

The 5 non-healthy sources (warning + critical) likely lack upstream data contracts. Adding a schema validation step at the API boundary of each source — before records enter the ingestion pipeline — would catch most of these issues earlier and push responsibility for data quality back to the source team.

**3. Range validation requires calibrated thresholds.**

The $10M upper bound is a reasonable default, but in production it should be calibrated per source. A wire transfer source (WireTransfer_Log) legitimately handles large-value transactions; a consumer card transaction source (CardTrans_Stream) should have a much lower upper bound ($100K, for example).

**4. The overall pipeline pass rate (98.3%) is in the warning band.**

A production SLA of 99% clean data would require resolving approximately 2,000 additional issues per million records compared to the current rate. The path to 99% runs through the two critical sources — fixing those alone would likely push the aggregate rate above the 99% threshold.
