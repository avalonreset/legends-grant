# legends-grant agent recipe

Complete CLI reference and execution workflow for `legends-grant` (`python -m grant_engine`). See also [docs/GRANT-RECIPE.md](GRANT-RECIPE.md) and [docs/RUNTIME.md](RUNTIME.md).

## CLI Subcommand Reference

Run all commands via `python -m grant_engine` (or the installed `grant-engine` entry point):

| Subcommand | Command Syntax | Purpose | Network / Side Effects |
| --- | --- | --- | --- |
| `doctor` | `python -m grant_engine doctor` | Check offline package readiness, 115-source registry count, and optional `pypdf` availability | Offline, read-only |
| `sources` | `python -m grant_engine sources [--registry REG] [--jurisdiction J] [--applicant-type A] [--purpose P] [--output OUT.json] [--overwrite]` | List and filter the nationwide 115-source grant registry | Offline |
| `plan` | `python -m grant_engine plan [--registry REG] [--jurisdiction J] [--applicant-type A] [--purpose P] [--output OUT.json] [--overwrite]` | Rank candidate sources and emit explicit agent research tasks for unadapted sources | Offline |
| `discover` (`grants-gov`) | `python -m grant_engine discover grants-gov --query QUERY [--limit 25] [--page-size 25] --output OUT.json [--overwrite]` | Retrieve bounded federal opportunity hits and details from `api.grants.gov` | Public HTTPS (`api.grants.gov`), writes `OUT.json` |
| `discover` (`common-grants`) | `python -m grant_engine discover common-grants --base-url URL --source-id ID [--limit 25] [--page-size 25] --output OUT.json [--overwrite]` | Retrieve bounded opportunities from vetted state CommonGrants feeds (`commongrants-ca`, `commongrants-pa`, `commongrants-wa`, `commongrants-md`) | Public HTTPS (`*.api.cg.a6lab.ai`), writes `OUT.json` |
| `ingest` | `python -m grant_engine ingest --db DB.sqlite --input PACKET.json` | Ingest normalized public opportunity packets into the append-only SQLite evidence store | Local SQLite write |
| `search` | `python -m grant_engine search --db DB.sqlite [--query Q] [--status S] [--record-type T] [--jurisdiction J] [--limit 25] [--output OUT.json] [--overwrite]` | Search local SQLite evidence with freshness and source-authority labels | Offline |
| `report` | `python -m grant_engine report --db DB.sqlite [--output OUT.md] [--overwrite]` | Render human-readable summary of stored public opportunities and unassessed eligibility | Offline |
| `export` | `python -m grant_engine export --db DB.sqlite [--history] [--output OUT.json] [--overwrite]` | Export current or full-history records and runs from the SQLite evidence store | Offline |
| `check` | `python -m grant_engine check --db DB.sqlite` | Verify SQLite evidence store hash integrity, revision triggers, and index consistency | Offline |
| `replay` | `python -m grant_engine replay --db NEW_DB.sqlite --input EXPORT.json` | Replay an exported history packet into a fresh SQLite store | Local SQLite write |
| `changes` | `python -m grant_engine changes --before BEFORE.json --after AFTER.json [--output OUT.json] [--overwrite]` | Compare two evidence exports to flag status, deadline, or notice changes | Offline |
| `collect-document` | `python -m grant_engine collect-document --url HTTPS_URL --bundle DIR [--output OUT.json] [--overwrite]` | Download one explicit public HTTPS notice or attachment, compute SHA-256, extract text/links | Public HTTPS (`HTTPS_URL`), writes bundle artifacts |
| `verify-documents` | `python -m grant_engine verify-documents --bundle DIR [--output OUT.json] [--overwrite]` | Verify saved document bundle hashes offline | Offline |
| `review` | `python -m grant_engine review --review REVIEW.json --facts FACTS.json [--as-of ISO_TS] --output OUT.json [--overwrite]` | Evaluate explicitly reviewed eligibility rules against separate private applicant facts | Offline, writes private assessment |
| `proposal` (`init` / `scaffold`) | `python -m grant_engine proposal scaffold [--opportunity-id ID] --proposal-out PROP.json --facts-out FACTS.json [--output OUT.json] [--overwrite]` | Generate offline proposal and private applicant-facts JSON scaffolds | Offline, writes scaffold files |
| `proposal` (`check`) | `python -m grant_engine proposal check --proposal PROP.json --facts FACTS.json [--output OUT.json] [--overwrite]` | Check deterministic proposal constraints (word limits, budget math, citations, placeholders) | Offline |
| `proposal` (`render`) | `python -m grant_engine proposal render --proposal PROP.json --facts FACTS.json --output DRAFT.md [--overwrite]` | Render a Markdown proposal review draft from checked proposal and facts JSON | Offline, writes Markdown draft |

## Standard Workflow Sequence

1. **Readiness & Source Planning**:

   ```bash
   python -m grant_engine doctor
   python -m grant_engine plan --jurisdiction PA --applicant-type business --purpose workforce --output plan.json
   ```

2. **Public Evidence Collection & Storage**:

   ```bash
   python -m grant_engine discover grants-gov --query "workforce training" --limit 10 --output federal.json
   python -m grant_engine ingest --db evidence.sqlite --input federal.json
   python -m grant_engine check --db evidence.sqlite
   ```

3. **Notice Collection & Qualification Review**:

   ```bash
   python -m grant_engine collect-document --url https://example.gov/nofo.pdf --bundle ./notices/opp-1
   python -m grant_engine verify-documents --bundle ./notices/opp-1
   python -m grant_engine review --review qualification-review.json --facts private-facts.json --output review-result.json
   ```

4. **Proposal Drafting & Verification**:

   ```bash
   python -m grant_engine proposal scaffold --opportunity-id opp-1 --proposal-out proposal.json --facts-out proposal-facts.json
   python -m grant_engine proposal check --proposal proposal.json --facts proposal-facts.json
   python -m grant_engine proposal render --proposal proposal.json --facts proposal-facts.json --output proposal-draft.md
   ```

## EDR and Security Guardrails

- Zero browser state or local desktop credential store reads (`Local State`, `Login Data`, `Cookies`, `IndexedDB`, `LevelDB`, DPAPI, Keychain).
- Zero executable shell wrappers (`.ps1`, `.sh`, `.bat`, `.cmd`, `.vbs`, `.wsf`, `.hta`, `.scr`) shipped inside the repository.
- Outbound network traffic is restricted to explicit user-invoked public HTTPS grant endpoints (`api.grants.gov`, vetted `*.api.cg.a6lab.ai` CommonGrants state feeds, and explicit HTTPS URLs passed to `collect-document`). API feed adapters disable HTTP redirects (`NoRedirect`), while `collect-document` follows at most `max_redirects=5` public HTTPS hops with per-hop SSRF and DNS-pinning validation.
- All CLI file and directory inputs, outputs, SQLite database paths, and document bundles refuse symlinks (and symlinked non-system parent directories) and require `--overwrite` before replacing existing output files.
- PDF text extraction runs in a bounded subprocess via `python -m grant_engine.documents` with a 15-second timeout, 200-page limit, and 2-million-character cap, with zero inline `python -c` execution or hidden-window flags.
- All PNG and WebP assets are stripped of ancillary metadata chunks (`tEXt`, `iTXt`, `zTXt`, `eXIf`, `EXIF`, `XMP`) before commit.
- Never store private applicant profiles or secrets inside the public SQLite evidence database, and never submit applications without explicit authorization.
