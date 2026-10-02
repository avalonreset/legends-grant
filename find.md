# find

Search the US funding landscape by applicant, project and geography. There is
no federal-first requirement. A neighborhood charity, city department, startup,
tribe and university need different source mixes.

## Plan a search

1. Read authorized applicant context from `legends-empire` or another named
   source. Capture entity, project location and beneficiaries, purpose, amount,
   timing and financial constraints. Ask only for facts needed for the next gate.
2. Use `grant_engine/data/us-sources.json` and `grant_engine plan` to select national and
   jurisdiction sources. Applicant tags are nonexhaustive discovery hints.
3. Expand the geography into city, county, workforce board, community foundation,
   utility territory, tribal and sector administrators where relevant. Follow
   their official links to live opportunities; a directory entry is not a grant.
4. Search purpose synonyms, activities and beneficiaries, not just industry codes
   or the word grant. Include subgrants, rebates, vouchers, prizes and training
   subsidies as separately classified funding instruments.
5. Use structured adapters where implemented; otherwise inspect public pages,
   notices and attachments through available research tools. Preserve URLs,
   retrieval times, exact terms and unresolved access failures.

## Available automation

See `docs/RUNTIME.md` for bounded Grants.gov and four public CommonGrants feed
commands. The latter are third-party sources, not official state APIs. Verify
their records at the awarding agency before qualification. Feed health is not
proof that each record was rechecked recently.

Other source routes currently produce agent research tasks, not completed
searches. Record each source as searched, partial, blocked or not attempted.
Never report no opportunities when extraction or access failed.

## Source distinctions

- Grants.gov: federal opportunity discovery; eligibility still comes from the
  complete current notice and amendments.
- Assistance Listings: program directory; not every program has an open cycle.
- USAspending, NIH RePORTER, foundation filings: funding history and prospect
  discovery; historical awards are not open applications.
- SAM contract opportunities: procurement, a separate instrument from grants.
- State/local/private portals: program- and jurisdiction-specific evidence;
  read application details even when an aggregator supplies structured fields.
- Commercial databases: use only permitted access and storage. A documented API
  does not establish comprehensive coverage or redistribution rights.

## Deliver a search receipt

Provide candidate records with source and cycle identities, instrument, status,
amount, deadline including timezone, official evidence and next verification
step. Name missing fields and unavailable sources. Then use `qualify.md` and
`match.md`; collection is not qualification. Do not infer closure from absence
in a limited query or merge separate annual cycles on title alone.
