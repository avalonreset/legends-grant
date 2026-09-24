# match

Turn a vault-mapped business into a ranked grant shortlist. This is what
beats a generic "get me a grant" ask: the vault already knows the business,
so matching replaces infinite searching.

## Intake (from vault first, ask only for gaps)

Pull from the vault business note (see `vault-map.md`) before asking:

- Must-haves: legal name, entity type, state, NAICS, employees, revenue,
  years in business, ownership flags (woman, veteran, minority, rural,
  tribal), SAM.gov UEI status, use of funds, amount needed.
- Multi-client: one profile per client under `profiles/`; shared
  `sources.md` and state files serve all of them. Never mix client facts.
- Gaps: ask once for missing must-haves, then work. Never invent them.

## Order of battle

1. Federal API sweep (`find.md` Tier 1): grants.gov keyword from NAICS
   plus use-of-funds terms, `oppStatuses: posted`; forecasts second.
2. Nexus pass: applicant state file + STEP / USDA-RBDG geography check.
3. Private pass: `private-rolling.md` programs whose who-it-fits flags
   intersect the profile.
4. Funder-history pass (USAspending): who got funded for what, to calibrate
   ask size and narrative angle.

## Scoring (0-12, show the math)

- Eligibility fit 0-4: entity + geography + NAICS/size + use-of-funds.
- Deadline realism 0-3: days left vs package effort.
- Award fit 0-3: amount vs need, match/cost-share feasible.
- Channel ease 0-2: API/portal/email (2), human-click portal (1),
  mail/wet-sign (0, still listed with prep plan).

Rank by score, then deadline. Anything scoring 0 on eligibility is OUT
with the notice quote, not silently dropped. Top candidates get
opportunity notes; the rest stay a ranked list with one-line reasons.

## Output contract

Shortlist table plus verdict per candidate plus next action
(qualify-detail, draft-now, submit-with-auth, human-step).
Link each row to its opportunity note once written.
