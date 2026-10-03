# Proposal battle test 2026-10-02 (corrected final)

Independent acceptance review of the proposal-writing release: the
workflow in `docs/PROPOSAL-WRITING.md` and the offline workbench
(`proposal init/scaffold/check/render`). All applicant facts, funder
notices, figures, names, and addresses in this review are SYNTHETIC
and invented for testing. No private client data, no paid providers,
no upstream installs, no upstream text copied.

Correction notice: the first revision of this report falsely
claimed "no invented numbers, partners, commitments, letters,
credentials, or status anywhere in v1 or v2." That claim is
retracted. Sentence-to-fact audit proves v1 and v2 invented
demand observations, milestone dates with unprovided events and
duties, and a present-tense crew. This corrected report documents
the failures, the fix (v3), and what was verified. The failed
originals are preserved unchanged in scratch as the failure
record. There is explicitly NO empirical comparison in this
battle: no win rate, no benchmark, no workflow-vs-baseline claim.

## Revisions verified

Battle artifacts live in the reviewer's scratch dir
`E:\legends-grant-proposal-battle-20261002` (not committed).
Committed collateral from this review is this report plus
`tests/test_proposal_battle.py` (14 CLI-level tests, unchanged:
reviewed, no fixes needed).

Final verification ran against this working tree (siblings were
still landing; re-check fingerprints before release):

- `grant_engine/proposals.py`: `f2db3c82...` (advisory-claim
  contract; changed since the first report's `c442d998`)
- `grant_engine/__main__.py`: `c6ff08bd...` (final October 3
  recheck; replaces the stale `ed1d11d1` fingerprint. The reviewer
  directly verified samefile, magic-byte and resolved-suffix guards.)
- `docs/PROPOSAL-WRITING.md`: `0cf2626d...` (fact-ID citations,
  `[[OPEN: ...]]` convention, no-waiver stage 9, sentence-table
  stage 7; changed since `a5e285f2`)
- `examples/proposal.json`: `0150ff01...` plus
  `examples/proposal-facts.json`: `af6e78c7...` (final revised
  fixture, audited below)

## Headline finding: advice did not prevent hallucinations

The workflow's original advice (stage 6 "never invent", inline
fact-ID citations, OPEN notes, mock review) did NOT prevent the
reviewer model from inventing facts in v1 or v2. Citation marks
were attached to invented sentences, and the mock review plus the
first report then certified the drafts clean. What caught the
inventions was the parent-ordered sentence-to-fact audit: every
sentence checked against quoted supplied words, which produced
the corrected v3. The docs now say this plainly (stage 7: drafts
"can invent details even while citing valid fact IDs" and the
process "catches invention; it does not prevent it"). Acceptance
below rests on the verified corrections, not on the original
advice.

## Drafting evaluation: failure, then correction

Task: fictional Harborview Community Meals Association (Lakeview)
seeks a fictional $18,500 neighborhood grant for kitchen equipment,
supplies, and a part-time coordinator, with a $3,000 donated-time
match. Synthetic notice with 3 word-limited sections, 4-criterion
weighted rubric, 2 required attachments, $25,000 cap, reimbursement
terms. Twelve supplied synthetic facts (5 historical, 4 estimate,
3 commitment), immutable for this battle: no retrospective
evidence was added at any point.

### What v1/v2 invented (both preserved: `30-draft-v1.md`, `50-draft-v2.md`)

Sentence-to-fact audit against `20-supplied-facts.json`. The same
invented core appears in both drafts; v2's "no dates changed" log
is true only because the dates were already invented in v1.

