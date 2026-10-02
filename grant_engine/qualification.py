"""Conservative, local review of an explicitly reviewed grant rule inventory.

``evaluate_review(review, facts, as_of=None)`` is pure: it never stores applicant
facts or writes to the public evidence store. ``facts`` is a separate private
mapping; outputs contain requirement IDs and decisions, never fact values.

This is a review validator, NOT automatic extraction or legal interpretation.
An agent/reviewer must collect the current controlling notice, attachments and
amendments; supply their text and SHA-256 hashes; inspect the entire inventory;
and attest completeness. Hashes and quote checks bind a decision to the supplied
text, but cannot prove a reviewer found every clause or that a URL is official.
The authority/currentness declarations are assertions requiring external review.

See examples/qualification-review.json for the exact version-1 interchange.
Predicates support equals, one_of, at_least, at_most and contains. Untranslatable
rules use manual and remain unknown. Missing facts never pass. ``decision`` is
the reviewer's proposed pass/fail/unknown, checked against the actual predicate;
an unknown assertion cannot be upgraded automatically. All rules are mandatory.
Do not put optional scoring criteria in this inventory. Clauses that do not
require an applicant fact can reference a separately confirmed boolean fact.

The result "eligible-for-review" only means the supplied current evidence and
reviewed predicates passed; it is never approval, an award, or proof of complete
eligibility. Refresh the source and rerun before important application actions.
"""

import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from .core import public_only


def _object(value, required, optional=(), where="review"):
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{where} must be an object")
    if set(required) - value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError(f"{where} has missing or unsupported fields")


def _string(value, where):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where} must be a nonempty string")


def _boolean(value, where):
    if type(value) is not bool:
        raise ValueError(f"{where} must be boolean")


