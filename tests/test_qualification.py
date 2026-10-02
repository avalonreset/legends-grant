import copy
import hashlib
import json
from pathlib import Path
import unittest

from grant_engine.qualification import evaluate_review


FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "qualification-review.json"
AS_OF = "2030-10-02T12:00:00Z"


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.review = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.facts = {"entity_type": "nonprofit", "state": "PA", "cash_match": 5000}

    def evaluate(self):
        return evaluate_review(self.review, self.facts, AS_OF)

    def test_complete_review_is_not_approval(self):
        result = self.evaluate()
        self.assertEqual(result["decision"], "eligible-for-review")
        self.assertIn("Not funder approval", result["limitation"])
        self.assertEqual(len(result["application_checklist"]), 2)
        self.assertTrue(all(r["status"] == "not_prepared" for r in result["application_checklist"]))

    def test_input_is_not_mutated(self):
        before = copy.deepcopy((self.review, self.facts))
        self.evaluate()
        self.assertEqual(before, (self.review, self.facts))

    def test_missing_fact_never_passes(self):
        del self.facts["state"]
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_null_fact_never_passes(self):
        self.facts["state"] = None
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_false_pass_is_detected(self):
        self.facts["entity_type"] = "business"
        result = self.evaluate()
        self.assertEqual(result["decision"], "unresolved")
        self.assertIn("review_decision_not_supported:entity", result["blockers"])

    def test_supported_fail_is_ineligible(self):
        self.facts["entity_type"] = "business"
        self.review["requirements"][0]["decision"] = "fail"
        self.assertEqual(self.evaluate()["decision"], "ineligible")

    def test_unknown_review_stays_unknown(self):
        self.review["requirements"][0]["decision"] = "unknown"
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_manual_rule_never_automatically_passes(self):
        self.review["requirements"][0]["operator"] = "manual"
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_missing_disqualifying_attachment_blocks(self):
        self.review["inventory"]["required_document_ids"].append("restrictions-appendix")
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_incomplete_rule_inventory_blocks_even_if_all_selected_rules_pass(self):
        self.review["inventory"]["all_rules_reviewed"] = False
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_incomplete_document_inventory_blocks(self):
        self.review["inventory"]["complete"] = False
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_unreviewed_amendment_blocks(self):
        doc = copy.deepcopy(self.review["documents"][0])
        doc.update(id="amendment", kind="amendment", reviewed_sha256=None)
        self.review["documents"].append(doc)
        self.review["inventory"]["required_document_ids"].append("amendment")
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_changed_document_hash_blocks(self):
        self.review["documents"][0]["text"] += " Businesses only."
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_changed_reviewed_revision_blocks(self):
        doc = self.review["documents"][0]
        doc["text"] += " Businesses only."
        doc["sha256"] = hashlib.sha256(doc["text"].encode()).hexdigest()
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_missing_citation_document_blocks(self):
        self.review["requirements"][0]["citations"][0]["document_id"] = "missing"
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_invented_quote_blocks(self):
        self.review["requirements"][0]["citations"][0]["quote"] = "All LLCs qualify automatically."
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_stale_evidence_blocks(self):
        self.review["documents"][0]["retrieved_at"] = "2030-01-01T00:00:00Z"
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_stale_amendment_check_blocks(self):
        self.review["inventory"]["amendments_checked_at"] = "2030-01-01T00:00:00Z"
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_future_evidence_blocks(self):
        self.review["documents"][0]["retrieved_at"] = "2031-01-01T00:00:00Z"
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_conflicts_block(self):
        self.review["inventory"]["conflicts"] = ["Amendment and notice disagree on entity type."]
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_third_party_evidence_cannot_clear(self):
        self.review["documents"][0]["authoritative"] = False
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_missing_controlling_notice_blocks(self):
        self.review["documents"][0]["kind"] = "attachment"
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_closed_loans_history_cannot_clear(self):
        for field, value in [("status", "closed"), ("status", "cancelled"), ("instrument", "loan"), ("instrument", "tax_credit"), ("record_type", "historical_award")]:
            with self.subTest(field=field, value=value):
                previous = self.review["opportunity"][field]
                self.review["opportunity"][field] = value
                self.assertEqual(self.evaluate()["decision"], "ineligible")
                self.review["opportunity"][field] = previous

    def test_uncertain_states_block(self):
        for field, value in [("status", "unknown"), ("status", "forecast"), ("instrument", "unknown"), ("access", "invitation_only"), ("access", "unknown")]:
            with self.subTest(field=field, value=value):
                previous = self.review["opportunity"][field]
                self.review["opportunity"][field] = value
                self.assertEqual(self.evaluate()["decision"], "unresolved")
                self.review["opportunity"][field] = previous

    def test_deadline_boundary_closed(self):
        self.review["opportunity"]["deadline"] = AS_OF
        self.assertEqual(self.evaluate()["decision"], "ineligible")

    def test_deadline_requires_timezone(self):
        self.review["opportunity"]["deadline"] = "2030-11-01"
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_missing_deadline_blocks_unless_explicit_rolling(self):
        self.review["opportunity"]["deadline"] = None
        self.assertEqual(self.evaluate()["decision"], "unresolved")
        self.review["opportunity"]["status"] = "rolling"
        self.assertEqual(self.evaluate()["decision"], "eligible-for-review")

    def test_boolean_cannot_count_as_numeric_fact(self):
        self.facts["cash_match"] = True
        self.assertEqual(self.evaluate()["decision"], "unresolved")

    def test_malformed_equals_fact_cannot_support_rejection(self):
        rule = self.review["requirements"][0]
        rule["decision"] = "fail"
        for value in (["nonprofit"], [], True, 1, 1.0):
            with self.subTest(value=value):
                self.facts["entity_type"] = value
                result = self.evaluate()
                self.assertEqual(result["decision"], "unresolved")
                self.assertEqual(result["requirements"][0]["decision"], "unknown")
                self.assertNotIn("requirement_failed:entity", result["reasons"])

    def test_malformed_one_of_fact_cannot_support_rejection(self):
        rule = self.review["requirements"][1]
        rule["decision"] = "fail"
        for value in (["PA"], [], True, 1, 1.0):
            with self.subTest(value=value):
                self.facts["state"] = value
                result = self.evaluate()
                self.assertEqual(result["decision"], "unresolved")
                self.assertEqual(result["requirements"][1]["decision"], "unknown")

    def test_boolean_numeric_equality_is_unknown_in_both_directions(self):
        rule = self.review["requirements"][0]
        rule.update(operator="equals", decision="fail")
        for expected, actual in [(True, 1), (1, True), (False, 0), (0, False)]:
            with self.subTest(expected=expected, actual=actual):
                rule["expected"] = expected
                self.facts["entity_type"] = actual
                self.assertEqual(self.evaluate()["requirements"][0]["decision"], "unknown")

    def test_numeric_one_of_does_not_accept_boolean(self):
        rule = self.review["requirements"][0]
        rule.update(operator="one_of", expected=[1, 2.0], decision="fail")
        self.facts["entity_type"] = True
        self.assertEqual(self.evaluate()["requirements"][0]["decision"], "unknown")

    def test_contains_malformed_or_heterogeneous_array_is_unknown(self):
        rule = self.review["requirements"][1]
        rule.update(operator="contains", expected="PA")
        for value in ("PA", ["PA", 1], ["PA", True], ["PA", None], [1, 2]):
            for proposed in ("pass", "fail"):
                with self.subTest(value=value, proposed=proposed):
                    self.facts["state"] = value
                    rule["decision"] = proposed
                    result = self.evaluate()
                    self.assertEqual(result["decision"], "unresolved")
                    self.assertEqual(result["requirements"][1]["decision"], "unknown")

    def test_contains_does_not_conflate_bool_and_number(self):
        rule = self.review["requirements"][1]
        rule.update(operator="contains", expected=1, decision="fail")
        self.facts["state"] = [True]
        self.assertEqual(self.evaluate()["requirements"][1]["decision"], "unknown")

    def test_valid_typed_absence_still_supports_rejection(self):
        rule = self.review["requirements"][1]
        for operator, expected, actual in [("equals", "PA", "NY"), ("one_of", ["PA"], "NY"),
                                            ("contains", "PA", []), ("contains", "PA", ["NY"])]:
            with self.subTest(operator=operator, actual=actual):
                rule.update(operator=operator, expected=expected, decision="fail")
                self.facts["state"] = actual
                self.assertEqual(self.evaluate()["decision"], "ineligible")

    def test_numeric_types_are_compatible_but_not_boolean(self):
        rule = self.review["requirements"][0]
        for operator, expected, actual in [("equals", 1, 1.0), ("one_of", [1], 1.0), ("contains", 1, [1.0, 2])]:
            with self.subTest(operator=operator):
                rule.update(operator=operator, expected=expected, decision="pass")
                self.facts["entity_type"] = actual
                self.assertEqual(self.evaluate()["decision"], "eligible-for-review")

    def test_private_values_are_not_output(self):
        self.facts["confidential_note"] = "private-canary-983478"
        self.assertNotIn("private-canary", json.dumps(self.evaluate()))

    def test_fact_fingerprint_changes_with_facts(self):
        first = self.evaluate()["private_facts_sha256"]
        self.facts["cash_match"] = 6000
        self.assertNotEqual(first, self.evaluate()["private_facts_sha256"])
        self.assertEqual(len(first), 64)

    def test_extra_fields_are_rejected(self):
        self.review["approved"] = True
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_nested_schema_errors(self):
        mutations = [("opportunity", "status", "OPEN"), ("inventory", "complete", "true"), ("inventory", "max_age_days", 365)]
        for section, field, value in mutations:
            with self.subTest(section=section, field=field):
                previous = self.review[section][field]
                self.review[section][field] = value
                with self.assertRaises(ValueError):
                    self.evaluate()
                self.review[section][field] = previous

    def test_empty_or_duplicate_rules_rejected(self):
        self.review["requirements"].append(copy.deepcopy(self.review["requirements"][0]))
        with self.assertRaises(ValueError):
            self.evaluate()
        self.review["requirements"] = []
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_nonfinite_private_fact_rejected(self):
        self.facts["cash_match"] = float("nan")
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_secret_url_rejected(self):
        self.review["documents"][0]["url"] = "https://example.org/notice?token=secret"
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_no_rule_citations_rejected(self):
        self.review["requirements"][0]["citations"] = []
        with self.assertRaises(ValueError):
            self.evaluate()


if __name__ == "__main__":
    unittest.main()
