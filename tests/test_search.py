"""Search/compare tests use real adapter nesting and synthetic public facts."""
import copy
import unittest

from grant_engine.common_grants import discover as common_discover
from grant_engine.core import Store
from grant_engine.grants_gov import discover as federal_discover
from grant_engine.search import compare_packets, search


AS_OF = "2026-10-02T00:00:00Z"


def federal(title="Research training", description="Rural energy innovation"):
    def transport(endpoint, payload):
        if endpoint == "search2":
            return {"hitCount": 1, "oppHits": [{"id": "123", "title": title, "oppStatus": "posted", "closeDate": "12/31/2026"}]}
        return {"id": 123, "synopsis": {"synopsisDesc": description}}
    record = federal_discover("energy", transport=transport)["records"][0]
    record["retrieved_at"] = "2026-10-01T00:00:00Z"
    return record


def common(state="pa", **changes):
    item = {"id": "abc", "title": "Workforce renewal", "description": "<p>Training for clean energy &amp; rural employers.</p>",
            "source": "https://example.gov/notice", "status": {"value": "open"},
            "customFields": {"fundingInstrument": {"value": "loan", "type": "string"}}}
    item.update(changes)
    def transport(url):
        return {"items": [item], "paginationInfo": {"page": 1, "pageSize": 25, "totalPages": 1, "totalItems": 1}}
    record = common_discover("https://" + state + ".api.cg.a6lab.ai", "commongrants-" + state, transport=transport)["records"][0]
    record["retrieved_at"] = "2026-10-01T00:00:00Z"
    return record


def packet(*records):
    return {"schema_version": 2, "records": list(records), "runs": []}


