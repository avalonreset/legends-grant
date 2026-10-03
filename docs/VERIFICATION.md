# Verification

## v0.3.0 proposal workbench

Reverified October 3, 2026. The proposal commands scaffold, mechanically check and
render agent-written drafts; they do not generate narrative or establish that a
claim is supported. The writing recipe supplies the drafting and review process.

Tests cover missing answers and attachments, word limits, citation IDs, decimal
budget arithmetic, placeholders, advisory claim mentions, private evidence
separation and output paths that would overwrite inputs or SQLite databases.
The shipped synthetic example deliberately retains missing required attachments.
A successful command exit is not a passing proposal assessment.

The [proposal battle report](PROPOSAL-BATTLE-TEST.md) records actual failures and
corrections. Early agent drafts invented details despite valid citation IDs;
review caught those errors and prompted explicit claim-to-source checks. A
constructed bad draft is an adversarial illustration, not a measured comparison
against another model. No award-success or writing-superiority result is claimed.

The full suite runs 246 tests on Windows Python 3.11, with two filesystem-related
symlink cases skipped where creation privileges are unavailable. The Muse worker
also ran the suite on Linux successfully. The existing discovery and qualification
checks remain part of the full suite.
The resumed Windows run completed 246 tests: 244 passed and two skipped.
A rebuilt wheel installed into a clean environment reports version 0.3.0 and
successfully checks and renders the synthetic proposal outside the checkout.
Those outputs match the shipped examples after newline normalization.
Package inspection confirmed proposal code in the wheel, writing instructions
and examples in the source archive, and upstream credits in package metadata.
Reproduce the suite and synthetic proposal commands in [RUNTIME.md](RUNTIME.md).
The release tag and CI identify the final tested source and platform results.

## v0.2.0 discovery and evidence verification

Verified October 2, 2026. This release adds executable discovery and evidence
workflows to the previous Markdown-led module. Tests measure the contracts below;
they do not measure nationwide grant recall or award success.

## Evidence

| Check | Result |
|---|---|
| Offline suite | 171 tests passed on Windows Python 3.11 |
| Source routing | 115 sources; all 50 states, DC and five territories; 336 state/applicant combinations |
| Structured retrieval | Grants.gov plus four third-party CommonGrants state feeds |
| Live discovery | Ten observations from five feeds; bounded, incomplete flags retained |
| Official documents | Six primary documents, including a 22-page PDF; 22 selected text conditions retained |
| Adversarial collection | Box app shell detected as a blocker after a reproduced false success; attachment labels retained |
| Evidence integrity | Immutable revisions/observations, duplicate handling, replay, hashes, indexed columns and trigger checks |
| Reviewed qualification | Synthetic evidence and applicant cases; stale, missing, conflicting and mistyped inputs cannot clear the gate |
| Installed package | Wheel installed in a separate Windows environment; doctor, bundled registry, synthetic review and live PDF collection work outside checkout |
| Public contract | Version/changelog/identity/README checks pass locally; pinned router skill verified against live upstream bytes |
| CI configuration | Windows and Linux, Python 3.11 and 3.13; installs PDF extra and tests package outside checkout |

The [independent battle report](BATTLE-TEST-2026-10-02.md) records source URLs,
actual observed failures, fixes and remaining gaps. Raw third-party documents
stay outside the public release tree. The optional PDF integration was exercised
with pypdf 6.19.0. The core does not require it or any paid provider.

## Independent review and iteration

Five scoped implementation/review workers and a separate Muse review examined
runtime behavior and public claims. Reproduced findings prompted fixes for:

- Oversized feed pages and contradictory completeness claims.
- Corrupted database index columns, missing integrity triggers and future-dated observations.
- Partial HTTP bodies, empty app shells, login pages and sensitive query parameters.
- Missing attachment labels and PDF visible-link inventory.
- Incompatible applicant fact types producing unjustified negative decisions.
- Missing detail warnings, ignored query flags, unused purpose hints and nationwide geography aliases.
- Missing packaged source data, stale documentation and broken legacy state links.

Reviewers also identified intentional limits: federal scope describes where a
source searches, not applicant eligibility; keyword search returns visibly typed
records; posted/forecast federal discovery does not monitor closed notices. These
are documented boundaries, not evidence of an automated eligibility service.

## Reproduce

```powershell
python -m pip install '.[pdf]'
python -m unittest discover -s tests -v
python -m grant_engine doctor
python -m grant_engine plan --jurisdiction US --applicant-type nonprofit
```

Follow [RUNTIME.md](RUNTIME.md) for bounded live discovery, collection and replay,
and [QUALIFICATION.md](QUALIFICATION.md) for the synthetic review. Inspect every
receipt: an intact failed collection can pass artifact integrity checks.

The vendored router skill matches `cto-legends` v0.2.1 at commit
`dace1edb8534cb4494e60066ec88cb12470c61ae`, Git blob
`3d71f7123d76fa96fd4e2b91026aee938915c6fa`. No cross-module runtime dependency
or paid provider was added. Public CI results are linked from the repository's
Actions page; the release tag identifies the final tested source.

## Limits

Five source feeds are automated; 110 registry routes remain agent research.
There is no claim of comprehensive local/private discovery, semantic search,
cross-source deduplication, autonomous complete-notice crawling, OCR, automatic
rule extraction, alerts or application submission. A positive review checks only
supplied rules and evidence; source authority, completeness and quote meaning
must be reviewed independently. No actual applicant qualified or received funding
through this test, and no comparative win against a generic agent was measured.
