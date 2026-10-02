"""No-key adapter based on Grants.gov's official search2/fetchOpportunity docs.

https://www.grants.gov/api/common/search2
https://www.grants.gov/api/common/fetchopportunity
Responses retain public data after dropping service-issued authentication fields.
"""
import json
from urllib.request import Request, HTTPRedirectHandler, build_opener

from .core import digest, now, public_only, normalize

BASE = "https://api.grants.gov/v1/api/"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("API redirect refused")


def post(endpoint, payload):
    request = Request(BASE + endpoint, json.dumps(payload).encode(), {"Content-Type": "application/json", "User-Agent": "legends-grant-public/0.2 evidence-prototype"}, method="POST")
    with build_opener(NoRedirect()).open(request, timeout=30) as response:
        raw = response.read(10_000_001)
    if len(raw) > 10_000_000:
        raise ValueError("Response exceeds 10 MB bound")
    data = json.loads(raw)
    if data.get("errorcode") != 0 or not isinstance(data.get("data"), dict):
        raise ValueError("Provider returned an error or unexpected schema")
    return public_only(data["data"], redact=True)


def discover(query, limit=25, page_size=25, transport=post):
    if not query.strip() or type(limit) is not int or type(page_size) is not int or not 1 <= limit <= 1000 or not 1 <= page_size <= 100:
        raise ValueError("Query required; limit 1..1000; page_size 1..100")
    fetched = now()
    run = {"source_id": "grants-gov", "fetched_at": fetched, "adapter_version": "0.2.0", "query": query, "limit": limit, "complete": False, "errors": [], "requests": [], "hit_count": None, "next_start": 0, "cost": {"paid_calls": 0}}
    records, seen = [], set()
    offset = 0
    try:
        while len(records) < limit:
            request = {"keyword": query, "rows": min(page_size, limit - len(records)), "startRecordNum": offset, "oppStatuses": "forecasted|posted"}
            data = public_only(transport("search2", request), redact=True)
            hits = data.get("oppHits")
            count = data.get("hitCount")
            if not isinstance(hits, list) or type(count) is not int or count < 0:
                raise ValueError("Unexpected search schema")
            if type(data.get("startRecord", offset)) is not int or data.get("startRecord", offset) != offset:
                raise ValueError("Provider ignored pagination offset")
            if len(hits) > request["rows"] or offset + len(hits) > count:
                raise ValueError("Response exceeds requested page size or declared total")
            if run["hit_count"] is not None and count != run["hit_count"]:
                raise ValueError("Result count changed during pagination; rerun required")
            run["hit_count"] = count
            run["requests"].append({"endpoint": BASE + "search2", "request": request, "response": data, "sha256": digest(data)})
            if not hits:
                if offset < count:
                    raise ValueError("Empty page before declared result count")
                run["complete"] = not run["errors"]
                break
            for hit in hits[:limit - len(records)]:
                identifier = str(hit["id"])
                if not identifier.isdigit() or identifier in seen:
                    raise ValueError("Repeated or invalid opportunity identifier")
                seen.add(identifier)
                detail = None
                try:
                    detail = public_only(transport("fetchOpportunity", {"opportunityId": int(identifier)}), redact=True)
                    if str(detail.get("id")) != identifier:
                        raise ValueError("Detail identity mismatch")
                except Exception as exc:
                    detail = None
                    # Never include remote exception text: it may contain credentials.
                    run["errors"].append({"stage": "detail", "id": identifier, "error_type": type(exc).__name__})
                evidence = {"search_hit": hit, "detail": detail, "detail_endpoint": BASE + "fetchOpportunity", "detail_sha256": digest(detail) if detail else None}
                # Opportunity number identifies a competition, not necessarily a
                # recurring program. Use an explicit unknown-program namespace.
                records.append({"source_id": "grants-gov", "program_id": "unresolved-program:" + identifier, "cycle_id": identifier, "record_type": "opportunity", "title": hit["title"], "status": {"posted": "open", "forecasted": "forecast", "closed": "closed", "archived": "archived"}.get(hit.get("oppStatus"), "unknown"), "url": "https://www.grants.gov/search-results-detail/" + identifier, "retrieved_at": fetched, "evidence": evidence, "metadata": {"opportunity_number": hit.get("number"), "program_identity": "unresolved", "open_date_raw": hit.get("openDate") or None, "close_date_raw": hit.get("closeDate") or None, "eligibility": "unassessed", "attachments_fetched": False}})
                try:
                    records[-1] = normalize(records[-1])
                except (ValueError, TypeError):
                    records.pop()
                    raise
            offset += len(hits)
            run["next_start"] = offset
            if offset >= count:
                run["complete"] = len(seen) == count and not run["errors"]
                break
    except Exception as exc:
        run["errors"].append({"stage": "search", "error_type": type(exc).__name__})
    run["records_returned"] = len(records)
    run["bounded"] = run["hit_count"] is not None and run["hit_count"] > len(records)
    run["limitations"] = ["Keyword/index coverage only", "No attachment retrieval or eligibility assessment", "No closure inferred from missing records", "Partial records are observations, never replacement datasets"]
    return {"schema_version": 1, "records": records, "run": run}
