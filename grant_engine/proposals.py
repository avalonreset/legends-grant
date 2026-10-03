"""Offline proposal workbench: scaffold, mechanically check, and render drafts.

The engine does NOT write narrative, submit applications, or judge quality.
Narrative drafting happens in the agent recipe (LLM writing); this module
links that writing to supplied fact IDs as coarse per-answer citations,
checks mechanical requirements, and renders a reviewable Markdown draft
package. Citation lists do not prove semantic support; a reviewer confirms
that quoted text actually backs each claim. The engine makes no award,
eligibility, or submission claim, and it provides no submit path.

Inputs are two separate JSON files, mirroring the qualification split:

- proposal file: funder questions, limits, rubric, planned project and
  budget, draft answers with citations, attachment manifest, shared-evidence
  request, and an explicit substantive-review record.
- facts file: applicant evidence with stable IDs. Each fact declares a kind
  (``historical``, ``estimate``, ``commitment``) and a visibility
  (``private``, ``shareable``). Estimates and future commitments stay
  labeled; they are never rewritten as historical fact.

``check_proposal(proposal, facts)`` is pure: it validates schema (raising
``ValueError`` for malformed input), then returns mechanical blockers for
incomplete or inconsistent drafts, plus advisory warnings for ambiguous
narrative a reviewer should confirm. Its output omits answer and fact
statements but carries case metadata and sums (blocker IDs, word counts,
budget totals, review record, notes), which can be private, so it must
remain in private case storage. ``render_package(proposal, facts)``
writes the private review draft, including cited fact statements grouped
by kind, and must stay in private case storage.

Word counting is defined once here: split text on Unicode whitespace and
count tokens containing at least one Unicode alphanumeric character. Money
is decimal strings (``"15000.00"``) compared with ``decimal.Decimal``;
JSON numbers are rejected so float error cannot enter budget arithmetic.

A mechanically clean check is never called ready or verified. Factual
entailment (whether quoted text actually supports a claim) and rubric
quality remain substantive agent or human review, recorded explicitly in
``substantive_review`` and echoed unchanged by this tool.
"""

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

SCHEMA_VERSION = 1

FACT_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
MONEY_RE = re.compile(r"\d+(\.\d{1,2})?")
FACT_KINDS = ("historical", "estimate", "commitment")
VISIBILITY = ("private", "shareable")
REVIEW_STATUS = ("not_reviewed", "in_review", "reviewed")
FUNDING_SOURCES = ("grant", "match", "other")
ATTACHMENT_STATE = ("prepared", "missing")

# Explicit unresolved-placeholder markers scanned in draft text (answers,
# project title/summary, budget use-of-funds and line labels).
PLACEHOLDER_RES = (
    re.compile(r"\{\{"),
    re.compile(r"\}\}"),
    re.compile(r"\[\["),
    re.compile(r"\]\]"),
    re.compile(r"\?\?\?"),
    re.compile(r"\b(TODO|TBD|TBC|XXX)\b", re.IGNORECASE),
)

# Advisory narrative flags scanned in draft text only, never in funder
# prompts. A match is a manual-review warning, never a blocker: the engine
# cannot tell truthful history ("secured grant funding in 2024") from an
# unsupported guarantee, so a reviewer confirms the context and support.
# Each rule is (name, patterns). Plain administrative prose such as
# "board-approved budget", "eligible expenses", or "our team is qualified"
# is deliberately not matched.
CLAIM_RULES = (
    ("eligibility_mention", (
        re.compile(r"\b(we are|applicant is|organization is)\s+eligible\b", re.IGNORECASE),
    )),
    ("award_mention", (
        re.compile(r"\b(guaranteed|assured|secured)\b.{0,40}\b(award|funding|grant)\b", re.IGNORECASE),
        re.compile(r"\b(award|funding|grant)\b.{0,40}\b(guaranteed|assured|secured)\b", re.IGNORECASE),
        re.compile(r"\bwill be (awarded|funded)\b", re.IGNORECASE),
    )),
    ("submission_mention", (
        re.compile(r"\b(has been submitted|was submitted|already submitted)\b", re.IGNORECASE),
        re.compile(r"\bsubmission (is |was )?(complete|confirmed|received)\b", re.IGNORECASE),
    )),
)

