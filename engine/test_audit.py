"""Tests for engine/audit.py — CMS rate comparison + report generation.

Uses stdlib `unittest`. No external deps. The CMSComparator and
ReportGenerator are pure functions (no I/O, no LLM, no subprocess),
so they can be tested in isolation.

Run: `python3 -m unittest engine.test_audit -v` (from the repo root)
or:  `cd engine && python3 -m unittest test_audit -v`

What's covered:
- CMS_RATES table integrity (every key is a 5-digit CPT string,
  every value is a positive integer, no duplicates).
- CMSComparator.compare() happy path: exact match, under, just over,
  and well over the 20% flagged threshold.
- CMSComparator skips services with no cpt_code, no billed_amount,
  or unknown CPT codes.
- Multi-unit calculation: billed = cms_rate * units.
- Flagged threshold: > 20% over CMS rate.
- ReportGenerator.generate() assembles findings + cms_overcharge
  in the right order and produces a stable shape.
- ReportGenerator._dispute_letter() / _phone_script() handle empty
  findings and missing fields gracefully.

The CMS_RATES table is a real product data table; a wrong value
would let overcharges slip through silently, so the integrity
test is load-bearing.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the engine dir to sys.path so we can import audit.py as a
# standalone module (it has no package marker; it's run as a script
# in production by the cron worker).
THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))

# `audit` is run as a script in production; importing it may try to
# read environment variables or import optional deps (pdfplumber,
# pytesseract). Those are in try/except inside the module, so
# importing is safe in the absence of those deps.
from audit import CMS_RATES, CMSComparator, ReportGenerator  # noqa: E402


# ----- CMS_RATES table integrity -----------------------------------------

class TestCMSRatesTable(unittest.TestCase):
    """The CMS_RATES table is a hardcoded dict of CPT code → $ amount.
    A wrong value would let overcharges slip through silently. The
    integrity tests below pin the shape so a future refactor that
    introduces bad data fails loudly."""

    def test_table_is_non_empty(self) -> None:
        self.assertGreater(len(CMS_RATES), 0, "CMS_RATES is empty")

    def test_every_key_is_a_5_digit_cpt_string(self) -> None:
        for cpt in CMS_RATES.keys():
            self.assertIsInstance(cpt, str, f"key {cpt!r} is not a string")
            self.assertEqual(len(cpt), 5, f"key {cpt!r} is not 5 digits")
            self.assertTrue(cpt.isdigit(), f"key {cpt!r} is not all digits")

    def test_every_value_is_a_positive_integer(self) -> None:
        for cpt, rate in CMS_RATES.items():
            self.assertIsInstance(rate, int, f"rate for {cpt} is {type(rate).__name__}, not int")
            self.assertGreater(rate, 0, f"rate for {cpt} is not positive")

    def test_no_duplicate_keys(self) -> None:
        # Dict keys are unique by construction, but assert the count
        # equals the unique-key set size to catch a future refactor
        # that stores rates in a non-dict structure.
        self.assertEqual(len(CMS_RATES), len(set(CMS_RATES.keys())))

    def test_rates_are_realistic_for_known_cpt_codes(self) -> None:
        # A few known CPT codes with publicly-verifiable CMS rates
        # (Medicare Physician Fee Schedule 2024). These are rough
        # ranges; the audit engine is conservative, so a rate that
        # is wildly off-base is what we want to catch.
        # 99213 (established patient office visit, level 3): ~$75
        self.assertGreaterEqual(CMS_RATES["99213"], 50)
        self.assertLessEqual(CMS_RATES["99213"], 150)
        # 99284 (ED visit, high severity): ~$250
        self.assertGreaterEqual(CMS_RATES["99284"], 150)
        self.assertLessEqual(CMS_RATES["99284"], 400)
        # 99285 (ED visit, critical): ~$370
        self.assertGreaterEqual(CMS_RATES["99285"], 250)
        self.assertLessEqual(CMS_RATES["99285"], 500)

    def test_specific_known_values(self) -> None:
        # Pin the exact dollar amounts for the most common codes.
        # This catches a typo (off-by-one) in the table.
        # If a future billing change updates the rates, this test
        # will fail and force a deliberate code update.
        self.assertEqual(CMS_RATES["99213"], 76)
        self.assertEqual(CMS_RATES["99214"], 111)
        self.assertEqual(CMS_RATES["99284"], 266)
        self.assertEqual(CMS_RATES["99285"], 377)
        self.assertEqual(CMS_RATES["93000"], 28)


# ----- CMSComparator.compare() --------------------------------------------

class TestCMSComparator(unittest.TestCase):
    """CMSComparator.compare() takes a list of service dicts and returns
    a list of rate-comparison results. A service is included in the
    output if it has a cpt_code and billed_amount AND the cpt_code is
    in CMS_RATES. A service is flagged if billed > 1.2 * cms_rate."""

    def setUp(self) -> None:
        self.cms = CMSComparator()

    def test_exact_match_is_not_flagged(self) -> None:
        # 99213 = $76. Billed exactly $76 → difference is 0, not flagged.
        result = self.cms.compare([
            {"cpt_code": "99213", "billed_amount": 76, "units": 1, "description": "Office visit"}
        ])
        self.assertEqual(len(result), 1)
        r = result[0]
        self.assertEqual(r["cpt"], "99213")
        self.assertEqual(r["billed"], 76.0)
        self.assertEqual(r["cms_rate"], 76.0)
        self.assertEqual(r["difference"], 0.0)
        self.assertEqual(r["pct_over"], 0.0)
        self.assertFalse(r["flagged"])

    def test_just_under_threshold_is_not_flagged(self) -> None:
        # 99213 = $76. Billed $90 → 18.4% over, just under the 20%
        # threshold → not flagged.
        result = self.cms.compare([
            {"cpt_code": "99213", "billed_amount": 90, "units": 1, "description": "Office visit"}
        ])
        self.assertEqual(len(result), 1)
        # 18.4% rounds to 18.4 with the helper's round(_, 1)
        self.assertAlmostEqual(result[0]["pct_over"], 18.4, places=1)
        self.assertFalse(result[0]["flagged"])

    def test_just_over_threshold_is_flagged(self) -> None:
        # 99213 = $76. Billed $95 → 25% over, above the 20% threshold
        # → flagged.
        result = self.cms.compare([
            {"cpt_code": "99213", "billed_amount": 95, "units": 1, "description": "Office visit"}
        ])
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0]["pct_over"], 25.0, places=1)
        self.assertTrue(result[0]["flagged"])

    def test_well_over_threshold_is_flagged(self) -> None:
        # 99213 = $76. Billed $300 → ~295% over → flagged.
        result = self.cms.compare([
            {"cpt_code": "99213", "billed_amount": 300, "units": 1, "description": "Office visit"}
        ])
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["flagged"])
        self.assertGreater(result[0]["pct_over"], 200)

    def test_underbilling_is_not_flagged(self) -> None:
        # 99213 = $76. Billed $50 → underbilling (patient paid less
        # than the CMS rate). The audit engine is for overcharges,
        # not underbilling, so this should NOT be flagged.
        result = self.cms.compare([
            {"cpt_code": "99213", "billed_amount": 50, "units": 1, "description": "Office visit"}
        ])
        self.assertEqual(len(result), 1)
        # pct_over is negative, but flagged is False because the
        # check is `diff/expected > 0.2` (strictly positive).
        self.assertFalse(result[0]["flagged"])
        self.assertLess(result[0]["pct_over"], 0)

    def test_unknown_cpt_code_is_skipped(self) -> None:
        # A CPT code not in CMS_RATES is not in the output. The
        # caller can still audit the service via the LLM extractor,
        # but the CMS comparison has no opinion.
        result = self.cms.compare([
            {"cpt_code": "99999", "billed_amount": 100, "units": 1, "description": "Mystery"}
        ])
        self.assertEqual(len(result), 0)

    def test_service_missing_cpt_is_skipped(self) -> None:
        result = self.cms.compare([
            {"billed_amount": 100, "units": 1, "description": "No cpt_code"}
        ])
        self.assertEqual(len(result), 0)

    def test_service_missing_billed_is_skipped(self) -> None:
        result = self.cms.compare([
            {"cpt_code": "99213", "units": 1, "description": "No billed_amount"}
        ])
        self.assertEqual(len(result), 0)

    def test_multi_units_calculation(self) -> None:
        # 99213 = $76. Billed 2 units at $200 → expected = 76*2 = 152.
        # difference = 200 - 152 = 48, pct_over = 48/152 = 31.6% → flagged.
        result = self.cms.compare([
            {"cpt_code": "99213", "billed_amount": 200, "units": 2, "description": "Office visit x2"}
        ])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["cms_rate"], 152.0)
        self.assertEqual(result[0]["difference"], 48.0)
        self.assertAlmostEqual(result[0]["pct_over"], 31.6, places=1)
        self.assertTrue(result[0]["flagged"])

    def test_default_units_is_1(self) -> None:
        # A service without a `units` key defaults to 1 unit.
        result = self.cms.compare([
            {"cpt_code": "99213", "billed_amount": 76, "description": "Office visit (no units)"}
        ])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["cms_rate"], 76.0)

    def test_zero_billed_is_skipped(self) -> None:
        # Zero billed is not a real overcharge scenario; skip.
        result = self.cms.compare([
            {"cpt_code": "99213", "billed_amount": 0, "units": 1, "description": "Office visit (free)"}
        ])
        self.assertEqual(len(result), 0)

    def test_empty_input_yields_empty_output(self) -> None:
        self.assertEqual(self.cms.compare([]), [])

    def test_multiple_services_each_produce_a_result(self) -> None:
        services = [
            {"cpt_code": "99213", "billed_amount": 76, "units": 1, "description": "Office visit"},
            {"cpt_code": "99284", "billed_amount": 266, "units": 1, "description": "ED visit"},
            {"cpt_code": "99999", "billed_amount": 100, "units": 1, "description": "Mystery"},
        ]
        result = self.cms.compare(services)
        # 99999 is unknown → skipped. 2 results expected.
        self.assertEqual(len(result), 2)
        cpts = sorted(r["cpt"] for r in result)
        self.assertEqual(cpts, ["99213", "99284"])

    def test_result_preserves_description(self) -> None:
        result = self.cms.compare([
            {"cpt_code": "99213", "billed_amount": 76, "units": 1, "description": "Established patient visit, level 3"}
        ])
        self.assertEqual(result[0]["service"], "Established patient visit, level 3")

    def test_rounding_is_two_decimal_places(self) -> None:
        # 99213 = $76. Billed $80 → diff 4, pct_over 5.26...
        # diff is round(_, 2) = 4.0. pct_over is round(_, 1) = 5.3.
        result = self.cms.compare([
            {"cpt_code": "99213", "billed_amount": 80, "units": 1, "description": "Office visit"}
        ])
        # billed and cms_rate are round(_, 2)
        self.assertEqual(result[0]["billed"], 80.0)
        self.assertEqual(result[0]["cms_rate"], 76.0)
        # difference is round(_, 2)
        self.assertEqual(result[0]["difference"], 4.0)
        # pct_over is round(_, 1)
        self.assertAlmostEqual(result[0]["pct_over"], 5.3, places=1)


# ----- ReportGenerator -----------------------------------------------------

class TestReportGenerator(unittest.TestCase):
    """ReportGenerator is also a pure function: it assembles the
    findings + rate_comparisons into a structured report. Tests
    cover the assembly logic, the dispute letter / phone script
    generation, and the edge cases (empty findings, missing
    fields)."""

    def setUp(self) -> None:
        self.reporter = ReportGenerator()

    def test_empty_findings_produces_minimal_report(self) -> None:
        result = self.reporter.generate(
            {"total_billed": 100, "provider_name": "Test Hospital", "services": []},
            [],  # no rate comparisons
            [],  # no findings
        )
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["rate_comparisons"], [])
        self.assertIsNone(result["dispute_letter"])
        self.assertIsNone(result["phone_script"])
        self.assertEqual(result["billed_amount"], "$100.00")
        self.assertEqual(result["service_count"], 0)
        self.assertEqual(result["error_count"], 0)
        self.assertEqual(result["savings_estimate"], "$0")

    def test_finding_with_amount_appears_in_report(self) -> None:
        result = self.reporter.generate(
            {"total_billed": 500, "services": [{"cpt_code": "99213"}]},
            [],
            [{"type": "upcoding", "severity": "high", "code": "99213", "amount": 100.0, "description": "x", "detail": "y", "citation": None}],
        )
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["type"], "upcoding")
        # Savings estimate includes the finding's amount.
        self.assertEqual(result["savings_estimate"], "$100")

    def test_flagged_rate_comparison_appears_as_cms_overcharge_finding(self) -> None:
        # A rate comparison with `flagged: True` is converted to a
        # `cms_overcharge` finding in the report, with severity
        # 'medium' if pct_over > 50, 'low' otherwise.
        result = self.reporter.generate(
            {"total_billed": 500, "services": [{"cpt_code": "99213"}]},
            [
                {
                    "service": "Office visit",
                    "cpt": "99213",
                    "billed": 200.0,
                    "cms_rate": 76.0,
                    "difference": 124.0,
                    "pct_over": 163.2,
                    "flagged": True,
                }
            ],
            [],
        )
        # The report has 1 finding (the cms_overcharge).
        self.assertEqual(len(result["findings"]), 1)
        f = result[0] if isinstance(result, list) else result["findings"][0]
        self.assertEqual(f["type"], "cms_overcharge")
        self.assertEqual(f["code"], "99213")
        # 163.2% > 50 → severity is medium.
        self.assertEqual(f["severity"], "medium")

    def test_findings_are_sorted_by_severity(self) -> None:
        # The report sorts findings: high → medium → low.
        result = self.reporter.generate(
            {"total_billed": 1000, "services": []},
            [],
            [
                {"type": "x", "severity": "low", "amount": 10, "description": "low", "detail": "", "code": None, "citation": None},
                {"type": "x", "severity": "high", "amount": 30, "description": "high", "detail": "", "code": None, "citation": None},
                {"type": "x", "severity": "medium", "amount": 20, "description": "med", "detail": "", "code": None, "citation": None},
            ],
        )
        findings = result["findings"]
        severities = [f["severity"] for f in findings]
        self.assertEqual(severities, ["high", "medium", "low"])

    def test_dispute_letter_contains_total_disputed(self) -> None:
        result = self.reporter.generate(
            {
                "total_billed": 500.0,
                "provider_name": "Test Hospital",
                "account_number": "MH-12345",
                "services": [],
            },
            [],
            [
                {"type": "upcoding", "severity": "high", "amount": 100.0, "description": "Wrong code", "detail": "Used 99214 instead of 99213", "code": "99214", "citation": "CPT guidelines"}
            ],
        )
        letter = result["dispute_letter"]
        self.assertIsNotNone(letter)
        # The letter includes the account number and the total disputed.
        self.assertIn("MH-12345", letter)
        self.assertIn("$100.00", letter)
        # And the finding description.
        self.assertIn("Wrong code", letter)

    def test_phone_script_contains_findings(self) -> None:
        result = self.reporter.generate(
            {"total_billed": 100, "services": []},
            [],
            [
                {"type": "unbundling", "severity": "medium", "amount": 50.0, "description": "Split billing", "detail": "Bundled services billed separately", "code": "99213", "citation": None}
            ],
        )
        script = result["phone_script"]
        self.assertIsNotNone(script)
        self.assertIn("Split billing", script)
        self.assertIn("$50.00", script)


if __name__ == "__main__":
    unittest.main(verbosity=2)
