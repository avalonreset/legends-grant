"""Proposal workbench contracts: scaffold, mechanical check, private render."""
import contextlib
import copy
import io
import json
import re
import tempfile
import unittest
from pathlib import Path

from grant_engine.__main__ import main
from grant_engine.proposals import check_proposal, count_words, new_scaffold, render_package


ROOT = Path(__file__).resolve().parents[1]
BANNED_OUTPUT = re.compile(r"\b(ready|verified)\b", re.IGNORECASE)


def passing_proposal():
    return {
        "schema_version": 1,
        "opportunity_id": "synthetic-test",
        "funder_name": "Synthetic Funder",
        "questions": [
            {"id": "need", "prompt": "Submit a need statement. A submission is complete only after portal upload.",
             "required": True, "max_words": 50},
            {"id": "plan", "prompt": "Describe the plan.", "required": True, "max_words": 50},
            {"id": "extra", "prompt": "Anything else.", "required": False, "max_words": None},
        ],
        "attachments_required": [
            {"id": "quote", "description": "Vendor quote.", "required": True},
            {"id": "photo", "description": "Site photo.", "required": False},
        ],
        "rubric": [{"id": "need", "description": "Need is specific."}],
        "limits": {"max_total_words": 200, "max_request": "25000.00",
                   "unallowable_categories": ["alcohol"], "notes": ""},
        "project": {"title": "Synthetic kitchen project", "summary": "Replace old ovens with two efficient units."},
        "budget": {"currency": "USD", "total_requested": "5000.00", "total_project": "6500.00",
                   "use_of_funds": "Grant funds buy ovens and installation.",
                   "lines": [{"id": "ovens", "label": "Ovens", "category": "equipment",
                              "amount": "4000.00", "funding_source": "grant"},
                             {"id": "install", "label": "Installation", "category": "services",
                              "amount": "1000.00", "funding_source": "grant"},
                             {"id": "volunteer", "label": "Volunteer help", "category": "in-kind",
                              "amount": "1500.00", "funding_source": "match"}]},
        "answers": [
            {"question_id": "need", "text": "Neighbors request more meal seats each week.",
             "fact_refs": ["org-founded"]},
            {"question_id": "plan", "text": "We plan to install ovens in spring.",
             "fact_refs": ["year1-projection", "match-pledge"]},
        ],
        "attachments": [{"attachment_id": "quote", "status": "prepared"}],
        "shared_evidence": {"fact_ids": ["org-founded"]},
        "substantive_review": {"status": "not_reviewed", "reviewer": None, "reviewed_at": None, "notes": ""},
    }


def passing_facts():
    return {
        "schema_version": 1,
        "facts": {
            "org-founded": {"statement": "Synthetic org began in 2019.", "kind": "historical",
                            "visibility": "shareable", "source": "Synthetic record"},
            "year1-projection": {"statement": "Synthetic plan projects 15000 meals.",
                                 "kind": "estimate", "visibility": "private"},
            "match-pledge": {"statement": "Synthetic board pledges volunteer hours.",
                             "kind": "commitment", "visibility": "private"},
        },
    }


class WordCountTests(unittest.TestCase):
    def test_defined_counting_ignores_punctuation_only_tokens(self):
        self.assertEqual(count_words("hello, world!"), 2)
        self.assertEqual(count_words("--- ..."), 0)
        self.assertEqual(count_words(""), 0)
        self.assertEqual(count_words("2029 brings 15,000 meals"), 4)
        self.assertEqual(count_words("state-of-the-art"), 1)
        self.assertEqual(count_words("caf\u00e9 na\u00efve"), 2)


