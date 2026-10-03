# Proposal writing workflow

Agent process for drafting real grant narrative for general applicants:
nonprofits, small businesses, and workforce grants. Research proposals
(NSF, NIH) are an optional appendix, not the default.

Governing rule: the current funder notice, instructions, and rubric
override everything here. This document never overrides page limits,
required forms, formatting rules, eligibility terms, or submission
channels. When the notice and this guide disagree, follow the notice
and say so.

What this is not: there is no automated win prediction, no numeric
score of draft quality, and no submission without authorization under
`apply.md`. A strong draft is still only a draft until the applicant
verifies every fact and the package passes the final checklist.

Plain punctuation in generated copy; no em dashes.

## Stage 1: Ingest the current notice and rubric

Goal: know exactly what the funder asks for before writing a word.

- Collect the current notice plus every required attachment,
  amendment, and instruction file with `collect-document`.
- Extract: eligible applicants, eligible activities, award range and
  instrument, match and cash-flow terms, deadline and timezone,
  page and file limits, required sections and their order, review
  criteria and weights, submission channel, contact for questions.
- Record the document inventory and retrieval dates. If an amendment
  check is stale, refresh it; do not draft against an old notice.
- Output: a short notice brief (one page or less) with section IDs
  quoted from the funder's own wording.

Stop rule: if the notice is missing, expired, or unreadable, stop and
report the gap. Never reconstruct requirements from memory.

## Stage 2: Interview the applicant, keep gaps visible

Goal: gather only the facts this notice requires, with evidence.

- Ask for facts the notice makes relevant: entity and status,
  geography served, project activities, beneficiaries, timeline,
  budget figures, match sources, staff and partners, registrations.
  Do not demand identifiers the notice does not require.
- Every material fact needs a stated basis: a named document, a
  record, or the applicant's direct confirmation with a date.
- Facts without a basis become interview gaps, written down
  explicitly as bracketed notes (for example:
  `[[OPEN: fiscal sponsor EIN, not supplied]]`). The brackets matter:
  `proposal check` flags them as unresolved placeholders.
- Keep applicant facts in private case storage, never in the public
  evidence store.

Stop rule: gaps do not block outlining, but no gap may be silently
filled later. Each gap travels with the draft until resolved.

## Stage 3: Project logic and outcomes

Goal: a short causal chain the narrative will follow.

- Write, in the applicant's own terms: need, activities, outputs,
  near-term outcomes, and how success will be observed.
- Each link must be verifiable: who does what, for whom, by when,
  and what evidence will show it happened.
- For workforce grants, tie activities to named employer needs,
  credentials, or placement paths only where the applicant supplied
  them. For small business grants, tie funds to specific cost items
  and business effects the applicant can document.
- Mark any link that rests on an unresolved fact as conditional.

## Stage 4: Budget and milestones

Goal: numbers that add up and match the narrative.

- Build the budget table from supplied figures only. Every line
  item traces to an applicant figure or a quoted vendor/rate source.
- Check arithmetic, match percentage, unallowable costs per the
  notice, and the payment timing (reimbursement versus upfront).
- Draft milestones as dated, checkable events, not aspirations.
- If a required figure is missing, leave the cell marked
  `[[OPEN: ...]]` with the owner and due date; never plug a plausible
  number.

## Stage 5: Requirement-aligned outline

Goal: a section-by-section map from rubric to draft.

- Mirror the funder's required section order and headings exactly.
- Under each heading, list the rubric points it must answer, the
  applicant facts that answer them, and the OPEN items still missing.
- Assign page or word budgets from the notice limits.
- Validate the outline against the notice and the supplied facts
  yourself: every required section covered, every rubric point
  mapped, every fact cited by an ID present in the facts file.
  Request clarification only for material unresolved project
  choices (which program to propose, what amount to request);
  otherwise proceed to drafting under the existing authorization.
  No routine approval gate sits between outline and draft.

## Stage 6: Draft actual sections, not placeholders

Goal: complete narrative prose the applicant can react to.

- Write full paragraphs under each required heading, in the
  applicant's voice. No lorem ipsum, no `[insert impact here]`,
  no skeleton bullets passed off as a draft.
- Cite the factual basis inline with the fact ID in brackets
  during drafting (for example: `[org-founded]`), and notice
  passages by section (for example: `[notice: eligibility p. 2]`).
  Cite only IDs present in the facts file; never invent a source
  label. Inline marks count toward the checker's word limits, so
  convert or strip them per the funder's format before the final
  `proposal check`, and keep a marked copy for the file.
- Carry every unresolved fact into the draft as a visible
  `[[OPEN: ...]]` note at the exact point where it matters, so
  `proposal check` reports it as an unresolved placeholder. A draft
  with three honest OPEN notes beats a smooth draft with one
  invented fact.
