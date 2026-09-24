# federal

US federal entry points for business grants and R and D funding.
Endpoint status verified 2026-09-24; see `sources.md`.

- grants.gov: central federal database. Search + synopsis + forecast.
  Agent route: search2 + fetchOpportunity (no key, LIVE).
- SAM.gov: Assistance Listings (programs) + Opportunities (postings) +
  entity registration. API search needs a free public API key
  (doc-verified; live re-probe pending real key).
- SBA: STEP, size standards, SOME direct programs; mostly gateway to
  partners (SBDC, SCORE, Women's Business Centers).
- SBIR / STTR (sbir.gov): phased R and D awards across agencies.
  Fits tech and R and D businesses, not general operating cash.
  API host is `api.www.sbir.gov`; live health unconfirmed (403 +
  maintenance notice on probe date).
- USDA RBDG: rural business development. Geography-gated; check the map.
- EDA: regional economic development, often via intermediaries.
- MBDA: minority business development centers and programs.
- NIH Guide + RePORTER, NSF awards API, USAspending: LIVE lanes for
  health R and D plus who-got-funded research. Use USAspending to shape
  targeting before writing.

Working rule: federal API truth first, state file second for nexus,
private rolling third for speed. Record CFDA number where present.
