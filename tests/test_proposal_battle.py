"""Independent battle acceptance for proposal drafting (black-box CLI).

These tests exercise the shipped `proposal` commands end to end with a
small synthetic community task. They assert observable CLI behavior
(exit codes, check verdicts, refusal messages, rendered wording), not
implementation internals. All names, figures, and passages are invented.
"""
import contextlib
import copy
import io
import json
import unittest
from pathlib import Path
import tempfile

from grant_engine.__main__ import main


def battle_facts():
    return {
        "schema_version": 1,
        "facts": {
            "org-founded": {
                "statement": "SYNTHETIC: the association began operating in 2021.",
                "kind": "historical",
                "visibility": "shareable",
                "source": "Synthetic intake",
            },
            "meals-count": {
                "statement": "SYNTHETIC: the program served about 4800 meals in 2025.",
                "kind": "historical",
                "visibility": "private",
                "source": "Synthetic program log",
            },
            "cost-quote": {
                "statement": "SYNTHETIC: a vendor quoted $100.00 for equipment.",
                "kind": "estimate",
                "visibility": "private",
                "source": "Synthetic quote",
            },
            "schedule-plan": {
                "statement": "SYNTHETIC: the table will run each Saturday of the grant year.",
                "kind": "commitment",
                "visibility": "shareable",
                "source": "Synthetic board minute",
            },
        },
    }


def battle_proposal():
    return {
        "schema_version": 1,
        "opportunity_id": "synthetic-lakeview-2027",
        "funder_name": "Lakeview Community Foundation (SYNTHETIC)",
        "questions": [
            {"id": "need", "prompt": "Describe the need. (SYNTHETIC.)",
             "required": True, "max_words": 200},
            {"id": "activities", "prompt": "Describe activities. (SYNTHETIC.)",
             "required": True, "max_words": 250},
        ],
        "attachments_required": [
            {"id": "budget-worksheet", "description": "Budget. (SYNTHETIC.)", "required": True},
            {"id": "proof-of-location", "description": "Venue proof. (SYNTHETIC.)", "required": True},
        ],
        "limits": {"max_total_words": 600, "max_request": "25000.00",
                   "unallowable_categories": ["alcohol", "lobbying"], "notes": ""},
        "project": {"title": "Harborview Meal Table (SYNTHETIC)",
                    "summary": "A free weekly meal table adding equipment."},
        "budget": {
            "currency": "USD",
            "total_requested": "150.00",
            "total_project": "175.00",
            "use_of_funds": "Grant funds buy equipment and supplies for Saturday meal service.",
            "lines": [
                {"id": "equip", "label": "Equipment", "category": "equipment",
                 "amount": "100.00", "funding_source": "grant"},
                {"id": "supplies", "label": "Supplies", "category": "supplies",
                 "amount": "50.00", "funding_source": "grant"},
                {"id": "match-time", "label": "Donated time", "category": "in-kind",
                 "amount": "25.00", "funding_source": "match"},
            ],
        },
        "answers": [
            {"question_id": "need",
             "text": "The association has run a weekly meal table since 2021. "
                     "In 2025 the program served about 4,800 meals.",
             "fact_refs": ["org-founded", "meals-count"]},
            {"question_id": "activities",
             "text": "Each Saturday of the grant year the table runs with the new equipment.",
             "fact_refs": ["schedule-plan", "cost-quote"]},
        ],
        "attachments": [
            {"attachment_id": "budget-worksheet", "status": "prepared"},
            {"attachment_id": "proof-of-location", "status": "prepared"},
        ],
        "shared_evidence": {"fact_ids": ["org-founded", "schedule-plan"]},
        "substantive_review": {"status": "not_reviewed", "reviewer": None,
                               "reviewed_at": None, "notes": ""},
    }


class ProposalBattleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def invoke(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = main([str(argument) for argument in arguments])
            except SystemExit as exc:
                code = exc.code
        return code, stdout.getvalue(), stderr.getvalue()

    def json_file(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def case_files(self, proposal=None, facts=None):
        proposal_path = self.json_file("proposal.json", proposal or battle_proposal())
        facts_path = self.json_file("facts.json", facts or battle_facts())
        return proposal_path, facts_path

    def check(self, proposal, facts=None):
        proposal_path, facts_path = self.case_files(proposal, facts)
        output = self.root / "check.json"
        code, _, error = self.invoke("proposal", "check", "--proposal", proposal_path,
                                     "--facts", facts_path, "--output", output)
        self.assertEqual((code, error), (0, ""))
        return json.loads(output.read_text(encoding="utf-8"))

    def render(self, proposal, facts=None):
        proposal_path, facts_path = self.case_files(proposal, facts)
        output = self.root / "draft.md"
        code, _, error = self.invoke("proposal", "render", "--proposal", proposal_path,
                                     "--facts", facts_path, "--output", output)
        self.assertEqual((code, error), (0, ""))
        return output.read_text(encoding="utf-8")

    def test_clean_battle_package_passes_with_echoed_sums_and_kinds(self):
        result = self.check(battle_proposal())
        self.assertTrue(result["mechanical_checks_passed"])
        self.assertEqual((result["blockers"], result["warnings"]), ([], []))
        self.assertEqual(result["budget"]["grant_lines_sum"], "150.00")
        self.assertEqual(result["budget"]["all_lines_sum"], "175.00")
        kinds = {entry["question_id"]: entry["fact_kinds"] for entry in result["answers"]}
        self.assertEqual(kinds["need"], {"historical": 2})
        self.assertEqual(kinds["activities"], {"commitment": 1, "estimate": 1})

    def test_honest_open_notes_and_missing_proof_block_as_placeholders(self):
        proposal = battle_proposal()
        proposal["answers"][0]["text"] += " [[OPEN: neighborhood figure not supplied.]]"
        proposal["attachments"][1]["status"] = "missing"
        result = self.check(proposal)
        self.assertFalse(result["mechanical_checks_passed"])
        self.assertIn("unresolved_placeholder:answer:need", result["blockers"])
        self.assertIn("missing_attachment:proof-of-location", result["blockers"])

    def test_structural_blockers_cover_citations_sums_limits(self):
        proposal = battle_proposal()
        proposal["answers"][0]["fact_refs"] = ["no-such-fact"]
        proposal["answers"][1]["fact_refs"] = []
        proposal["budget"]["total_requested"] = "150.01"
        proposal["answers"][1]["text"] = "word " * 300
        result = self.check(proposal)
        self.assertFalse(result["mechanical_checks_passed"])
        for blocker in ("unknown_fact_ref:need:no-such-fact",
                        "answer_missing_citations:activities",
                        "budget_sum_mismatch",
                        "answer_over_limit:activities"):
            self.assertIn(blocker, result["blockers"])

    def test_historical_secured_funding_warns_without_blocking(self):
        proposal = battle_proposal()
        proposal["answers"][0]["text"] += " In 2024 we secured grant funding for the pilot kitchen."
        result = self.check(proposal)
        self.assertEqual(result["blockers"], [])
        self.assertTrue(result["mechanical_checks_passed"])
        self.assertIn("claim_to_review:answer:need:award_mention", result["warnings"])

    def test_evidence_linked_eligibility_sentence_warns_without_blocking(self):
        proposal = battle_proposal()
        proposal["answers"][0]["text"] += " We are eligible: the notice requires Lakeview service."
        result = self.check(proposal)
        self.assertEqual(result["blockers"], [])
        self.assertTrue(result["mechanical_checks_passed"])
        self.assertIn("claim_to_review:answer:need:eligibility_mention", result["warnings"])

    def test_misleading_citation_passes_mechanically_with_limitation(self):
        # The checker confirms references resolve; entailment stays human
        # review. This passing result must carry its limitation, not
        # readiness.
        proposal = battle_proposal()
        proposal["answers"][0]["text"] = "Our published research proves the method at scale."
        proposal["answers"][0]["fact_refs"] = ["org-founded"]
        result = self.check(proposal)
        self.assertTrue(result["mechanical_checks_passed"])
        self.assertIn("Factual entailment", result["limitation"])
        self.assertIn("never submits", result["limitation"])

    def test_reviewed_status_is_echoed_and_never_upgrades_mechanics(self):
        clean = battle_proposal()
        clean["substantive_review"] = {"status": "reviewed", "reviewer": "SYNTHETIC reviewer",
                                       "reviewed_at": "2026-10-02T12:00:00+00:00", "notes": ""}
        result = self.check(clean)
        self.assertTrue(result["mechanical_checks_passed"])
        self.assertEqual(result["substantive_review"]["status"], "reviewed")
        dirty = copy.deepcopy(clean)
        dirty["attachments"][1]["status"] = "missing"
        result = self.check(dirty)
        self.assertFalse(result["mechanical_checks_passed"])
        self.assertIn("missing_attachment:proof-of-location", result["blockers"])
        self.assertEqual(result["substantive_review"]["status"], "reviewed")

    def test_render_carries_limitation_advisories_and_no_readiness_claim(self):
        proposal = battle_proposal()
        proposal["answers"][0]["text"] += " The funding is guaranteed."
        draft = self.render(proposal)
        self.assertIn("PRIVATE", draft)
        self.assertIn("Mechanical checks: PASS", draft)
        self.assertIn("claim_to_review:answer:need:award_mention", draft)
        self.assertIn("Advisory only", draft)
        self.assertIn("Historical facts", draft)
        self.assertIn("Estimates and projections", draft)
        self.assertIn("Future commitments", draft)
        self.assertIn("never submits", draft)
        lowered = draft.lower()
        self.assertNotIn("ready", lowered)
        self.assertNotIn("verified", lowered)

    def test_check_output_contains_ids_and_counts_not_prose(self):
        result = self.check(battle_proposal())
        raw = json.dumps(result)
        self.assertNotIn("4,800 meals", raw)
        self.assertNotIn("began operating in 2021", raw)
        self.assertIn("org-founded", raw)

    def test_output_must_not_overwrite_hardlink_alias_of_input(self):
        proposal_path, facts_path = self.case_files()
        before = proposal_path.read_bytes()
        alias = self.root / "alias.json"
        try:
            alias.hardlink_to(proposal_path)
        except OSError:
            self.skipTest("filesystem refuses hardlinks")
        code, _, error = self.invoke("proposal", "check", "--proposal", proposal_path,
                                     "--facts", facts_path, "--output", alias)
        self.assertEqual(code, 2)
        self.assertIn("must not overwrite", error)
        self.assertEqual(proposal_path.read_bytes(), before)

    def test_output_must_not_target_extensionless_database(self):
        proposal_path, facts_path = self.case_files()
        target = self.root / "evidence"
        target.write_bytes(b"SQLite format 3\x00" + b"\x00" * 84)
        code, _, error = self.invoke("proposal", "render", "--proposal", proposal_path,
                                     "--facts", facts_path, "--output", target)
        self.assertEqual(code, 2)
        self.assertIn("evidence database", error)
        self.assertEqual(target.read_bytes(), b"SQLite format 3\x00" + b"\x00" * 84)

    def test_output_must_not_target_symlink_to_database(self):
        proposal_path, facts_path = self.case_files()
        real = self.root / "real-store"
        real.write_bytes(b"SQLite format 3\x00" + b"\x00" * 84)
        alias = self.root / "alias.md"
        try:
            alias.symlink_to(real)
        except OSError:
            self.skipTest("platform refuses symlinks")
        code, _, error = self.invoke("proposal", "check", "--proposal", proposal_path,
                                     "--facts", facts_path, "--output", alias)
        self.assertEqual(code, 2)
        self.assertIn("evidence database", error)
        self.assertEqual(real.read_bytes()[:16], b"SQLite format 3\x00")

    def test_init_scaffold_checks_with_honest_blockers(self):
        proposal_out = self.root / "new-proposal.json"
        facts_out = self.root / "new-facts.json"
        code, _, error = self.invoke("proposal", "init", "--proposal-out", proposal_out,
                                     "--facts-out", facts_out, "--opportunity-id", "synthetic-init")
        self.assertEqual((code, error), (0, ""))
        code, _, error = self.invoke("proposal", "check", "--proposal", proposal_out,
                                     "--facts", facts_out, "--output", self.root / "init-check.json")
        self.assertEqual((code, error), (0, ""))
        result = json.loads((self.root / "init-check.json").read_text(encoding="utf-8"))
        self.assertFalse(result["mechanical_checks_passed"])
        self.assertTrue(any(blocker.startswith("unresolved_placeholder") for blocker in result["blockers"]))

    def test_schema_errors_exit_nonzero_without_leaking_input(self):
        proposal = battle_proposal()
        proposal["substantive_review"]["reviewer"] = "SYNTHETIC reviewer"
        proposal_path, facts_path = self.case_files(proposal)
        code, output, error = self.invoke("proposal", "check", "--proposal", proposal_path,
                                          "--facts", facts_path, "--output", self.root / "out.json")
        self.assertEqual(code, 2)
        self.assertNotIn("4,800", output + error)
        self.assertNotIn("Lakeview", output + error)


if __name__ == "__main__":
    unittest.main()
