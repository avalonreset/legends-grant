"""End-to-end CLI contracts with real local files; only collection I/O is mocked."""
import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from grant_engine import __version__
from grant_engine.__main__ import REGISTRY, main
from grant_engine.documents import FetchResponse


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "qualification-review.json"


class CLIWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.db = self.root / "public.db"

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

    def seed(self):
        record = {"source_id": "commongrants-pa", "program_id": "fixture-workforce", "cycle_id": "2030",
                  "title": "Synthetic rural workforce training", "record_type": "opportunity", "status": "open",
                  "url": "https://example.org/synthetic-notice", "retrieved_at": "2020-10-01T12:00:00Z",
                  "evidence": {"common_grants_item": {"description": "Synthetic employee training award"}},
                  "metadata": {"authority": "third-party-normalized", "is_confirmed_grant": False}}
        path = self.json_file("seed.json", {"records": [record]})
        code, output, error = self.invoke("ingest", "--db", self.db, "--input", path)
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(json.loads(output)["revisions_added"], 1)
        return record

    def test_offline_doctor_default_packaged_registry_and_version_outside_repo(self):
        self.assertTrue(REGISTRY.is_file())
        self.assertEqual(REGISTRY.parent.parent.name, "grant_engine")
        # Packaged registry resolution must not depend on the repository cwd.
        with contextlib.chdir(self.root):
            code, output, error = self.invoke("doctor")
            self.assertEqual((code, error), (0, ""))
            report = json.loads(output)
            self.assertTrue(report["ok"])
            self.assertFalse(report["network_tested"])
            self.assertEqual(report["version"], __version__)
            self.assertGreaterEqual(report["sources"], 100)
            code, output, error = self.invoke("plan", "--jurisdiction", "PA", "--applicant-type", "nonprofit")
            self.assertEqual((code, error), (0, ""))
            routes = json.loads(output)
            self.assertGreater(len(routes["sources"]), 0)
            self.assertEqual(routes["qualification"], "unassessed")
            code, output, error = self.invoke("--version")
            self.assertEqual((code, output.strip(), error), (0, __version__, ""))

    def test_ingest_search_export_change_and_replay_workflow(self):
        record = self.seed()
        before, after = self.root / "before.json", self.root / "after.json"
        self.assertEqual(self.invoke("export", "--db", self.db, "--output", before)[0], 0)
        code, output, error = self.invoke("search", "--db", self.db, "--query", "rural training", "--status", "open", "--record-type", "opportunity", "--jurisdiction", "PA")
        self.assertEqual((code, error), (0, ""))
        hit = json.loads(output)["results"][0]
        self.assertEqual(hit["source_id"], record["source_id"])
        self.assertEqual(hit["authority"], "third-party-normalized")
        self.assertEqual(hit["eligibility"], "unassessed")
        revision = copy.deepcopy(record)
        revision["status"] = "closed"
        revision["retrieved_at"] = "2020-10-02T12:00:00Z"
        revision["metadata"]["close_date_raw"] = "2030-10-02"
        path = self.json_file("revision.json", {"records": [revision]})
        self.assertEqual(self.invoke("ingest", "--db", self.db, "--input", path)[0], 0)
        self.assertEqual(self.invoke("export", "--db", self.db, "--output", after)[0], 0)
        code, output, error = self.invoke("changes", "--before", before, "--after", after)
        self.assertEqual((code, error), (0, ""))
        delta = json.loads(output)
        self.assertEqual(delta["counts"]["changed"], 1)
        self.assertIn("/status", delta["changes"][0]["changed_fields"])
        self.assertIn("/metadata/close_date_raw", delta["changes"][0]["changed_fields"])
        self.assertFalse(delta["changes"][0]["closure_inferred"])
        replay = self.root / "replay.db"
        self.assertEqual(self.invoke("replay", "--db", replay, "--input", after)[0], 0)
        code, output, error = self.invoke("check", "--db", replay)
        self.assertEqual((code, error), (0, ""))
        self.assertTrue(json.loads(output)["ok"])
        self.assertEqual(self.invoke("export", "--db", replay)[1], self.invoke("export", "--db", self.db)[1])

    def test_collect_extract_verify_and_detect_tampering(self):
        bundle = self.root / "documents"
        body = b'<h1>Synthetic grant notice</h1><p>Employees receive training.</p><a href="/attachment.pdf">Rules</a>'
        with patch("grant_engine.documents._addresses", return_value=["93.184.216.34"]), patch(
            "grant_engine.documents._fetch", return_value=FetchResponse(200, {"content-type": "text/html; charset=utf-8"}, body)
        ) as network:
            code, output, error = self.invoke("collect-document", "--url", "https://example.org/notice", "--bundle", bundle)
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(network.call_count, 1)
        receipt = json.loads(output)
        self.assertTrue(receipt["ok"])
        self.assertFalse(receipt["notice_complete"])
        self.assertEqual(receipt["document"]["links"], ["https://example.org/attachment.pdf"])
        self.assertFalse(receipt["document"]["links_fetched"])
        self.assertEqual(self.invoke("verify-documents", "--bundle", bundle)[0], 0)
        extracted = bundle / receipt["document"]["text"]["path"]
        self.assertIn("Employees receive training", extracted.read_text(encoding="utf-8"))
        extracted.write_text("altered fixture", encoding="utf-8")
        code, output, error = self.invoke("verify-documents", "--bundle", bundle)
        self.assertEqual((code, error), (2, ""))
        self.assertFalse(json.loads(output)["ok"])

    def test_review_example_uses_separate_private_facts_and_preserves_public_store(self):
        self.seed()
        original_export = self.invoke("export", "--db", self.db)[1]
        db_bytes = self.db.read_bytes()
        facts = self.json_file("private-facts.json", {"entity_type": "nonprofit", "state": "PA", "cash_match": 5000,
                                                       "internal_reference": "PRIVATE-FACT-SENTINEL"})
        assessment = self.root / "private-assessment.json"
        code, output, error = self.invoke("review", "--review", EXAMPLE, "--facts", facts,
                                          "--as-of", "2030-10-02T12:00:00Z", "--output", assessment)
        self.assertEqual((code, output, error), (0, "", ""))
        result = json.loads(assessment.read_text(encoding="utf-8"))
        self.assertEqual(result["decision"], "eligible-for-review")
        self.assertEqual({entry["id"] for entry in result["application_checklist"]}, {"project-narrative", "budget"})
        self.assertNotIn("PRIVATE-FACT-SENTINEL", assessment.read_text(encoding="utf-8"))
        self.assertEqual(self.db.read_bytes(), db_bytes)
        self.assertEqual(self.invoke("export", "--db", self.db)[1], original_export)
        self.assertEqual(list(self.root.glob("*.db")), [self.db])
        # Unknown facts remain unresolved even if the proposed review says pass.
        facts.write_text('{"entity_type":"nonprofit","state":"PA"}', encoding="utf-8")
        self.assertEqual(self.invoke("review", "--review", EXAMPLE, "--facts", facts,
                                     "--as-of", "2030-10-02T12:00:00Z", "--output", assessment)[0], 0)
        result = json.loads(assessment.read_text(encoding="utf-8"))
        self.assertEqual(result["decision"], "unresolved")
        self.assertTrue(result["blockers"])

    def test_discovery_never_ignores_query_and_requires_federal_query(self):
        path = self.root / "should-not-exist.json"
        code, output, error = self.invoke("discover", "common-grants", "--query", "housing", "--output", path)
        self.assertEqual((code, output), (2, ""))
        self.assertIn("does not support --query", error)
        self.assertFalse(path.exists())
        code, output, error = self.invoke("discover", "grants-gov", "--output", path)
        self.assertEqual((code, output), (2, ""))
        self.assertIn("requires --query", error)
        self.assertFalse(path.exists())

    def test_json_bound_checked_before_decoding(self):
        from grant_engine.__main__ import InputError, read_json
        oversized = self.root / "oversized.json"
        with oversized.open("wb") as handle:
            handle.seek(50_000_000)
            handle.write(b"x")
        with self.assertRaises(InputError):
            read_json(oversized)

    def test_failed_paths_do_not_create_success_or_expose_private_input(self):
        code, output, error = self.invoke("search", "--db", self.db)
        self.assertEqual((code, output), (2, ""))
        self.assertFalse(self.db.exists())
        self.assertIn("Command failed", error)
        invalid = self.root / "bad-private-input.json"
        invalid.write_text("PRIVATE-INPUT-SENTINEL is malformed", encoding="utf-8")
        output_path = self.root / "failed-review.json"
        code, output, error = self.invoke("review", "--review", EXAMPLE, "--facts", invalid, "--output", output_path)
        self.assertEqual((code, output), (2, ""))
        self.assertNotIn("PRIVATE-INPUT-SENTINEL", error)
        self.assertNotIn(str(invalid), error)
        self.assertFalse(output_path.exists())
        self.assertEqual(self.invoke("verify-documents", "--bundle", self.root / "absent")[0], 2)
        code, output, error = self.invoke("collect-document", "--url", "https://localhost/private", "--bundle", self.root / "failed-bundle")
        self.assertEqual((code, error), (2, ""))
        self.assertFalse(json.loads(output)["ok"])
        self.assertFalse(json.loads(output)["retrieved"])


if __name__ == "__main__":
    unittest.main()
