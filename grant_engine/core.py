"""Small, dependency-free public evidence store and source planner."""
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from urllib.parse import urlsplit, parse_qsl


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def utc_timestamp(value):
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("Timestamp requires timezone")
    return timestamp.astimezone(timezone.utc).isoformat(timespec="microseconds")


def future_observation(value):
    """Allow small clock skew, never let a future record own current status."""
    cutoff = datetime.fromisoformat(now()) + timedelta(minutes=5)
    return datetime.fromisoformat(utc_timestamp(value)) > cutoff


def material_hash(record):
    value = {k: v for k, v in record.items() if k != "retrieved_at"}
    value["evidence"] = {k: v for k, v in record["evidence"].items() if k != "feed_url"} if isinstance(record["evidence"], dict) else record["evidence"]
    return digest(value)


def normalize_run(run):
    public_only(run)
    result = dict(run)
    if not isinstance(result["source_id"], str) or not result["source_id"].strip() or type(result["complete"]) is not bool:
        raise ValueError("Invalid source run")
    result["fetched_at"] = utc_timestamp(result["fetched_at"])
    if not isinstance(result.get("errors", []), list):
        raise ValueError("Run errors must be an array")
    if result["complete"] and result.get("errors"):
        raise ValueError("A run with errors cannot be complete")
    for field in ("hit_count", "records_returned", "next_start", "limit"):
        value = result.get(field)
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError("Run counts must be nonnegative integers")
    if "bounded" in result and type(result["bounded"]) is not bool:
        raise ValueError("Run bounded flag must be boolean")
    if result["complete"] and result.get("bounded"):
        raise ValueError("A bounded run cannot be complete")
    if result["complete"] and result.get("hit_count") is not None and result.get("records_returned") is not None and result["hit_count"] != result["records_returned"]:
        raise ValueError("Complete run counts disagree")
    return result


SENSITIVE = {"token", "accesstoken", "refreshtoken", "accesskey", "apikey", "authorization", "password", "secret", "ssn", "ein", "applicant", "applicantprofile", "profile", "bankaccount", "clientid"}


def public_only(value, redact=False):
    """Reject structured private inputs; remove API-issued authentication fields.

    This is defense in depth, not detection of secrets embedded in arbitrary prose.
    The database is ONLY for public source records, never client profiles.
    """
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            normalized = re.sub(r"[^a-z]", "", key.lower())
            if normalized in SENSITIVE:
                if redact:
                    continue
                raise ValueError("Public evidence cannot contain private or credential fields")
            result[key] = public_only(item, redact)
        return result
    if isinstance(value, list):
        return [public_only(x, redact) for x in value]
    if isinstance(value, str) and value.startswith(("https://", "http://")):
        parsed = urlsplit(value)
        if parsed.username or parsed.password or any(re.sub(r"[^a-z]", "", k.lower()) in SENSITIVE for k, _ in parse_qsl(parsed.query)):
            raise ValueError("Credential-bearing URL is not public evidence")
    return value