LIMITATION = (
    "Mechanical format and arithmetic checks only. Factual entailment, "
    "citation support, and rubric quality require substantive agent or human "
    "review. This tool never submits, and its output makes no award or "
    "eligibility claim. Keep this case output private."
)


def _object(value, required, optional=(), where="proposal"):
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(where + " must be an object")
    if set(required) - value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError(where + " has missing or unsupported fields")


def _string(value, where):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(where + " must be a nonempty string")


def _text(value, where):
    if not isinstance(value, str):
        raise ValueError(where + " must be a string")


def _boolean(value, where):
    if type(value) is not bool:
        raise ValueError(where + " must be boolean")


def _array(value, where, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(where + " must be " + ("a nonempty" if nonempty else "an") + " array")


def _pos_int_or_null(value, where):
    if value is None:
        return
    if type(value) is not int or value <= 0:
        raise ValueError(where + " must be a positive integer or null")


def _time(value, where):
    _string(value, where)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(where + " must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(where + " requires timezone")
    return parsed.astimezone(timezone.utc)


def _fact_id(value, where):
    _string(value, where)
    if not FACT_ID_RE.fullmatch(value):
        raise ValueError(where + " must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}")


def _money(value, where):
    if type(value) is not str or not MONEY_RE.fullmatch(value):
        raise ValueError(where + " must be a decimal money string like \"15000.00\"")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(where + " is not valid decimal money") from exc
    if amount < 0:
        raise ValueError(where + " must not be negative")
    return amount


def _fmt(amount):
    return format(amount, ".2f")


def count_words(text):
    """Defined word count: whitespace-split tokens with >=1 alnum char."""
    return sum(1 for token in text.split() if any(char.isalnum() for char in token))


def _has_placeholder(text):
    return any(pattern.search(text) for pattern in PLACEHOLDER_RES)


def _claim_rules(text):
    return [name for name, patterns in CLAIM_RULES if any(p.search(text) for p in patterns)]


def _validate_facts(facts):
    _object(facts, ("schema_version", "facts"), where="facts")
    if type(facts["schema_version"]) is not int or facts["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Unsupported facts schema_version")
    entries = facts["facts"]
    if not isinstance(entries, dict) or not all(isinstance(key, str) for key in entries):
        raise ValueError("facts.facts must be an object")
    if not entries:
        raise ValueError("facts.facts must not be empty")
    validated = {}
    for key, entry in entries.items():
        _fact_id(key, "fact id")
        _object(entry, ("statement", "kind", "visibility"), ("source",), where="fact:" + key)
        _string(entry["statement"], "fact:" + key + ".statement")
        if len(entry["statement"]) > 5000:
            raise ValueError("fact:" + key + ".statement exceeds 5000 characters")
        if entry["kind"] not in FACT_KINDS:
            raise ValueError("fact:" + key + ".kind must be historical, estimate, or commitment")
        if entry["visibility"] not in VISIBILITY:
            raise ValueError("fact:" + key + ".visibility must be private or shareable")
        if "source" in entry:
            _string(entry["source"], "fact:" + key + ".source")
        validated[key] = entry
    return validated


def _validate_proposal(proposal):
    _object(proposal, ("schema_version", "opportunity_id", "questions", "budget", "answers", "substantive_review"),
            ("funder_name", "program", "attachments_required", "rubric", "limits", "project",
             "attachments", "shared_evidence"), where="proposal")
    if type(proposal["schema_version"]) is not int or proposal["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Unsupported proposal schema_version")
    _string(proposal["opportunity_id"], "proposal.opportunity_id")
    for field in ("funder_name", "program"):
        if field in proposal:
            _string(proposal[field], "proposal." + field)

    questions = proposal["questions"]
    _array(questions, "proposal.questions", nonempty=True)
    seen = set()
    for item in questions:
        _object(item, ("id", "prompt", "required"), ("max_words", "guidance"), where="question")
        _string(item["id"], "question.id")
        _string(item["prompt"], "question.prompt")
        _boolean(item["required"], "question.required")
        if item["id"] in seen:
            raise ValueError("Duplicate question id")
        seen.add(item["id"])
        _pos_int_or_null(item.get("max_words"), "question.max_words")
        if "guidance" in item:
            _string(item["guidance"], "question.guidance")
    by_question = {item["id"]: item for item in questions}

    required_docs = {}
    if "attachments_required" in proposal:
        _array(proposal["attachments_required"], "proposal.attachments_required")
        for item in proposal["attachments_required"]:
            _object(item, ("id", "description", "required"), where="attachments_required")
            _string(item["id"], "attachments_required.id")
            _string(item["description"], "attachments_required.description")
            _boolean(item["required"], "attachments_required.required")
            if item["id"] in required_docs:
                raise ValueError("Duplicate attachments_required id")
            required_docs[item["id"]] = item

    if "rubric" in proposal:
        _array(proposal["rubric"], "proposal.rubric")
        seen_rubric = set()
        for item in proposal["rubric"]:
            _object(item, ("id", "description"), where="rubric")
            _string(item["id"], "rubric.id")
            _string(item["description"], "rubric.description")
            if item["id"] in seen_rubric:
                raise ValueError("Duplicate rubric id")
            seen_rubric.add(item["id"])

    limits = {"max_total_words": None, "max_request": None, "unallowable_categories": [], "notes": ""}
    if "limits" in proposal:
        _object(proposal["limits"], (), ("max_total_words", "max_request", "unallowable_categories", "notes"),
                where="proposal.limits")
        raw = proposal["limits"]
        _pos_int_or_null(raw.get("max_total_words"), "proposal.limits.max_total_words")
        limits["max_total_words"] = raw.get("max_total_words")
        if raw.get("max_request") is not None:
            limits["max_request"] = _money(raw["max_request"], "proposal.limits.max_request")
        if "unallowable_categories" in raw:
            _array(raw["unallowable_categories"], "proposal.limits.unallowable_categories")
            for category in raw["unallowable_categories"]:
                _string(category, "proposal.limits.unallowable_categories entry")
            limits["unallowable_categories"] = list(raw["unallowable_categories"])
        if "notes" in raw:
            _text(raw["notes"], "proposal.limits.notes")
            limits["notes"] = raw["notes"]

    project = None
    if "project" in proposal:
        _object(proposal["project"], ("title", "summary"), where="proposal.project")
        _string(proposal["project"]["title"], "proposal.project.title")
        _string(proposal["project"]["summary"], "proposal.project.summary")
        project = proposal["project"]

    budget = proposal["budget"]
    _object(budget, ("currency", "total_requested", "use_of_funds", "lines"), ("total_project",), where="proposal.budget")
    if budget["currency"] != "USD":
        raise ValueError("proposal.budget.currency must be USD in schema 1")
    total_requested = _money(budget["total_requested"], "proposal.budget.total_requested")
    if total_requested <= 0:
        raise ValueError("proposal.budget.total_requested must be greater than zero")
    total_project = None
    if budget.get("total_project") is not None:
        total_project = _money(budget["total_project"], "proposal.budget.total_project")
    _string(budget["use_of_funds"], "proposal.budget.use_of_funds")
    _array(budget["lines"], "proposal.budget.lines", nonempty=True)
    seen_lines = set()
    lines = []
    for line in budget["lines"]:
        _object(line, ("id", "label", "category", "amount", "funding_source"), where="budget.line")
        _string(line["id"], "budget.line.id")
        _string(line["label"], "budget.line.label")
        _string(line["category"], "budget.line.category")
        if line["id"] in seen_lines:
            raise ValueError("Duplicate budget line id")
        seen_lines.add(line["id"])
        if line["funding_source"] not in FUNDING_SOURCES:
            raise ValueError("budget.line.funding_source must be grant, match, or other")
        lines.append({"id": line["id"], "label": line["label"], "category": line["category"],
                      "amount": _money(line["amount"], "budget.line:" + line["id"] + ".amount"),
                      "funding_source": line["funding_source"]})

    answers = proposal["answers"]
    _array(answers, "proposal.answers")
    seen_answers = set()
    for answer in answers:
        _object(answer, ("question_id", "text", "fact_refs"), where="answer")
        _string(answer["question_id"], "answer.question_id")
        _text(answer["text"], "answer.text")
        _array(answer["fact_refs"], "answer.fact_refs")
        for ref in answer["fact_refs"]:
            _string(ref, "answer.fact_refs entry")
        if answer["question_id"] in seen_answers:
            raise ValueError("Duplicate answer for question " + answer["question_id"])
        if answer["question_id"] not in by_question:
            raise ValueError("Answer references unknown question " + answer["question_id"])
        seen_answers.add(answer["question_id"])
    by_answer = {answer["question_id"]: answer for answer in answers}

    manifest = {}
    if "attachments" in proposal:
        _array(proposal["attachments"], "proposal.attachments")
        for item in proposal["attachments"]:
            _object(item, ("attachment_id", "status"), ("note",), where="attachments")
            _string(item["attachment_id"], "attachments.attachment_id")
            if item["attachment_id"] in manifest:
                raise ValueError("Duplicate attachments entry")
            if item["attachment_id"] not in required_docs:
                raise ValueError("Attachments entry without a declared requirement")
            if item["status"] not in ATTACHMENT_STATE:
                raise ValueError("attachments.status must be prepared or missing")
            if "note" in item:
                _text(item["note"], "attachments.note")
            manifest[item["attachment_id"]] = item

    shared = []
    if "shared_evidence" in proposal:
        _object(proposal["shared_evidence"], ("fact_ids",), where="proposal.shared_evidence")
        _array(proposal["shared_evidence"]["fact_ids"], "proposal.shared_evidence.fact_ids")
        for fid in proposal["shared_evidence"]["fact_ids"]:
            _string(fid, "proposal.shared_evidence.fact_ids entry")
        if len(set(proposal["shared_evidence"]["fact_ids"])) != len(proposal["shared_evidence"]["fact_ids"]):
            raise ValueError("Duplicate shared_evidence fact id")
        shared = list(proposal["shared_evidence"]["fact_ids"])

    review = proposal["substantive_review"]
    _object(review, ("status", "reviewer", "reviewed_at"), ("notes",), where="proposal.substantive_review")
    if review["status"] not in REVIEW_STATUS:
        raise ValueError("substantive_review.status must be not_reviewed, in_review, or reviewed")
    if review["reviewer"] is not None:
        _string(review["reviewer"], "proposal.substantive_review.reviewer")
    if review["reviewed_at"] is not None:
        _time(review["reviewed_at"], "proposal.substantive_review.reviewed_at")
    if review["status"] == "reviewed" and (review["reviewer"] is None or review["reviewed_at"] is None):
        raise ValueError("A reviewed status requires reviewer and reviewed_at")
    if review["status"] == "not_reviewed" and (review["reviewer"] is not None or review["reviewed_at"] is not None):
        raise ValueError("A not_reviewed status must not name a reviewer")
    if review["status"] == "in_review" and review["reviewed_at"] is not None:
        raise ValueError("An in_review status must not carry reviewed_at")
    if "notes" in review:
        _text(review["notes"], "proposal.substantive_review.notes")

    return {"questions": by_question, "required_docs": required_docs, "limits": limits,
            "project": project, "total_requested": total_requested, "total_project": total_project,
            "lines": lines, "answers": by_answer, "manifest": manifest, "shared": shared}


def check_proposal(proposal, facts):
    """Mechanically check a draft; raise ValueError for malformed schema.

    Evidence gaps and draft inconsistencies produce blockers rather than
    raising. Ambiguous narrative (eligibility, award, or submission
    mentions) produces advisory ``warnings`` for manual review; warnings
    never affect ``mechanical_checks_passed`` because the engine cannot
    judge truthful history. The result echoes ``substantive_review``
    unchanged and never calls the proposal ready or verified: entailment
    and rubric quality stay substantive review. Neither input is mutated.
    """
    valid = _validate_proposal(proposal)
    known = _validate_facts(facts)
    blockers = []
    warnings = []
    answer_reports = []
    total_words = 0

    def scan(text, where):
        if _has_placeholder(text):
            blockers.append("unresolved_placeholder:" + where)
        for rule in _claim_rules(text):
            warnings.append("claim_to_review:" + where + ":" + rule)

    for qid, question in valid["questions"].items():
        answer = valid["answers"].get(qid)
        if answer is None or not answer["text"].strip():
            if question["required"]:
                blockers.append("missing_answer:" + qid)
            answer_reports.append({"question_id": qid, "words": 0, "max_words": question.get("max_words"),
                                   "fact_refs": [], "fact_kinds": {}, "cited_unknown": []})
            continue
        where = "answer:" + qid
        words = count_words(answer["text"])
        total_words += words
        if question.get("max_words") is not None and words > question["max_words"]:
            blockers.append("answer_over_limit:" + qid)
        if not answer["fact_refs"]:
            blockers.append("answer_missing_citations:" + qid)
        kinds = {}
        unknown = []
        for ref in answer["fact_refs"]:
            entry = known.get(ref)
            if entry is None:
                blockers.append("unknown_fact_ref:" + qid + ":" + ref)
                unknown.append(ref)
            else:
                kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1
        scan(answer["text"], where)
        answer_reports.append({"question_id": qid, "words": words, "max_words": question.get("max_words"),
                               "fact_refs": list(answer["fact_refs"]), "fact_kinds": kinds,
                               "cited_unknown": unknown})

    if valid["limits"]["max_total_words"] is not None and total_words > valid["limits"]["max_total_words"]:
        blockers.append("total_over_limit")

    if valid["project"] is not None:
        scan(valid["project"]["title"], "project.title")
        scan(valid["project"]["summary"], "project.summary")

    budget_raw = proposal["budget"]
    scan(budget_raw["use_of_funds"], "budget.use_of_funds")
    grant_sum = sum((line["amount"] for line in valid["lines"] if line["funding_source"] == "grant"), Decimal("0"))
    all_sum = sum((line["amount"] for line in valid["lines"]), Decimal("0"))
    if grant_sum != valid["total_requested"]:
        blockers.append("budget_sum_mismatch")
    if valid["total_project"] is not None and all_sum != valid["total_project"]:
        blockers.append("budget_project_sum_mismatch")
    if valid["limits"]["max_request"] is not None and valid["total_requested"] > valid["limits"]["max_request"]:
        blockers.append("budget_exceeds_max")
    for line in valid["lines"]:
        scan(line["label"], "budget.line:" + line["id"])
        if line["category"] in valid["limits"]["unallowable_categories"]:
            blockers.append("budget_unallowable_category:" + line["id"])

    attachments = []
    for aid, required in valid["required_docs"].items():
        entry = valid["manifest"].get(aid)
        state = entry["status"] if entry is not None else "missing"
        if required["required"] and state != "prepared":
            blockers.append("missing_attachment:" + aid)
        attachments.append({"id": aid, "required": required["required"], "state": state})

    withheld = []
    unknown_shared = []
    for fid in valid["shared"]:
        entry = known.get(fid)
        if entry is None:
            blockers.append("unknown_shared_fact:" + fid)
            unknown_shared.append(fid)
        elif entry["visibility"] != "shareable":
            blockers.append("private_fact_in_shared_evidence:" + fid)
            withheld.append(fid)

    review = proposal["substantive_review"]
    echoed = {"status": review["status"], "reviewer": review["reviewer"],
              "reviewed_at": review["reviewed_at"], "notes": review.get("notes", "")}
    return {"schema_version": SCHEMA_VERSION, "opportunity_id": proposal["opportunity_id"],
            "mechanical_checks_passed": not blockers, "blockers": list(dict.fromkeys(blockers)),
            "warnings": list(dict.fromkeys(warnings)),
            "total_words": total_words, "answers": answer_reports,
            "budget": {"currency": "USD", "total_requested": _fmt(valid["total_requested"]),
                       "total_project": _fmt(valid["total_project"]) if valid["total_project"] is not None else None,
                       "grant_lines_sum": _fmt(grant_sum), "all_lines_sum": _fmt(all_sum),
                       "line_count": len(valid["lines"])},
            "attachments": attachments,
            "shared_evidence": {"requested": list(valid["shared"]), "withheld_private": withheld,
                                "unknown": unknown_shared},
            "substantive_review": echoed, "limitation": LIMITATION}


def new_scaffold(opportunity_id="synthetic-opportunity"):
    """Return (proposal, facts) starter files with honest unresolved markers."""
    if not isinstance(opportunity_id, str) or not opportunity_id.strip():
        raise ValueError("opportunity_id must be a nonempty string")
    proposal = {
        "schema_version": SCHEMA_VERSION,
        "opportunity_id": opportunity_id,
        "funder_name": "SYNTHETIC FUNDER (replace)",
        "questions": [{"id": "need", "prompt": "Describe the community need and who benefits. (Replace with the funder exact wording.)",
                       "required": True, "max_words": 250}],
        "attachments_required": [{"id": "budget-worksheet", "description": "Line-item budget worksheet. (Replace with the funder list.)",
                                  "required": True}],
        "rubric": [{"id": "need", "description": "Need is specific and supported. (Replace with the funder rubric; scoring stays human review.)"}],
        "limits": {"max_total_words": 1000, "max_request": "25000.00",
                   "unallowable_categories": ["alcohol", "lobbying"], "notes": ""},
        "project": {"title": "SYNTHETIC project title (replace)",
                    "summary": "TODO: replace with a one-paragraph project summary."},
        "budget": {"currency": "USD", "total_requested": "5000.00", "total_project": "6500.00",
                   "use_of_funds": "TODO: replace with a one-paragraph use-of-funds statement.",
                   "lines": [{"id": "line1", "label": "Equipment", "category": "equipment",
                              "amount": "5000.00", "funding_source": "grant"},
                             {"id": "match1", "label": "Volunteer labor (match)", "category": "in-kind",
                              "amount": "1500.00", "funding_source": "match"}]},
        "answers": [{"question_id": "need",
                     "text": "TODO: draft the need answer, then cite supplied facts such as org-founded.",
                     "fact_refs": ["org-founded"]}],
        "attachments": [],
        "shared_evidence": {"fact_ids": ["org-founded"]},
        "substantive_review": {"status": "not_reviewed", "reviewer": None, "reviewed_at": None, "notes": ""},
    }
    facts = {
        "schema_version": SCHEMA_VERSION,
        "facts": {
            "org-founded": {"statement": "SYNTHETIC: the organization began operating in 2019.",
                            "kind": "historical", "visibility": "shareable",
                            "source": "Synthetic articles of incorporation"},
            "meals-2029": {"statement": "SYNTHETIC: the kitchen served about 12000 meals in 2029.",
                           "kind": "historical", "visibility": "private", "source": "Synthetic annual log"},
            "year1-projection": {"statement": "SYNTHETIC: the plan projects serving 15000 meals in year one.",
                                 "kind": "estimate", "visibility": "private", "source": "Synthetic planning sheet"},
        },
    }
    return proposal, facts


def render_package(proposal, facts):
    """Render the private Markdown draft package; raise ValueError if malformed."""
    result = check_proposal(proposal, facts)
    known = _validate_facts(facts)
    lines = ["# Proposal draft package (PRIVATE)", "",
             "Private case draft. Keep this file and the facts file in case storage,",
             "outside the public evidence store. Sharing needs a separate review.", ""]
    lines.append("Opportunity: " + proposal["opportunity_id"])
    if "funder_name" in proposal:
        lines.append("Funder: " + proposal["funder_name"])
    if "program" in proposal:
        lines.append("Program: " + proposal["program"])
    lines.append("")

    status = "PASS" if result["mechanical_checks_passed"] else "FAIL"
    review = result["substantive_review"]
    review_line = "Substantive review: " + review["status"]
    if review["reviewer"]:
        review_line += " by " + review["reviewer"]
    if review["reviewed_at"]:
        review_line += " at " + review["reviewed_at"]
    review_line += "."
    lines.extend(["## Check status", "",
                  "Mechanical checks: " + status + " (" + str(len(result["blockers"])) + " blockers).",
                  "Total draft words: " + str(result["total_words"]) + ".",
                  review_line,
                  "",
                  "The engine scaffolds, checks, and renders agent-written drafts; it does not",
                  "write narrative, submit, or claim award or eligibility. Narrative writing",
                  "happens in the agent recipe. Factual entailment and rubric quality remain",
                  "substantive agent or human review.", ""])

    if "project" in proposal:
        lines.extend(["## Project", "", "Title: " + proposal["project"]["title"], "",
                      proposal["project"]["summary"], ""])

    lines.extend(["## Draft answers", ""])
    reports = {entry["question_id"]: entry for entry in result["answers"]}
    questions = {item["id"]: item for item in proposal["questions"]}
    for qid, question in questions.items():
        report = reports[qid]
        limit = "no limit" if report["max_words"] is None else str(report["max_words"]) + " words"
        lines.extend(["### " + qid + " (" + str(report["words"]) + " words; limit " + limit + ")", "",
                      "Prompt: " + question["prompt"], ""])
        answer = next((a for a in proposal["answers"] if a["question_id"] == qid), None)
        if answer is None or not answer["text"].strip():
            lines.extend(["No draft text supplied.", ""])
        else:
            lines.extend([answer["text"], ""])
        if report["fact_refs"]:
            lines.append("Cited facts:")
            for ref in report["fact_refs"]:
                entry = known.get(ref)
                if entry is None:
                    lines.append("- " + ref + " (unknown fact; resolve before sharing)")
                else:
                    lines.append("- " + ref + " (" + entry["kind"] + ", " + entry["visibility"] + ")")
            lines.append("")
        else:
            lines.extend(["Cited facts: none listed.", ""])

    budget = result["budget"]
    lines.extend(["## Budget (USD)", "", proposal["budget"]["use_of_funds"], "",
                  "| Line | Category | Source | Amount |", "|---|---|---|---|"])
    for line in proposal["budget"]["lines"]:
        lines.append("| " + line["id"] + ": " + line["label"] + " | " + line["category"] + " | "
                     + line["funding_source"] + " | " + line["amount"] + " |")
    lines.extend(["",
                  "Grant lines sum: " + budget["grant_lines_sum"] + "; total requested: " + budget["total_requested"] + ".",
                  "All lines sum: " + budget["all_lines_sum"]
                  + ("; total project: " + budget["total_project"] + "." if budget["total_project"] else "."),
                  "Arithmetic uses decimal money strings; JSON numbers are rejected.", ""])

    if "attachments_required" in proposal and proposal["attachments_required"]:
        lines.extend(["## Attachments", ""])
        states = {entry["id"]: entry for entry in result["attachments"]}
        for item in proposal["attachments_required"]:
            state = states[item["id"]]["state"]
            lines.append("- " + item["id"] + " (" + ("required" if item["required"] else "optional")
                         + ", " + state + "): " + item["description"])
        lines.append("")

    if "rubric" in proposal and proposal["rubric"]:
        lines.extend(["## Funder rubric (scoring stays human review)", ""])
        for item in proposal["rubric"]:
            lines.append("- " + item["id"] + ": " + item["description"])
        lines.append("")

    shared = result["shared_evidence"]
    lines.extend(["## Shared evidence candidates", ""])
    if not shared["requested"]:
        lines.extend(["None declared.", ""])
    else:
        for fid in shared["requested"]:
            entry = known.get(fid)
            if entry is None:
                lines.append("- " + fid + ": unknown fact; withheld.")
            elif entry["visibility"] != "shareable":
                lines.append("- " + fid + ": PRIVATE; withheld from shared evidence.")
            else:
                lines.append("- " + fid + " (" + entry["kind"] + "): " + entry["statement"])
        lines.append("")

    lines.extend(["## Cited facts appendix (private)", ""])
    for kind in FACT_KINDS:
        cited = sorted({ref for report in result["answers"] for ref in report["fact_refs"]
                        if ref in known and known[ref]["kind"] == kind})
        label = {"historical": "Historical facts", "estimate": "Estimates and projections",
                 "commitment": "Future commitments"}[kind]
        lines.append("### " + label)
        lines.append("")
        if not cited:
            lines.extend(["None cited.", ""])
            continue
        for ref in cited:
            entry = known[ref]
            lines.append("- " + ref + " (" + entry["visibility"] + "): " + entry["statement"])
        lines.append("")

    lines.extend(["## Blockers", ""])
    if not result["blockers"]:
        lines.extend(["None. Mechanical checks passed; substantive review still applies.", ""])
    else:
        for blocker in result["blockers"]:
            lines.append("- " + blocker)
        lines.append("")

    lines.extend(["## Manual review flags", ""])
    if not result["warnings"]:
        lines.extend(["None.", ""])
    else:
        lines.extend(["Advisory only; confirm the context and support.",
                      "These do not change mechanical checks.", ""])
        for warning in result["warnings"]:
            lines.append("- " + warning)
        lines.append("")

    lines.extend(["## Limitations", "", LIMITATION, ""])
    return "\n".join(lines)
