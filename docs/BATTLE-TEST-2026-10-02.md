# Independent live battle test - 2026-10-02

This is a small failure-hunting exercise for the local 0.2 development tree. It is not a discovery-recall study, a grant-eligibility benchmark, a complete notice review, or proof that any applicant qualifies. No private applicant data or paid services were used.

## Reproducible evidence

Public raw artifacts, text, immutable collection receipts, feed packets, scripts and clause checks are retained in the maintainer's local test workspace outside the release tree. Third-party documents are not redistributed in the package. The collector is exercised through its Python API; feed discovery uses the existing adapters. The report records observed results, not anticipated release results.

## Five live feed checks

At approximately 13:09 UTC, each adapter requested at most two records:

| Source | Returned | Source-reported total | Errors | Correct coverage state |
|---|---:|---:|---:|---|
| Grants.gov, query workforce | 2 | 216 | 0 | bounded; incomplete |
| California CommonGrants | 2 | 2,010 | 0 | bounded; incomplete |
| Pennsylvania CommonGrants | 2 | 386 | 0 | bounded; incomplete |
| Washington CommonGrants | 2 | 125 | 0 | bounded; incomplete |
| Maryland CommonGrants | 2 | 792 | 0 | bounded; incomplete |

Totals are source assertions at collection time. They are not verified counts of currently open grants. The CA sample begins with a loan. Maryland contains a mixed grant/loan/other-assistance item and unknown normalized status. Pennsylvania's two sampled items have identical titles but different identifiers. Those observations require instrument filtering and cautious duplicate handling; an open source record is not a verified grant. State feeds are third-party discovery evidence.

## Six primary-source document checks

All six initial calls retrieved raw content, produced text, and passed saved-artifact hash verification. A manually selected set of 22 critical strings survived extraction; that checks specific content preservation, not complete semantic accuracy.

| Primary source | Format and purpose | Independently checked content | Result |
|---|---|---|---|
| [Bucks County IWT](https://buckscounty.gov/1678/Incumbent-Worker-Training) | Local workforce reimbursement, HTML | Detailed eligibility includes 37.5-hour employment, six-month history, employer size contribution bands, and a branch allowing an outside-county employer when workers reside in Bucks | Text retained all six sampled conditions |
| [WEDnetPA FY26-27 guidelines](https://wednetpa.com/wp-content/uploads/2026/07/FY-26-27-Company-Guidelines-rev.-07-01-26.pdf) | State workforce reimbursement, PDF | 22-page source; current fiscal-year end, wage threshold, provider language and claim window retained | 47,496 extracted text bytes; pypdf available in test interpreter |
| [Washington climate planning](https://www.commerce.wa.gov/funding/climate-planning-grant-reopens-7-5-million-available/) | State/local-government funding, HTML negative control | Explicit closed-application banner survives despite the optimistic title; instructions, questions, FAQ and budget are hosted on Box | Text retained closure; attachment inventory exposed a gap below |
| [Texas Skills for Success](https://www.twc.texas.gov/programs/skills-for-success) | State employer workforce program, HTML | Named college administrator, private-employer restriction, and paid-training condition | Sampled restrictions retained |
| [Knight Foundation funding process](https://knightfoundation.org/how-we-fund/) | Private funder prospect, HTML | Most funding starts through foundation strategies/relationships; specific open calls are occasional | Should remain a prospect, not an always-open opportunity |
| [SBA microloans](https://www.sba.gov/funding-programs/loans/microloans) | Federal loan, HTML negative control | Redirect recorded; repayment and interest language retained | Clearly a loan, not grant evidence |

The Bucks detailed page adds a meaningful geographic exception absent from the shorthand [general employer page](https://buckscounty.gov/553/Employer-Community-Connections). That is not established as a formal contradiction; it is a warning against making eligibility exclusions from a landing-page summary.

## Failures and limits found

1. **A successful HTTP response was mistaken for useful document extraction.** Following the Washington application-instructions Box share yielded a JavaScript application shell whose extracted text was only `Box` (three bytes), but the original collector reported `ok=true` and `extracted`. Its links were static JS/CSS/font assets. The raw failure is retained in `wa-attachment-receipt.json`. Reported to the collector implementer for a regression and an insufficient-content state.
2. **Bare URLs conceal attachment purpose.** The Washington page correctly inventories five Box shares, but the initial output drops their human labels. URL suffixes alone cannot identify the FAQ, application instructions, questions and Word budget. Requested labelled links so an agent can plan explicit follow-up fetches.
3. **PDF links need a declared limitation.** WEDnet's PDF contains five visible HTTPS strings and no URI annotations; the initial collector emits an empty link inventory. Text is present, but the agent must still review the full text for referenced resources.
4. **A collected page is not a complete notice.** No exhaustive attachment collection or source-amendment review was performed. Every initial receipt keeps `notice_complete=false`, and all feed records remain unassessed. A machine gate must not infer application readiness from these successful extraction checks.
5. **No automatic semantic extraction was tested.** Finding the closure words or repayment language is not the same as interpreting and applying them. Geographic exceptions, invitation-only intake, local deadlines and private-funder conditions still require review.

## Scope of conclusions

The corpus spans federal, state, local and private sources and includes the Mid-Atlantic, Texas and Washington. It is intentionally small and adversarial. It does not establish nationwide source completeness, discovery recall, applicant matching accuracy, time saved against a generic agent, or success securing awards. No applications, contacts or submissions occurred.

## Fix verification

Retested all three affected live sources after the fixes:

- **Box shell is now blocked:** `ok=false`, `ExtractionBlocked`, `blocked_insufficient_html_text`; raw and three-byte text artifacts remain available and integrity checks pass. This repairs the false-success classification. It does **not** retrieve the actual Box-hosted PDF, which still requires a browser/manual/provider fallback.
- **All five Washington Box links now have accurate labels:** webinar slides, grant FAQ, application instructions, application questions, and Word scope/budget. An agent can select explicit follow-up documents without guessing from opaque URLs.
- **WEDnet now inventories four unique visible URLs** from the five PDF text occurrences. Annotation-only links and line-wrapped URLs remain documented limitations.

Before/after evidence is retained separately; `fix-summary.json` and `*-fixed-receipt.json` contain retest results. The short-HTML rule is a conservative heuristic, not universal JavaScript-shell detection. Longer anti-bot pages or login pages may need additional handling.

The search implementer additionally replayed the collected CA and PA records through the new local search: the California loan receives an explicit `loan_or_mixed_instrument` warning, and both same-title Pennsylvania cycles remain separate. That is a reported cross-check by the search implementer, not an independently reproduced discovery benchmark.

No real applicant eligibility decisions were issued. The qualification module consumes reviewer-supplied rules and exact text citations; this corpus was not fully reviewed for all rules or applicable documents and cannot honestly clear its complete-inventory gate.