def normalize(record):
    public_only(record)
    result = dict(record)
    for key in ("source_id", "program_id", "cycle_id", "title", "url", "retrieved_at", "evidence"):
        if key not in result or result[key] in (None, ""):
            raise ValueError("Record requires " + key)
    for key in ("source_id", "program_id", "cycle_id", "title", "url", "retrieved_at"):
        if not isinstance(result[key], str) or not result[key].strip():
            raise ValueError("Record identity and provenance must be strings")
    if urlsplit(result["url"]).scheme not in ("http", "https"):
        raise ValueError("Evidence URL must be HTTP(S)")
    result["retrieved_at"] = utc_timestamp(result["retrieved_at"])
    result.setdefault("record_type", "opportunity")
    result.setdefault("status", "unknown")
    if result["record_type"] not in ("opportunity", "program", "funder_prospect", "historical_award", "directory"):
        raise ValueError("Unsupported record_type")
    if result["status"] not in ("unknown", "open", "forecast", "rolling", "closed", "cancelled", "archived"):
        raise ValueError("Unsupported status")
    return result


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 2):
            self.db.close()
            raise ValueError("Unsupported database schema version")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS revisions (
          seq INTEGER PRIMARY KEY, source_id TEXT NOT NULL, program_id TEXT NOT NULL,
          cycle_id TEXT NOT NULL, hash TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS runs (
          seq INTEGER PRIMARY KEY, source_id TEXT NOT NULL, fetched_at TEXT NOT NULL,
          complete INTEGER NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS observations (
          seq INTEGER PRIMARY KEY, source_id TEXT NOT NULL, program_id TEXT NOT NULL,
          cycle_id TEXT NOT NULL, observed_at TEXT NOT NULL, hash TEXT UNIQUE NOT NULL,
          revision_seq INTEGER NOT NULL REFERENCES revisions(seq), payload TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS revision_no_update BEFORE UPDATE ON revisions
          BEGIN SELECT RAISE(ABORT, 'Immutable evidence'); END;
        CREATE TRIGGER IF NOT EXISTS revision_no_delete BEFORE DELETE ON revisions
          BEGIN SELECT RAISE(ABORT, 'Immutable evidence'); END;
        CREATE TRIGGER IF NOT EXISTS run_no_update BEFORE UPDATE ON runs
          BEGIN SELECT RAISE(ABORT, 'Immutable run'); END;
        CREATE TRIGGER IF NOT EXISTS run_no_delete BEFORE DELETE ON runs
          BEGIN SELECT RAISE(ABORT, 'Immutable run'); END;
        CREATE TRIGGER IF NOT EXISTS observation_no_update BEFORE UPDATE ON observations
          BEGIN SELECT RAISE(ABORT, 'Immutable observation'); END;
        CREATE TRIGGER IF NOT EXISTS observation_no_delete BEFORE DELETE ON observations
          BEGIN SELECT RAISE(ABORT, 'Immutable observation'); END;
        PRAGMA user_version=2;
        """)

    def close(self):
        self.db.close()

    def ingest(self, packet):
        public_only(packet)
        if isinstance(packet, dict) and "run" in packet and "runs" in packet:
            raise ValueError("Packet cannot contain both run and runs")
        records = packet if isinstance(packet, list) else packet.get("records", [])
        normalized = [normalize(record) for record in records]
        if any(future_observation(record["retrieved_at"]) for record in normalized):
            raise ValueError("Observation timestamp exceeds current time plus five minutes")
        runs = ([packet["run"]] if "run" in packet else packet.get("runs", [])) if isinstance(packet, dict) else []
        runs = [normalize_run(run) for run in runs]
        added = 0
        with self.db:
            for record in normalized:
                # Retrieval is an observation, not a material program change.
                ids = (record["source_id"], record["program_id"], record["cycle_id"])
                checksum = material_hash(record)
                previous = self.db.execute("SELECT seq FROM revisions WHERE source_id=? AND program_id=? AND cycle_id=? AND hash=?", (*ids, checksum)).fetchone()
                if previous:
                    revision_seq = previous[0]
                else:
                    revision_seq = self.db.execute("INSERT INTO revisions(source_id,program_id,cycle_id,hash,payload) VALUES(?,?,?,?,?)", (*ids, checksum, canonical(record))).lastrowid
                    added += 1
                self.db.execute("INSERT OR IGNORE INTO observations(source_id,program_id,cycle_id,observed_at,hash,revision_seq,payload) VALUES(?,?,?,?,?,?,?)", (*ids, record["retrieved_at"], digest(record), revision_seq, canonical(record)))
            for run in runs:
                if not self.db.execute("SELECT 1 FROM runs WHERE payload=?", (canonical(run),)).fetchone():
                    self.db.execute("INSERT INTO runs(source_id,fetched_at,complete,payload) VALUES(?,?,?,?)", (run["source_id"], run["fetched_at"], int(run["complete"]), canonical(run)))
        return added

    def export(self, history=False):
        query = "SELECT payload FROM observations ORDER BY seq" if history else "SELECT payload FROM (SELECT payload,source_id,program_id,cycle_id, ROW_NUMBER() OVER (PARTITION BY source_id,program_id,cycle_id ORDER BY observed_at DESC,seq DESC) AS rank FROM observations) WHERE rank=1 ORDER BY source_id,program_id,cycle_id"
        return {"schema_version": 2, "records": [json.loads(r[0]) for r in self.db.execute(query)], "runs": [json.loads(r[0]) for r in self.db.execute("SELECT payload FROM runs ORDER BY seq")]}

    def check(self):
        issues = []
        if self.db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            issues.append("SQLite integrity check failed")
        required_triggers = {table + suffix for table in ("revision", "run", "observation") for suffix in ("_no_update", "_no_delete")}
        triggers = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        if not required_triggers <= triggers:
            issues.append("Missing immutability trigger")
        for source, program, cycle, checksum, payload in self.db.execute("SELECT source_id,program_id,cycle_id,hash,payload FROM revisions"):
            record = normalize(json.loads(payload))
            if future_observation(record["retrieved_at"]):
                issues.append("Future revision observation timestamp")
            if checksum != material_hash(record):
                issues.append("Revision checksum mismatch")
            if (source, program, cycle) != tuple(record[key] for key in ("source_id", "program_id", "cycle_id")):
                issues.append("Revision index mismatch")
        for source, program, cycle, observed, checksum, payload, revision_hash in self.db.execute("SELECT o.source_id,o.program_id,o.cycle_id,o.observed_at,o.hash,o.payload,r.hash FROM observations o LEFT JOIN revisions r ON o.revision_seq=r.seq"):
            record = normalize(json.loads(payload))
            if future_observation(record["retrieved_at"]):
                issues.append("Future observation timestamp")
            if digest(record) != checksum or material_hash(record) != revision_hash:
                issues.append("Observation checksum mismatch")
            if (source, program, cycle, observed) != tuple(record[key] for key in ("source_id", "program_id", "cycle_id", "retrieved_at")):
                issues.append("Observation index mismatch")
        for source, fetched, complete, payload in self.db.execute("SELECT source_id,fetched_at,complete,payload FROM runs"):
            run = normalize_run(json.loads(payload))
            if (source, fetched, complete) != (run["source_id"], run["fetched_at"], int(run["complete"])):
                issues.append("Run index mismatch")
        return {"ok": not issues, "issues": issues, "revisions": self.db.execute("SELECT COUNT(*) FROM revisions").fetchone()[0]}


def values(value):
    return [value] if isinstance(value, str) else (value or [])


def load_registry(path):
    with open(path, encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    sources = payload if isinstance(payload, list) else payload["sources"]
    ids = [s["id"] for s in sources]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate source ids")
    public_only(sources)
    return sources


def applicant_tag(value):
    tag = re.sub(r"[\s-]+", "_", str(value).strip().lower())
    aliases = {
        "business": "for_profit", "businesses": "for_profit",
        "small_business": "for_profit", "small_businesses": "for_profit",
        "nonprofits": "nonprofit", "non_profit": "nonprofit", "non_profits": "nonprofit",
        "public_agency": "government", "public_agencies": "government",
        "local_government": "government", "state_government": "government",
        "local_governments": "government", "state_governments": "government",
        "municipal_government": "government", "municipalities": "government",
        "county_government": "government", "counties": "government",
        "government_agencies": "government", "state_agencies": "government",
        "cities": "government", "towns": "government",
        "state_and_local_governments": "government",
        "tribal_governments": "tribal_government", "tribe": "tribal_government",
        "tribes": "tribal_government", "tribal": "tribal_government",
        "research_institutions": "research_institution",
        "researchers": "researcher", "individuals": "individual",
        "universities": "education", "university": "education",
        "higher_education": "education", "educational_institutions": "education",
        "education_institutions": "education", "community_colleges": "education",
        "training_providers": "training_provider", "farmers": "farmer",
        "artists": "artist", "students": "student", "startups": "for_profit",
        "startup": "for_profit", "employers": "for_profit", "employer": "for_profit",
    }
    return aliases.get(tag, tag)


def jurisdiction_tag(value):
    tag = str(value).strip().upper()
    return "VI" if tag == "USVI" else tag


def plan(sources, jurisdiction=None, applicant_type=None, purpose=None):
    result = []
    jurisdiction = jurisdiction_tag(jurisdiction) if jurisdiction else None
    if jurisdiction in {"US", "USA", "NATIONAL", "ALL", "*"}:
        jurisdiction = None
    for source in sources:
        jurisdictions = [jurisdiction_tag(x) for x in values(source.get("jurisdictions", source.get("jurisdiction")))]
        applicants = [applicant_tag(x) for x in values(source.get("applicant_types"))]
        purposes = [str(x).lower() for x in values(source.get("purposes"))]
        if jurisdiction and jurisdictions and not set(jurisdictions) & {jurisdiction.upper(), "US", "USA", "NATIONAL", "ALL", "*"}:
            continue
        applicant_match = bool(applicant_type and set(applicants) & {applicant_tag(applicant_type), "all", "*"})
        if applicant_type and applicants and not applicant_match and source.get("applicant_types_exhaustive") is True:
            continue
        exact_purpose = bool(purpose and purpose.lower() in purposes)
        purpose_terms = set(re.findall(r"\w+", purpose.casefold())) if purpose else set()
        hint_text = " ".join(str(source.get(key, "")) for key in ("name", "description", "notes", "source_kind"))
        hint_terms = set(re.findall(r"\w+", hint_text.casefold().replace("_", " ")))
        textual_purpose = bool(purpose_terms and purpose_terms <= hint_terms)
        # Purpose tags are discovery hints, never proof of eligibility.
        score = int(bool(jurisdiction and jurisdiction.upper() in jurisdictions)) * 2 + int(exact_purpose or textual_purpose) + int(applicant_match)
        item = dict(source)
        item.update(route_score=score, reason={"jurisdiction_match": bool(jurisdiction and jurisdiction.upper() in jurisdictions), "purpose_match": exact_purpose, "purpose_text_hint_match": textual_purpose, "applicant_hint_match": applicant_match}, action="structured_discovery" if source.get("adapter") in ("grants-gov", "common-grants") else "agent_research", eligibility="unassessed")
        if item["action"] == "agent_research":
            item["research_task"] = "Inspect the official source and current notices; preserve dated evidence, administrator, applicant restrictions and cycle. Directory presence does not establish an open grant."
        result.append(item)
    return sorted(result, key=lambda x: (-x["route_score"], x["id"]))


def report(packet):
    lines = ["# Public grant evidence report", "", "Discovery evidence only. Eligibility is unassessed; source coverage is not exhaustive.", ""]
    for run in packet.get("runs", []):
        lines.append(f"- Source {run['source_id']}: complete={run.get('complete', False)}; fetched {run['fetched_at']}; errors={len(run.get('errors', []))}")
    for record in packet["records"]:
        title = record["title"].replace("\n", " ")
        lines.extend(["", "## " + title, "", f"- Type: {record['record_type']}; observed status: {record['status']}", f"- Source: {record['url']}", f"- Retrieved: {record['retrieved_at']}", f"- Identity: {record['source_id']} / {record['program_id']} / {record['cycle_id']}", "- Eligibility: unassessed; inspect governing notice and amendments."])
        metadata = record.get("metadata", {})
        lines.extend([f"- Authority: {metadata.get('authority', 'unspecified; verify upstream source')}", f"- Funding instrument (raw): {canonical(metadata.get('instrument_raw'))}", f"- Confirmed grant instrument: {metadata.get('is_confirmed_grant', 'unknown')}"])
        if "official_notice_url_available" in metadata:
            lines.extend([f"- Upstream notice URL supplied: {metadata['official_notice_url_available']} (authority remains unverified)", f"- Notice URL usable for HTTPS collection: {metadata.get('source_url_usable_for_collection', False)}", f"- Notice URL requires HTTPS resolution: {metadata.get('source_url_requires_https_resolution', False)}"])
        if isinstance(record.get("evidence"), dict) and record["evidence"].get("feed_url"):
            lines.append("- Third-party feed: " + record["evidence"]["feed_url"])
    return "\n".join(lines) + "\n"