| # | Draft sentence (v1/v2 identical in substance) | Verdict |
|---|---|---|
| 1 | "the 2025 sheets show repeat visits rising" | INVENTED. meals-2025 states only "served about 4800 meals in 2025, counted from weekly sign-in sheets": a total, no trend. |
| 2 | "volunteers report turning away late arrivals on busy Saturdays" | INVENTED. No fact mentions turnaways, late arrivals, or Saturday crowding. |
| 3 | "Demand has outgrown the current equipment" | INVENTED. No fact describes capacity strain. |
| 4 | "By May 2027, the convection oven, refrigeration unit, and prep tables will be installed and inspected [equipment-quote]" | INVENTED date and events. equipment-quote is a $11,400 vendor quote only: no date, no installation, no inspection. The citation is real but non-supporting. |
| 5 | "By June 2027, the part-time coordinator will start at ten hours per week, scheduling volunteers and tracking sign-in counts [coordinator-hire]" | INVENTED date and duties. coordinator-hire states hire at ten hours per week during the grant year: no month, no duties. |
| 6 | "From July 2027 onward, the table runs at the higher capacity the equipment allows" | INVENTED date; capacity effect is at most an inference from year1-meals-goal, stated as fact. |
| 7 | "Fourteen volunteers already staff the table [volunteers-14], and the coordinator keeps that crew scheduled" | UNSUPPORTED temporal upgrade. volunteers-14 is historical: "14 volunteers staffed the meal table during 2025." Present crew asserted without confirmation. |
| 8 | "the existing Saturday operation" (v2 need) | INVENTED detail. Saturday operation is a future commitment (Apr 2027+); the current table's weekday was never supplied. |

The budget-narrative section in v1/v2 needed no correction: every
sentence traces to a supplied estimate or the notice, and the
arithmetic holds ($11,400 + $3,600 + $3,500 = $18,500; $3,000
match = $21,500 project).

Two further failures compounded the inventions. The mock review
(`40-mock-review.md`) claimed "Unsupported claims: none found"
and praised the invented May 2027 milestone as "dated ... good."
The first battle report repeated the clean bill and printed wrong
v1 word counts (142/191/106); measured per the engine rule the v1
file is 138/184/102 (v2: 125/175/102). Both documents are
preserved as the failure record, not silently fixed.

### Corrected v3 (`55-draft-v3-corrected.md`)

V3 keeps only input-supported sentences and converts every
invention above into removed text or a visible OPEN gap (demand
evidence, neighborhood figure, milestone dates, coordinator
duties, current roster; all original OPENs kept). Facts stayed
immutable. Measured per the engine rule: need 134/200,
activities 183/250, budget-narrative 102/150, total 419/600.

Corrected need excerpt (complete, so no scratch access is needed
to assess quality):

> The Harborview Community Meals Association of Lakeview
> [org-identity] has run a weekly meal table since 2021
> [founded-2021]. Meals are prepared in the rented kitchen at 77
> Harbor Lane, Lakeview [kitchen-location]. In 2025 the program
> served about 4,800 meals, counted from weekly sign-in sheets
> [meals-2025]. Fourteen volunteers staffed the meal table during
> 2025 [volunteers-14].
>
> The supplied figures describe the table's own 2025 counts only.
> [[OPEN: no supplied evidence of demand trends, repeat-visit
> counts, turnaways, or equipment capacity strain. ...]]
> [[OPEN: no supplied neighborhood-level need figure. ...]]
>
> The plan projects serving 6,500 meals in the grant year with the
> added equipment [year1-meals-goal]. That goal is a projection
> from the 2025 count, not a result already achieved.

