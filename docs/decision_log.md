# Decision Log

Key architectural and design decisions made during development, with rationale.

---

## 1. Why 7 checks, not more?

**Decision:** Implement exactly 7 check categories (2 completeness, 2 business rule, 1 referential integrity, 1 uniqueness, 1 range validation).

**Rationale:**

These seven categories cover the most common enterprise failure modes in financial data pipelines according to practitioner experience and the DAMA Data Quality survey. They map cleanly to ISO 8000 data quality dimensions and produce a dashboard that is comprehensible at a glance.

Checks deliberately excluded from this demo:

| Excluded check | Why excluded |
|---|---|
| Cross-source referential integrity | Would require joining across source DataFrames — significantly increases complexity for marginal demo value |
| Statistical distribution drift | Requires baseline distribution storage and rolling-window comparison — better suited to a dedicated monitoring system (e.g., Great Expectations, Monte Carlo) |
| Format / regex validation | Account ID and currency format validation would add 2–3 more checks; excluded to keep the check count comprehensible |
| Schema drift detection | Requires a schema registry — out of scope for a batch validator without a persistent schema store |

In a production system (e.g., the Capital One pipeline referenced in the README), all of the above would be implemented. The seven included checks are the minimum viable set for a credible data quality demo.

---

## 2. Why synthetic data?

**Decision:** Generate synthetic financial transaction data rather than using a public dataset.

**Rationale:**

1. **No proprietary data exposure.** The original production system processed data from 3,000+ sources for a financial institution. Reconstructing it with synthetic data demonstrates the same validation logic without any data governance risk.

2. **Realistic distributions.** The log-normal amount distribution (mean=8.5, sigma=2.5) and the tiered quality model produce synthetic data that behaves realistically under validation — not all sources pass, not all sources fail catastrophically.

3. **Reproducibility.** The `seed: 42` config parameter makes every run produce identical results, enabling reproducible demos and deterministic tests.

4. **Control over issue injection.** Synthetic data allows precise control over what types and rates of issues appear, making it possible to demonstrate all seven check categories without relying on a public dataset that might not contain the relevant failure modes.

**Alternative considered:** Using a public financial dataset (e.g., Kaggle credit card fraud dataset). Rejected because: (a) public datasets don't contain the full field set needed for all 7 checks; (b) the quality distribution is fixed and may not contain the failure modes we want to demonstrate.

---

## 3. Why three health tiers?

**Decision:** Classify sources as healthy / warning / critical based on overall pass percentage.

**Rationale:**

Three tiers reflect the standard operational response model for financial data pipelines:

- **Healthy (>= 99%):** Data meets the minimum quality threshold for automated processing. No manual intervention required.
- **Warning (97.5–99%):** Data quality is degraded but not enough to halt processing. The data team is alerted and reviews the source before the next batch window closes.
- **Critical (< 97.5%):** Data quality is insufficient for automated processing. The pipeline halts ingestion from this source; the incident response runbook is triggered.

The 99% / 97.5% thresholds specifically are industry conventions derived from SLA definitions in financial services data contracts. The gap between thresholds (1.5 percentage points) provides an early-warning window: a source trending toward critical will spend time in warning first, allowing intervention before processing is halted.

**Alternative considered:** Five tiers (excellent / good / fair / poor / critical). Rejected because: (a) three tiers map cleanly to traffic light semantics (green / amber / red) which the dashboard implements; (b) additional tiers would require more threshold parameters without adding operational clarity.

---

## 4. Why config-driven rules?

**Decision:** Externalise all rule parameters (valid status codes, amount bounds, health thresholds, simulation parameters) to `configs/validation/rules.yaml` rather than hardcoding them.

**Rationale:**

1. **Reusability across data domains.** A different financial product (e.g., insurance claims instead of banking transactions) would have different valid status codes, different amount ranges, and different currency sets. Changing the config file rather than the code enables reuse without forking.

2. **Separation of concerns.** Business rule parameters are business decisions, not engineering decisions. Externalising them to YAML makes it clear that they can be changed by a data governance team without touching Python code.

3. **Auditability.** YAML config files are easy to version-control and diff. Changes to validation rules are visible in `git log` without reading Python diffs.

4. **Testability.** Each check function accepts a `config` dict parameter. Tests can override individual parameters without mocking file I/O.

**Tradeoff acknowledged:** Config-driven rules add a layer of indirection. For a single-domain, single-use validator, hardcoded values would be simpler. The config layer is justified here because the framework is designed to be reusable across the 50+ source types in the source catalogue.
