# legends-grant: agentically assisted business grant finding and application

Markdown-driven Legends module for finding, qualifying, and applying for
US business grants. Your agent does as much of the work as possible:
search live grant sources, match them against your vault-mapped business,
draft the package, and submit where the channel allows once you authorize
that exact send.

## Agent setup (via `cto-legends`)

Part of the [CTO Legends](https://github.com/avalonreset/cto-legends) ecosystem. `cto-legends` is the only registered skill; this repo vendors a pinned copy at `skills/cto-legends/SKILL.md`.

Install with `cto-legends install legends-grant`, then follow the module recipe the router loads. Do not register this module as its own skill.

Standalone use: `docs/GRANT-RECIPE.md` is the agent entry point.

## Why this beats asking an agent for grants

A generic ask returns a link list. legends-grant returns a sourced,
qualified, submittable answer:

1. MAP your vault-mapped business (or each client) to a profile once.
2. SWEEP federal APIs first, state programs second, private rolling third.
3. SCORE every candidate 0-12 with the math shown.
4. GATE each top pick against the live notice text, quoted, not guessed.
5. BUILD the narrative, budget, and attachments.
6. SEND once per authorization, receipt or it did not happen.
7. TRACK award windows and reporting duties.

A run that ends in honest OUTs is still a victory: it spent an hour, not
six weeks, and the notes stay warm for the next round.

## Live sources, verified

Federal no-key APIs: grants.gov search2 + fetchOpportunity, NIH Guide,
NIH RePORTER, USAspending. Key-gated: SAM.gov Assistance Listings and
Opportunities v2. Structured: SBA STEP, USDA RBDG, EDA, MBDA, 50-state
index. Private rolling: Hello Alice, IFundWomen, Amber, NASE, Verizon.
Dead programs are marked dead (FedEx retired, Comcast RISE formless).

## Repo layout

- `docs/GRANT-RECIPE.md`: agent entry point and routing
- `find.md`, `match.md`, `qualify.md`, `apply.md`: the four working lanes
- `submit-lanes.md`: agent-agnostic submission contract (any harness)
- `vault-map.md`: plug vault-mapped businesses and client portfolios in
- `sources.md`, `federal.md`, `private-rolling.md`, `veteran.md`: registry
- `states/`: 50-state index plus live state files
- `glossary.md`, `victory-path.md`: plain-English terms, 7-step checklist
- `bin/lg-selftest.sh`: no-key federal lane self-test
- `test/fixtures/`: five business archetypes for battle-testing

Personal run data (`profiles/`, `opportunities/`) never ships: see
`.gitignore`. One profile per business, one note per opportunity, every
claim with source plus retrieved date.

## Self-test

```sh
bash bin/lg-selftest.sh
```

## License

MIT. See LICENSE.
