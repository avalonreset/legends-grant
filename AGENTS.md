# legends-grant agent operating instructions

Use `legends-grant` (`python -m grant_engine`) for US federal, state, local, tribal, and foundation grant discovery, SQLite evidence collection, conservative qualification review, and evidence-linked proposal drafting.

Read [docs/AGENT-RECIPE.md](docs/AGENT-RECIPE.md) and [docs/GRANT-RECIPE.md](docs/GRANT-RECIPE.md) before running collection or drafting workflows.

## Operating rules

1. Run `python -m grant_engine doctor` first to verify offline readiness, the 115-source nationwide registry (`grant_engine/data/us-sources.json`), and optional PDF extraction support (`pypdf`).
2. Plan sources by applicant type, jurisdiction, and project purpose (`python -m grant_engine plan`) rather than defaulting to federal-only search.
3. Keep the SQLite evidence store (`Store`) strictly public-only. Never store private applicant profiles, SSNs, EINs, bank details, or credentials inside the public evidence database.
4. Keep eligibility reviews (`review`) and proposal packages (`proposal`) separate from public opportunity evidence, and never convert unknown facts or unverified clauses into assumed passes.
5. Never submit a grant application automatically. Any external submission requires explicit user authorization and a verified receipt.

## EDR and Security Guardrails

- Zero browser state or local desktop credential store reads (`Local State`, `Login Data`, `Cookies`, `IndexedDB`, `LevelDB`, DPAPI, Keychain).
- Zero executable shell wrappers (`.ps1`, `.sh`, `.bat`, `.cmd`, `.vbs`, `.wsf`, `.hta`, `.scr`) shipped inside the repository.
- Outbound network traffic is restricted to explicit user-invoked public HTTPS grant endpoints (`api.grants.gov`, vetted `*.api.cg.a6lab.ai` CommonGrants state feeds, and explicit HTTPS URLs passed to `collect-document`) with HTTP redirects disabled (`NoRedirect`).
- PDF text extraction runs in a bounded subprocess via `python -m grant_engine.documents` with a 15-second timeout, 200-page limit, and 2-million-character cap, with zero inline `python -c` execution or hidden-window flags.
- All PNG and WebP assets are stripped of ancillary metadata chunks (`tEXt`, `iTXt`, `zTXt`, `eXIf`, `EXIF`, `XMP`) before commit.
