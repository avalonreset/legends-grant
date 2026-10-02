import hashlib
import json
import socket
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from grant_engine.core import canonical
from grant_engine.documents import (DocumentError, FetchResponse, collect_document,
                                    public_url, verify_bundle)


URL = "https://example.gov/notices/2026"


def public_dns(*args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))]


class DocumentsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def collect(self, body=b"Public notice", content_type="text/plain", **options):
        return collect_document(URL, self.root, resolver=public_dns,
            transport=lambda *args: FetchResponse(200, {"content-type": content_type}, body), **options)

    def test_html_extraction_links_and_honest_completeness(self):
        result = self.collect(b'<h1>Grant &amp; training</h1><script>SECRET SCRIPT</script><p>Apply now. Applications require a full budget and matching funds.</p><a href="../terms.pdf">Terms</a><a href="https://example.gov/x?api_key=secret">Bad</a>', "text/html")
        self.assertTrue(result["ok"])
        self.assertFalse(result["notice_complete"])
        self.assertEqual(result["authority"], "unassessed")
        doc = result["document"]
        text = (self.root / doc["text"]["path"]).read_text()
        self.assertIn("Grant & training", text)
        self.assertNotIn("SECRET SCRIPT", text)
        self.assertEqual(doc["links"], ["https://example.gov/terms.pdf"])
        self.assertEqual(doc["link_details"][0]["label"], "Terms")
        self.assertFalse(doc["links_fetched"])
        self.assertTrue(verify_bundle(self.root)["ok"])

    def test_content_addressing_reuses_raw_artifact(self):
        a, b = self.collect(), self.collect()
        self.assertEqual(a["document"]["raw"], b["document"]["raw"])
        self.assertEqual(verify_bundle(self.root)["artifacts"], 2)

    def test_corrupted_artifact_is_detected_and_not_overwritten(self):
        result = self.collect()
        raw_path = self.root / result["document"]["raw"]["path"]
        raw_path.write_bytes(b"tampered")
        self.assertFalse(verify_bundle(self.root)["ok"])
        self.assertFalse(self.collect()["ok"])
        self.assertEqual(raw_path.read_bytes(), b"tampered")

    def test_manifest_corruption_and_empty_bundle_fail(self):
        self.assertFalse(verify_bundle(self.root)["ok"])
        result = self.collect()
        (self.root / result["receipt_path"]).write_bytes(b"{}")
        self.assertFalse(verify_bundle(self.root)["ok"])

    def test_pdf_missing_dependency_preserves_bytes(self):
        with patch.dict("sys.modules", {"pypdf": None}):
            result = self.collect(b"%PDF-1.7\nfixture", "application/pdf")
        self.assertFalse(result["ok"])
        self.assertTrue(result["retrieved"])
        self.assertEqual(result["document"]["extraction_status"], "blocked_pdf_dependency")
        self.assertTrue(verify_bundle(self.root)["ok"])

    def test_pdf_worker_timeout_preserves_raw_and_is_explicit(self):
        with patch.dict("sys.modules", {"pypdf": object()}), patch("grant_engine.documents.subprocess.run", side_effect=subprocess.TimeoutExpired("parser", 15)):
            result = self.collect(b"%PDF-1.7\nfixture", "application/pdf")
        self.assertFalse(result["ok"])
        self.assertTrue(result["retrieved"])
        self.assertEqual(result["document"]["extraction_status"], "blocked_pdf_timeout")

    def test_pdf_worker_limits_are_not_success(self):
        for status in ("blocked_pdf_page_limit", "blocked_pdf_text_limit", "blocked_scan_requires_ocr", "blocked_encrypted_pdf"):
            process = subprocess.CompletedProcess([], 0, json.dumps({"text": "", "status": status}).encode())
            with patch.dict("sys.modules", {"pypdf": object()}), patch("grant_engine.documents.subprocess.run", return_value=process):
                result = self.collect(b"%PDF-1.7\nfixture", "application/pdf")
            self.assertFalse(result["ok"])
            self.assertEqual(result["document"]["extraction_status"], status)

    def test_base_href_and_table_cells(self):
        result = self.collect(b'<head><base href="/grant-files/"></head><table><tr><td>Match</td><td>20%</td></tr></table><a href="terms.pdf">terms</a>', "text/html")
        self.assertEqual(result["document"]["links"], ["https://example.gov/grant-files/terms.pdf"])
        self.assertIn("Match\n20%", (self.root / result["document"]["text"]["path"]).read_text())

    def test_real_world_box_shell_is_blocked_not_document_success(self):
        result = self.collect(b'<html><head><title>Box</title><link rel="stylesheet" href="/assets/app.css"></head><body><script src="app.js"></script></body></html>', "text/html")
        self.assertTrue(result["retrieved"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["document"]["extraction_status"], "blocked_insufficient_html_text")
        self.assertEqual(result["document"]["links"], [])

    def test_html_challenge_is_explicitly_blocked(self):
        result = self.collect(b'<h1>Checking your browser</h1><p>Please verify you are human to continue to this website.</p>', "text/html")
        self.assertFalse(result["ok"])
        self.assertEqual(result["document"]["extraction_status"], "blocked_interactive_html")

    def test_plain_text_visible_url_inventory(self):
        result = self.collect(b'See https://example.gov/terms.pdf and https://example.gov?token=SECRET')
        self.assertEqual(result["document"]["links"], ["https://example.gov/terms.pdf"])

    def test_unsupported_format_preserved_honestly(self):
        result = self.collect(b"binary spreadsheet", "application/vnd.ms-excel")
        self.assertTrue(result["retrieved"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["document"]["extraction_status"], "blocked_unsupported_format")

    def test_empty_and_oversize_are_failures(self):
        for body, bounds in ((b"", {}), (b"12345", {"max_bytes": 4})):
            with self.subTest(body=body):
                result = self.collect(body, **bounds)
                self.assertFalse(result["ok"])
                self.assertFalse(result["retrieved"])
                self.assertTrue(result["errors"])

    def test_bad_encoding_is_not_silently_replaced(self):
        result = self.collect(b"\xffhello")
        self.assertEqual(result["document"]["extraction_status"], "blocked_text_encoding")

    def test_credential_input_not_written_to_receipt(self):
        for url in ("https://user:TOPSECRET@example.gov", "https://example.gov?X-Amz-Signature=TOPSECRET", "https://example.gov?access_token=TOPSECRET"):
            result = collect_document(url, self.root, resolver=public_dns)
            self.assertFalse(result["ok"])
            self.assertNotIn("TOPSECRET", canonical(result))
            self.assertNotIn("TOPSECRET", (self.root / result["receipt_path"]).read_text())

    def test_private_query_keys_match_store_and_never_reach_transport(self):
        for key in ("ssn", "ein", "bank_account", "client_id", "applicant", "profile", "applicant_profile", "profile[ssn]", "profile%5Bname%5D", "data[ssn]", "ssn123"):
            calls = []
            url = "https://example.gov/notice?" + key + "=TOPSECRET"
            result = collect_document(url, self.root, resolver=public_dns, transport=lambda *args: calls.append(args))
            self.assertFalse(result["ok"], key)
            self.assertEqual(calls, [])
            self.assertNotIn("TOPSECRET", canonical(result))
            self.assertNotIn("TOPSECRET", (self.root / result["receipt_path"]).read_text())

    def test_nonsecret_public_query_parameters_still_work(self):
        self.assertEqual(public_url("https://example.gov/notice?state=PA&year=2026&page=1&program_id=abc"), "https://example.gov/notice?state=PA&year=2026&page=1&program_id=abc")

    def test_login_forms_are_blocked_even_with_substantial_text(self):
        boilerplate = b'<p>Welcome to the grant management system. Search our program information and applicant resources.</p>'
        for form in (b'<form><input type="password"></form>', b'<form action="/account/login"><input name="email"></form>', b'<form id="sign-in"><button>Continue</button></form>'):
            result = self.collect(boilerplate + form, "text/html")
            self.assertTrue(result["retrieved"])
            self.assertFalse(result["ok"])
            self.assertEqual(result["document"]["extraction_status"], "blocked_login_html")

    def test_login_required_context_is_blocked(self):
        result = self.collect(b'<h1>Applicant portal</h1><p>Please sign in to view this document. You may contact our help desk for account assistance.</p>', "text/html")
        self.assertFalse(result["ok"])
        self.assertEqual(result["document"]["extraction_status"], "blocked_login_html")

    def test_ordinary_login_link_does_not_claim_content_is_login_page(self):
        result = self.collect(b'<h1>Public grant notice</h1><p>Eligible organizations may apply for funding by the published deadline.</p><a href="/login">Login</a>', "text/html")
        self.assertTrue(result["ok"])
        self.assertTrue(result["content_review_required"])

    def test_public_url_rejections(self):
        for url in ("http://example.gov", "file:///tmp/a", "https://localhost", "https://example.internal", "https://127.0.0.1", "https://169.254.169.254/latest", "https://[::1]", "https://example.gov:8443", "https://example.gov/\r\nx"):
            with self.subTest(url=url), self.assertRaises(DocumentError):
                public_url(url)

    def test_dns_private_and_mixed_answers_never_call_transport(self):
        for addresses in (["127.0.0.1"], ["8.8.8.8", "10.0.0.1"]):
            calls = []
            dns = lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443)) for ip in addresses]
            result = collect_document(URL, self.root, resolver=dns, transport=lambda *a: calls.append(a))
            self.assertFalse(result["ok"])
            self.assertEqual(calls, [])

    def test_safe_redirect_collected_with_provenance(self):
        calls = []
        def fetch(url, *args):
            calls.append(url)
            if url == URL:
                return FetchResponse(302, {"Location": "/final"}, b"")
            return FetchResponse(200, {"Content-Type": "text/plain"}, b"Amended grant")
        result = collect_document(URL, self.root, resolver=public_dns, transport=fetch)
        self.assertTrue(result["ok"])
        self.assertEqual(len(calls), 2)
        self.assertEqual(result["document"]["url"], "https://example.gov/final")
        self.assertEqual(len(result["redirects"]), 1)

    def test_redirect_to_private_dns_is_blocked(self):
        calls = []
        def dns(host, *args, **kwargs):
            return public_dns() if host == "example.gov" else [(2, 1, 6, "", ("10.0.0.1", 443))]
        def fetch(url, *args):
            calls.append(url)
            return FetchResponse(302, {"location": "https://internal.example.gov/"}, b"")
        result = collect_document(URL, self.root, resolver=dns, transport=fetch)
        self.assertFalse(result["ok"])
        self.assertEqual(calls, [URL])

    def test_redirect_credentials_are_not_persisted(self):
        result = collect_document(URL, self.root, resolver=public_dns, transport=lambda *args: FetchResponse(302, {"location": "https://example.gov?token=TOPSECRET"}, b""))
        self.assertFalse(result["ok"])
        self.assertNotIn("TOPSECRET", canonical(result))

    def test_redirect_loop_and_limit(self):
        for limit in (0, 3):
            result = collect_document(URL, self.root, resolver=public_dns, max_redirects=limit, transport=lambda *args: FetchResponse(302, {"location": URL}, b""))
            self.assertFalse(result["ok"])

    def test_timeout_error_is_receipted_without_exception_details(self):
        def timeout(*args):
            raise TimeoutError("TOPSECRET diagnostic")
        result = collect_document(URL, self.root, resolver=public_dns, transport=timeout)
        self.assertFalse(result["ok"])
        self.assertEqual(result["errors"][0]["error_type"], "TimeoutError")
        self.assertNotIn("TOPSECRET", canonical(result))

    def test_http_errors_are_not_empty_success(self):
        for status in (204, 403, 404, 429, 503):
            result = collect_document(URL, self.root, resolver=public_dns, transport=lambda *args: FetchResponse(status, {}, b"failure"))
            self.assertFalse(result["ok"])
            self.assertFalse(result["retrieved"])
            self.assertEqual(result["errors"][0]["code"], "http_status_" + str(status))

    def test_compressed_response_refused(self):
        result = collect_document(URL, self.root, resolver=public_dns, transport=lambda *args: FetchResponse(200, {"content-encoding": "gzip"}, b"fixture"))
        self.assertFalse(result["ok"])

    def test_truncated_or_invalid_content_length_is_not_success(self):
        for length in ("100000", "-1", "39, 100000", "invalid"):
            result = collect_document(URL, self.root, resolver=public_dns, transport=lambda *args: FetchResponse(200, {"content-type": "text/plain", "content-length": length}, b"Eligible applicants include nonprofits."))
            self.assertFalse(result["ok"])
            self.assertFalse(result["retrieved"])

    def test_path_escape_even_in_rehashed_receipt_refused(self):
        result = self.collect()
        receipt = json.loads((self.root / result["receipt_path"]).read_bytes())
        receipt["document"]["raw"]["path"] = "../../private.txt"
        data = canonical(receipt).encode()
        (self.root / "receipts" / (hashlib.sha256(data).hexdigest() + ".json")).write_bytes(data)
        self.assertFalse(verify_bundle(self.root)["ok"])

    def test_limits_rejected_before_io(self):
        for options in ({"max_bytes": 0}, {"timeout": 0}, {"max_redirects": 11}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.collect(**options)


if __name__ == "__main__":
    unittest.main()
