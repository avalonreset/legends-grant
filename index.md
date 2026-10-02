# index

Home for `legends-grant`. US nationwide discovery and reviewed evidence, v0.2.0.

- Agent entry: [GRANT-RECIPE](docs/GRANT-RECIPE.md)
- Lanes: [find](find.md) · [match](match.md) · [qualify](qualify.md) · [apply](apply.md) · [submit lanes](submit-lanes.md)
- Brain: [sources](sources.md) · [federal](federal.md) · [private-rolling](private-rolling.md) · [vault map](vault-map.md)
- States: [states index](states/_Index.md)
- Templates: [business profile](business-profile-template.md) · [opportunity note](opportunity-note-template.md)
- Self-test: `python -m unittest discover -s tests`; offline readiness:
  `python -m grant_engine doctor`.

## Current development

- [Nationwide design](docs/NATIONWIDE-DESIGN.md), [source research](docs/SOURCE-RESEARCH.md), [coverage](docs/COVERAGE.md)
- [115-source registry](grant_engine/data/us-sources.json), [runtime guide](docs/RUNTIME.md)
- Two adapter types support five configured sources. All other routes are agent
  research tasks. Reviewed qualification requires agent-prepared evidence and rules;
  automatic monitoring and application submissions are not implemented.

## Historical 0.1.0 status

- 0.1.0: federal no-key lanes verified live; SAM key-gated lanes doc-verified
  pending real key; SBIR API 403 + maintenance notice, re-probe later;
  state lane STUB (index ready, rows fill on real requests).
