# Changelog

All notable changes to `legends-grant` will be documented here.

## 0.3.3 - 2026-11-11

- Enforced ancestor-chain symlink refusal (`refuse_symlink`) and explicit `--overwrite` protection (`open(..., "x")`) across all CLI file inputs, outputs, `--db`, `--registry`, and `collect-document` / `verify-documents` bundle directories and artifacts (`CWE-59`, `CWE-73`, EDR Law 2).
- Hardened `collect-document` SSRF validation (`public_url` and `_addresses` in `grant_engine/documents.py`) against IPv6 NAT64 (`64:ff9b::/96`, `64:ff9b:1::/48`), 6to4 (`2002::/16`), Teredo (`2001::/32`), IPv4-mapped IPv6 addresses, and reserved IANA ranges (`CWE-918`), and capped HTML/text link inventories at `MAX_INVENTORIED_LINKS = 2000`.
- Sanitized untrusted external fields (`title`, `url`, `program_id`, `cycle_id`, `feed_url`, budget table cells, and funder prompts) against raw HTML tags and Markdown pipe/newline injection in `Store.report()` and `render_package()` (`CWE-79`, `CWE-1236`).
- Synchronized `docs/AGENT-RECIPE.md`, `AGENTS.md`, `docs/GRANT-RECIPE.md`, `README.md`, `SECURITY.md`, `MANIFEST.in`, `pyproject.toml`, `.github/workflows/runtime.yml` (`pip>=26.2.2`), and `scripts/check_release.py` to Gold Standard parity.

## 0.3.2 - 2026-11-05

- Added `AGENTS.md`, `docs/AGENT-RECIPE.md`, `THIRD_PARTY_NOTICES.md`, `assets/manifest.json`, and `scripts/check_release.py` Gold Standard static release gate.
- Documented explicit EDR and Security Guardrails across `AGENTS.md`, `docs/AGENT-RECIPE.md`, and `docs/GRANT-RECIPE.md`, and removed legacy `bin/lg-selftest.sh` wrapper.
- Expanded `.github/workflows/runtime.yml` and `.github/workflows/contract.yml` to run across Ubuntu, Windows, and macOS with 40-character SHA action pins and explicit `contents: read` permissions.

## 0.3.1 - 2026-11-04

- Replace inline `python -c` and hidden-window subprocess flags in `grant_engine/documents.py` PDF extraction with a standard module entry point (`python -m grant_engine.documents`) and captured `stderr=PIPE` while preserving the 15-second timeout and 200-page / 2-million-character parser bounds.

## 0.3.0 - 2026-10-03

- Add a proposal-writing workflow from funder questions and supplied facts through
  narrative drafting, rubric review, revision, budget and attachment preparation.
- Add offline proposal scaffold, check and Markdown render commands, with separate
  applicant facts, explicit evidence references and mechanical constraint checks.
- Preserve historical facts, estimates and commitments as distinct evidence types;
  substantive claim support and writing quality remain agent or human review.
- Add synthetic nonacademic examples, adversarial tests and an independent
  draft-review-revision exercise. These do not measure award success.
- Credit the grant-writing and academic-editing projects consulted for methods;
  no upstream prompt pack or hosted writing service is bundled.

## 0.2.1 - 2026-10-02

- Add prominent README credits for upstream feed operators, design references,
  federal data and the optional PDF dependency, with explicit reuse boundaries.
- Include repository, documentation, issues and release links in package metadata.
- Documentation and packaging only; discovery and qualification behavior is unchanged.

## 0.2.0 - 2026-10-02

- Replaces federal-first routing with applicant/project-led nationwide discovery.
- Adds a researched 115-source registry spanning all 50 states, DC and five
  territories, plus national and third-party discovery routes.
- Adds standard-library Python source planning, bounded Grants.gov and four
  CommonGrants feed consumers, immutable public evidence and replay/check tools.
- Documents source provenance, mixed funding instruments, GitHub reuse, access
  limits and the remaining qualification/monitoring/application build plan.
- Adds bounded public document collection, content hashes, HTML/text extraction,
  optional PDF extraction, attachment link inventory and bundle verification.
- Adds local evidence search, source/status/freshness labels and snapshot comparison.
- Adds explicit reviewed-rule evaluation against separate private applicant facts;
  missing evidence, incomplete inventories and unresolved conflicts block a positive review.
- Packages the registry and CLI for use outside a source checkout, with offline
  readiness checks, adversarial tests and Windows/Linux CI.
- No automatic grant submissions, paid-provider dependencies, exhaustive coverage
  or autonomous eligibility extraction. See the verification and battle-test reports.

## 0.1.0 - 2026-09-25

Router-native reset: de-skillified to the single `cto-legends` router
skill (vendored pinned copy at `skills/cto-legends/SKILL.md`), root
`SKILL.md` moved to `docs/GRANT-RECIPE.md` with skill frontmatter
removed, `VERSION` set to `0.1.0`, contract CI added. No capability
change: federal no-key lanes verified live 2026-09-24.
