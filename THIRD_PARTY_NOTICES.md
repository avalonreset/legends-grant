# Third-Party Notices

`legends-grant` (`legends-grant-evidence`) is licensed under the MIT License (`LICENSE`).

## Runtime Dependencies

- **Python Standard Library**: Python Software Foundation License v2. The core `grant_engine` runtime uses only the Python 3.11+ standard library.

## Optional Dependencies

- **pypdf** (`pypdf>=6,<7`, installed via `.[pdf]`): BSD-3-Clause License. Used optionally for bounded offline PDF text extraction in `grant_engine.documents`.

## Public Data Feeds and Design References

- **Grants.gov Public API** (`https://www.grants.gov/`): United States federal government public opportunity data.
- **Agile Six CommonGrants State Adapters** (`CA`, `PA`, `WA`, `MD`) and **CommonGrants Specification**: Public state opportunity feeds consumed via HTTPS; no upstream server code is bundled.
- **eseckel/ai-for-grant-writing** (CC-BY-4.0) and **AIScientists-Dev/academic-humanizer** (MIT): Consulted as methodological references for proposal rubric design; no upstream text or code is bundled.
