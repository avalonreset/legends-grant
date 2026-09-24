# find

How the agent searches. Tier 1 first, always. Verified 2026-09-24.

## 1. Federal APIs (verified live)

- grants.gov search2: `POST https://api.grants.gov/v1/api/search2`,
  body `{"keyword":"<terms>","oppStatuses":"posted","rows":25}`. No key.
  Returns 200 with `errorcode: 0`, `hitCount` int, `oppHits[]`.
  `oppStatuses` accepts `posted` and `forecasted`. Retry once on timeout;
  keyword-heavy queries can time out, minimal retry returns 200.
- grants.gov detail: `POST https://api.grants.gov/v1/api/fetchOpportunity`,
  body `{"opportunityId": <int>}`. No key. Working key is the int
  `opportunityId` (example 336962 resolves to FA8651-22-S0021).
  The `opportunityNumber` variant returns backend-unavailable; do not use it.
- NIH Guide: `GET https://search.grants.nih.gov/guide/api/data`
  (`searchText`, `from`, `size`). Open. Plain queries verified 200.
- NIH RePORTER: `POST https://api.reporter.nih.gov/v2/projects/Search`,
  body `{"criteria":{"fiscalYears":[2024,2025]},"limit":20}`. Open.
- USAspending: `POST https://api.usaspending.gov/api/v2/search/spending_by_award`
  with `filters.award_type_codes`, plus
  `GET /api/v2/recipient/state/`. Open. Best for who-got-funded research.
- sbir.gov: `GET https://api.www.sbir.gov/public/api/solicitations?keyword=`
  and `/awards?agency=`. Note the host is `api.www.sbir.gov`
  (`api.sbir.gov` does not resolve). Docs carry a maintenance notice;
  direct curls returned 403 on 2026-09-24, so treat SBIR API as
  doc-verified, live-unconfirmed until re-probed.

## 2. Key-gated federal (doc-verified, needs Benjamin key)

- SAM.gov Opportunities v2:
  `GET https://api.sam.gov/opportunities/v2/search` with date params plus
  `api_key`. Limit max 1000. Doc:
  `https://open.gsa.gov/api/get-opportunities-public-api/`.
  Dummy-key probe from this machine returned empty 404 via gateway;
  needs a real key, then re-verify.
- SAM.gov Assistance Listings:
  `GET https://api.sam.gov/assistance-listings/v1/search` (plus alpha).
  Doc: `https://open.gsa.gov/api/assistance-listings-api/`.
  Same key story as above.
- SAM daily CSV mirror (no key): Contract Opportunities Full CSV public
  extract. Use before spending key quota.

## 3. State and structured

Check `states/_Index.md` for the applicant state file, then run the USDA
rural check where relevant: 1) confirm the rural county for the cited
program, 2) check the state file for a dated map result, 3) else open the
live USDA map or notice per task and quote it, never carry a verdict
forward, 4) record verdict + URL + date in the note. Veteran-owned
profiles also read `veteran.md` before scoring. Then SBA STEP,
USDA RBDG, EDA, MBDA, SBDC and Women's Business Centers. State lane is
still STUB as of 2026-09-24: index exists, live program rows fill on real
requests with retrieved dates. Record program, agency, deadline, URL,
retrieved date in an opportunity note.

## 4. Private rolling

Check `private-rolling.md`. Rolling means the cycle date in the note is
the truth, not a blog post.

## 5. Browser last

GrantWatch, Instrumentl, Foundation Directory, JS-gated portals. Note the
paywall or gate in the opportunity note. Never present a snippet as terms;
open the notice and quote the notice.

## Output

Ranked list with: title, funder, amount, deadline, eligibility verdict
pointer (`qualify.md`), submission channel, source URL plus retrieved date.
Write opportunity notes for the top candidates, not for everything.
See `match.md` for scoring.
