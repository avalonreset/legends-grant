# legends-grant

Agent entry point for US grant discovery and application work. Run
`python -m grant_engine doctor` using the module runtime before collection.
This checks local readiness; it makes no live provider requests.

## Route the task

- New search: `vault-map.md`, `find.md`, `grant_engine/data/us-sources.json`, then `match.md`.
- Nationwide product work: `docs/NATIONWIDE-DESIGN.md`, `docs/SOURCE-RESEARCH.md`
  and `docs/COVERAGE.md`.
- Run collection: `docs/RUNTIME.md`. Choose sources by applicant and purpose.
- Eligibility: `qualify.md`; verify current official notices and attachments.
- Applications: `apply.md` and `submit-lanes.md`. Draft within the request;
  submission requires authorization for that external action and a receipt.

No federal-first ordering. Federal, state, local, tribal and private sources
can all be the first useful route. Existing `states/` notes are background;
the researched machine-readable registry is `grant_engine/data/us-sources.json`.

## Intake and evidence

Use authorized `legends-empire` context or the applicant's named source. Obtain
entity type, project geography, purpose, beneficiaries, amount, timing and cash
constraints. Ownership, size, registrations and other details are requested
when a candidate's actual requirements make them relevant. Do not require an
individual or nonprofit to invent business identifiers.

Keep private profiles separate from the public evidence store. Store source
and retrieval dates, distinguish official and third-party evidence, preserve
unknowns and keep revisions. A search snippet, API success or open status does
not establish eligibility. Prior awards do not establish an open competition.

## Tools without overclaiming

The CLI plans sources, retrieves bounded public records, searches local evidence,
collects explicit public documents, verifies artifacts, compares snapshots and
evaluates reviewed rules. Research, rule extraction, clause interpretation,
notice completeness and final application decisions remain agent work.
No scheduler or automatic submission service is installed. Alexandria is not a dependency.

Use `collect-document` for the current notice and each required attachment or
amendment. Inspect the link inventory; it is not proof that all governing files
were found. Confirm the authoritative document set independently, then prepare
the review described in `docs/QUALIFICATION.md`. Keep private facts and review
outputs outside the public Store. Never convert unknowns into assumed passes.

For unimplemented sources, execute the planner's research tasks using available
web/browser tools, follow official documents, and report blocked access. Do not
bypass access controls or assume a vendor API permits bulk storage.

Use plain punctuation; no em dashes in generated public copy.
