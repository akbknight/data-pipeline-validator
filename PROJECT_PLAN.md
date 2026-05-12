# Project Plan

Upgrade plan for transforming `validate.py` from a single-file script into a production-grade Python package.

---

## Goals

1. Modularise the monolithic `validate.py` into a well-structured `src/` package
2. Make validation rules configuration-driven (no hardcoded values in Python)
3. Add a full test suite with pytest
4. Add documentation: methodology, architecture, decision log, data dictionary
5. Add research and analysis reports
6. Keep the root `validate.py` shim so existing invocations continue to work
7. Keep `validation_report.json` and `index.html` at the project root (dashboard reads them there)

---

## Package Structure

```
data-pipeline-validator/
├── validate.py                  # Root shim (backwards-compatible)
├── validation_report.json       # Pre-computed report (dashboard input)
├── index.html                   # Interactive dashboard (DO NOT MODIFY)
├── README.md                    # Upgraded professional README
├── pyproject.toml               # PEP 517 package metadata
├── requirements.txt             # Pip-installable dependencies
├── Makefile                     # Developer convenience targets
├── .gitignore                   # Standard Python gitignore
│
├── configs/
│   └── validation/
│       └── rules.yaml           # All rule parameters, thresholds, sim config
│
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── generator.py         # generate_source_data() + SOURCE_NAMES
│   ├── checks/
│   │   ├── __init__.py          # ALL_CHECKS list + exports
│   │   ├── completeness.py      # check_null_amounts, check_null_accounts
│   │   ├── business_rules.py    # check_no_negative_amounts, check_no_future_dates
│   │   ├── referential_integrity.py  # check_valid_status_codes
│   │   ├── uniqueness.py        # check_unique_record_ids
│   │   └── range_validation.py  # check_amount_range
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── validator.py         # validate_source() — config-driven
│   │   └── runner.py            # run_pipeline() — full loop + JSON output
│   └── cli/
│       ├── __init__.py
│       └── run.py               # main() entry point
│
├── tests/
│   ├── __init__.py
│   ├── test_checks.py           # Unit tests for all 7 check functions
│   └── test_validator.py        # Integration tests for validate_source()
│
├── docs/
│   ├── methodology.md           # ISO 8000 dimensions, check rationale
│   ├── architecture.md          # Data flow + module dependency diagram
│   ├── decision_log.md          # Key design decisions with rationale
│   └── data_dictionary.md       # Field documentation
│
└── reports/
    ├── research_notes.md        # DAMA dimensions, failure modes, references
    ├── eda.md                   # Synthetic dataset characterisation
    └── results.md               # Validation results interpretation
```

---

## Phase Breakdown

### Phase 1: Directory Structure and Source Modules

- Create `src/` package hierarchy
- Extract `generate_source_data()` to `src/data/generator.py`
- Extract each check to its own module in `src/checks/`
- Create `src/checks/__init__.py` with `ALL_CHECKS`
- Extract `validate_source()` to `src/pipeline/validator.py`
- Extract pipeline loop to `src/pipeline/runner.py`
- Create `src/cli/run.py` entry point
- Update root `validate.py` to be a shim

### Phase 2: Configuration

- Create `configs/validation/rules.yaml` with all rule parameters
- Update `validate_source()` to read from config
- Update `run_pipeline()` to read simulation params from config

### Phase 3: Project Files

- Write `pyproject.toml` with correct metadata and entry point
- Write `requirements.txt`
- Write `Makefile` with install, run, test, lint, clean targets
- Write `.gitignore`

### Phase 4: Tests

- Write `tests/test_checks.py` with unit tests for all 7 check functions
- Write `tests/test_validator.py` with integration tests for `validate_source()`

### Phase 5: Documentation

- Write `docs/methodology.md`
- Write `docs/architecture.md`
- Write `docs/decision_log.md`
- Write `docs/data_dictionary.md`

### Phase 6: Reports

- Write `reports/research_notes.md`
- Write `reports/eda.md`
- Write `reports/results.md`

### Phase 7: Final Polish

- Write `PROJECT_PLAN.md` (this file)
- Write `FINAL_REVIEW.md`
- Upgrade `README.md`
- Run tests to verify everything works
- Commit and push

---

## Success Criteria

- `python validate.py` runs without error and produces `validation_report.json`
- `python -m src.cli.run` runs identically
- All tests in `tests/` pass with `pytest tests/ -v`
- `configs/validation/rules.yaml` controls all rule parameters and thresholds
- `index.html` dashboard still works unchanged
- All modules import cleanly from `src/`
