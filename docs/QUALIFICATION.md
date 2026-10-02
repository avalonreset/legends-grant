# Evidence-linked qualification review

The qualification command evaluates a supplied, reviewed set of mandatory rules against a separate private facts file. It checks schema, evidence hashes, exact quoted text, document inventory, freshness, opportunity state and explicit predicates. It does not discover rules, interpret legal language, authenticate websites, decide whether quoted language supports a rule, or prove that the reviewer found every clause.

The included files are fictional test data. They are not an available grant or a real applicant. Replay the example from the repository root:

```powershell
python -m grant_engine review --review examples/qualification-review.json --facts examples/qualification-facts.json --as-of 2030-10-02T12:00:00Z --output synthetic-assessment.json
```

Omit `--as-of` for a current review. An explicit date is a historical/synthetic replay, not a current eligibility claim. The example's dates are intentionally fixed, so its evidence fails freshness checks outside that interval.

## Files and privacy

The review file contains public source text and reviewed rules. Applicant facts belong only in the separate private file. The evaluator does not write to SQLite or store a profile. Keep real inputs and output in private case storage, outside the public repository and public evidence store. The CLI requires an explicit output file: the result reveals an applicant's assessment even though it omits fact values.

The output contains `private_facts_sha256`, a deterministic fingerprint of the facts used. A different fingerprint means a previous result must be reevaluated. This is not encryption, proof that a fact is true or current, or a scheduler. Keep the fingerprint private with the assessment. The caller must confirm facts and rerun when they change.

## Review format

The root object requires exactly `schema_version` (integer `1`), `opportunity`, `documents`, `inventory`, `requirements`, and `application_requirements`. Unknown fields and unsupported enum values are rejected. The [complete example](../examples/qualification-review.json) is the executable format reference.

`opportunity` requires:

- `id`: program/cycle identifier supplied by the reviewer.
- `record_type`: `opportunity`, `program`, `directory`, `historical_award`, or `funder_prospect`.
- `status`: `open`, `rolling`, `closed`, `cancelled`, `forecast`, or `unknown`.
- `instrument`: `grant`, `reimbursement`, `loan`, `tax_credit`, `prize`, or `unknown`.
- `access`: `open`, `invitation_only`, or `unknown`.
- `deadline`: an ISO timestamp including timezone, or `null` for a reviewed rolling program. A nonrolling opportunity without a deadline remains unresolved. Deadline equality counts as expired.
- `citations`: an object with the five keys `record_type`, `status`, `instrument`, `access`, and `deadline`; each maps to a nonempty citation array. Rolling programs still need a citation supporting their deadline treatment.

Each citation has `document_id`, an exact nonempty `quote`, and a human-readable `locator` such as page and section. Quotes must occur exactly in the referenced document text. This verifies that the text exists; reviewers must verify that it actually supports the associated assertion. Hash/quote matching alone cannot do that.

Every `documents` entry requires `id`, public HTTPS `url`, `kind` (`notice`, `attachment`, `amendment`, or `instructions`), boolean `authoritative`, timezone-aware `retrieved_at`, `text`, lowercase `sha256`, and `reviewed_sha256` (matching hash or `null` while unreviewed).

Both hashes bind the supplied UTF-8 **text**, not a PDF's raw bytes, downloaded HTML bytes, or a collection-manifest blob. Compute `sha256(text.encode('utf-8')).hexdigest()`. Preserve raw collection artifacts separately. Any text change needs a new hash and review; copying a raw PDF hash into this format fails validation. `reviewed_sha256` attests the reviewer reviewed that exact text. A hash is an integrity binding, not a signature or source-authentication service.

The reviewer must verify each URL belongs to the controlling publisher and that the evidence is current before setting `authoritative: true`. The evaluator makes no network request to authenticate those assertions. Third-party normalized feeds can discover leads but cannot clear this gate on their own.

`inventory` requires:

- `required_document_ids`: a nonempty unique list, exactly matching the included documents. Include the controlling notice, all required attachments/instructions and all applicable amendments. At least one document must have kind `notice`.
- `complete`: boolean attestation that collection is complete.
- `all_rules_reviewed`: boolean attestation that the entire controlling document set was reviewed for mandatory requirements, exceptions, exclusions and practical conditions.
- `amendments_checked_at`: timezone-aware timestamp for the latest source check.
- `max_age_days`: integer freshness limit from 1 through 30. Choose a tighter value for volatile notices or funder requirements; the ceiling is a product limit, not a guarantee that 30-day evidence is current.
- `conflicts`: array of unresolved conflict descriptions; any entry blocks qualification.

The inventory checks catch declared missing documents and incomplete review. **They cannot detect an attachment or disqualifying clause that the reviewer omitted from the inventory.** Mark completeness false when collection or interpretation is uncertain. Before an application action, refresh the controlling source and verify amendments regardless of this configurable age limit.

Each `requirements` entry is mandatory and needs `id`, `description`, `fact_key`, `operator`, `expected`, `decision` and `citations`. IDs must be unique. `decision` is the reviewer's proposed `pass`, `fail` or `unknown`; the evaluator checks it against the private fact and predicate. Do not include optional ranking preferences here.

| Operator | Expected value | Behavior |
|---|---|---|
| `equals` | Non-null scalar | Exact, case-sensitive comparison; booleans do not equal numbers |
| `one_of` | Nonempty array of non-null scalars | Exact membership |
| `at_least` / `at_most` | Finite number | Numeric comparison; booleans and numeric strings are not numbers |
| `contains` | Non-null scalar | Exact membership in a private fact array |
| `manual` | Scalar or null | Remains unknown; no automatic interpretation |

Facts are a flat JSON object whose values are finite scalars, null, or scalar arrays. Missing and null facts remain unknown. A supplied `unknown` decision cannot be upgraded automatically. A proposed pass unsupported by the predicate remains unresolved. For complex legal clauses, exceptions, optional branches, unresolved units or eligibility judgments, use `manual` and resolve them through further review; do not approximate them with an easier predicate. The runtime currently cannot clear a manual rule.

`application_requirements` is a nonempty array of objects with unique `id`, public `description`, and `citations`. Output checklist entries begin at `not_prepared`. These are preparation tasks, not checked attachments, generated application answers, portal validation or proof of submission.

## Decisions

- `eligible-for-review`: all supplied checks passed. This is a conditional internal review outcome, never funder approval or proof of complete eligibility.
- `ineligible`: current, internally consistent supplied evidence supports a failed mandatory predicate, closed/expired opportunity, non-opportunity record, or non-grant instrument. Interpret `reasons` in context: an excluded loan may still be useful financing, but is outside this grant decision.
- `unresolved`: any missing/stale/non-authoritative evidence, unreviewed revision, conflicting assertion, incomplete inventory, unknown fact, unsupported decision or manual rule requires work. Unresolved blockers take precedence over failure reasons because stale or incomplete evidence must not become a definitive negative assessment either.

Results include individual requirement decisions, blocker/reason codes, document hashes and an application checklist. They provide a reproducible review record. They do not automate extraction, grant applications, monitoring, change alerts or an award decision.

Python callers use `evaluate_review(review, facts, as_of=None)` from `grant_engine.qualification`. Malformed schema raises `ValueError`; valid but incomplete evidence returns `unresolved`. No input is mutated and no persistent state is written.
