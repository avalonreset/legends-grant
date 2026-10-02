"""Offline discovery search and material comparison of current store exports.

Search ranks lexical relevance, never eligibility. Source geography is a routing
hint, not a statement about eligible applicants. Absence never means closure.
"""
import html
import re
from datetime import datetime, timezone

from .core import canonical, jurisdiction_tag, material_hash, normalize

MAX_RECORDS = 10000
MAX_PACKET_BYTES = 50_000_000
STATUSES = {"unknown", "open", "forecast", "rolling", "closed", "cancelled", "archived"}
TYPES = {"opportunity", "program", "funder_prospect", "historical_award", "directory"}
IDENTITY = ("source_id", "program_id", "cycle_id")
TEXT_KEYS = {"description", "synopsisdescription", "synopsisdesc", "summary", "abstract", "purpose", "objectives"}
RESTRICTION_KEYS = {"eligibility", "eligibilitydescription", "applicanteligibilitydesc",
                    "applicanteligibilitydescription", "restrictions", "geographicrestrictions",
                    "eligibilitycriteria", "eligibleapplicants", "acceptedapplicanttypes", "applicanttypes"}


def _current(packet):
    if not isinstance(packet, dict) or not isinstance(packet.get("records"), list):
        raise ValueError("A current store export packet with records is required")
    if len(packet["records"]) > MAX_RECORDS:
        raise ValueError("Search and comparison support at most 10000 records per packet")
    if len(canonical(packet["records"]).encode("utf-8")) > MAX_PACKET_BYTES:
        raise ValueError("Record packet exceeds 50 MB")
    result = {}
    for raw in packet["records"]:
        record = normalize(raw)
        identity = tuple(record[key] for key in IDENTITY)
        if identity in result:
            raise ValueError("Duplicate identities: use a current export, not history")
        result[identity] = record
    return result


def _plain(value):
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", value)).split())


def _field_text(value):
    """Read textual source fields, including CommonGrants custom-field wrappers."""
    if isinstance(value, str):
        return [_plain(value[:100000])]
    if isinstance(value, list):
        return [text for item in value for text in _field_text(item)]
    if isinstance(value, dict):
        return [text for key, item in value.items() if key in {"value", "description", "name", "label", "text"}
                for text in _field_text(item)]
    return []


def _descriptions(value, depth=0, source_fields=False):
    # Target prose fields, excluding URLs, credential-like text, hashes and IDs.
    if depth > 12:
        return []
    result = []
    if isinstance(value, dict):
        for key, item in value.items():
            tag = re.sub(r"[^a-z]", "", key.lower())
            if tag in TEXT_KEYS or (source_fields and tag in RESTRICTION_KEYS):
                result.extend(_field_text(item))
            elif isinstance(item, (dict, list)):
                result.extend(_descriptions(item, depth + 1, source_fields))
    elif isinstance(value, list):
        for item in value:
            result.extend(_descriptions(item, depth + 1, source_fields))
    return result


def _scope(record):
    metadata = record.get("metadata", {})
    raw = metadata.get("jurisdictions", metadata.get("jurisdiction", []))
    raw = [raw] if isinstance(raw, str) else raw
    scopes = {jurisdiction_tag(value) for value in raw} if isinstance(raw, list) else set()
    source = record["source_id"]
    if source in {"commongrants-ca", "commongrants-pa", "commongrants-wa", "commongrants-md"}:
        scopes.add(source.rsplit("-", 1)[1].upper())
    elif source == "grants-gov":
        scopes.add("US")
    return sorted(scopes)


def _instant(value):
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("as_of must be a timezone-aware timestamp")
    return value.astimezone(timezone.utc)


