# Research Notes

Background reading and reference material informing the validation framework design.

---

## DAMA Data Quality Dimensions (ISO 8000)

The Data Management Association (DAMA) International defines six primary data quality dimensions in the DAMA Data Management Body of Knowledge (DMBOK). These dimensions are formalised in ISO 8000 and are the standard framework for enterprise data quality programs.

### The Six Dimensions

**1. Completeness**
The degree to which required data is present. Measured as: (populated fields / total expected fields) * 100. In financial pipelines, completeness is the first check applied — records with missing mandatory fields cannot participate in any downstream process.

**2. Accuracy**
The degree to which data correctly represents the real-world entity or event. Accuracy is the hardest dimension to validate automatically because it requires a ground truth reference. In this framework, amount sign validation (no negative amounts) and range validation (no $0 or $10M+ values) serve as proxies for accuracy.

**3. Consistency**
The degree to which data is coherent across systems and time. Consistency checks verify that related fields have mutually compatible values (e.g., a status of COMPLETED should not appear with a future transaction_date). The No Future Dates check is a consistency check between the transaction_date and the current date.

**4. Timeliness**
The degree to which data is available when needed, and that temporal fields reflect the correct time context. The No Future Dates check enforces timeliness — a future-dated transaction is not yet timely (it represents an event that has not occurred).

**5. Uniqueness**
The degree to which each entity is represented exactly once. The Unique Record ID check enforces uniqueness within a source batch. In production, cross-source uniqueness (global deduplication) would be an additional check.

**6. Validity**
The degree to which data values conform to defined formats, ranges, and authorised enumerations. The Valid Status Code check and the Amount Range Check are validity checks.

### Mapping to This Framework

| DAMA Dimension | This Framework | Check |
|---|---|---|
| Completeness | Direct | Null Amount Check, Null Account ID Check |
| Accuracy | Proxy | No Negative Amount, Amount Range Check |
| Consistency | Partial | No Future Dates |
| Timeliness | Partial | No Future Dates |
| Uniqueness | Direct | Unique Record ID Check |
| Validity | Direct | Valid Status Code, Amount Range Check |

---

## Common Failure Modes in Enterprise Financial Data Pipelines

Based on practitioner experience and published case studies:

**1. Null / missing values (Completeness)**
Most common failure mode in batch ETL pipelines. Causes: JOIN failures on account master, extraction timeouts leaving partial records, schema changes in source system that add NOT NULL columns without migration.

**2. Duplicate records (Uniqueness)**
Second most common. Causes: ETL retry without deduplication (idempotency failure), parallel extraction jobs writing to the same output, source system replication lag causing double-write.

**3. Invalid enumeration values (Validity / Referential Integrity)**
Frequency increases with API version changes. A new status value added by the upstream team without coordinating with the downstream schema is the canonical example. AML and compliance systems are particularly sensitive — an unrecognised status prevents the transaction from entering the AML screening queue.

**4. Date errors (Timeliness / Consistency)**
Future dates: usually timezone misconfiguration or batch timestamp errors. Historical date errors (e.g., epoch date 1970-01-01): usually a null-to-integer conversion error in the ETL layer.

**5. Amount sign / range errors (Accuracy)**
Negative amounts from misapplied credit/debit indicators. Zero amounts from extraction failures. Very large amounts (near-integer overflow) from format parsing errors (e.g., a CSV where the amount column contains a comma-formatted number that was not parsed correctly).

**6. Encoding / character set issues**
Not covered in this framework. Common in sources that mix UTF-8 and Latin-1 encodings — special characters in customer names can corrupt downstream string processing.

**7. Schema drift**
Not covered in this framework. Column renamed or removed in upstream source without notification. Caught by schema registry checks or column presence validation.

---

## References

- Redman, T. C. (2016). *Data Driven: Creating a Data Culture*. Harvard Business Review Press. — Practitioner-oriented treatment of data quality; the "1% error rate costs 10% of revenue" heuristic is attributed to Redman.

- DAMA International. (2017). *DAMA-DMBOK: Data Management Body of Knowledge* (2nd ed.). Technics Publications. — Canonical reference for the six data quality dimensions.

- ISO 8000-8:2015. *Data Quality — Part 8: Information and data quality: Concepts and measuring*. International Organization for Standardization. — Formalises completeness, accuracy, consistency, currentness, uniqueness, validity as the primary dimensions.

- Pipino, L. L., Lee, Y. W., & Wang, R. Y. (2002). Data quality assessment. *Communications of the ACM*, 45(4), 211–218. — Academic treatment of data quality metrics; provides the mathematical framework for dimension measurement.

- Great Expectations Documentation (2024). *Data Quality Concepts*. [greatexpectations.io](https://greatexpectations.io). — Practical implementation patterns for the checks implemented in this framework.