class ScaffoldTests(unittest.TestCase):
    def test_scaffold_is_valid_schema_with_honest_blockers(self):
        proposal, facts = new_scaffold("synthetic-x")
        result = check_proposal(proposal, facts)
        self.assertFalse(result["mechanical_checks_passed"])
        self.assertIn("unresolved_placeholder:answer:need", result["blockers"])
        self.assertIn("missing_attachment:budget-worksheet", result["blockers"])
        self.assertEqual(result["substantive_review"]["status"], "not_reviewed")

    def test_scaffold_rejects_blank_opportunity(self):
        with self.assertRaises(ValueError):
            new_scaffold("  ")


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.proposal = passing_proposal()
        self.facts = passing_facts()

    def check(self):
        return check_proposal(self.proposal, self.facts)

    def test_passing_draft(self):
        result = self.check()
        self.assertTrue(result["mechanical_checks_passed"])
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["budget"]["grant_lines_sum"], "5000.00")
        self.assertEqual(result["budget"]["all_lines_sum"], "6500.00")
        kinds = {entry["question_id"]: entry["fact_kinds"] for entry in result["answers"]}
        self.assertEqual(kinds["need"], {"historical": 1})
        self.assertEqual(kinds["plan"], {"estimate": 1, "commitment": 1})

    def test_inputs_are_not_mutated(self):
        before = copy.deepcopy((self.proposal, self.facts))
        self.check()
        self.assertEqual(before, (self.proposal, self.facts))

    def test_missing_required_answer_blocks(self):
        self.proposal["answers"] = [a for a in self.proposal["answers"] if a["question_id"] != "need"]
        self.assertIn("missing_answer:need", self.check()["blockers"])

    def test_blank_answer_counts_as_missing(self):
        self.proposal["answers"][0]["text"] = "   "
        self.assertIn("missing_answer:need", self.check()["blockers"])

    def test_optional_question_may_stay_unanswered(self):
        self.assertNotIn("missing_answer:extra", self.check()["blockers"])

    def test_answer_without_citations_blocks(self):
        self.proposal["answers"][0]["fact_refs"] = []
        self.assertIn("answer_missing_citations:need", self.check()["blockers"])

    def test_unknown_fact_ref_blocks(self):
        self.proposal["answers"][0]["fact_refs"] = ["no-such-fact"]
        result = self.check()
        self.assertIn("unknown_fact_ref:need:no-such-fact", result["blockers"])
        self.assertEqual(result["answers"][0]["cited_unknown"], ["no-such-fact"])

    def test_duplicate_answer_is_malformed(self):
        self.proposal["answers"].append(copy.deepcopy(self.proposal["answers"][0]))
        with self.assertRaises(ValueError):
            self.check()

    def test_answer_to_unknown_question_is_malformed(self):
        self.proposal["answers"][0]["question_id"] = "no-such-question"
        with self.assertRaises(ValueError):
            self.check()

    def test_unknown_fields_rejected(self):
        self.proposal["submit"] = True
        with self.assertRaises(ValueError):
            self.check()

    def test_bad_schema_version_rejected(self):
        self.proposal["schema_version"] = 2
        with self.assertRaises(ValueError):
            self.check()

    def test_per_answer_limit(self):
        self.proposal["answers"][0]["text"] = "word " * 51
        self.assertIn("answer_over_limit:need", self.check()["blockers"])

    def test_total_limit(self):
        self.proposal["limits"]["max_total_words"] = 5
        self.assertIn("total_over_limit", self.check()["blockers"])

    def test_placeholder_markers(self):
        for marker in ("{{x}}", "[[x]]", "a ??? b", "TODO", "tbd", "TBC", "xxx"):
            with self.subTest(marker=marker):
                proposal = passing_proposal()
                proposal["answers"][0]["text"] = "Draft text " + marker
                self.assertIn("unresolved_placeholder:answer:need", check_proposal(proposal, self.facts)["blockers"])

    def test_placeholders_scanned_outside_answers(self):
        self.proposal["project"]["summary"] = "Summary with TBD inside."
        self.proposal["budget"]["use_of_funds"] = "Funds buy {{ovens}}."
        result = self.check()
        self.assertIn("unresolved_placeholder:project.summary", result["blockers"])
        self.assertIn("unresolved_placeholder:budget.use_of_funds", result["blockers"])

    def test_claim_mentions_warn_without_blocking(self):
        cases = [("We are eligible for this program.", "eligibility_mention"),
                 ("This is guaranteed funding.", "award_mention"),
                 ("We will be awarded the grant.", "award_mention"),
                 ("We secured grant funding in 2024.", "award_mention"),
                 ("The application has been submitted.", "submission_mention"),
                 ("Submission is complete.", "submission_mention")]
        for text, rule in cases:
            with self.subTest(text=text):
                proposal = passing_proposal()
                proposal["answers"][0]["text"] = text + " Cited context here."
                proposal["answers"][0]["fact_refs"] = ["org-founded"]
                result = check_proposal(proposal, self.facts)
                self.assertIn("claim_to_review:answer:need:" + rule, result["warnings"])
                self.assertEqual(result["blockers"], [])
                self.assertTrue(result["mechanical_checks_passed"])

    def test_truthful_admin_prose_is_not_flagged(self):
        proposal = passing_proposal()
        proposal["answers"][0]["text"] = ("Our board-approved budget lists eligible expenses, and our team "
                                          "is qualified to do this work. Grant funds will be used for ovens.")
        result = check_proposal(proposal, self.facts)
        self.assertEqual(result["warnings"], [])
        self.assertTrue(result["mechanical_checks_passed"])

    def test_funder_prompt_submit_wording_is_not_scanned(self):
        result = self.check()
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["blockers"], [])

    def test_budget_grant_sum_mismatch(self):
        self.proposal["budget"]["lines"][0]["amount"] = "3999.99"
        self.assertIn("budget_sum_mismatch", self.check()["blockers"])

    def test_budget_project_sum_mismatch(self):
        self.proposal["budget"]["total_project"] = "6500.01"
        self.assertIn("budget_project_sum_mismatch", self.check()["blockers"])

    def test_budget_exceeds_max(self):
        self.proposal["limits"]["max_request"] = "4999.99"
        self.assertIn("budget_exceeds_max", self.check()["blockers"])

    def test_budget_unallowable_category(self):
        self.proposal["budget"]["lines"][0]["category"] = "alcohol"
        self.assertIn("budget_unallowable_category:ovens", self.check()["blockers"])

    def test_money_rejects_float_and_bad_strings(self):
        for bad in (5000.00, "5000.000", "-5.00", "five", "", None):
            with self.subTest(bad=bad):
                proposal = passing_proposal()
                proposal["budget"]["lines"][0]["amount"] = bad
                with self.assertRaises(ValueError):
                    check_proposal(proposal, self.facts)

    def test_decimal_arithmetic_is_exact(self):
        proposal = passing_proposal()
        proposal["budget"]["total_requested"] = "0.30"
        proposal["budget"]["total_project"] = None
        proposal["budget"]["lines"] = [
            {"id": "a", "label": "A", "category": "goods", "amount": "0.10", "funding_source": "grant"},
            {"id": "b", "label": "B", "category": "goods", "amount": "0.20", "funding_source": "grant"},
            {"id": "c", "label": "C", "category": "goods", "amount": "6200.00", "funding_source": "other"},
        ]
        proposal["budget"]["total_requested"] = "0.30"
        result = check_proposal(proposal, self.facts)
        self.assertNotIn("budget_sum_mismatch", result["blockers"])
        self.assertEqual(result["budget"]["grant_lines_sum"], "0.30")

    def test_zero_total_requested_rejected(self):
        self.proposal["budget"]["total_requested"] = "0.00"
        with self.assertRaises(ValueError):
            self.check()

    def test_non_usd_rejected(self):
        self.proposal["budget"]["currency"] = "EUR"
        with self.assertRaises(ValueError):
            self.check()

    def test_missing_attachment_blocks(self):
        self.proposal["attachments"] = []
        self.assertIn("missing_attachment:quote", self.check()["blockers"])
        self.proposal["attachments"] = [{"attachment_id": "quote", "status": "missing"}]
        self.assertIn("missing_attachment:quote", self.check()["blockers"])

    def test_optional_attachment_may_stay_missing(self):
        self.assertNotIn("missing_attachment:photo", self.check()["blockers"])

    def test_manifest_without_declaration_is_malformed(self):
        self.proposal["attachments"] = [{"attachment_id": "ghost", "status": "prepared"}]
        with self.assertRaises(ValueError):
            self.check()

    def test_private_fact_in_shared_evidence_blocks(self):
        self.proposal["shared_evidence"] = {"fact_ids": ["year1-projection"]}
        result = self.check()
        self.assertIn("private_fact_in_shared_evidence:year1-projection", result["blockers"])
        self.assertEqual(result["shared_evidence"]["withheld_private"], ["year1-projection"])

    def test_unknown_shared_fact_blocks(self):
        self.proposal["shared_evidence"] = {"fact_ids": ["ghost"]}
        self.assertIn("unknown_shared_fact:ghost", self.check()["blockers"])

    def test_duplicate_shared_fact_is_malformed(self):
        self.proposal["shared_evidence"] = {"fact_ids": ["org-founded", "org-founded"]}
        with self.assertRaises(ValueError):
            self.check()

    def test_check_output_omits_private_fact_values(self):
        self.facts["facts"]["org-founded"]["statement"] = "SENTINEL-PRIVATE-VALUE"
        output = json.dumps(self.check())
        self.assertNotIn("SENTINEL-PRIVATE-VALUE", output)
        self.assertNotIn(self.proposal["answers"][0]["text"], output)

    def test_substantive_review_echoed_unchanged(self):
        self.proposal["substantive_review"] = {"status": "reviewed", "reviewer": "A. Human",
                                               "reviewed_at": "2030-10-02T12:00:00Z", "notes": "Read fully."}
        result = self.check()
        self.assertTrue(result["mechanical_checks_passed"])
        self.assertEqual(result["substantive_review"]["reviewer"], "A. Human")

    def test_substantive_review_states_validated(self):
        bad = [
            {"status": "reviewed", "reviewer": None, "reviewed_at": None},
            {"status": "not_reviewed", "reviewer": "Nobody", "reviewed_at": None},
            {"status": "in_review", "reviewer": None, "reviewed_at": "2030-10-02T12:00:00Z"},
            {"status": "approved", "reviewer": None, "reviewed_at": None},
        ]
        for review in bad:
            with self.subTest(review=review):
                proposal = passing_proposal()
                proposal["substantive_review"] = review
                with self.assertRaises(ValueError):
                    check_proposal(proposal, self.facts)

    def test_mechanical_success_never_says_ready_or_verified(self):
        output = json.dumps(self.check())
        self.assertIsNone(BANNED_OUTPUT.search(output))

    def test_fact_schema_validated(self):
        cases = [
            {"statement": "", "kind": "historical", "visibility": "shareable"},
            {"statement": "x", "kind": "rumor", "visibility": "shareable"},
            {"statement": "x", "kind": "historical", "visibility": "public"},
            {"statement": "x" * 5001, "kind": "historical", "visibility": "private"},
        ]
        for entry in cases:
            with self.subTest(entry=entry):
                facts = passing_facts()
                facts["facts"]["org-founded"] = entry
                with self.assertRaises(ValueError):
                    check_proposal(self.proposal, facts)

    def test_empty_facts_rejected(self):
        with self.assertRaises(ValueError):
            check_proposal(self.proposal, {"schema_version": 1, "facts": {}})

    def test_bad_fact_id_rejected(self):
        facts = passing_facts()
        facts["facts"]["bad id!"] = facts["facts"].pop("org-founded")
        with self.assertRaises(ValueError):
            check_proposal(self.proposal, facts)


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.proposal = passing_proposal()
        self.facts = passing_facts()

    def test_passing_render_marks_status_and_kinds(self):
        text = render_package(self.proposal, self.facts)
        self.assertIn("Mechanical checks: PASS (0 blockers).", text)
        self.assertIn("Substantive review: not_reviewed.", text)
        self.assertIn("### Historical facts", text)
        self.assertIn("### Estimates and projections", text)
        self.assertIn("### Future commitments", text)
        self.assertIn("agent-written drafts", text)
        self.assertIn("(PRIVATE)", text)

    def test_in_review_render_names_reviewer_without_timestamp(self):
        self.proposal["substantive_review"] = {"status": "in_review", "reviewer": "A. Human",
                                               "reviewed_at": None, "notes": ""}
        text = render_package(self.proposal, self.facts)
        self.assertIn("Substantive review: in_review by A. Human.", text)

    def test_render_lists_claim_warnings_as_advisory(self):
        self.proposal["answers"][0]["text"] = "We secured grant funding in 2024 for a prior project."
        text = render_package(self.proposal, self.facts)
        self.assertIn("Mechanical checks: PASS", text)
        self.assertIn("claim_to_review:answer:need:award_mention", text)
        self.assertIn("Advisory only", text)

    def test_failing_render_lists_blockers(self):
        self.proposal["answers"] = []
        text = render_package(self.proposal, self.facts)
        self.assertIn("Mechanical checks: FAIL", text)
        self.assertIn("missing_answer:need", text)

    def test_private_shared_fact_withheld_from_shared_section(self):
        self.proposal["shared_evidence"] = {"fact_ids": ["year1-projection"]}
        text = render_package(self.proposal, self.facts)
        shared = text.split("## Shared evidence candidates")[1].split("## Cited facts appendix")[0]
        appendix = text.split("## Cited facts appendix")[1]
        self.assertIn("withheld from shared evidence", shared)
        self.assertNotIn("15000 meals", shared)
        self.assertIn("15000 meals", appendix)

    def test_render_never_says_ready_or_verified(self):
        self.assertIsNone(BANNED_OUTPUT.search(render_package(self.proposal, self.facts)))

    def test_render_rejects_malformed(self):
        self.proposal["budget"]["currency"] = "EUR"
        with self.assertRaises(ValueError):
            render_package(self.proposal, self.facts)


