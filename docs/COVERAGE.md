# Discovery coverage

Research date: **2026-10-01**. The registry is `grant_engine/data/us-sources.json`. This is a set of discovery routes, not a nationwide collection of open grants or a claim of exhaustive funding coverage.

## Counts and their meaning

| Measure | Count | Meaning |
|---|---:|---|
| Registry source rows | 115 | Distinct source IDs and canonical source URLs |
| State/district/territory research rows | 88 | 30 eastern and 58 western/territorial entries |
| Jurisdictions represented by those 88 rows | 56 | Exactly 50 states, DC, AS, GU, MP, PR and VI |
| National discovery/research rows | 23 | Federal sources and administrator, program, private and historical-data routes |
| Third-party CommonGrants feed rows | 4 | CA, PA, WA and MD AgileSix prototype feeds |
| Implemented adapter types referenced | 2 | `grants-gov` and `common-grants` |
| Source rows routed to structured discovery | 5 | One Grants.gov source and four CommonGrants sources |
| Source rows routed to agent research | 110 | No automated collection connector asserted for these rows |
| Opportunity records contained in this registry | 0 | Source rows are not opportunity evidence records |

Actual opportunity collection counts belong to discovery packets and store exports, together with retrieval timestamps, run limits, errors and completion flags. A configured adapter does not establish a successful live run. This registry assembly made no live collection claim and did not measure national recall. Earlier bounded API observations in the research are not full inventory proofs.

## Planner contract

Each row has matching `id` and `source_id`, an HTTPS URL, jurisdiction, source kind, access mode, evidence URLs and research retrieval date. All `applicant_types_exhaustive` values are `false`. Applicant labels are nonexhaustive discovery hints, not eligibility restrictions. The planner retains sources for review even where those hints do not match a requested applicant type; exact labels and existing engine aliases only affect ranking. Purpose tagging is not exhaustive and does not establish eligible use of funds.

The original 88 research rows retain their descriptions, applicant labels, verification states and evidence. Missing explicit date fields were filled from the documented 2026-10-01 research date. Virgin Islands routing uses `VI`; its original `USVI` label is retained in `research_jurisdiction`. `US` identifies national routes and is not a 57th state/territory.

The four configured CommonGrants base URLs are exactly:

- https://pa.api.cg.a6lab.ai (`commongrants-pa`)
- https://ca.api.cg.a6lab.ai (`commongrants-ca`)
- https://wa.api.cg.a6lab.ai (`commongrants-wa`)
- https://md.api.cg.a6lab.ai (`commongrants-md`)

These are **third-party prototype feeds, not official state endpoints**. Their records can overlap official state sources and must not inflate jurisdiction or unique-opportunity counts. Review original funder notices for authority, amendments, deadlines and eligibility. Their live status, completeness and freshness are not established by being present in this file.

## What remains incomplete

State coverage means at least one researched entry point in each jurisdiction. It does not mean every agency, county, municipality, tribal government, school district, utility, community foundation or corporation is represented. Some sources cover only one department, applicant class or funding sector. Massachusetts and Vermont entries include documented direct-fetch failures; several territory sources have narrower scope or weaker access evidence. Preserve each row's verification status rather than promoting everything to live-verified.

National directories locate administrators. HUD grantees, workforce boards, land-grant institutions, arts agencies, humanities councils, tribal governments and community foundations each require downstream notice discovery. Directory presence is not evidence of an open application cycle. Native philanthropy maps, Grantmakers.io and USAspending are historical/prospecting sources and cannot establish open opportunities. Corporate giving can be invitation-only or require organization verification.

Funding instruments remain distinct: grants, reimbursements, rebates, loans, tax incentives, prizes, equity, procurement and in-kind benefits are not interchangeable. A program's beneficiary is not necessarily its direct applicant; USDA RBDG, for example, can support businesses through eligible intermediaries without admitting ordinary for-profit businesses as direct grantees.

Only two adapter types are configured. DSIRE's documented APIs, CareerOneStop's authenticated API, Simpler.Grants.gov, SAM.gov and private platform integration surfaces are research routes here, not implemented adapters. Public pages and downloadable guidance do not establish supported bulk access or redistribution rights. No account, subscription or credential was created for this assembly.

## Validation receipt

The registry loaded successfully through `grant_engine.core.load_registry`. Checks passed for 115 unique IDs, 115 unique canonical URLs, matching source IDs, all applicant hints marked nonexhaustive, valid HTTPS source/evidence URLs, all four exact CommonGrants bases, and exactly the required 56 jurisdictions. A CA/individual planner invocation returned 26 source routes with eligibility unassessed. Original state research text/evidence is preserved; this is schema/planner verification, not notice or network verification.
