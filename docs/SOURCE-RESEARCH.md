# Nationwide source research and collection strategy

Research date: October 1, 2026. Public primary documentation and a source registry were investigated across all 50 states, DC, five inhabited territories and national/local/private discovery networks. Official-page or search-index verification establishes a source entry point; it does not establish working ingestion, current application availability or exhaustive coverage. No commercial account, purchase, subscription, outreach or application was performed for this research.

The product uses several source classes together. Source selection follows the applicant and purpose. Federal APIs are one valuable collection method, not the mandatory first search for every applicant. The implemented evidence CLI and proposed product boundaries are described in [NATIONWIDE-DESIGN.md](NATIONWIDE-DESIGN.md).

## What a source can prove

| Source class | Useful evidence | What it cannot establish by itself |
|---|---|---|
| Current official notice | Application terms, cycle, eligibility, deadlines and amendments | Applicant compliance with facts not yet supplied |
| Programme catalogue | Programme identity, purpose and administrator | Open application window or remaining funds |
| Directory | Organizations, jurisdictions and official routing | Available grant or applicant eligibility |
| Historical award/filing | Prior recipients, giving patterns and intermediary relationships | An open competition, future award or invitation |
| Application platform | Submission destination, forms and customer workflow | A comprehensive catalogue of all funders using it |
| Licensed discovery feed | Aggregated metadata under its contract | Unrestricted republication, accurate original terms or universal coverage |
| Search result/newsletter | Candidate notices and changes | Final evidence when the governing notice is unavailable |