class CLIProposalTests(unittest.TestCase):
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

    def test_init_check_render_round_trip(self):
        proposal_out = self.root / "draft-proposal.json"
        facts_out = self.root / "draft-facts.json"
        code, output, error = self.invoke("proposal", "init", "--proposal-out", proposal_out,
                                          "--facts-out", facts_out, "--opportunity-id", "cli-x")
        self.assertEqual((code, error), (0, ""))
        self.assertTrue(proposal_out.is_file())
        self.assertTrue(facts_out.is_file())
        code, output, error = self.invoke("proposal", "scaffold", "--proposal-out", proposal_out,
                                          "--facts-out", facts_out, "--overwrite")
        self.assertEqual((code, error), (0, ""))
        check_out = self.root / "check.json"
        code, output, error = self.invoke("proposal", "check", "--proposal", proposal_out,
                                          "--facts", facts_out, "--output", check_out)
        self.assertEqual((code, output, error), (0, "", ""))
        self.assertFalse(json.loads(check_out.read_text(encoding="utf-8"))["mechanical_checks_passed"])
        draft_out = self.root / "draft.md"
        code, output, error = self.invoke("proposal", "render", "--proposal", proposal_out,
                                          "--facts", facts_out, "--output", draft_out)
        self.assertEqual((code, output, error), (0, "", ""))
        self.assertIn("Mechanical checks: FAIL", draft_out.read_text(encoding="utf-8"))

    def test_init_refuses_existing_without_overwrite(self):
        proposal_out = self.json_file("p.json", {"schema_version": 1})
        facts_out = self.root / "f.json"
        code, _, error = self.invoke("proposal", "init", "--proposal-out", proposal_out,
                                     "--facts-out", facts_out)
        self.assertEqual(code, 2)
        self.assertIn("exists", error)
        self.assertFalse(facts_out.exists())

    def test_output_must_not_overwrite_inputs(self):
        proposal = self.json_file("p.json", passing_proposal())
        facts = self.json_file("f.json", passing_facts())
        before = proposal.read_bytes()
        code, _, error = self.invoke("proposal", "check", "--proposal", proposal,
                                     "--facts", facts, "--output", proposal)
        self.assertEqual(code, 2)
        self.assertIn("must not overwrite", error)
        self.assertEqual(proposal.read_bytes(), before)
        code, _, error = self.invoke("proposal", "render", "--proposal", proposal,
                                     "--facts", facts, "--output", facts)
        self.assertEqual(code, 2)
        self.assertIn("must not overwrite", error)

    def test_output_must_not_target_evidence_db(self):
        proposal = self.json_file("p.json", passing_proposal())
        facts = self.json_file("f.json", passing_facts())
        target = self.root / "public.sqlite"
        code, _, error = self.invoke("proposal", "render", "--proposal", proposal,
                                     "--facts", facts, "--output", target)
        self.assertEqual(code, 2)
        self.assertIn("evidence database", error)
        self.assertFalse(target.exists())

    def test_output_must_not_target_symlink_to_evidence_db(self):
        proposal = self.json_file("p.json", passing_proposal())
        facts = self.json_file("f.json", passing_facts())
        real = self.root / "real.sqlite"
        real.write_bytes(b"SQLite format 3\x00" + b"\x00" * 84)
        alias = self.root / "alias.md"
        try:
            alias.symlink_to(real)
        except OSError:
            self.skipTest("symlinks unavailable")
        code, _, error = self.invoke("proposal", "render", "--proposal", proposal,
                                     "--facts", facts, "--output", alias)
        self.assertEqual(code, 2)
        self.assertIn("evidence database", error)
        self.assertEqual(real.read_bytes(), b"SQLite format 3\x00" + b"\x00" * 84)

    def test_output_must_not_target_extensionless_sqlite(self):
        proposal = self.json_file("p.json", passing_proposal())
        facts = self.json_file("f.json", passing_facts())
        target = self.root / "extensionless_store"
        target.write_bytes(b"SQLite format 3\x00" + b"\x00" * 84)
        code, _, error = self.invoke("proposal", "render", "--proposal", proposal,
                                     "--facts", facts, "--output", target)
        self.assertEqual(code, 2)
        self.assertIn("evidence database", error)
        self.assertEqual(target.read_bytes(), b"SQLite format 3\x00" + b"\x00" * 84)

    def test_output_must_not_target_hardlink_alias_of_input(self):
        proposal = self.json_file("p.json", passing_proposal())
        facts = self.json_file("f.json", passing_facts())
        alias = self.root / "hardlink-alias.json"
        try:
            import os
            os.link(proposal, alias)
        except OSError:
            self.skipTest("hardlinks unavailable")
        before = proposal.read_bytes()
        code, _, error = self.invoke("proposal", "check", "--proposal", proposal,
                                     "--facts", facts, "--output", alias)
        self.assertEqual(code, 2)
        self.assertIn("must not overwrite", error)
        self.assertEqual(proposal.read_bytes(), before)

    def test_failed_paths_do_not_expose_private_input(self):
        proposal = self.json_file("p.json", passing_proposal())
        facts = self.root / "bad-facts.json"
        facts.write_text("PRIVATE-INPUT-SENTINEL is malformed", encoding="utf-8")
        output = self.root / "failed-check.json"
        code, stdout, error = self.invoke("proposal", "check", "--proposal", proposal,
                                          "--facts", facts, "--output", output)
        self.assertEqual((code, stdout), (2, ""))
        self.assertNotIn("PRIVATE-INPUT-SENTINEL", error)
        self.assertFalse(output.exists())

    def test_proposal_commands_leave_evidence_db_bytes_untouched(self):
        db = self.root / "evidence.db"
        db.write_bytes(b"sentinel-bytes")
        proposal = self.json_file("p.json", passing_proposal())
        facts = self.json_file("f.json", passing_facts())
        draft = self.root / "draft.md"
        self.assertEqual(self.invoke("proposal", "check", "--proposal", proposal, "--facts", facts)[0], 0)
        self.assertEqual(self.invoke("proposal", "render", "--proposal", proposal,
                                     "--facts", facts, "--output", draft)[0], 0)
        self.assertEqual(db.read_bytes(), b"sentinel-bytes")
        self.assertEqual(list(self.root.glob("*.db")), [db])