def _array(value, where, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(f"{where} must be {'a nonempty' if nonempty else 'an'} array")


def _time(value):
    _string(value, "timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Timestamp must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("Timestamp requires timezone")
    return parsed.astimezone(timezone.utc)


def _scalar(value):
    return value is None or type(value) in (str, bool, int) or (type(value) is float and math.isfinite(value))


def _number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def _same(left, right):
    # Python otherwise considers True == 1, an unsafe qualification shortcut.
    return type(left) is type(right) and left == right or (
        type(left) in (int, float) and type(right) in (int, float) and left == right
    )


def _compatible(left, right):
    """Only comparable scalar facts can support a definitive rule decision."""
    return (left is not None and right is not None and _scalar(left) and _scalar(right)
            and (type(left) is type(right) or (_number(left) and _number(right))))


def _predicate(rule, facts):
    actual = facts.get(rule["fact_key"])
    expected = rule["expected"]
    if actual is None or rule["operator"] == "manual":
        return "unknown"
    op = rule["operator"]
    if op == "equals":
        if not _compatible(actual, expected):
            return "unknown"
        passed = _same(actual, expected)
    elif op == "one_of":
        if not any(_compatible(actual, item) for item in expected):
            return "unknown"
        passed = any(_same(actual, item) for item in expected)
    elif op in ("at_least", "at_most"):
        if not _number(actual):
            return "unknown"
        passed = actual >= expected if op == "at_least" else actual <= expected
    elif op == "contains":
        if not isinstance(actual, list):
            return "unknown"
        # A mixed/malformed fact array is not a verified absence or presence.
        # Empty arrays represent known absence; missing/null facts do not.
        if any(not _compatible(item, expected) for item in actual):
            return "unknown"
        passed = any(_same(item, expected) for item in actual)
    else:
        raise ValueError("Unsupported predicate")
    return "pass" if passed else "fail"


def evaluate_review(review, facts, as_of=None):
    """Validate and evaluate; raise ValueError for malformed schema.

    Evidence gaps and review inconsistencies produce unresolved, rather than
    raising. ``as_of`` is an optional timezone-aware ISO timestamp for replay.
    Caller must keep both the review output and facts in private case storage.
    """
    _object(review, ("schema_version", "opportunity", "documents", "inventory", "requirements", "application_requirements"))
    if type(review["schema_version"]) is not int or review["schema_version"] != 1:
        raise ValueError("Unsupported review schema_version")
    public_only(review)
    if not isinstance(facts, dict) or not all(isinstance(k, str) and k.strip() for k in facts):
        raise ValueError("facts must be a separate private object")
    for value in facts.values():
        if not _scalar(value) and not (isinstance(value, list) and all(_scalar(item) for item in value)):
            raise ValueError("Fact values must be finite scalars or scalar arrays")
    clock = _time(as_of) if as_of is not None else datetime.now(timezone.utc)
    blockers = []
    reasons = []
    documents = {}
    _array(review["documents"], "documents", True)
    for doc in review["documents"]:
        _object(doc, ("id", "url", "kind", "authoritative", "retrieved_at", "text", "sha256", "reviewed_sha256"), where="document")
        for field in ("id", "url", "text", "sha256"):
            _string(doc[field], f"document.{field}")
        if doc["id"] in documents:
            raise ValueError("Duplicate document id")
        url = urlsplit(doc["url"])
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            raise ValueError("Document URL must be public HTTPS without credentials")
        if doc["kind"] not in ("notice", "attachment", "amendment", "instructions"):
            raise ValueError("Unsupported document kind")
        _boolean(doc["authoritative"], "document.authoritative")
        if not re.fullmatch(r"[a-f0-9]{64}", doc["sha256"]):
            raise ValueError("sha256 must be lowercase SHA-256")
        if doc["reviewed_sha256"] is not None and (not isinstance(doc["reviewed_sha256"], str) or not re.fullmatch(r"[a-f0-9]{64}", doc["reviewed_sha256"])):
            raise ValueError("reviewed_sha256 must be SHA-256 or null")
        if hashlib.sha256(doc["text"].encode("utf-8")).hexdigest() != doc["sha256"]:
            blockers.append("document_hash_mismatch:" + doc["id"])
        if doc["reviewed_sha256"] != doc["sha256"]:
            blockers.append("unreviewed_document_revision:" + doc["id"])
        if not doc["authoritative"]:
            blockers.append("non_authoritative_document:" + doc["id"])
        retrieved = _time(doc["retrieved_at"])
        if retrieved > clock:
            blockers.append("future_document:" + doc["id"])
        documents[doc["id"]] = doc

    def citations(items, label):
        _array(items, "citations", True)
        for citation in items:
            _object(citation, ("document_id", "quote", "locator"), where="citation")
            for value in citation.values():
                _string(value, "citation")
            doc = documents.get(citation["document_id"])
            if doc is None:
                blockers.append("missing_cited_document:" + label)
            elif citation["quote"] not in doc["text"]:
                blockers.append("unsupported_quote:" + label)

    inventory = review["inventory"]
    _object(inventory, ("required_document_ids", "complete", "all_rules_reviewed", "amendments_checked_at", "max_age_days", "conflicts"), where="inventory")
    for field in ("complete", "all_rules_reviewed"):
        _boolean(inventory[field], "inventory." + field)
        if not inventory[field]:
            blockers.append("inventory_" + field + "_not_confirmed")
    _array(inventory["required_document_ids"], "required_document_ids", True)
    for item in inventory["required_document_ids"]:
        _string(item, "required_document_id")
    if len(set(inventory["required_document_ids"])) != len(inventory["required_document_ids"]):
        raise ValueError("Duplicate required document id")
    if set(inventory["required_document_ids"]) != set(documents):
        blockers.append("document_inventory_mismatch")
    if not any(doc["kind"] == "notice" for doc in documents.values()):
        blockers.append("missing_controlling_notice")
    if type(inventory["max_age_days"]) is not int or not 1 <= inventory["max_age_days"] <= 30:
        raise ValueError("max_age_days must be an integer from 1 to 30")
    threshold = clock - timedelta(days=inventory["max_age_days"])
    amended = _time(inventory["amendments_checked_at"])
    if amended > clock or amended < threshold:
        blockers.append("amendment_check_stale_or_future")
    for doc in documents.values():
        if _time(doc["retrieved_at"]) < threshold:
            blockers.append("stale_document:" + doc["id"])
    _array(inventory["conflicts"], "conflicts")
    for item in inventory["conflicts"]:
        _string(item, "conflict")
    if inventory["conflicts"]:
        blockers.append("unresolved_evidence_conflicts")

    opportunity = review["opportunity"]
    _object(opportunity, ("id", "record_type", "status", "instrument", "access", "deadline", "citations"), where="opportunity")
    _string(opportunity["id"], "opportunity.id")
    enums = {"record_type": ("opportunity", "program", "directory", "historical_award", "funder_prospect"),
             "status": ("open", "rolling", "closed", "cancelled", "forecast", "unknown"),
             "instrument": ("grant", "reimbursement", "loan", "tax_credit", "prize", "unknown"),
             "access": ("open", "invitation_only", "unknown")}
    for key, options in enums.items():
        if opportunity[key] not in options:
            raise ValueError("Unsupported opportunity." + key)
    _object(opportunity["citations"], ("record_type", "status", "instrument", "access", "deadline"), where="opportunity.citations")
    for key, refs in opportunity["citations"].items():
        citations(refs, "opportunity." + key)
    if opportunity["record_type"] != "opportunity":
        reasons.append("not_an_open_opportunity_record")
    if opportunity["status"] in ("closed", "cancelled"):
        reasons.append("opportunity_" + opportunity["status"])
    elif opportunity["status"] not in ("open", "rolling"):
        blockers.append("opportunity_not_confirmed_open")
    if opportunity["instrument"] in ("loan", "tax_credit", "prize"):
        reasons.append("not_a_grant_or_reimbursement")
    elif opportunity["instrument"] == "unknown":
        blockers.append("unknown_funding_instrument")
    if opportunity["access"] != "open":
        blockers.append("application_access_requires_review")
    if opportunity["deadline"] is None:
        if opportunity["status"] != "rolling":
            blockers.append("missing_deadline")
    elif _time(opportunity["deadline"]) <= clock:
        reasons.append("deadline_passed")

    results = []
    ids = set()
    _array(review["requirements"], "requirements", True)
    for rule in review["requirements"]:
        _object(rule, ("id", "description", "fact_key", "operator", "expected", "decision", "citations"), where="requirement")
        for key in ("id", "description", "fact_key"):
            _string(rule[key], "requirement." + key)
        if rule["id"] in ids:
            raise ValueError("Duplicate requirement id")
        ids.add(rule["id"])
        if rule["operator"] not in ("equals", "one_of", "at_least", "at_most", "contains", "manual"):
            raise ValueError("Unsupported requirement operator")
        if rule["decision"] not in ("pass", "fail", "unknown"):
            raise ValueError("Unsupported review decision")
        expected = rule["expected"]
        if rule["operator"] == "one_of":
            if not isinstance(expected, list) or not expected or not all(_scalar(v) and v is not None for v in expected):
                raise ValueError("one_of requires nonempty scalar expected array")
        elif rule["operator"] in ("at_least", "at_most"):
            if not _number(expected):
                raise ValueError("Numeric predicate requires finite number")
        elif not _scalar(expected) or (expected is None and rule["operator"] != "manual"):
            raise ValueError("Predicate expected must be a non-null finite scalar")
        citations(rule["citations"], rule["id"])
        actual = _predicate(rule, facts)
        decision = actual
        if rule["decision"] == "unknown":
            decision = "unknown"
        elif actual != rule["decision"]:
            blockers.append("review_decision_not_supported:" + rule["id"])
            decision = "unknown"
        if decision == "fail":
            reasons.append("requirement_failed:" + rule["id"])
        if decision == "unknown":
            blockers.append("requirement_unresolved:" + rule["id"])
        results.append({"id": rule["id"], "decision": decision})

    checklist = []
    checklist_ids = set()
    _array(review["application_requirements"], "application_requirements", True)
    for item in review["application_requirements"]:
        _object(item, ("id", "description", "citations"), where="application_requirement")
        _string(item["id"], "application_requirement.id")
        _string(item["description"], "application_requirement.description")
        if item["id"] in checklist_ids:
            raise ValueError("Duplicate application requirement id")
        checklist_ids.add(item["id"])
        citations(item["citations"], "application." + item["id"])
        checklist.append({"id": item["id"], "description": item["description"], "status": "not_prepared", "citations": item["citations"]})
    decision = "unresolved" if blockers else "ineligible" if reasons else "eligible-for-review"
    fact_hash = hashlib.sha256(json.dumps(facts, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
    return {"schema_version": 1, "opportunity_id": opportunity["id"], "as_of": clock.isoformat(),
            "private_facts_sha256": fact_hash,
            "decision": decision, "blockers": list(dict.fromkeys(blockers)), "reasons": list(dict.fromkeys(reasons)),
            "requirements": results, "application_checklist": checklist,
            "evidence_hashes": {key: doc["sha256"] for key, doc in documents.items()},
            "limitation": "Reviewed supplied rules only; completeness and source authority are reviewer assertions. Not funder approval. Keep this case output private."}
