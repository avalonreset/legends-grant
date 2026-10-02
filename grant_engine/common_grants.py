"""Read-only reuse of public AgileSix CommonGrants-compatible state feeds.

These are third-party normalized feeds, not authoritative state endpoints.
No third-party implementation is vendored or executed. Official notice review
is required; the source registry must keep upstream notices and feed distinct.
"""
import json
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

from .core import digest, now, public_only, normalize

HOSTS = {state: "https://" + state + ".api.cg.a6lab.ai" for state in ("ca", "pa", "wa", "md")}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Feed redirect refused")


def get(url):
    request = Request(url, headers={"User-Agent": "legends-grant-public/0.2 evidence-prototype"})
    with build_opener(NoRedirect()).open(request, timeout=30) as response:
        raw = response.read(10_000_001)
    if len(raw) > 10_000_000:
        raise ValueError("Response exceeds 10 MB bound")
    return public_only(json.loads(raw), redact=True)


def discover(base_url, source_id, limit=25, page_size=25, transport=get):
    base_url = base_url.rstrip("/")
    if base_url not in HOSTS.values():
        raise ValueError("Only vetted public AgileSix state hosts are supported")
    if source_id != "commongrants-" + next(s for s, host in HOSTS.items() if host == base_url):
        raise ValueError("Source identifier must match commongrants-<state>")
    if type(limit) is not int or type(page_size) is not int or not 1 <= limit <= 1000 or not 1 <= page_size <= 100:
        raise ValueError("limit 1..1000; page_size 1..100")
    fetched = now()
    run = {"source_id": source_id, "fetched_at": fetched, "adapter_version": "0.2.0", "complete": False, "bounded": False, "errors": [], "requests": [], "limit": limit, "hit_count": None, "provider": "AgileSix third-party CommonGrants feed", "cost": {"paid_calls": 0}}
    records, seen = [], set()
    page = 1
    size = min(page_size, limit)
    try:
        while len(records) < limit:
            url = f"{base_url}/common-grants/opportunities?page={page}&pageSize={size}"
            data = public_only(transport(url), redact=True)
            items, info = data["items"], data["paginationInfo"]
            total = info["totalItems"]
            if not isinstance(items, list) or type(total) is not int or total < 0 or type(info["page"]) is not int or type(info["pageSize"]) is not int or type(info["totalPages"]) is not int or info["totalPages"] < 0 or info["page"] != page or info["pageSize"] != size:
                raise ValueError("Unexpected pagination schema")
            if len(items) > size or len(seen) + len(items) > total:
                raise ValueError("Response exceeds requested page size or declared total")
            if run["hit_count"] is not None and total != run["hit_count"]:
                raise ValueError("Dataset changed during pagination")
            run["hit_count"] = total
            run["requests"].append({"url": url, "response": data, "sha256": digest(data)})
            if not items and len(seen) < total:
                raise ValueError("Empty page before totalItems")
            for item in items[:limit - len(records)]:
                if not isinstance(item.get("id"), str) or not item["id"].strip():
                    raise ValueError("Missing opportunity identifier")
                identifier = str(item["id"])
                if identifier in seen:
                    raise ValueError("Repeated opportunity id")
                seen.add(identifier)
                source_url = item.get("source")
                try:
                    source_parts = urlsplit(source_url) if isinstance(source_url, str) else None
                    notice_available = bool(source_parts and source_parts.scheme in ("http", "https") and source_parts.hostname and source_parts.hostname != urlsplit(base_url).hostname)
                except ValueError:
                    notice_available = False
                if not notice_available:
                    source_url = base_url + "/common-grants/opportunities"
                requires_https = notice_available and source_parts.scheme == "http"
                state = item.get("status", {}).get("value")
                status = {"open": "open", "closed": "closed", "forecasted": "forecast", "forecast": "forecast", "ongoing": "rolling", "archived": "archived"}.get(state, "unknown")
                instrument = item.get("customFields", {}).get("fundingInstrument", {})
                records.append({"source_id": source_id, "program_id": "unresolved-program:" + identifier, "cycle_id": identifier, "record_type": "opportunity", "title": item["title"], "status": status, "url": source_url, "retrieved_at": fetched, "evidence": {"common_grants_item": item, "feed_url": url, "sha256": digest(item)}, "metadata": {"authority": "third-party-normalized", "program_identity": "unresolved", "eligibility": "unassessed", "instrument_raw": instrument, "is_confirmed_grant": False, "attachments_fetched": False, "official_notice_url_available": notice_available, "source_url_usable_for_collection": notice_available and not requires_https, "source_url_requires_https_resolution": requires_https, "notice_url_authority_verified": False}})
                try:
                    records[-1] = normalize(records[-1])
                except (ValueError, TypeError):
                    records.pop()
                    raise
            if page >= info["totalPages"] or len(seen) >= total:
                run["complete"] = len(seen) == total
                if len(seen) < total and len(records) < limit:
                    raise ValueError("Pages ended before totalItems")
                break
            page += 1
    except Exception as exc:
        run["errors"].append({"error_type": type(exc).__name__, "page": page})
        run["complete"] = False
    run["bounded"] = run["hit_count"] is not None and run["hit_count"] > len(records)
    run["records_returned"] = len(records)
    run["limitations"] = ["Third-party normalization; review official notices", "Mixed funding instruments and statuses; not all items are open grants", "No keyword or applicant filtering", "No qualification or attachment retrieval", "No closure inferred from absence"]
    return {"schema_version": 1, "records": records, "run": run}