def search(packet, query="", *, status=None, record_type=None, jurisdiction=None,
           limit=25, as_of=None, stale_days=30):
    """Return ranked source records; multiword queries require every word.

    Blank query lists records. A state filter includes nationwide sources and
    records of unknown scope (explicitly marked); it never establishes residency
    eligibility. Staleness describes observation age, not program status.
    """
    if not isinstance(query, str) or len(query) > 1000:
        raise ValueError("query must be a string of at most 1000 characters")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be 1..1000")
    if type(stale_days) is not int or not 1 <= stale_days <= 3650:
        raise ValueError("stale_days must be 1..3650")
    if status is not None and status not in STATUSES:
        raise ValueError("Unsupported status filter")
    if record_type is not None and record_type not in TYPES:
        raise ValueError("Unsupported record type filter")
    clock = _instant(as_of)
    terms = sorted(set(re.findall(r"\w+", query.casefold())))
    if query.strip() and not terms:
        raise ValueError("query needs at least one word")
    target = jurisdiction_tag(jurisdiction) if jurisdiction else None
    national = {"US", "USA", "NATIONAL", "ALL", "*"}
    # Nationwide means all US source routes, including state sources.
    if target in national:
        target = None
    matches = []
    for record in _current(packet).values():
        if status and record["status"] != status:
            continue
        if record_type and record["record_type"] != record_type:
            continue
        scope = _scope(record)
        if target and scope and not set(scope) & (national | {target}):
            continue
        title = _plain(record["title"])
        description = " ".join(dict.fromkeys(_descriptions(record.get("metadata", {})) + _descriptions(record["evidence"], source_fields=True)))[:100000]
        title_words = set(re.findall(r"\w+", title.casefold()))
        body_words = set(re.findall(r"\w+", description.casefold()))
        if not all(term in title_words or term in body_words for term in terms):
            continue
        score = sum(5 if term in title_words else 1 for term in terms)
        age = (clock - _instant(record["retrieved_at"])).total_seconds() / 86400
        freshness = "future_observation" if age < 0 else "stale" if age > stale_days else "recent_observation"
        metadata = record.get("metadata", {})
        instrument = metadata.get("instrument_raw")
        instrument_text = canonical(instrument).casefold()
        labels = ["eligibility_unassessed", freshness]
        warnings = []
        evidence = record["evidence"] if isinstance(record["evidence"], dict) else {}
        if record["source_id"] == "grants-gov" and evidence.get("detail") is None:
            warnings.append("missing_detail")
        if metadata.get("official_notice_url_available") is False:
            warnings.append("official_notice_url_missing")
        if record["url"].startswith("http://"):
            warnings.append("insecure_notice_url")
        labels.extend(warnings)
        if record["status"] == "unknown":
            labels.append("status_unknown")
        if record["status"] not in {"open", "rolling"}:
            labels.append("not_observed_open")
        if record["record_type"] != "opportunity":
            labels.append("not_an_opportunity_record")
        if re.search(r"\bloans?\b", instrument_text):
            labels.append("loan_or_mixed_instrument")
        if metadata.get("is_confirmed_grant") is not True:
            labels.append("grant_instrument_unconfirmed")
        authority = metadata.get("authority") or ("official-federal-index" if record["source_id"] == "grants-gov" else "unspecified")
        matches.append({**{key: record[key] for key in IDENTITY}, "title": title,
                        "description": description, "url": record["url"],
                        "status": record["status"], "record_type": record["record_type"],
                        "retrieved_at": record["retrieved_at"], "authority": authority,
                        "official_notice_url_available": metadata.get("official_notice_url_available"),
                        "source_url_usable_for_collection": metadata.get("source_url_usable_for_collection"),
                        "notice_url_authority_verified": metadata.get("notice_url_authority_verified"),
                        "instrument_raw": instrument, "source_jurisdictions": scope,
                        "jurisdiction_match": "unfiltered" if not target else "unknown" if not scope else "source_scope",
                        "freshness": freshness, "labels": labels, "warnings": warnings, "eligibility": "unassessed",
                        "relevance_score": score, "matched_terms": terms,
                        "material_hash": material_hash(record)})
    matches.sort(key=lambda item: (-item["relevance_score"], item["status"] not in {"open", "rolling"}, *(item[key] for key in IDENTITY)))
    return {"query": query, "filters": {"status": status, "record_type": record_type, "jurisdiction": target},
            "matched_count": len(matches), "returned_count": min(limit, len(matches)),
            "truncated": len(matches) > limit, "results": matches[:limit],
            "eligibility": "unassessed", "as_of": clock.isoformat(),
            "limitations": ["Lexical relevance only; no eligibility decision", "Source geography is not applicant eligibility",
                            "Unknown geography remains visible", "No live revalidation; freshness is observation age",
                            "Only current records in this local packet are searched"]}


def _material(record):
    result = {key: value for key, value in record.items() if key != "retrieved_at"}
    if isinstance(record["evidence"], dict):
        result["evidence"] = {key: value for key, value in record["evidence"].items() if key != "feed_url"}
    return result


def _changed_fields(before, after, prefix=""):
    if isinstance(before, dict) and isinstance(after, dict):
        fields = []
        for key in sorted(before.keys() | after.keys()):
            path = prefix + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in before or key not in after:
                fields.append(path)
            else:
                fields.extend(_changed_fields(before[key], after[key], path))
        return fields
    return [] if canonical(before) == canonical(after) else [prefix]


def compare_packets(before, after, *, limit=1000):
    """Compare two current exports. Paths use JSON Pointer; arrays are atomic.

    Run histories do not alter material records. An empty/outage packet produces
    no_longer_observed entries, which explicitly preserve the last known status.
    """
    if type(limit) is not int or not 1 <= limit <= 10000:
        raise ValueError("limit must be 1..10000")
    old, new = _current(before), _current(after)
    changes = []
    counts = {"added": 0, "changed": 0, "no_longer_observed": 0, "unchanged": 0}
    for identity in sorted(old.keys() | new.keys()):
        previous, current = old.get(identity), new.get(identity)
        if previous is None:
            kind = "added"
        elif current is None:
            kind = "no_longer_observed"
        elif material_hash(previous) != material_hash(current):
            kind = "changed"
        else:
            counts["unchanged"] += 1
            continue
        counts[kind] += 1
        if len(changes) >= limit:
            continue
        record = current or previous
        changes.append({**dict(zip(IDENTITY, identity)), "change": kind,
                        "title": record["title"], "url": record["url"],
                        "previous_status": previous["status"] if previous else None,
                        "current_status": current["status"] if current else None,
                        "last_observed_status": record["status"], "closure_inferred": False,
                        "before_hash": material_hash(previous) if previous else None,
                        "after_hash": material_hash(current) if current else None,
                        "changed_fields": _changed_fields(_material(previous), _material(current)) if previous and current else [],
                        "eligibility": "unassessed"})
    total = sum(counts[key] for key in ("added", "changed", "no_longer_observed"))
    return {"counts": counts, "change_count": total, "returned_count": len(changes),
            "truncated": total > limit, "changes": changes,
            "limitations": ["Absence means no longer observed in this packet, never closed",
                            "Comparison is source/program/cycle scoped; no cross-source identity merging",
                            "No eligibility determination or automatic action"]}