- In the proposal file, link each answer to its evidence with
  `fact_refs` IDs from the separate facts file, and label estimates
  and future commitments with their kind. The checker confirms the
  references resolve; it cannot confirm the text actually supports
  the claim, so that entailment stays in the mock review.
- Never invent numbers, partners, preliminary results, letters of
  support, credentials, or status. This is the observed failure in
  some public editing examples, where the polished version adds
  specific figures, prior results, or partner names absent from the
  original. In this workflow, any specific the evidence does not
  contain is a gap, not an improvement.
- Match verbs to evidence: completed work is past tense with its
  record; planned work is future tense with its milestone; uncertain
  effects are conditional. Do not upgrade a hope into a result.

## Stage 7: Independent mock review

Goal: a cold read against the actual rubric, plus a claim-by-claim
evidence audit. Battle testing showed drafts can invent details
(demand observations, dates, demographics) even while citing valid
fact IDs, so citation presence is not evidence of support.

- Review in a separate context when available, and in a different
  pass than drafting in any case: give the reviewer the notice,
  the facts file, and the draft, not the writer's conclusions.
  Re-read the notice first, then score nothing and predict nothing.
- For each criterion return a verdict of met, unmet, or unclear,
  with a short quote from the draft and the notice passage it must
  satisfy. No numeric scores, no win likelihood, no ranking guess.
- Build a sentence-by-sentence claim/evidence table for every
  material claim in the project summary, the answers, and the
  budget narrative. For each sentence quote the exact supplied
  support (fact ID plus the supporting words, or the notice
  section), then classify it: supported (stated in evidence),
  inference (follows from evidence but adds a step, mark the step),
  proposal (future commitment under applicant authorization),
  or unsupported. Preserve modality and time: past claims need
  past evidence, plans stay conditional on milestones, and every
  date, headcount, and amount is checked digit by digit.
- Remove each unsupported detail or mark it `[[OPEN: ...]]` at the
  exact point where it matters. Never fix the table by inventing a
  retrospective fact or stretching a fact ID beyond its words; the
  only cure is real supplied evidence or a visible gap.
- Work through every `claim_to_review` warning from `proposal
  check` here: each is advisory, never a blocker, and the reviewer
  confirms whether the passage is truthful history with support or
  an unsupported guarantee to fix.
- Mock review findings go back to the applicant; the agent does not
  silently rewrite findings away without new evidence.

This process catches invention; it does not prevent it. The
workbench stays a coarse mechanical check: it confirms references
resolve, limits hold, and arithmetic adds up, never that a sentence
is true.

