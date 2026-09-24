# sources

Registry of grant sources. Retrieved dates beat memory. Status as of 2026-09-24.

## Tier 1: verified live, no key, no browser

| Source | Route | Status |
|---|---|---|
| grants.gov search | `POST https://api.grants.gov/v1/api/search2` | LIVE, `errorcode 0`, hitCount int |
| grants.gov detail | `POST https://api.grants.gov/v1/api/fetchOpportunity` with int `opportunityId` | LIVE |
| NIH Guide | `GET https://search.grants.nih.gov/guide/api/data` | LIVE |
| NIH RePORTER | `POST https://api.reporter.nih.gov/v2/projects/Search` | LIVE |
| USAspending awards + recipient-by-state | `POST .../search/spending_by_award`, `GET .../recipient/state/` | LIVE |
| SAM daily CSV extract | Contract Opportunities Full CSV public extract | LIVE, no key |

## Tier 1b: doc-verified, key or health gated

| Source | Route | Status |
|---|---|---|
| SAM.gov Opportunities v2 | `GET https://api.sam.gov/opportunities/v2/search` + `api_key` | needs real key; dummy probe 404s at gateway |
| SAM.gov Assistance Listings | `GET https://api.sam.gov/assistance-listings/v1/search` | needs real key |
| sbir.gov solicitations + awards | `GET https://api.www.sbir.gov/public/api/...` (note `api.www` host) | 403 + maintenance notice on 2026-09-24; re-probe later |

## Tier 2: structured pages, no open API

SBA grants and STEP, USDA RBDG, EDA, MBDA, SBDC network, Women's Business
Centers, state economic development portals (see states index).

## Tier 3: browser or paywall

GrantWatch, Instrumentl, Foundation Directory Online, corporate portals,
JS-gated state and local sites. Record gate plus retrieved date.

## Private rolling (national)

Hello Alice, IFundWomen, Amber Grants / WomensNet, NASE Growth Grants,
FedEx, Comcast, Verizon. See `private-rolling.md` for cycle tracking.