class WorkedExampleTests(unittest.TestCase):
    def test_shipped_example_reports_only_honest_attachment_gaps(self):
        proposal = json.loads((ROOT / "examples" / "proposal.json").read_text(encoding="utf-8"))
        facts = json.loads((ROOT / "examples" / "proposal-facts.json").read_text(encoding="utf-8"))
        result = check_proposal(proposal, facts)
        self.assertFalse(result["mechanical_checks_passed"])
        self.assertEqual(result["blockers"], ["missing_attachment:501c3-letter",
                                              "missing_attachment:equipment-quote"])
        self.assertEqual(result["warnings"], [])

    def test_shipped_snapshots_are_readable_and_consistent(self):
        check_snapshot = ROOT / "examples" / "proposal-check.json"
        draft_snapshot = ROOT / "examples" / "proposal-draft.md"
        self.assertTrue(check_snapshot.is_file())
        self.assertTrue(draft_snapshot.is_file())
        snapshot = json.loads(check_snapshot.read_text(encoding="utf-8"))
        self.assertFalse(snapshot["mechanical_checks_passed"])
        self.assertEqual(snapshot["warnings"], [])
        draft = draft_snapshot.read_text(encoding="utf-8")
        self.assertIn("Mechanical checks: FAIL", draft)
        self.assertIn("missing_attachment:equipment-quote", draft)
        self.assertIn("SYNTHETIC", draft)
        self.assertIn("Estimates and projections", draft)

    def test_shipped_example_contains_no_unsupplied_embellishments(self):
        text = (ROOT / "examples" / "proposal.json").read_text(encoding="utf-8")
        for phrase in ("turn away", "families", "seniors", "failing", "six volunteers",
                       "five days", "closed week", "manager schedules", "vendor handles",
                       "safety checklist", "quote supports", "current menu", "current staff",
                       "busy nights", "2029", "2030"):
            self.assertNotIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