Professional discovery combines open-call searches, historical prospecting, administrator tracing, programme calendars and relationships. [Candid's prospecting guidance](https://candid.org/blogs/funder-prospecting-strategy-securing-nonprofit-grants-101/) supports using past giving and mission fit. [Its application guidance](https://learning.candid.org/find-funder-application-instructions/269056) emphasizes approach requirements. A promising funder can belong in a prospecting queue while being ineligible for an apply-now queue.

## Federal sources within the national portfolio

| Source | Access and role | Limits and next verification |
|---|---|---|
| [Grants.gov API](https://www.grants.gov/api/api-guide), [XML extracts](https://www.grants.gov/help/xml-extract/), [RSS](https://www.grants.gov/connect/rss-feeds) | No-auth search/detail; daily bulk baseline and change hints. The CLI has a bounded search/detail adapter. | Full snapshot reconciliation is proposed. Preserve forecasts, archived records and instrument codes. Observe [attribution terms](https://www.grants.gov/api/terms-conditions). RSS alone does not establish complete history. |
| [Simpler.Grants.gov API](https://wiki.simpler.grants.gov/product/api) and [extracts](https://wiki.simpler.grants.gov/product/api/extracts) | Keyed native API, JSON/CSV extracts and CommonGrants integration; official [open-source application](https://github.com/HHS/simpler-grants-gov). | Substantially overlaps Grants.gov. Crosswalk legacy IDs rather than double-count. Documentation/code pagination differences need deployed-contract testing. Reuse focused schemas and tests, not an entire infrastructure fork. |
| [SAM Assistance Listings](https://open.gsa.gov/api/assistance-listings-api/) | Keyed programme/administrator reference. Documentation specifies low quotas for some nonfederal users. | Not an open-cycle feed. Resolve documented pagination inconsistencies before full collection; published date is not a proven modification cursor. |
| [USAspending](https://api.usaspending.gov/), [NIH RePORTER](https://api.reporter.nih.gov/), [NSF awards](https://www.nsf.gov/awardsearch/) | Award history, recipient research and potential intermediaries. | Keep separate from opportunities. Preserve award/obligation/outlay semantics and reporting dates. |
| [SBIR resources](https://www.sbir.gov/data-resources) and [topics](https://www.sbir.gov/topics) | Research-commercialization solicitations/topics and historical exports. | [API page](https://www.sbir.gov/api) reports maintenance. Originating agency notices may be newer. Separate contracts from grants and exports from full corpus. |
| [Federal Register API](https://www.federalregister.gov/developers/documentation/api/v1) | Notices, corrections, withdrawals and policy changes. | Classify notice purpose and link exact programme/cycle IDs; searching “grant” is not a complete opportunity inventory. |
| [USA.gov active challenges](https://www.usa.gov/find-active-challenge) and [agency/archive directory](https://www.usa.gov/other-government-challenges) | Prize/challenge discovery after [Challenge.gov's March 2026 sunset](https://digital.gov/services/challenge-gov/). | Preserve competition stages and noncash awards; archived challenges are historical. No exhaustive successor bulk feed established. |

Agency authority can differ from generic assumptions. [NIH's FY2026 notice](https://grants.nih.gov/grants/guide/notice-files/NOT-OD-25-143.html) makes Grants.gov the official NOFO source while NIH Guide continues policy/informational notices. [NSF RSS](https://www.nsf.gov/rss), [NASA NSPIRES](https://nspires.nasaprs.com/external/) and [DOE NETL eXCHANGE](https://netl-exchange.energy.gov/) illustrate additional feed, programme-element and document-revision needs. Follow current migration notices and preserve multiple application-stage deadlines.

CommonGrants supports interchange but requires losslessness checks. The reviewed [HHS integration](https://github.com/HHS/simpler-grants-gov/blob/8584b47a4ed4e88a27db4fc10a48629527b69665/api/src/api/common_grants/COMMON_GRANTS_INTEGRATION.md) and [transformation code](https://github.com/HHS/simpler-grants-gov/blob/8584b47a4ed4e88a27db4fc10a48629527b69665/api/src/services/common_grants/transformation.py) show why native competition dates, skipped filters, omitted malformed records and timestamp fallbacks need independent attention. Code observations do not by themselves establish production failures.

## State and territory collection

The [source registry](../grant_engine/data/us-sources.json) is a navigation and source-planning asset. It is not 50 functioning state adapters. Many central portals cover particular departments or applicant classes; some explicitly say they are non-comprehensive. Most reviewed sources expose HTML, tables, PDFs or account-based application systems. A documented download, search-index result, successful page fetch and functioning adapter are distinct readiness states.

Representative sources show the range of work needed:

| Geography | Primary source | Collection implication |
|---|---|---|
| Northeast | [Maine Community Funding Finder](https://www.maine.gov/moca/funding) | Applicant/agency/instrument filters and mixed funders; verify original notice deadlines instead of trusting a status badge. |
| Northeast | [New York SFS guidance](https://www.sfs.ny.gov/index.php/vendors) | Public opportunity discovery and separate account/prequalification workflow; old Grants Gateway assumptions are obsolete. |
| Northeast | [Rhode Island opportunities](https://controller.admin.ri.gov/grants-management/state-rhode-island-grant-funding-opportunities) | State-agency calls and application portal; email alerts are an optional separately authorized channel. |
| Mid-Atlantic | [Pennsylvania grants](https://www.pa.gov/grants), [Maryland resource library](https://grants.maryland.gov/Pages/Resource-Library.aspx) | A multi-agency finder and a referral directory require different adapter contracts. |
| Southeast | [North Carolina directory](https://www.nc.gov/your-government/all-nc-state-services/grant-opportunities), [Alabama ADECA](https://adeca.alabama.gov/about/funding-opportunities/) | Programme catalogue versus agency-specific open calls; neither implies every local or private programme is covered. |
| Midwest | [Indiana agency opportunities](https://www.in.gov/sba/grants/resources-for-subrecipients/state-agency-grant-opportunities/), [North Dakota public opportunities](https://grants.nd.gov/storefrontFOList.do) | Public discovery and authenticated application are separate; agency-specific systems may sit outside central portals. |
| Midwest | [Wisconsin DOJ](https://www.wisdoj.gov/Pages/Grants/grants.aspx), [Ohio portal](https://grantsportal.ohio.gov/) | DOJ migrated to WebGrants in 2026. Ohio research encountered a loading shell/timeout, so browser extraction remains a verification task. |
| Mountain | [New Mexico grant search](https://platform.dfa.nm.gov/grant-search.html), [Montana WebGrants](https://funding.mt.gov/index.jsp) | New Mexico mixes state/federal records; deduplicate mirrors. Montana agency migrations make a single legacy portal insufficient. |
| Mountain | [Utah business funding](https://business.utah.gov/grants-funding/), [Wyoming grants office](https://sbd.wyo.gov/grants) | Instruments and past/available programmes differ. A hub's stale-information warning must remain visible. |
| South Central | [Texas ESBD grants](https://www.txsmartbuy.gov/esbd-grants), [Governor PSO eGrants](https://egrants.gov.texas.gov/), [HHS](https://grants.hhs.texas.gov/Grants/) | Statewide search and agency eGrants are distinct. ESBD's officially linked endpoint returned 404 during research and is not ingestion-ready; HHS showed no open opportunities, a valid source state. |
| Pacific | [Washington FundHubWA](https://fundhub.wa.gov/funding-opportunities/), [California open dataset](https://lab.data.ca.gov/dataset/california-grants-portal) | Washington is climate/energy/infrastructure-focused and mixes instruments. California documents daily CSV/query options; exact download/API execution still needs verification. Inbound agency JSON publishing docs are not consumer API docs. |
| Alaska | [GEMS](https://gems.dhss.alaska.gov/Home/) | Agency solicitations and RFIs/RFPs need classification; account required to apply does not imply account required for all public discovery. |
| Puerto Rico | [Justice notices](https://www.justicia.pr.gov/category/avisospublicos-subvencionesestatales/), [DDEC incentives](https://www.desarrollo.pr.gov/ayudas-e-incentivos?tab=expandir) | Separate current calls, historical cycles, scholarships and business incentives; bilingual/source-language evidence matters. |
| Guam/USVI | [Guam grants](https://www.guam.gov/grants/), [USVI LEPC programmes](https://lepc.vi.gov/grant-programs/) | Stale gateway material and programme-only indexes require fresh notice discovery. |
| American Samoa/CNMI | [AS Commerce news](https://doc.as.gov/news), [CNMI opioid council](https://www.cnmioag.org/cnmi-opc/) | Mixed news and specialised settlement-funded calls, not territory-wide catalogues. The observed AS FY2026 call was closed; cycle status must come from the actual notice. |

A state-level link list cannot measure local/private completeness. Expand central portals with agency, county, municipality, tribal and intermediary routes. The current third-party CommonGrants adapter covers four allowlisted state feeds; its availability does not replace official-source verification or establish those states as preferred product markets.

## National directories leading to local and private notices

| Network | Primary seed | Actionable route and limits |
|---|---|---|
| Community foundations | [Council on Foundations locator](https://cof.org/page/community-foundation-locator) | Foundation → competitive funds/affiliates → actual cycle. Donor-advised, scholarship and invited-only programmes remain distinct. |
| CDBG and related pass-through | [HUD grantee catalogue](https://catalog.data.gov/dataset/hud-exchange-grantee-database) | Jurisdiction → administrator → local NOFA/action plan/amendments. Catalogue-check date is not a fresh grant notice. |
| Workforce boards | [CareerOneStop directory](https://cloudfront.careeronestop.org/LocalHelp/WorkforceDevelopment/find-workforce-development-boards-help.aspx), [API](https://api.careeronestop.org/api-explorer/) | Board → employer services → current training rules and funds. Directory API is keyed; provider inclusion does not guarantee sales. |
| Rural/extension | [USDA offices](https://www.rd.usda.gov/about-rd/state-offices), [NIFA university directory](https://www.nifa.usda.gov/grants/land-grant-university-website-directory) | Programme/state office or 1862/1890/1994 institution → local notice. Assistance resources are not automatically awards. |
| Agriculture | [SARE grants](https://www.sare.org/grants/) | Four regional programmes with different producer/research/education routes; historical project search stays separate. |
| Arts/humanities | [NEA organizations](https://www.arts.gov/state-and-regional-arts-organizations), [NEH councils](https://www.neh.gov/about/state-humanities-councils) | State/territorial/regional body → its live grant calendar and guidelines. Agency existence is not evidence of a funded open cycle. |
| Tribal/Native | [BIA directory with CSV/Excel](https://www.bia.gov/service/tribal-leaders-directory), [First Nations FAQ](https://www.firstnations.org/grantseeker-resource-frequently-asked-questions/) | Official tribal domains and Native RFPs; recognition, membership and leadership rules must be explicit. [NAP's funding map](https://nativephilanthropy.org/indigenous-data) is historical and says it does not distinguish Native-led recipients. |
| Utilities | [DSIRE data/tools](https://dsireusa.org/resources/data-and-tools/), official utility/cooperative sites | Incentive → sponsoring utility notice; utility charitable foundations are another lane. Service territory and customer class need validation. |
| Corporate giving | [Walmart facility giving](https://www.walmart.org/what-we-do/strengthening-community/spark-good/spark-good-facility-giving) and [eligibility](https://www.walmart.org/how-we-give/grant-eligibility) | Corporate page → local programme → rules. Grants, product donations, employee matching and sponsorship are separate. |
| Business competitions | [Hello Alice programmes](https://www.helloalice.com/small-business-grants-and-funding), [Arch Grants FAQ](https://archgrants.org/programs/faqs/) | Listing → sponsor/current rules. Loans, accelerators, grants and equity or relocation obligations cannot be flattened into “free money.” |

Useful local regression cases include [Maine Community Foundation's annual cycles](https://www.mainecf.org/apply-for-a-grant/), [Denver's filtered opportunities and Mountain Time deadlines](https://denverfoundation.org/funding-opportunities/), [Alaska foundation/affiliate grants](https://alaskacf.org/grants/), [Seattle central funding](https://www.seattle.gov/grants-and-funding), [Cook County CDBG](https://www.cookcountyil.gov/service/community-development-division) and [Austin equity grants](https://www.austintexas.gov/equity-inclusion/grant-programs). [Communities Foundation of Texas](https://www.cftexas.org/nonprofits/grants/) says nearly all opportunities are invitation-only and its gateway profile is not an application. That is a valuable negative match, not a broken search result.

## GitHub reuse and verified third-party state feeds

The companion investigation reviewed 27 substantive GitHub candidates at varying depth, including source, licence, repository trees, metadata and selected upstream CI. Repository presence and README claims were not treated as proof of production completeness. No third-party project was installed or executed.

Read-only checks of these list endpoints, using one record per page, returned HTTP 200 and valid opportunity envelopes. Their OpenAPI endpoints also returned 200. These checks crossed into October 2 UTC; they establish bounded access, not full pagination or an SLA.

| Feed | Public endpoint | Important observed caveat |
|---|---|---|
| California | [CA CommonGrants](https://ca.api.cg.a6lab.ai/common-grants/opportunities?page=1&pageSize=1) | First record was a loan. Feed membership is not proof of grant instrument. |
| Pennsylvania | [PA CommonGrants](https://pa.api.cg.a6lab.ai/common-grants/opportunities?page=1&pageSize=1) | First record lacked description/known ceiling; preserve unknowns and retrieve official guidance. |
| Washington | [WA CommonGrants](https://wa.api.cg.a6lab.ai/common-grants/opportunities?page=1&pageSize=1) | Example distinguished eligible direct government applicants from organizations that may be subrecipients. |
| Maryland | [MD CommonGrants](https://md.api.cg.a6lab.ai/common-grants/opportunities?page=1&pageSize=1) | Example mixed instruments and explicitly said it was not accepting applications. Recurrence text cannot override that flag. |

These are Agile Six-operated feeds, not official state endpoints. Their provider sync timestamp is distinct from a record's modification date and the time the originating notice was verified. Do not convert catalogue counts across statuses/instruments into a count of available grants. Consumer adapters use read-only list/detail/search routes, never administrative sync routes.

The useful reuse choices are:

| Project | Reviewed evidence | Adoption decision |
|---|---|---|
| [Agile Six grant seeker](https://github.com/agilesix/cg-mcp-grant-seeker/tree/ac7cded9332a18387b274fb49880ff8ddf01c8c6) | MIT; inspected core separates success, empty and error; source-scoped IDs, bounded hydration and partial-source failures. [Packaging guide](https://github.com/agilesix/cg-mcp-grant-seeker/blob/ac7cded9332a18387b274fb49880ff8ddf01c8c6/docs/shared-grant-service.md). | Consume its public feeds directly for the Python product. Consider the small service core for a future TypeScript product rather than copying its whole MCP/UI application. Its default federal Simpler source still requires a token. |
| [CA adapter](https://github.com/agilesix/cg-api-ca), [PA adapter](https://github.com/agilesix/cg-api-pa), [WA adapter](https://github.com/agilesix/cg-api-wa), [MD adapter](https://github.com/agilesix/cg-api-md) | MIT source plugins and ETL; different upstreams and retention policies. CA/WA retain removed upstream records at last-known state; MD has a different removal policy. | Reuse contracts and source knowledge. Do not duplicate four ETL infrastructures or treat a provider deletion as funder cancellation. Full-catalog ingestion needs explicit pagination beyond service collection limits. |
| [OpenProse grant-finder](https://github.com/openprose/grant-finder/tree/35e947d928d4d9ce377fb31f21fa774fe5a90425) | MIT Go CLI, SQLite evidence ledger, packet schemas, federal API/XML/RSS code and fixtures. Source inspection found its adaptive limiter methods are no-ops. | Reuse evidence/packet ideas or evaluate a bounded CLI boundary. Federal-heavy manifest and incomplete pacing do not justify replacing this product with a supposedly complete national engine. |
| [cyanheads Grants.gov MCP](https://github.com/cyanheads/grantsgov-mcp-server/tree/55ff52dc97fea45d0209911344e1a33a1f3867dd) | Apache-2.0; detailed date, amount, forecast, ambiguity and filtering semantics; new project with framework coupling. | Implementation reference for field correctness, not a reason to adopt a full MCP framework for a few HTTP calls. |
| [GSA-TTS Grants.gov MCP](https://github.com/GSA-TTS/mcp-server-grants-gov) | MIT, small Python adapter with validated inputs and pagination; no tests directory observed in reviewed tree. | Useful small reference. Organization name does not establish broad national source coverage. |
| [HHS Simpler.Grants.gov](https://github.com/HHS/simpler-grants-gov) | Official API/application, US public domain and worldwide CC0 dedication. | Reuse selected schemas and transformation tests; preserve native evidence. Avoid a full federal portal deployment fork. |
| [Grantmakers legacy site](https://github.com/grantmakers/grantmakers.github.io) and [NEXT](https://github.com/grantmakers/grantmakers-next) | Legacy site has MIT evidence; separate NEXT repository's reuse licence was unresolved. | Historical foundation research and architecture reference. Do not assume the old project's licence covers the new repository or that its hosted search index is freely replicable. |
| [NODC ef2](https://github.com/Nonprofit-Open-Data-Collective/ef2) | Current historical IRS processing successor using R/DuckDB and concordances; older irs990efile explicitly deprecated. | Evaluate processed data before building another raw-XML warehouse. Confirm needed 990-PF fields and data rights; historical giving remains separate. |

Other investigations included archived FOA tools, notebooks, capstones, faculty-matching prototypes, state MCP wrappers, proposal platforms and older IRS parsers. They supplied ideas but did not establish comprehensive current coverage. Several had missing or ambiguous project licences, paid backend dependencies, stale endpoints or only README-level implementation claims. Selection should reward verified source behavior and maintainability, not stars or an “AI-powered” label.

## Commercial data and real integrations

| Candidate | Verified documentation | Product decision |
|---|---|---|
| Candid | Separate [API products](https://candid.org/data/explore-apis/) and [open-opportunity endpoint](https://developer.candid.org/reference/get_v1-opportunity). | Evaluate live opportunities separately from historical grants. [API agreement](https://candid.org/terms-of-service/api-license-agreement/) requires a permitted-use review, including competitive databases and AI processing. |
| Instrumentl | [Customer integration API](https://help.instrumentl.com/en/articles/10020925-api-integration) on specified subscription tiers. | Existing-customer workflow connector; not established as an unrestricted catalogue resale licence. |
| OpenGrants | [REST/data model](https://opengrants.io/learn/funding-portal/a01-data-model/), [OpenAPI](https://ops.opengrants.io/openapi.json), [API/MCP product](https://opengrants.io/product/). Vendor claims federal, state, municipal and IRS-derived records. | Strong candidate for incremental local/private comparison. Claims untested. [Pricing](https://opengrants.io/how-opengrants-pricing-works/) lists Developer at $299/month or $239/month billed annually; [API terms](https://opengrants.io/opengrants-legal/) restrict permanent copies, caching and redistribution absent permission. Clarify rights for the actual product before adopting. |
| GrantForward/Kuali | [March 2026 announcement](https://www.kuali.co/post/kuali-announces-grantforward-integration) and [integration guide](https://kuali.zendesk.com/hc/en-us/articles/52493406350363-Integrating-GrantForward-in-Kuali-Research). | Real institutional discovery-to-proposal integration. No general developer resale API established; evaluate an existing institutional entitlement or negotiated partnership. |
| Pivot-RP/Cayuse | [API integration description](https://exlibrisgroup.com/blog/streamlining-the-research-lifecycle-from-pre-award-to-post-award-and-beyond/), [current docs](https://pivot-rp.zendesk.com/hc/en-us/categories/41029935473937-Product-Documentation). | Research/university connector with export/embedding options; verify current contract and endpoints. Not proof of nationwide small-business coverage. |
| InfoEd SPIN | [Harvard's public Python client](https://github.com/harvard-vpal/spin-search). | Concrete integration precedent. Client code does not supply subscription access or data rights. Audit current compatibility and repository licence before reuse. |
| DSIRE | [Legacy JSON/XML and change-date routes](https://dsireusa.org/resources/data-and-tools/), [new API docs](https://docs.dsireusa.org/). | Valuable specialist incentives feed; reconcile hosts, auth, terms and live schema before production. Do not assume legacy documentation means a free supported feed. |
| GivingData | [Enterprise API documentation](https://gdcentral.givingdata.com/api-documentation-cv0gf19n) for publishing, CRM and payments. | Authorized funder-publishing partnership candidate. Customer records are not a national shared opportunity API. |
| Submittable | [Public Discover marketplace](https://www.submittable.com/discover) and [customer API updates](https://www.submittable.com/blog/new-at-submittable). | Marketplace is secondary discovery with mixed call types. Management API access does not imply access to all hosted opportunities. |
| Benevity | [Giving API](https://developer.benevity.org/) and [grants product](https://benevity.com/products/grants). | Giving/customer workflow integration, not established as corporate open-grant discovery feed. |
| GrantTrove | [Developer API](https://granttrove.com/developers), [published sources](https://granttrove.com/data-sources). | Compare incremental breadth before purchase; documented sources overlap federal/California/IRS baseline. |
| HigherGov | [API repository](https://github.com/HigherGov/API). | Potential federal/procurement accelerator. State/local contract coverage must not be advertised as state/local grant coverage. |
| GrantStation / GrantWatch | [GrantStation EULA](https://grantstation.com/eula), [GrantWatch terms](https://www.grantwatch.com/terms-and-conditions.php). | Research seats or negotiated access are distinct from backend licences. GrantWatch's reviewed terms prohibit automated/API access; exclude it from automated ingestion. |

A technical API and a suitable licence are separate requirements. Before purchasing data, obtain terms for customer display, cached/derived records, AI processing, exports, evidence retention, attribution and termination. “Unlimited requests” is not a promise of unlimited throughput or unrestricted downstream use. No pricing, SLA or coverage claim above was independently audited.

## Agent-assisted collection without buying a data API

Use the registry to select exact official domains, then inspect current funding pages, programme calendars, sitemaps and notices. Prefer supported exports and feeds, then permitted public HTML/PDF extraction. A browser is appropriate where rendering is necessary; undocumented network endpoints are not automatically supported public APIs. Public access alone is not blanket permission to crawl or republish.

Extract dates, IDs, canonical links and evidence deterministically where possible. Let the agent resolve bounded ambiguity using the notice text, returning unknown when evidence is insufficient. Preserve original language and explicit translations when needed. Separate extraction errors from genuinely absent fields.

Use conservative per-host limits, conditional requests, bounded retries and recorded failures. Do not bypass login, CAPTCHA, paywalls or access blocks. No account creation, newsletter subscription or contact-form submission is necessary for the first public-source benchmark. Applicant/organization registration is a later, separately authorized action.

Useful reusable code includes [HHS Simpler.Grants.gov](https://github.com/HHS/simpler-grants-gov), [Grantmakers.io historical-filing projects](https://github.com/grantmakers), [Scrapy](https://github.com/scrapy/scrapy) and the SPIN client above. Reuse requires repository-specific licence and maintenance review. None supplies a complete, fresh, nationally comprehensive local/private grant corpus. Source software rights do not automatically license collected content.

Firecrawl and Alexandria remain optional evaluation candidates, not selected dependencies or evidence of additional grant coverage. Compare any retrieval service against direct collection on the same sources, including cost, failed extraction, provenance and permitted use.

## Proposal-writing upstream review

Reviewed October 2, 2026, read-only; no upstream code was installed
or executed. The synthesis in `docs/PROPOSAL-WRITING.md` is
independently written. No upstream prose is copied into this project,
so no upstream license text is reproduced here. Links, reviewed
commit IDs, and license observations below are the attribution
record. Our MIT license covers our own code and docs; it does not
cover upstream CC-BY material. If future work adapts CC-BY text,
preserve its required attribution, license, and change notices.

| Project | Reviewed revision | License observation |
|---|---|---|
| [eseckel/ai-for-grant-writing](https://github.com/eseckel/ai-for-grant-writing) | `0d405fad57f4c82ff2205323c30a3c039cc1b3cf` (HEAD at review) | LICENSE file is CC-BY-4.0. |
| [AIScientists-Dev/academic-humanizer](https://github.com/AIScientists-Dev/academic-humanizer) | `94b88b23703bed7df507acae7d6d5876209a0cdf` (HEAD at review) | LICENSE file states MIT (Copyright 2026 AIScientists-Dev); GitHub license detection shows NOASSERTION, so the file text is treated as authoritative. |

What each upstream contains:

- ai-for-grant-writing is a curated resource list: a service
  comparison table, prompt collections, prompt engineering links,
  quick prompt blocks (clarity, persuasion, structure, mission and
  review-criteria alignment, titles, risks, timelines), and
  grant-writing-specific references (PLOS, Nature, NIH, NSF,
  Stanford, UNC, SSRC, Grants.gov).
- academic-humanizer is SKILL.md v0.3.3 plus examples: six editing
  layers (general AI-tell catalog, academic tells, scholarly
  preserves, claim-evidence discipline, voice matching, NSF/NIH
  proposal mode), an audit-then-rewrite loop, and before/after
  examples for papers, an NIH Specific Aims page, and an NSF CAREER
  summary. It acknowledges blader/humanizer and koaeraser/ARMS as
  influences; those were not directly reviewed.

Adopted into our workflow (rewritten, not copied):

- Notice-first drafting: prompts that align text to the specific
  announcement and review criteria became stages 1, 5, and 7.
- Mock review as a separate pass became stage 7, with verdicts and
  no numeric scores.
- Timeline and milestone drafting became stage 4.
- AI-tell removal and claim-evidence discipline became stage 8 and
  the evidence rules, generalized beyond academic prose.
- Proposal weak moves (vague importance, method-as-aim, dominoed
  aims, boilerplate impacts plans) inform stages 3 and 6.

Deferred or corrected:

- Service recommendations: no provider endorsement, no paid calls.
- Verbatim prompt blocks: rewritten as process stages instead.
- Default academic register: community, small business, and
  workforce proposals keep a plain applicant voice; the academic
  register applies only to the research appendix.
- NIH scoring: the upstream line that Significance, Innovation, and
  Approach are separately scored sections is stale for most
  research project grants with due dates on or after January 25,
  2025. Our appendix uses the official simplified framework
  (Factor 1 and Factor 2 scored, Factor 3 sufficiency, all
  informing Overall Impact).
- Example technique that adds numbers, preliminary evidence, or
  partner names absent from the source passage: forbidden here.
  Unsupported specifics are OPEN gaps, never improvements.

Primary grant-writing guidance selected for general applicants,
verified reachable at review:

- [Grants.gov grants 101](https://www.grants.gov/learn-grants/grants-101)
- [UNC grant proposals guide](https://writingcenter.unc.edu/tips-and-tools/grant-proposals-or-give-me-the-money/)
- [PLOS ten simple rules for LLMs and grants](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1011863)
- [NIH write your application](https://grants.nih.gov/grants-process/write-application) (research only)
- [NIH simplified review framework](https://www.grants.nih.gov/policy-and-compliance/policy-topics/peer-review/simplifying-review/framework) (research only)
- [NSF PAPPG](https://www.nsf.gov/policies/pappg) (research only; the 2004 proposal guide linked upstream is structure background, not current rules)

## Concrete next tests

1. **Source-method matrix:** test official feed, HTML table, PDF notice, dynamic page, migrated portal and invited-only funder fixtures across regions. Track entry-point verification separately from connector readiness and current-call verification.
2. **Administrator graph pilot:** review 60 sources spanning foundations, cities/counties, workforce, utilities, arts/humanities, rural/extension and Native sources. Include Alaska, Hawaii and a territory. Trace the actual administrator and notice; publish the sample selection method.
3. **Forty-cycle reference corpus:** independently label applicant role, geography, instrument, status and deadline. Include expired, historical, loan, equity, procurement, scholarship, beneficiary-only and unknown-funds negative cases.
4. **Snapshot/change proof:** compare two dated collections and replay controlled amendments in saved permitted fixtures. Detect a PDF-only deadline change and prove that outage does not become closure.
5. **Vendor comparison:** use the same profiles/reference corpus for OpenGrants and institutional/private vendors when sample access is authorized. Count unique qualifying current results beyond the public baseline, not raw records or historical funding dollars.
6. **Economics:** record collection/OCR/model costs, fixed subscriptions, maintenance and reviewer minutes per actionable opportunity. Buy a feed only when its incremental coverage or saved work justifies cost and permitted uses fit the product.

Publish known gaps by source family, geography and applicant type. “No result in these checked sources” is a supportable finding. “No funding exists” and “nationwide coverage complete” are not supported by this research.

## Additional open-source funding lead (2026-10-03)

Reviewed [ralphtheninja/open-funding](https://github.com/ralphtheninja/open-funding/tree/ba41e620deb3f2b4f661a9ae6f3050f3b97097c8)
at revision `ba41e620deb3f2b4f661a9ae6f3050f3b97097c8` through an independent
read-only source review. This is a curated Markdown guide to funding open-source
projects, not an opportunity API or executable discovery engine.

Useful follow-up seeds include CZI Essential Open Source Software, Open
Technology Fund, Python Software Foundation and ARDC. Its fiscal-hosting links
also suggest an applicant-affiliation research route. None of these leads was
qualified or integrated by this review; each needs current official program
terms, geography, instrument, eligibility and deadline verification.

The guide mixes grants, fellowships, noncash support, crowdfunding, non-US
programs and archived entries. Missing or old deadlines do not establish current
availability, and placement in its archive does not establish that a funder has
ceased operating. Do not bulk-import the list as open grant opportunities.

Its README declares CC BY-SA 4.0 even though there is no separate LICENSE file.
We link to the guide and record our own evaluation; no text, dataset or code is
copied into this MIT-licensed product. This is a future source-research lead,
not a new v0.3.0 feed or dependency.
