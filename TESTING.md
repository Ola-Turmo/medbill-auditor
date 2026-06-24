# Testing — medbill-auditor

This repo uses **Python's built-in `unittest`** for the audit engine
unit tests. No external dependencies.

## Run

From the repo root:

```sh
python3 -m unittest engine.test_audit -v
```

or, equivalently, from inside the `engine/` directory:

```sh
cd engine && python3 -m unittest test_audit -v
```

Or run a single test class:

```sh
python3 -m unittest engine.test_audit.TestCMSComparator.test_exact_match_is_not_flagged
```

## What the tests cover

Three test classes, 27 tests, <1s total runtime:

### `TestCMSRatesTable` (6 tests) — table integrity

The `CMS_RATES` dict in `engine/audit.py` is a hardcoded mapping of
CPT code → dollar amount. It's a real product data table: a wrong
value would let overcharges slip through silently. The integrity
tests pin the shape so a future refactor that introduces bad data
fails loudly.

- `test_table_is_non_empty` — guards against accidentally emptying
  the table.
- `test_every_key_is_a_5_digit_cpt_string` — every key is a 5-digit
  string (CPT codes are exactly 5 digits).
- `test_every_value_is_a_positive_integer` — no floats, no zeros,
  no negatives.
- `test_no_duplicate_keys` — `len(CMS_RATES) == len(set(...))`.
- `test_rates_are_realistic_for_known_cpt_codes` — rough public
  ranges for `99213`, `99284`, `99285`. A 10x off-base value would
  fail this test.
- `test_specific_known_values` — pins the exact dollar amount for
  the most common codes (catches off-by-one typos).

### `TestCMSComparator` (15 tests) — the rate-comparison function

`CMSComparator.compare(services)` is a pure function: takes a list of
service dicts, returns a list of comparison results. A service is
included in the output if it has a `cpt_code` and `billed_amount`
AND the `cpt_code` is in `CMS_RATES`. A service is flagged if
`billed > 1.2 * cms_rate`.

Coverage:

- Exact match (billed == cms_rate) → not flagged
- Just under the 20% threshold → not flagged
- Just over the 20% threshold → flagged
- Well over (300%) → flagged
- **Underbilling** (billed < cms_rate) → not flagged. The audit
  engine is for overcharges, not underbilling; a patient who
  paid less than the CMS rate is not a flag.
- Unknown CPT code → service is skipped
- Missing `cpt_code` → service is skipped
- Missing `billed_amount` → service is skipped
- Zero `billed_amount` → service is skipped
- Multi-unit calculation (2 units at $200 = 4 * $76 expected)
- Default `units` is 1 when the key is absent
- Empty input list → empty output
- Multiple services → one result each (in input order)
- Result preserves the `description` from the input service
- Rounding: `billed`/`cms_rate`/`difference` to 2 decimals;
  `pct_over` to 1 decimal

### `TestReportGenerator` (6 tests) — the report-assembly function

`ReportGenerator.generate(structured, rate_comparisons, findings)`
assembles a structured report (the `dispute_letter`, `phone_script`,
and the `findings` list with `cms_overcharge` syntheses from the
rate comparisons).

Coverage:

- Empty findings → minimal report with `savings_estimate: "$0"`
- A finding with an `amount` → appears in the report, contributes
  to the savings estimate
- A flagged rate comparison → synthesized as a `cms_overcharge`
  finding (with severity `medium` if `pct_over > 50`, else `low`)
- Findings are sorted by severity: `high` → `medium` → `low`
- The dispute letter contains the account number, the total
  disputed amount, and the finding description
- The phone script contains the finding description and amount

## Why stdlib `unittest` (and not pytest)

The audit engine is small (one file, ~190 lines) and uses zero
non-stdlib runtime dependencies for the parts the tests cover
(CMSComparator and ReportGenerator). Pulling pytest just to run
27 tests isn't worth the dep tree. Stdlib `unittest` is enough.

The OCR + LLM parts of the engine do require `pdfplumber`,
`pytesseract`, and a local LLM CLI, but those are tested by the
live `cron/process_queue.py` worker against the production API.
Unit tests for the OCR/LLM paths are out of scope for this
slice — they would need fixtures (sample PDFs, mock LLM CLIs) and
the cost of building that infrastructure is high for low
incremental value (the OCR/LLM paths are thin wrappers around
well-tested third-party tools).

## Adding a new test

1. If the function you're testing is in `engine/audit.py` and is
   pure (no I/O, no LLM, no subprocess), add the test to
   `engine/test_audit.py`.
2. If the function is impure (I/O, LLM), it belongs in
   `cron/process_queue.py` integration tests, NOT in
   `test_audit.py`. Mocking the I/O in `unittest` is possible but
   adds significant complexity; for now, those code paths are
   covered by the live cron worker's smoke run.
3. Use the existing test classes as a template:
   `TestCMSRatesTable` for data-table integrity, `TestCMSComparator`
   for pure comparison functions, `TestReportGenerator` for
   pure assembly functions.

## Cross-references

- `engine/audit.py` — the source under test.
- `engine/requirements.txt` — the production OCR deps (NOT
  needed for the unit tests).
- `cron/process_queue.py` — the live cron worker that imports
  the engine; uses the same functions as the tests.
- `engine/test_bills/sample_er_bill.txt` — sample bill text used
  for manual smoke testing of the OCR + LLM pipeline.
