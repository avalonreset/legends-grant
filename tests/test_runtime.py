import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from grant_engine.__main__ import main
from grant_engine.core import Store, normalize, plan, public_only, report
from grant_engine.grants_gov import discover
from grant_engine.common_grants import discover as discover_common, NoRedirect


def record(**changes):
    item = {"source_id": "state-pa", "program_id": "workforce", "cycle_id": "2026", "title": "Training", "status": "open", "url": "https://example.gov/grant", "retrieved_at": "2020-10-01T00:00:00Z", "evidence": {"notice": "Synthetic fixture"}}
    item.update(changes)
    return item


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(":memory:")

    def tearDown(self):
        self.store.close()

    def test_idempotent_and_new_retrieval(self):
        self.assertEqual(self.store.ingest([record()]), 1)
        self.assertEqual(self.store.ingest([record(retrieved_at="2020-10-02T00:00:00Z")]), 0)

    def test_revisions_revert_to_previous_value(self):
        for day, status in enumerate(("open", "closed", "open"), 1):
            self.store.ingest([record(status=status, retrieved_at=f"2020-10-0{day}T00:00:00Z")])
        self.assertEqual(len(self.store.export(True)["records"]), 3)
        self.assertEqual(self.store.export()["records"][0]["status"], "open")

    def test_atomic_invalid_record(self):
        with self.assertRaises(ValueError):
            self.store.ingest([record(), {"title": "incomplete"}])
        self.assertEqual(self.store.export()["records"], [])

    def test_atomic_invalid_run(self):
        with self.assertRaises(KeyError):
            self.store.ingest({"records": [record()], "run": {}})
        self.assertEqual(self.store.export()["records"], [])

    def test_cycles_and_sources_do_not_merge(self):
        self.store.ingest([record(), record(cycle_id="2027"), record(source_id="state-md")])
        self.assertEqual(len(self.store.export()["records"]), 3)

    def test_outage_never_closes(self):
        self.store.ingest([record()])
        self.store.ingest({"records": [], "run": {"source_id": "state-pa", "fetched_at": "2020-10-02T00:00:00Z", "complete": False, "errors": [{"error_type": "TimeoutError"}]}})
        self.assertEqual(self.store.export()["records"][0]["status"], "open")
        self.assertFalse(self.store.export()["runs"][0]["complete"])

    def test_immutable_sql(self):
        self.store.ingest([record()])
        for sql in ("DELETE FROM revisions", "UPDATE revisions SET hash='bad'"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.store.db.execute(sql)

    def test_replay(self):
        self.store.ingest([record()])
        self.store.ingest([record(status="closed")])
        with tempfile.TemporaryDirectory() as folder:
            other = Store(str(Path(folder) / "replay.db"))
            try:
                other.ingest(self.store.export(True))
                self.assertEqual(other.export(True), self.store.export(True))
                self.assertTrue(other.check()["ok"])
            finally:
                other.close()

    def test_unknown_preserved(self):
        item = record()
        del item["status"]
        self.assertEqual(normalize(item)["status"], "unknown")

    def test_public_store_rejects_profiles_and_secrets(self):
        for key in ("applicant", "profile", "api_key", "password", "ssn", "bank_account"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.store.ingest([record(evidence={key: "SENSITIVE-FIXTURE"})])
        self.assertEqual(self.store.export()["records"], [])

    def test_sensitive_url(self):
        for url in ("https://user:pass@example.gov", "https://example.gov?api_key=secret"):
            with self.assertRaises(ValueError):
                public_only({"url": url})

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            normalize(record(retrieved_at="2020-10-01"))

    def test_report_unassessed(self):
        self.store.ingest([record()])
        self.assertIn("Eligibility: unassessed", report(self.store.export()))

    def test_stale_ingest_cannot_reverse_newer_status(self):
        self.store.ingest([record(status="closed", retrieved_at="2020-10-02T00:00:00Z")])
        self.store.ingest([record(status="open", retrieved_at="2020-10-01T00:00:00Z")])
        self.assertEqual(self.store.export()["records"][0]["status"], "closed")

    def test_timestamp_offsets_are_ordered_in_utc(self):
        self.store.ingest([record(status="closed", retrieved_at="2020-10-01T03:00:00-04:00")])
        self.store.ingest([record(status="open", retrieved_at="2020-10-01T06:00:00Z")])
        self.assertEqual(self.store.export()["records"][0]["status"], "closed")

    def test_refresh_is_observation_not_revision(self):
        self.store.ingest([record()])
        self.assertEqual(self.store.ingest([record(retrieved_at="2020-10-02T00:00:00Z")]), 0)
        self.assertTrue(self.store.export()["records"][0]["retrieved_at"].startswith("2020-10-02"))
        self.assertEqual(len(self.store.export(True)["records"]), 2)
        self.assertEqual(self.store.check()["revisions"], 1)

    def test_run_idempotence(self):
        packet = {"records": [record()], "run": {"source_id": "state-pa", "fetched_at": "2020-10-01T00:00:00Z", "complete": True}}
        self.store.ingest(packet)
        self.store.ingest(packet)
        self.assertEqual(len(self.store.export()["runs"]), 1)

    def test_invalid_run_timestamp_is_atomic(self):
        with self.assertRaises(ValueError):
            self.store.ingest({"records": [record()], "run": {"source_id": "state-pa", "fetched_at": "not-a-date", "complete": False}})
        self.assertEqual(self.store.export()["records"], [])

    def test_feed_pagination_is_not_material(self):
        self.store.ingest([record(evidence={"feed_url": "https://example.gov?page=1", "common_grants_item": {"id": "1"}})])
        self.assertEqual(self.store.ingest([record(evidence={"feed_url": "https://example.gov?page=2", "common_grants_item": {"id": "1"}})]), 0)
        self.assertTrue(self.store.check()["ok"])

    def test_report_marks_third_party_loan(self):
        self.store.ingest([record(metadata={"authority": "third-party-normalized", "instrument_raw": {"value": "loan"}, "is_confirmed_grant": False})])
        output = report(self.store.export())
        self.assertIn("third-party-normalized", output)
        self.assertIn("loan", output)
        self.assertIn("Confirmed grant instrument: False", output)


class IntegrityRegressionTests(unittest.TestCase):
    def test_future_observation_cannot_hijack_current(self):
        store = Store(":memory:")
        try:
            with patch("grant_engine.core.now", return_value="2020-10-02T00:00:00+00:00"):
                store.ingest([record(status="closed")])
                with self.assertRaises(ValueError):
                    store.ingest([record(status="open", retrieved_at="2030-10-02T00:00:00Z")])
                self.assertEqual(store.export()["records"][0]["status"], "closed")
                store.ingest([record(status="closed", retrieved_at="2020-10-02T00:05:00Z")])
                self.assertTrue(store.check()["ok"])
                with self.assertRaises(ValueError):
                    store.ingest([record(retrieved_at="2020-10-02T00:05:01Z")])
            # Simulate an old database accepted under a clock later found wrong.
            with patch("grant_engine.core.now", return_value="2019-01-01T00:00:00+00:00"):
                self.assertFalse(store.check()["ok"])
        finally:
            store.close()

    def test_ambiguous_run_packet_is_atomic(self):
        store = Store(":memory:")
        try:
            with self.assertRaises(ValueError):
                store.ingest({"records": [record()], "run": {}, "runs": []})
            self.assertEqual(store.export()["records"], [])
        finally:
            store.close()

    def test_contradictory_and_invalid_run_counts_rejected(self):
        base = {"source_id": "fixture", "fetched_at": "2020-10-02T00:00:00Z", "complete": True}
        changes = ({"errors": [{"error_type": "TimeoutError"}]}, {"hit_count": True},
                   {"records_returned": -1}, {"bounded": True}, {"bounded": "false"},
                   {"hit_count": 5, "records_returned": 2})
        for fields in changes:
            with self.subTest(fields=fields):
                store = Store(":memory:")
                try:
                    with self.assertRaises(ValueError):
                        store.ingest({"records": [record()], "run": {**base, **fields}})
                    self.assertEqual(store.export()["records"], [])
                finally:
                    store.close()

    def test_index_corruption_is_detected(self):
        for table, trigger, update in (
            ("revisions", "revision_no_update", "source_id='forged'"),
            ("observations", "observation_no_update", "observed_at='9999-01-01'"),
            ("runs", "run_no_update", "complete=0"),
        ):
            with self.subTest(table=table):
                store = Store(":memory:")
                try:
                    store.ingest({"records": [record()], "run": {"source_id": "fixture", "fetched_at": "2020-10-02T00:00:00Z", "complete": True}})
                    store.db.execute("DROP TRIGGER " + trigger)
                    store.db.execute("UPDATE " + table + " SET " + update)
                    result = store.check()
                    self.assertFalse(result["ok"])
                    self.assertTrue(any("index mismatch" in issue for issue in result["issues"]))
                finally:
                    store.close()


class PlannerTests(unittest.TestCase):
    def test_registry_prose_can_supply_explicit_purpose_hint(self):
        sources = [{"id": "a", "name": "General loans", "jurisdictions": ["PA"]},
                   {"id": "z", "name": "Workforce board", "notes": "Training for employees", "jurisdictions": ["PA"]}]
        result = plan(sources, "PA", purpose="workforce training")
        self.assertEqual(result[0]["id"], "z")
        self.assertTrue(result[0]["reason"]["purpose_text_hint_match"])
        self.assertFalse(result[0]["reason"]["purpose_match"])
        self.assertEqual(result[0]["eligibility"], "unassessed")
        self.assertEqual(len(plan(sources, "PA", purpose="housing")), 2)

    def test_common_plural_aliases_improve_hints(self):
        for tag, requested in (("local governments", "government"), ("individuals", "individual"),
                               ("researchers", "researcher"), ("universities", "university"),
                               ("training providers", "training_provider")):
            with self.subTest(tag=tag):
                self.assertTrue(plan([{"id": "s", "applicant_types": [tag]}], applicant_type=requested)[0]["reason"]["applicant_hint_match"])

    def test_national_request_keeps_state_sources(self):
        sources = [{"id": "federal", "jurisdictions": ["US"]}, {"id": "ca", "jurisdictions": ["CA"]}, {"id": "vi", "jurisdictions": ["VI"]}]
        for jurisdiction in ("US", "USA", "national", "all", "*"):
            with self.subTest(jurisdiction=jurisdiction):
                self.assertEqual({item["id"] for item in plan(sources, jurisdiction)}, {"federal", "ca", "vi"})

    def test_local_purpose_precedes_federal(self):
        sources = [{"id": "federal", "jurisdictions": ["US"], "adapter": "grants-gov"}, {"id": "pa", "jurisdictions": ["PA"], "purposes": ["workforce"], "adapter": "unimplemented"}]
        result = plan(sources, "PA", "business", "workforce")
        self.assertEqual(result[0]["id"], "pa")
        self.assertEqual(result[0]["action"], "agent_research")
        self.assertIn("research_task", result[0])

    def test_distinct_applicant_and_geography(self):
        sources = [{"id": "pa", "jurisdictions": ["PA"], "applicant_types": ["business"]}, {"id": "ca", "jurisdictions": ["CA"]}, {"id": "charity", "jurisdictions": ["US"], "applicant_types": ["nonprofit"], "applicant_types_exhaustive": True}]
        self.assertEqual([s["id"] for s in plan(sources, "PA", "business")], ["pa"])

    def test_incomplete_applicant_tags_are_hints(self):
        self.assertEqual(len(plan([{"id": "public", "applicant_types": ["nonprofit"]}], applicant_type="business")), 1)

    def test_applicant_alias(self):
        self.assertTrue(plan([{"id": "business", "applicant_types": ["for_profit"]}], applicant_type="business")[0]["reason"]["applicant_hint_match"])

    def test_hyphenated_applicant_alias(self):
        self.assertEqual(len(plan([{"id": "business", "applicant_types": ["for-profit"], "applicant_types_exhaustive": True}], applicant_type="business")), 1)

    def test_plural_and_spaced_applicant_hints(self):
        for source_tag, requested in (("businesses", "for-profit"), ("nonprofits", "non-profit"), ("public agencies", "government"), ("tribal governments", "tribal-government"), ("research institutions", "research_institution")):
            with self.subTest(source_tag=source_tag):
                result = plan([{"id": "source", "applicant_types": [source_tag]}], applicant_type=requested)
                self.assertTrue(result[0]["reason"]["applicant_hint_match"])

    def test_virgin_islands_alias_in_both_directions(self):
        for source_tag, requested in (("USVI", "VI"), ("VI", "USVI")):
            result = plan([{"id": "vi", "jurisdictions": [source_tag]}], jurisdiction=requested)
            self.assertEqual(len(result), 1)
            self.assertTrue(result[0]["reason"]["jurisdiction_match"])

    def test_synonyms_do_not_turn_hints_into_exclusions(self):
        result = plan([{"id": "source", "applicant_types": ["research institutions"]}], applicant_type="nonprofits")
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["reason"]["applicant_hint_match"])


class CommonGrantsTests(unittest.TestCase):
    def test_missing_and_http_notice_urls_are_explicit(self):
        for source in (None, "", "https://", "https://pa.api.cg.a6lab.ai/common-grants/opportunities", "http://example.gov/notice", "https://example.gov/notice"):
            def fetch(url):
                return {"items": [{"id": "1", "title": "Fixture", "source": source}], "paginationInfo": {"page": 1, "pageSize": 1, "totalItems": 1, "totalPages": 1}}
            packet = discover_common("https://pa.api.cg.a6lab.ai", "commongrants-pa", 1, 1, fetch)
            self.assertTrue(packet["run"]["complete"])
            item = packet["records"][0]
            meta = item["metadata"]
            self.assertFalse(meta["notice_url_authority_verified"])
            self.assertEqual(meta["official_notice_url_available"], source in ("http://example.gov/notice", "https://example.gov/notice"))
            self.assertEqual(meta["source_url_usable_for_collection"], source == "https://example.gov/notice")
            self.assertEqual(meta["source_url_requires_https_resolution"], source == "http://example.gov/notice")
            if not meta["official_notice_url_available"]:
                self.assertEqual(item["url"], "https://pa.api.cg.a6lab.ai/common-grants/opportunities")

    def test_oversized_or_boolean_pagination_cannot_claim_complete(self):
        item = {"id": "1", "title": "Fixture", "source": "https://example.gov"}
        base = {"page": 1, "pageSize": 1, "totalItems": 1, "totalPages": 1}
        for items, changed in (([item, {**item, "id": "2"}], {}), ([item], {"totalItems": True}), ([item], {"pageSize": True}), ([item], {"totalPages": False}), ([item], {"totalItems": 0})):
            def fetch(url):
                return {"items": items, "paginationInfo": {**base, **changed}}
            packet = discover_common("https://pa.api.cg.a6lab.ai", "commongrants-pa", 1, 1, fetch)
            self.assertFalse(packet["run"]["complete"])
            self.assertTrue(packet["run"]["errors"])
            self.assertEqual(packet["records"], [])

    def test_redirect_is_rejected_before_following(self):
        with self.assertRaises(ValueError):
            NoRedirect().redirect_request(None, None, 302, "", {}, "http://127.0.0.1/private")

    def test_malformed_item_cannot_claim_complete(self):
        for item in ({"id": None, "title": "Fixture"}, {"id": "1", "title": None}):
            def fetch(url):
                return {"items": [item], "paginationInfo": {"page": 1, "pageSize": 1, "totalItems": 1, "totalPages": 1}}
            packet = discover_common("https://pa.api.cg.a6lab.ai", "commongrants-pa", 1, 1, fetch)
            self.assertFalse(packet["run"]["complete"])
            self.assertEqual(packet["records"], [])
            self.assertTrue(packet["run"]["errors"])
    def test_public_host_allowlist(self):
        for host in ("http://127.0.0.1", "https://pa.api.cg.a6lab.ai.attacker.test"):
            with self.assertRaises(ValueError):
                discover_common(host, "commongrants-pa")

    def test_source_identity(self):
        with self.assertRaises(ValueError):
            discover_common("https://pa.api.cg.a6lab.ai", "commongrants-ca")

    def test_pagination(self):
        def fetch(url):
            page = int(url.split("page=")[1].split("&")[0])
            return {"items": [{"id": str(page), "title": "Fixture", "status": {"value": "open"}, "source": "https://example.gov"}], "paginationInfo": {"page": page, "pageSize": 1, "totalPages": 2, "totalItems": 2}}
        packet = discover_common("https://pa.api.cg.a6lab.ai", "commongrants-pa", 2, 1, fetch)
        self.assertTrue(packet["run"]["complete"])
        self.assertEqual(len(packet["records"]), 2)
        self.assertEqual(packet["records"][0]["metadata"]["authority"], "third-party-normalized")
        self.assertFalse(packet["records"][0]["metadata"]["is_confirmed_grant"])
        for item in packet["records"]:
            normalize(item)

    def test_error_sanitized(self):
        def fetch(url):
            raise RuntimeError("SECRET")
        packet = discover_common("https://pa.api.cg.a6lab.ai", "commongrants-pa", transport=fetch)
        self.assertFalse(packet["run"]["complete"])
        self.assertNotIn("SECRET", json.dumps(packet))


class AdapterTests(unittest.TestCase):
    def test_federal_redirect_is_rejected_before_following(self):
        from grant_engine.grants_gov import NoRedirect as FederalNoRedirect
        with self.assertRaises(ValueError):
            FederalNoRedirect().redirect_request(None, None, 302, "", {}, "http://127.0.0.1/private")

    def test_oversized_or_boolean_counts_cannot_claim_complete(self):
        hit = {"id": "1", "title": "Fixture", "oppStatus": "posted"}
        for hits, count, start in (([hit, {**hit, "id": "2"}], 1, 0), ([hit], True, 0), ([hit], 0, 0), ([hit], 1, False)):
            def fetch(endpoint, payload):
                return {"hitCount": count, "startRecord": start, "oppHits": hits}
            packet = discover("test", 1, 1, fetch)
            self.assertFalse(packet["run"]["complete"])
            self.assertTrue(packet["run"]["errors"])
            self.assertEqual(packet["records"], [])

    def transport(self, total, calls, fail_detail=False):
        def fetch(endpoint, payload):
            calls.append((endpoint, payload))
            if endpoint == "fetchOpportunity":
                if fail_detail:
                    raise RuntimeError("SECRET-REMOTE-ERROR")
                return {"id": payload["opportunityId"], "token": "SECRET-TOKEN"}
            start = payload["startRecordNum"]
            return {"hitCount": total, "startRecord": start, "oppHits": [{"id": str(i), "title": "Fixture " + str(i), "oppStatus": "posted"} for i in range(start, min(total, start + payload["rows"]))], "accessKey": "SECRET-KEY"}
        return fetch

    def test_pagination_and_redaction(self):
        calls = []
        packet = discover("training", 5, 2, self.transport(5, calls))
        self.assertTrue(packet["run"]["complete"])
        self.assertEqual([p["startRecordNum"] for e, p in calls if e == "search2"], [0, 2, 4])
        self.assertNotIn("SECRET", json.dumps(packet))

    def test_limit_is_not_complete(self):
        packet = discover("training", 3, 2, self.transport(10, []))
        self.assertFalse(packet["run"]["complete"])
        self.assertTrue(packet["run"]["bounded"])
        self.assertEqual(len(packet["records"]), 3)

    def test_detail_failure_preserves_hit(self):
        packet = discover("training", 1, 1, self.transport(1, [], True))
        self.assertEqual(len(packet["records"]), 1)
        self.assertFalse(packet["run"]["complete"])
        self.assertIsNone(packet["records"][0]["evidence"]["detail"])
        self.assertNotIn("SECRET", json.dumps(packet))

    def test_search_failure_recorded(self):
        def failed(endpoint, payload):
            raise TimeoutError("SECRET")
        packet = discover("test", transport=failed)
        self.assertFalse(packet["run"]["complete"])
        self.assertEqual(packet["run"]["errors"][0]["error_type"], "TimeoutError")
        self.assertNotIn("SECRET", json.dumps(packet))

    def test_ignored_pagination(self):
        original = self.transport(4, [])
        def fetch(endpoint, payload):
            result = original(endpoint, payload)
            if endpoint == "search2":
                result["startRecord"] = 0
            return result
        packet = discover("test", 4, 2, fetch)
        self.assertFalse(packet["run"]["complete"])
        self.assertEqual(len(packet["records"]), 2)

    def test_repeated_page_without_offset(self):
        original = self.transport(4, [])
        def fetch(endpoint, payload):
            if endpoint == "search2":
                payload = {**payload, "startRecordNum": 0}
            result = original(endpoint, payload)
            result.pop("startRecord", None)
            return result
        packet = discover("test", 4, 2, fetch)
        self.assertFalse(packet["run"]["complete"])
        self.assertEqual(len(packet["records"]), 2)

    def test_zero_results(self):
        self.assertTrue(discover("test", transport=self.transport(0, []))["run"]["complete"])

    def test_detail_identity_mismatch(self):
        original = self.transport(1, [])
        def fetch(endpoint, payload):
            return {"id": 9999} if endpoint == "fetchOpportunity" else original(endpoint, payload)
        packet = discover("test", 1, 1, fetch)
        self.assertFalse(packet["run"]["complete"])
        self.assertIsNone(packet["records"][0]["evidence"]["detail"])

    def test_count_changes_invalidate_complete(self):
        original = self.transport(4, [])
        def fetch(endpoint, payload):
            result = original(endpoint, payload)
            if endpoint == "search2" and payload["startRecordNum"]:
                result["hitCount"] = 5
            return result
        self.assertFalse(discover("test", 4, 2, fetch)["run"]["complete"])

    def test_invalid_bound(self):
        with self.assertRaises(ValueError):
            discover("test", 1001)


class CLITests(unittest.TestCase):
    def test_help(self):
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
            main(["--help"])
        self.assertEqual(result.exception.code, 0)

    def test_ingest_export_replay_check(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            path = Path(folder)
            (path / "input.json").write_text(json.dumps([record()]))
            db, other = str(path / "a.db"), str(path / "b.db")
            self.assertEqual(main(["ingest", "--db", db, "--input", str(path / "input.json")]), 0)
            self.assertEqual(main(["export", "--db", db, "--history", "--output", str(path / "export.json")]), 0)
            self.assertEqual(main(["replay", "--db", other, "--input", str(path / "export.json")]), 0)
            self.assertEqual(main(["check", "--db", other]), 0)

    def test_error_output_does_not_echo_input(self):
        output = io.StringIO()
        with contextlib.redirect_stderr(output):
            self.assertEqual(main(["ingest", "--db", ":memory:", "--input", "SECRET-NONEXISTENT"]), 2)
        self.assertNotIn("SECRET", output.getvalue())


if __name__ == "__main__":
    unittest.main()