Brief table example (synthetic, using this guide's fact IDs):

| # | Draft sentence | Exact support quoted | Class |
|---|---|---|---|
| 1 | The Association proposes a free 12-week Saturday workshop in spring 2027. | workshop-plan: "one free 12-week youth bike repair cohort on Saturdays in spring 2027" | supported |
| 2 | Saturday demand is strong among neighborhood teens. | none supplied | unsupported: remove or mark `[[OPEN: demand evidence]]` |
| 3 | Two volunteer mechanics will teach up to 12 youth. | volunteer-staff: "two volunteer mechanics"; workshop-plan: "up to 12 youth ages 12 to 16" | supported |
| 4 | The program will expand citywide in 2028. | none supplied; applicant authorized only one cohort | unsupported: remove; no retrospective fact invention |

## Stage 8: Author-voice and clarity revision

Goal: clear prose that still sounds like the applicant.

- Apply selective editing: cut filler, split overlong sentences,
  remove AI tells (inflated openers, empty intensifiers, vague
  attributions, synonym cycling, hype verbs), and match each claim
  to its evidence pointer.
- Do NOT impose an academic register on community or business
  proposals. Plain, direct language is correct for most nonprofit,
  small business, and workforce funders. Keep the applicant's own
  terms for their work, clients, and neighborhood.
- Preserve every number, name, date, and quoted term exactly.
  Preserve legitimate hedging where the evidence is genuinely
  uncertain; do not upgrade "suggests" to "proves".
- Keep the revision proportionate: fix clarity and correctness,
  not personality. If the applicant supplied a writing sample,
  match its rhythm and vocabulary.

## Stage 9: Final consistency and package checklist

Goal: a submittable package, verified end to end.

- Cross-check: names, amounts, dates, and headcounts identical in
  narrative, budget, forms, and attachments. Run `proposal check`
  and clear every blocker in a mandatory class: missing required
  answers or required attachments, unresolved `[[OPEN: ...]]` on
  funder-mandated evidence, unknown fact references, and budget
  mismatches. These can never be waived into submission readiness;
  the package does not ship until each is resolved with real
  evidence. Only genuinely optional risks (wording choices,
  optional attachments, interpretive judgments recorded in the
  substantive review) may be explicitly accepted by the applicant
  as known risks, with owner and date noted, and they stay visible
  in the file rather than converting the package to ready.
- Verify limits: pages, words, file sizes, file names, margins,
  fonts, signatures, and required forms per the current notice.
- Confirm authorization under `apply.md` before any send, and
  record the receipt the same day.
- File the marked draft, the mock review, and the checklist with
  the case so the next cycle starts from evidence.

## Worked example (fully synthetic, nonacademic)

All facts below are invented for illustration. Nothing here
describes a real organization.

SUPPLIED SYNTHETIC FACTS (stable IDs, as in the facts file):

- org-name (historical, shareable): Maple Street Neighborhood
  Association, Dayton, Ohio.
- workshop-plan (commitment, shareable): one free 12-week youth
  bike repair cohort on Saturdays in spring 2027, up to 12 youth
  ages 12 to 16.
- venue-donation (commitment, shareable): donated church basement
  at 418 Maple Street, Dayton.
- volunteer-staff (historical, private): two volunteer mechanics;
  names on file with the applicant.
- budget-request (estimate, shareable): $8,000 requested for tools,
  parts, and safety gear.

No other evidence is supplied. The draft may cite only these IDs.

EXPLICIT GAP:

- OPEN: the funder requires 501(c)(3) status or a fiscal sponsor.
  The applicant has not supplied either. Do not assert it.

BEFORE (vague, AI-flavored, unsupported):

> In today's rapidly evolving world, underserved youth face
> unprecedented challenges that demand holistic, transformative
> solutions. Our groundbreaking empowerment initiative will leverage
> community synergies to serve hundreds of at-risk teens, fostering
> a vibrant tapestry of opportunity and generational change.

Problems: no supplied fact appears; "hundreds of teens" invents a
number (supplied figure is up to 12); status and venue are missing;
the register is hype, not the applicant's voice.

AFTER (plain, factual, gap visible):

> The Maple Street Neighborhood Association [org-name] proposes a
> free 12-week youth bike repair workshop on Saturdays in spring
> 2027 [workshop-plan] at the donated church basement at 418 Maple
> Street, Dayton [venue-donation]. Two volunteer mechanics will
> teach up to 12 youth ages 12 to 16 to repair and maintain
> bicycles [volunteer-staff] [workshop-plan]. We request $8,000 for
> tools, parts, and safety gear [budget-request]. [[OPEN: 501(c)(3)
> status or fiscal sponsor, required by the notice, not yet
> supplied]].

What changed: every sentence traces to a supplied fact ID from the
list above, and only those IDs; the invented reach number is gone;
the missing tax status is visible exactly where the reviewer will
look for it, and `proposal check` flags it as an unresolved
placeholder until real evidence replaces it. Nothing was added
about partners, prior results, or outcomes the applicant did not
supply, and no provenance beyond the supplied IDs was invented.

## Research appendix (optional)

Use only when the applicant seeks research funding. The current
funder instructions still govern; agency guides change.

- NSF proposals follow the current PAPPG and the specific
  solicitation. Older proposal guides describe stable structure
  but stale details; verify page limits and sections each cycle.
- NIH proposals follow the current application guide and the
  notice of funding opportunity. Under the simplified review
  framework in effect for most research project grants with due
  dates on or after January 25, 2025, reviewers score Factor 1
  (Importance of the Research, covering Significance and
  Innovation) and Factor 2 (Rigor and Feasibility, covering
  Approach) on a 1 to 9 scale, and evaluate Factor 3
  (Expertise and Resources, covering Investigator and
  Environment) as sufficient or with gaps identified, with no
  individual score. All three factors inform the Overall Impact
  score. See the official [simplified review framework](https://www.grants.nih.gov/policy-and-compliance/policy-topics/peer-review/simplifying-review/framework).
  Do not describe Significance, Innovation, and Approach as three
  separately scored criteria for those competitions.
- Claim-feasibility discipline applies: preliminary data, prior
  results, partners, and letters must come from the applicant's
  supplied record. If the support does not exist, flag the gap.

## Tool support

Run the nine stages above through the offline proposal workbench;
see `docs/RUNTIME.md` for the full contract.

```powershell
python -m grant_engine proposal scaffold --proposal-out case-proposal.json --facts-out case-facts.json --opportunity-id maple-bikes-2027
python -m grant_engine proposal check --proposal case-proposal.json --facts case-facts.json --output case-check.json
python -m grant_engine proposal render --proposal case-proposal.json --facts case-facts.json --output case-draft.md
```

Scaffold at stage 5, check after every drafting pass, render for
mock review and final assembly. The engine writes structure and
checks deterministic constraints; the agent writes every word of
narrative. Keep all four files in private case storage.
