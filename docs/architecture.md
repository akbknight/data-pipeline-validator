# Architecture

## System Overview

The data pipeline validator is a batch validation framework. It generates synthetic multi-source financial data, validates each source against a configurable rule set, and produces a JSON report consumed by a static HTML dashboard.

---

## Data Flow

```
configs/validation/rules.yaml
          |
          v
src/data/generator.py          <-- synthetic DataFrame per source
          |
          v
src/pipeline/validator.py      <-- applies ALL_CHECKS; produces result dict
          |
          v
src/pipeline/runner.py         <-- iterates sources; aggregates stats
          |
          v
validation_report.json         <-- root-level output
          |
          v
index.html (dashboard)         <-- reads JSON; renders charts and tables
```

The dashboard reads `validation_report.json` from the same directory at page load via a `fetch()` call. No server is required — the pipeline is a pure batch process and the dashboard is a static file.

---

## Module Dependency Diagram

```
src/cli/run.py
  └── src/pipeline/runner.py
        ├── src/data/generator.py
        │     └── (numpy, pandas)
        └── src/pipeline/validator.py
              ├── src/checks/__init__.py
              │     ├── src/checks/completeness.py
              │     ├── src/checks/business_rules.py
              │     ├── src/checks/referential_integrity.py
              │     ├── src/checks/uniqueness.py
              │     └── src/checks/range_validation.py
              └── configs/validation/rules.yaml  (via pyyaml)
```

### Dependency rules

- `src/checks/*` modules are **stateless**. Each check function accepts a DataFrame and an optional config dict; it does not import from any other `src/` module. This makes individual checks independently testable.
- `src/data/generator.py` has no dependency on `src/checks/` or `src/pipeline/`. It is a pure data-generation module.
- `src/pipeline/validator.py` depends on `src/checks` but not on `src/data`. This separation allows the validator to be used against real DataFrames (not just synthetic ones).
- `src/pipeline/runner.py` is the only module that depends on both `src/data` and `src/pipeline/validator`.
- Config loading is localised to `src/pipeline/validator.py` and `src/pipeline/runner.py`. Check functions receive the config dict as a parameter — they do not load YAML themselves.

---

## Configuration Loading

```
Project root
└── configs/
    └── validation/
        └── rules.yaml      <-- loaded by validator.py and runner.py at runtime
```

Both `validator.py` and `runner.py` resolve the config path relative to `Path(__file__).parent` chains, ensuring the path works regardless of the current working directory when the script is invoked.

Config is loaded once per process invocation (cached in `_config_cache` in `validator.py`).

---

## Output Schema

`validation_report.json` at the project root:

```json
{
  "generated": "YYYY-MM-DD HH:MM",
  "elapsed_seconds": 0.42,
  "summary": {
    "total_sources": 15,
    "total_records": 12050,
    "total_issues": 892,
    "healthy": 10,
    "warning": 3,
    "critical": 2,
    "overall_pass_pct": 98.31
  },
  "category_breakdown": [
    {"category": "Completeness", "issues": 340},
    ...
  ],
  "sources": [
    {
      "source": "CoreBanking_API",
      "records": 850,
      "checks": [
        {
          "check": "Null Amount Check",
          "category": "Completeness",
          "total": 850,
          "passed": 847,
          "failed": 3,
          "pct_pass": 99.6,
          "severity": "high"
        },
        ...
      ],
      "total_issues": 30,
      "overall_pass_pct": 99.5,
      "health": "healthy"
    },
    ...
  ]
}
```

---

## Backward Compatibility

`validate.py` at the project root is a one-line shim:

```python
from src.pipeline.runner import run_pipeline
if __name__ == "__main__":
    run_pipeline()
```

This preserves the original `python validate.py` invocation while routing all logic through the modular `src/` package.

---

## Extension Points

| What to extend | Where |
|---|---|
| Add a new check | Add a function to the relevant `src/checks/*.py` file; append it to `ALL_CHECKS` in `src/checks/__init__.py` |
| Add a new rule parameter | Add it to `configs/validation/rules.yaml`; read it in the relevant check function |
| Add a new data source | Add the source name to `SOURCE_NAMES` in `src/data/generator.py`; increase `n_sources` in config |
| Change health thresholds | Edit `thresholds` section in `configs/validation/rules.yaml` |
| Add CLI flags | Extend `src/cli/run.py` with `argparse` |