class SearchTests(unittest.TestCase):
    def test_current_store_exports_and_adapters_end_to_end(self):
        store = Store(":memory:")
        try:
            store.ingest(packet(federal(), common()))
            result = search(store.export(), "RURAL energy", as_of=AS_OF)
            self.assertEqual(result["matched_count"], 2)
            self.assertEqual(result["eligibility"], "unassessed")
            self.assertTrue(all(item["eligibility"] == "unassessed" for item in result["results"]))
            self.assertIn("& rural", next(item for item in result["results"] if item["source_id"] == "commongrants-pa")["description"])
        finally:
            store.close()

    def test_title_weight_and_deterministic_tie(self):
        result = search(packet(common(), federal(title="Energy workforce")), "energy", as_of=AS_OF)
        self.assertEqual(result["results"][0]["source_id"], "grants-gov")
        self.assertEqual(result["results"][0]["relevance_score"], 5)
        self.assertEqual(result["results"][1]["relevance_score"], 1)

    def test_ties_prefer_observed_open_without_hiding_closed(self):
        closed, opened = common("ca"), common("pa")
        closed["status"] = "closed"
        result = search(packet(closed, opened), "energy", as_of=AS_OF)
        self.assertEqual([item["status"] for item in result["results"]], ["open", "closed"])

    def test_missing_federal_detail_warning_survives_store_ingest(self):
        partial = federal()
        partial["evidence"]["detail"] = None
        store = Store(":memory:")
        try:
            store.ingest(packet(partial))
            result = search(store.export(), "training", as_of=AS_OF)["results"][0]
            self.assertIn("missing_detail", result["warnings"])
            self.assertIn("missing_detail", result["labels"])
        finally:
            store.close()

    def test_source_eligibility_is_searchable_but_unassessed_metadata_is_not(self):
        fed = federal()
        fed["evidence"]["detail"]["synopsis"]["applicantEligibilityDesc"] = "Tribal organizations with wetlands research"
        state = common()
        state["evidence"]["common_grants_item"]["customFields"]["eligibility"] = {"type": "string", "value": "Municipal utilities"}
        state["evidence"]["common_grants_item"]["restrictions"] = "Applicants located in Jefferson County"
        state["evidence"]["common_grants_item"]["acceptedApplicantTypes"] = ["nonprofits"]
        for query, expected_source in (("tribal wetlands", "grants-gov"), ("municipal utilities", "commongrants-pa"),
                                       ("jefferson", "commongrants-pa"), ("nonprofits", "commongrants-pa")):
            with self.subTest(query=query):
                result = search(packet(fed, state), query, as_of=AS_OF)
                self.assertEqual(result["matched_count"], 1)
                self.assertEqual(result["results"][0]["source_id"], expected_source)
                self.assertEqual(result["results"][0]["eligibility"], "unassessed")
        self.assertEqual(search(packet(fed, state), "unassessed", as_of=AS_OF)["matched_count"], 0)

    def test_missing_and_insecure_notice_urls_warn(self):
        missing, insecure = common("ca"), common("pa")
        missing["metadata"]["official_notice_url_available"] = False
        insecure["url"] = "http://example.org/notice"
        result = search(packet(missing, insecure), as_of=AS_OF)
        by_source = {item["source_id"]: item for item in result["results"]}
        self.assertIn("official_notice_url_missing", by_source["commongrants-ca"]["warnings"])
        self.assertIn("insecure_notice_url", by_source["commongrants-pa"]["warnings"])
        self.assertEqual(by_source["commongrants-pa"]["url"], "http://example.org/notice")

    def test_all_terms_required_not_substring_or_url(self):
        source = common()
        source["url"] = "https://example.gov/zebra"
        for query in ("energy zebra", "train", "missing"):
            self.assertEqual(search(packet(source), query, as_of=AS_OF)["matched_count"], 0)

    def test_unknown_closed_and_historical_labels_are_visible(self):
        unknown, closed, history = common(), common("ca"), common("md")
        unknown["status"] = "unknown"
        closed["status"] = "closed"
        history["record_type"] = "historical_award"
        results = search(packet(unknown, closed, history), as_of=AS_OF)["results"]
        by_id = {item["source_id"]: item for item in results}
        self.assertIn("status_unknown", by_id["commongrants-pa"]["labels"])
        self.assertIn("not_observed_open", by_id["commongrants-ca"]["labels"])
        self.assertIn("not_an_opportunity_record", by_id["commongrants-md"]["labels"])
        filtered = search(packet(unknown, closed, history), record_type="historical_award", status="open", as_of=AS_OF)
        self.assertEqual(filtered["matched_count"], 1)

    def test_authority_and_loan_preserved(self):
        result = search(packet(common()), as_of=AS_OF)["results"][0]
        self.assertEqual(result["authority"], "third-party-normalized")
        self.assertIn("loan_or_mixed_instrument", result["labels"])
        self.assertIn("grant_instrument_unconfirmed", result["labels"])
        self.assertEqual(result["instrument_raw"]["value"], "loan")

    def test_jurisdiction_routing_keeps_unknown_and_national(self):
        unknown = common("md")
        unknown["source_id"] = "unmapped"
        result = search(packet(common(), common("ca"), federal(), unknown), jurisdiction="pa", as_of=AS_OF)
        self.assertEqual({item["source_id"] for item in result["results"]}, {"commongrants-pa", "grants-gov", "unmapped"})
        self.assertEqual(next(item for item in result["results"] if item["source_id"] == "unmapped")["jurisdiction_match"], "unknown")

    def test_age_is_not_open_status(self):
        old = common()
        old["retrieved_at"] = "2025-01-01T00:00:00Z"
        result = search(packet(old), status="open", as_of=AS_OF)["results"][0]
        self.assertEqual(result["status"], "open")
        self.assertEqual(result["freshness"], "stale")
        future = search(packet(common()), as_of="2026-09-01T00:00:00Z")["results"][0]
        self.assertEqual(future["freshness"], "future_observation")

    def test_nationwide_aliases_include_state_and_federal_sources(self):
        for jurisdiction in ("US", "usa", "NATIONAL", "ALL", "*"):
            with self.subTest(jurisdiction=jurisdiction):
                result = search(packet(common(), common("ca"), federal()), jurisdiction=jurisdiction, as_of=AS_OF)
                self.assertEqual(result["matched_count"], 3)
                self.assertIsNone(result["filters"]["jurisdiction"])

    def test_bounds_and_filters(self):
        result = search(packet(common(), federal()), limit=1, as_of=AS_OF)
        self.assertEqual(result["matched_count"], 2)
        self.assertEqual(result["returned_count"], 1)
        self.assertTrue(result["truncated"])
        for arguments in ({"limit": 0}, {"limit": True}, {"limit": 1001}, {"query": "x" * 1001},
                          {"status": "approved"}, {"record_type": "loan"}, {"stale_days": 0},
                          {"as_of": "2026-10-02"}, {"query": "!!!"}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                search(packet(common()), **arguments)

    def test_duplicate_history_and_credentials_rejected(self):
        original = common()
        with self.assertRaises(ValueError):
            search(packet(original, original), as_of=AS_OF)
        original["evidence"]["api_key"] = "fixture"
        with self.assertRaises(ValueError):
            search(packet(original), as_of=AS_OF)

    def test_search_does_not_mutate_input(self):
        source = packet(common(), federal())
        previous = copy.deepcopy(source)
        search(source, "energy", as_of=AS_OF)
        self.assertEqual(previous, source)


class ComparisonTests(unittest.TestCase):
    def test_retrieval_and_feed_pagination_do_not_count(self):
        before = common()
        after = copy.deepcopy(before)
        after["retrieved_at"] = "2026-10-02T00:00:00Z"
        after["evidence"]["feed_url"] = "https://pa.api.cg.a6lab.ai/common-grants/opportunities?page=2"
        report = compare_packets(packet(before), packet(after))
        self.assertEqual(report["counts"]["unchanged"], 1)
        self.assertEqual(report["changes"], [])

    def test_material_deadline_and_metadata_changes(self):
        before = federal()
        after = copy.deepcopy(before)
        after["metadata"]["close_date_raw"] = "01/31/2027"
        after["status"] = "closed"
        after["evidence"]["detail"]["synopsis"]["synopsisDesc"] = "Amendment changes eligibility."
        result = compare_packets(packet(before), packet(after))["changes"][0]
        self.assertEqual(result["change"], "changed")
        self.assertIn("/metadata/close_date_raw", result["changed_fields"])
        self.assertIn("/status", result["changed_fields"])
        self.assertIn("/evidence/detail/synopsis/synopsisDesc", result["changed_fields"])
        self.assertEqual(result["source_id"], "grants-gov")
        self.assertNotEqual(result["before_hash"], result["after_hash"])

    def test_absence_and_outage_never_infer_closure(self):
        after = packet()
        after["runs"] = [{"source_id": "commongrants-pa", "complete": False, "errors": [{"error_type": "TimeoutError"}]}]
        result = compare_packets(packet(common()), after)["changes"][0]
        self.assertEqual(result["change"], "no_longer_observed")
        self.assertEqual(result["last_observed_status"], "open")
        self.assertIsNone(result["current_status"])
        self.assertFalse(result["closure_inferred"])

    def test_identity_keeps_sources_and_cycles_separate(self):
        before = common()
        after = copy.deepcopy(before)
        after["cycle_id"] = "next"
        report = compare_packets(packet(before), packet(after, common("ca")))
        self.assertEqual(report["counts"], {"added": 2, "changed": 0, "no_longer_observed": 1, "unchanged": 0})

    def test_change_count_not_truncated(self):
        result = compare_packets(packet(), packet(common(), federal()), limit=1)
        self.assertEqual(result["counts"]["added"], 2)
        self.assertEqual(result["change_count"], 2)
        self.assertEqual(result["returned_count"], 1)
        self.assertTrue(result["truncated"])

    def test_missing_null_and_boolean_number_material_changes_reported(self):
        before = common()
        after = copy.deepcopy(before)
        after["metadata"]["new_field"] = None
        after["metadata"]["is_confirmed_grant"] = 0
        result = compare_packets(packet(before), packet(after))["changes"][0]
        self.assertIn("/metadata/new_field", result["changed_fields"])
        self.assertIn("/metadata/is_confirmed_grant", result["changed_fields"])

    def test_history_rejected_and_input_unchanged(self):
        before = packet(common())
        after = copy.deepcopy(before)
        compare_packets(before, after)
        self.assertEqual(before, after)
        with self.assertRaises(ValueError):
            compare_packets(packet(common(), common()), after)


if __name__ == "__main__":
    unittest.main()
