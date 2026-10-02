"""Public registry coverage contract; runs offline with repository data only.

Coverage means discovery routes, not collected opportunities or eligibility.
Source inventories may grow. The current contract is 56 US jurisdictions and
five configured structured-discovery routes using two implemented adapters.
"""

import contextlib
import io
import json
import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from grant_engine.__main__ import main
from grant_engine.core import load_registry, plan


REGISTRY = Path(__file__).resolve().parents[1] / "grant_engine" / "data" / "us-sources.json"
JURISDICTIONS = frozenset(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN "
    "MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA "
    "WA WV WI WY DC AS GU MP PR VI".split()
)
APPLICANT_TYPES = (
    "business", "nonprofit", "government", "tribal", "individual", "researcher"
)
PROTOTYPE_BASES = {
    "commongrants-pa": "https://pa.api.cg.a6lab.ai",
    "commongrants-ca": "https://ca.api.cg.a6lab.ai",
    "commongrants-wa": "https://wa.api.cg.a6lab.ai",
    "commongrants-md": "https://md.api.cg.a6lab.ai",
}


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = load_registry(REGISTRY)

    def test_exact_nationwide_jurisdiction_coverage(self):
        self.assertEqual(len(JURISDICTIONS), 56)
        represented = {source["jurisdiction"] for source in self.sources}
        self.assertEqual(represented, JURISDICTIONS | {"US"})

    def test_unique_source_identity_and_public_https_evidence(self):
        ids = [source["id"] for source in self.sources]
        urls = [source["url"].rstrip("/") for source in self.sources]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(urls), len(set(urls)))
        for source in self.sources:
            with self.subTest(source=source["id"]):
                self.assertTrue(source["id"])
                self.assertEqual(source["source_id"], source["id"])
                self.assertTrue(source["evidence_urls"])
                for url in [source["url"], *source["evidence_urls"]]:
                    parsed = urlsplit(url)
                    self.assertEqual(parsed.scheme, "https", url)
                    self.assertTrue(parsed.hostname, url)
                    self.assertIsNone(parsed.username, url)
                    self.assertIsNone(parsed.password, url)

    def test_applicant_coverage_is_nonexhaustive(self):
        for source in self.sources:
            with self.subTest(source=source["id"]):
                self.assertIs(source["applicant_types_exhaustive"], False)

    def test_current_structured_discovery_contract(self):
        configured = Counter(
            source["adapter"] for source in self.sources if source.get("adapter")
        )
        self.assertEqual(configured, {"grants-gov": 1, "common-grants": 4})
        routes = plan(self.sources)
        structured = [r for r in routes if r["action"] == "structured_discovery"]
        self.assertEqual(len(structured), 5)
        self.assertEqual(
            {r["id"] for r in structured},
            {s["id"] for s in self.sources if s.get("adapter")},
        )
        self.assertEqual(
            sum(r["action"] == "agent_research" for r in routes),
            len(self.sources) - 5,
        )

    def test_prototype_feeds_are_not_official_state_sources(self):
        feeds = {
            source["id"]: source
            for source in self.sources
            if source.get("adapter") == "common-grants"
        }
        self.assertEqual(set(feeds), set(PROTOTYPE_BASES))
        for source_id, base in PROTOTYPE_BASES.items():
            with self.subTest(source=source_id):
                source = feeds[source_id]
                self.assertEqual(source["url"], base)
                self.assertEqual(source["base_url"], base)
                self.assertEqual(
                    source["source_kind"], "third_party_prototype_opportunity_feed"
                )

    def test_all_336_plans_retain_local_and_national_routes(self):
        national = {s["id"] for s in self.sources if s["jurisdiction"] == "US"}
        cases = 0
        for jurisdiction in sorted(JURISDICTIONS):
            local = {
                s["id"] for s in self.sources if s["jurisdiction"] == jurisdiction
            }
            self.assertTrue(local, jurisdiction)
            for applicant_type in APPLICANT_TYPES:
                with self.subTest(jurisdiction=jurisdiction, applicant=applicant_type):
                    cases += 1
                    routes = plan(self.sources, jurisdiction, applicant_type)
                    self.assertEqual({r["id"] for r in routes}, local | national)
                    self.assertEqual(len(routes), len(local | national))
                    self.assertEqual(routes[0]["jurisdiction"], jurisdiction)
                    self.assertTrue(all(r["eligibility"] == "unassessed" for r in routes))
                    for route in routes:
                        if route["action"] == "agent_research":
                            self.assertTrue(route.get("research_task"), route["id"])
        self.assertEqual(cases, 336)

    def test_nonmatching_hints_never_remove_local_routes(self):
        # Force a nonmatch independently of evolving applicant labels. This
        # catches accidental hard eligibility filtering even if real tags widen.
        for jurisdiction in sorted(JURISDICTIONS):
            with self.subTest(jurisdiction=jurisdiction):
                local = {
                    s["id"] for s in self.sources if s["jurisdiction"] == jurisdiction
                }
                routes = plan(self.sources, jurisdiction, "unmatched-review-fixture")
                selected = {r["id"]: r for r in routes}
                self.assertTrue(local <= set(selected))
                self.assertEqual(routes[0]["jurisdiction"], jurisdiction)
                for source_id in local:
                    self.assertEqual(selected[source_id]["eligibility"], "unassessed")

    def test_cli_matches_planner_for_all_336_combinations(self):
        for jurisdiction in sorted(JURISDICTIONS):
            for applicant_type in APPLICANT_TYPES:
                with self.subTest(jurisdiction=jurisdiction, applicant=applicant_type):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        result = main([
                            "plan", "--registry", str(REGISTRY),
                            "--jurisdiction", jurisdiction,
                            "--applicant-type", applicant_type,
                        ])
                    self.assertEqual(result, 0)
                    packet = json.loads(output.getvalue())
                    self.assertEqual(
                        packet["sources"],
                        plan(self.sources, jurisdiction, applicant_type),
                    )
                    self.assertEqual(packet["qualification"], "unassessed")


if __name__ == "__main__":
    unittest.main()
