"""Run with python -m grant_engine --help."""
import argparse
import json
import sys
import importlib.util
from pathlib import Path

from .core import Store, load_registry, plan, report
from .grants_gov import discover
from .common_grants import discover as discover_common
from . import __version__

REGISTRY = Path(__file__).resolve().parent / "data" / "us-sources.json"


class InputError(ValueError):
    """Fixed, safe CLI guidance, never source or applicant values."""


def read_json(path):
    # Bound bytes before decoding; JSON may expand further in memory.
    with Path(path).open("rb") as handle:
        raw = handle.read(50_000_001)
    if len(raw) > 50_000_000:
        raise InputError("Input exceeds the 50 MB JSON limit; split the evidence packet.")
    return json.loads(raw.decode("utf-8-sig"))


def write(value, path=None):
    text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv=None):
    parser = argparse.ArgumentParser(description="US grant discovery, evidence collection, and reviewed qualification. No automatic submissions.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Offline package and registry readiness; no network calls")
    for command in ("sources", "plan"):
        child = sub.add_parser(command, help="List/filter sources" if command == "sources" else "Plan sources and explicit agent research tasks")
        child.add_argument("--registry", default=str(REGISTRY))
        child.add_argument("--jurisdiction")
        child.add_argument("--applicant-type")
        child.add_argument("--purpose")
        child.add_argument("--output")
    child = sub.add_parser("discover", help="Bounded no-key Grants.gov or public CommonGrants evidence")
    child.add_argument("adapter", choices=["grants-gov", "common-grants"])
    child.add_argument("--query")
    child.add_argument("--base-url", help="Vetted public AgileSix CommonGrants host")
    child.add_argument("--source-id", help="commongrants-ca, commongrants-pa, commongrants-wa, commongrants-md")
    child.add_argument("--limit", type=int, default=25)
    child.add_argument("--page-size", type=int, default=25)
    child.add_argument("--output", required=True)
    child = sub.add_parser("search", help="Search current local evidence, not the entire web")
    child.add_argument("--db", required=True)
    child.add_argument("--query", default="")
    child.add_argument("--status")
    child.add_argument("--record-type")
    child.add_argument("--jurisdiction")
    child.add_argument("--limit", type=int, default=25)
    child.add_argument("--output")
    child = sub.add_parser("changes", help="Compare two current exports; absence never means closed")
    child.add_argument("--before", required=True)
    child.add_argument("--after", required=True)
    child.add_argument("--output")
    child = sub.add_parser("collect-document", help="Collect one explicit public HTTPS notice or attachment")
    child.add_argument("--url", required=True)
    child.add_argument("--bundle", required=True)
    child.add_argument("--output")
    child = sub.add_parser("verify-documents", help="Verify saved artifact hashes offline")
    child.add_argument("--bundle", required=True)
    child.add_argument("--output")
    child = sub.add_parser("review", help="Evaluate explicitly reviewed rules against separate private facts")
    child.add_argument("--review", required=True)
    child.add_argument("--facts", required=True)
    child.add_argument("--as-of", help="ISO date/time for reproducible review, otherwise now")
    child.add_argument("--output", required=True, help="Private assessment output; keep outside public evidence")
    for command in ("ingest", "export", "report", "check", "replay"):
        child = sub.add_parser(command)
        child.add_argument("--db", required=True)
        if command in ("ingest", "replay"):
            child.add_argument("--input", required=True, help="Public normalized JSON packet; replay restores exported history")
        if command in ("export", "report"):
            child.add_argument("--output")
        if command == "export":
            child.add_argument("--history", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            sources = load_registry(REGISTRY)
            write({"ok": True, "version": __version__, "sources": len(sources),
                   "structured_sources": sum(bool(s.get("adapter")) for s in sources),
                   "pdf_text_extraction": importlib.util.find_spec("pypdf") is not None,
                   "network_tested": False, "qualification": "requires explicit reviewed rules and separate facts"})
        elif args.command in ("sources", "plan"):
            selected = plan(load_registry(args.registry), args.jurisdiction, args.applicant_type, args.purpose)
            write({"sources": selected, "qualification": "unassessed", "coverage": "Registry routes are not completed searches"}, args.output)
        elif args.command == "discover":
            if args.adapter == "grants-gov":
                if not args.query or not args.query.strip():
                    raise InputError("Grants.gov discovery requires --query.")
                packet = discover(args.query or "", args.limit, args.page_size)
            else:
                if args.query is not None:
                    raise InputError("CommonGrants does not support --query. Collect a bounded feed, then use search on the saved evidence.")
                packet = discover_common(args.base_url or "", args.source_id, args.limit, args.page_size)
            write(packet, args.output)
            return 2 if packet["run"]["errors"] else 0
        elif args.command == "search":
            from .search import search
            if not Path(args.db).is_file():
                raise ValueError("Search requires an existing database")
            store = Store(args.db)
            try:
                write(search(store.export(), args.query, status=args.status,
                             record_type=args.record_type, jurisdiction=args.jurisdiction,
                             limit=args.limit), args.output)
            finally:
                store.close()
        elif args.command == "changes":
            from .search import compare_packets
            before = read_json(args.before)
            after = read_json(args.after)
            write(compare_packets(before, after), args.output)
        elif args.command in ("collect-document", "verify-documents"):
            from .documents import collect_document, verify_bundle
            result = (collect_document(args.url, args.bundle) if args.command == "collect-document"
                      else verify_bundle(args.bundle))
            write(result, args.output)
            return 0 if result["ok"] else 2
        elif args.command == "review":
            from .qualification import evaluate_review
            review = read_json(args.review)
            facts = read_json(args.facts)
            write(evaluate_review(review, facts, as_of=args.as_of), args.output)
        else:
            if args.command in ("check", "export", "report") and not Path(args.db).is_file():
                raise ValueError("Read commands require an existing database")
            store = Store(args.db)
            try:
                if args.command in ("ingest", "replay"):
                    if args.command == "replay" and (store.export(True)["records"] or store.export()["runs"]):
                        raise ValueError("Replay requires an empty destination store")
                    packet = read_json(args.input)
                    write({"revisions_added": store.ingest(packet)})
                elif args.command == "check":
                    result = store.check()
                    write(result)
                    return 0 if result["ok"] else 2
                elif args.command == "export":
                    write(store.export(args.history), args.output)
                else:
                    write(report(store.export()), args.output)
            finally:
                store.close()
        return 0
    except InputError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except FileNotFoundError:
        print("A required input file or output directory is missing. Check the command's explicit paths.", file=sys.stderr)
        return 2
    except Exception as exc:
        # File names, URLs, remote messages, and record values may be private.
        print("Command failed (" + type(exc).__name__ + "). Validate public input/schema and paths.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