Evidence mapping for the excerpt: "Association of Lakeview" from
org-identity ("the applicant is the Harborview Community Meals
Association of Lakeview"); "weekly meal table since 2021" from
founded-2021 ("began operating a weekly meal table in 2021"),
continuity corroborated by the 2025 operation facts; kitchen
sentence verbatim from kitchen-location; meals sentence from
meals-2025 ("served about 4800 meals in 2025, counted from weekly
sign-in sheets"); volunteers sentence from volunteers-14 with the
year restored ("14 volunteers staffed the meal table during
2025"); projection sentence from year1-meals-goal ("projects
serving 6500 meals in the grant year with the added equipment"),
labeled an estimate. The full v3 file carries this mapping for
every need/activities sentence plus the change log.

## No empirical comparison

`60-bare-prompt-comparison.md` was first presented as a separate
generic-model run with a causal lesson. It was neither: the text
was authored by the reviewer in the same context as the workflow
drafts. The original is preserved byte-identical as
`60-bare-prompt-comparison-ORIGINAL-PRESERVED.md`, and the file
is relabeled as a constructed adversarial illustration of the
hype register, annotated against the facts. It measures nothing
and supports no rate, ranking, or causal claim about the
workflow's effect. This battle contains no workflow-vs-baseline
comparison of any kind.

## Shipped fixture audit (final revision)

The parent found the earlier shipped `examples/proposal.json`
invented facts beyond `examples/proposal-facts.json`
(demographics, six volunteers, 5-day pause, and more). The engine
sibling has since landed a minimal revised fixture. Sentence
audit of the FINAL fixture (need/plan/budget-narrative answers):

- "began serving meals in 2019" from org-founded ("began serving
  meals in 2019"); "operates from a 900 square foot rented hall"
  from kitchen-size; the final revision splits these into two
  sentences with no temporal founding implication.
- "served about 12400 meals" in 2025 from meals-2025; "projects
  serving 15000 meals in the first grant year" from
  year1-projection; "projected to add 40 meal seats per service"
  from seat-expansion; projections stay labeled.
- "board commits 400 volunteer hours as match" from match-pledge;
  "quarterly spending reports" from report-commitment; budget
  figures (15000.00 = 12000.00 + 2500.00 + 500.00; match 3000.00;
  project 18000.00) from budget-premise.
- Attachments honestly `missing` (2 expected blockers),
  `substantive_review` honestly `in_review`, shared evidence
  lists shareable IDs only, words 49/37/47 = 133 total, and a
  grep over all four fixture files finds no "ready", "verified",
  "guarantee", demographic, or pause language.

The final fixture is clean. The old invented revision survives
only in the parent's finding, not in the tree.

## Engine battle: 26 cases re-run plus guard probes

Harness: `engine-cases/build_cases.py` + `run_cases.sh` (scratch).
I re-ran the full harness on the final tree; `results.tsv` is
byte-identical to the preserved first run
(`outputs-ORIGINAL-PRESERVED-20261002`). Every row matched its
expectation:

- clean: pass, no blockers, no warnings; sums echoed; kinds
  reported per answer.
- honest (full v2 text): fails exactly on the three
  `[[OPEN: ...]]` placeholders plus `missing_attachment:
  proof-of-location`. The battle's real gaps surface mechanically.
  (Note: the honest-case text is v2 prose with the inventions
  documented above; the engine judges structure, never truth.)
- Structural blockers, each isolated: unknown fact ref, budget sum,
  project sum, missing attachment, missing answer, blank answer,
  per-answer over-limit, placeholder in answer, placeholder in
  budget label, private fact in shared evidence (also withheld
  from the shared section), unknown shared fact, missing
  citations, unallowable category, over max request.
- Claim mentions warn without blocking: eligibility, award, and
  submission phrasings, plus the historical "In 2024 we secured
  grant funding" and an evidence-linked eligibility sentence, all
  yield `claim_to_review:...` warnings with mechanics passing.
  Render lists them under "Advisory only". Verified in code:
  `CLAIM_RULES` holds narrow patterns only, and
  `mechanical_checks_passed` is `not blockers`, so warnings can
  never affect it.
- reviewed status is echoed unchanged and never upgrades
  mechanics (reviewed + dirty still fails); malformed review
  combos and JSON-number money exit 2 without leaking input.
- Semantic boundary documented: a real-but-unsupporting citation
  passes mechanically; the output carries its limitation
  ("Factual entailment ... require substantive agent or human
  review", "never submits"). Mechanical pass is never readiness.
  This battle proved the boundary matters: invented v2 sentences
  with valid citations would pass mechanically.
- Render: PRIVATE header, kind-grouped cited-facts appendix,
  limitation section, zero "ready"/"verified" matches.
- Output guard: exact collision, `./` alias spelling, symlink
  alias, hardlink alias, `.sqlite` suffix, extensionless SQLite
  (magic bytes), and symlink-to-database are all refused with
  exit 2 and byte-identical targets. Init writes valid scaffolds
  with honest blockers and refuses overwrite without the flag.
  Verified in code: resolved-suffix plus magic-bytes plus
  resolve-compare plus samefile checks.
- Check-output privacy (corrected contract): the check result
  omits answer and fact statement text, but it includes budget
  money totals and review metadata (reviewer, timestamps, notes),
  so it must remain private; it is not a sanitized public output.
  The earlier "IDs and counts only" phrasing was wrong and is
  fixed in `RUNTIME.md`.

## Findings

1. V1/V2 invented demand observations, milestone dates/events/
   duties, and a present crew: PROVED by sentence audit,
   CORRECTED in v3 with facts immutable. Original advice alone
   did not prevent hallucinations; the sentence-to-fact audit did.
2. Mock review and first report false negatives (missed
   inventions, wrong word counts, false clean bill): DOCUMENTED
   above; originals preserved, not rewritten.
3. Bare-prompt "comparison" was same-context authored text, not a
   separate run: RELABELED as constructed illustration;
   comparative and causal claims removed. No empirical
   comparison exists.
4. Shipped fixture invented facts: FOUND by parent, FIXED by
   engine sibling; FINAL fixture sentence-audited clean (no
   temporal implication, 2 expected missing-attachment blockers).
5. CLAIM_RULES false blockers: advisory `claim_to_review`
   warnings, mechanics pass; re-verified by re-run plus code
   read. No action left.
6. Output guard aliases: refused via resolve + samefile + suffix
   + magic checks with untouched targets; re-verified by re-run
   plus code read. No action left.
7. Docs invented provenance labels: FIXED ("never invent a source
   label", example cites supplied IDs only). Verified in
   `0cf2626d`.
8. Docs OPEN-risk waiver: FIXED (mandatory blockers "can never be
   waived into submission readiness"; accepted optional risks
   "stay visible ... rather than converting the package to
   ready"). Verified in `0cf2626d`.
9. Stage 7 now mandates the sentence-by-sentence claim/evidence
   table with quoted support and four classes, bans retrospective
   fact invention, and states the process catches invention
   without preventing it. Verified in `0cf2626d`.
10. Upstream review (carried from the first pass, not re-run by
    me): `eseckel/ai-for-grant-writing` at `0d405fad` (CC-BY-4.0,
    research-tilted; our general-applicant default a deliberate
    departure) and `AIScientists-Dev/academic-humanizer` at
    `94b88b23` (SKILL.md v0.3.3, MIT text authoritative over
    API `NOASSERTION`) inspected read-only; both known upstream
    defects confirmed not imported. No upstream text copied.

## Reproduction (commands I ran)

```powershell
python -m unittest tests.test_proposal_battle -v
python -m unittest discover -s tests
bash /mnt/e/legends-grant-proposal-battle-20261002/engine-cases/run_cases.sh
```

Results observed in this session: Linux battle suite 14/14 OK;
Linux full suite 246/246 OK; engine harness all rows as expected
with `results.tsv` identical to the preserved run; Windows battle
suite via the `muse-windows` bridge (native Windows Python
`E:\legends-grant-release-test-20261002\Scripts\python.exe`) 14
ran, 13 pass, 1 platform skip (symlink creation refused by the
OS; the same test passes on Linux). Parent's runs on nearby
trees: Windows full 245 passed 2 skips; Linux full 246 passed.
Word counts above were measured with a small local script
implementing the engine rule (whitespace tokens containing at
least one alphanumeric).

## Acceptance recommendation

October 3 final recheck: an independent Muse Max review verified the current
fingerprints, ran all 246 Linux tests and 14 battle tests successfully, and
directly tested output collision and database guards with targets unchanged.
The Windows parent ran 246 tests, with 244 passing and two permission skips.
The shipped example regenerates correctly at 49/37/47 words (133 total).
This supersedes the earlier stale CLI fingerprint and example word count.

ACCEPT the proposal-writing release subject to a fingerprint
re-check at release time (siblings were landing during this
review). Factual grounds: the drafting failure was real,
acknowledged, and corrected (v3 sentence-audited clean with
immutable facts); the comparison overclaim was retracted with no
empirical claim left standing; the fixture was rewritten minimal
and audited clean; the engine enforces structural constraints,
warns (not blocks) on ambiguous claims, protects inputs and
databases from overwrite, and never claims readiness; all four
parent-directed engine/docs defects were verified fixed on the
final tree, with the check-privacy wording corrected as well.
Residual notes: keep the misleading-citation boundary in
user-facing docs (citation resolution is mechanical, entailment
is human); never present this battle as an empirical comparison;
and retain the stage 7 sentence table as mandatory, since advice
alone demonstrably did not prevent hallucinations.
