"""Bounded public document collection; a fetched page is never a complete notice.

Only explicit HTTPS URLs are fetched. Links are inventoried, never followed.
The default transport pins a validated public IP and verifies TLS against the
original hostname, including after redirects. No ambient proxies/cookies/auth.
"""
import hashlib
import http.client
import io
import ipaddress
import json
import re
import socket
import ssl
import subprocess
import sys
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlsplit, urlunsplit

from .core import SENSITIVE, canonical, now


class DocumentError(ValueError):
    """A safe, nonsecret failure reason suitable for a receipt."""


@dataclass
class FetchResponse:
    status: int
    headers: dict
    body: bytes


def public_url(url):
    """Validate URL syntax and reject credential-bearing query parameters."""
    if not isinstance(url, str) or len(url) > 8192 or re.search(r"[\x00-\x20\x7f\\]", url):
        raise DocumentError("invalid_url")
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        raise DocumentError("invalid_url") from None
    if parts.scheme != "https" or not parts.hostname or port not in (None, 443):
        raise DocumentError("public_https_required")
    if parts.username is not None or parts.password is not None:
        raise DocumentError("credential_url_refused")
    for key, _ in parse_qsl(parts.query, keep_blank_values=True):
        # Match the public store's policy, including structured query keys such
        # as profile[ssn]. Parameter names alone are enough to refuse collection;
        # values are never inspected, logged or copied into rejection receipts.
        normalized = re.sub(r"[^a-z]", "", key.lower())
        segments = re.findall(r"[a-z]+", key.lower())
        if normalized in SENSITIVE or any(segment in SENSITIVE for segment in segments):
            raise DocumentError("private_query_refused")
        key = re.sub(r"[^a-z0-9]", "", key.lower())
        if any(word in key for word in ("token", "secret", "password", "signature", "credential", "apikey", "accesskey", "authorization")) or key in {"key", "auth", "sig", "code", "session", "sessionid"}:
            raise DocumentError("credential_url_refused")
    host = parts.hostname.rstrip(".").lower()
    if host in {"localhost", "metadata.google.internal"} or host.endswith((".localhost", ".local", ".internal")):
        raise DocumentError("private_host_refused")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if not re.fullmatch(r"[a-z0-9.-]+", host) or "." not in host:
            raise DocumentError("invalid_public_hostname") from None
    else:
        if not address.is_global or address.is_multicast:
            raise DocumentError("private_address_refused")
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def _addresses(url, resolver):
    host = urlsplit(url).hostname
    result = resolver(host, 443, type=socket.SOCK_STREAM)
    addresses = list(dict.fromkeys(item[4][0] for item in result))
    if not addresses:
        raise DocumentError("dns_empty")
    for item in addresses:
        address = ipaddress.ip_address(item.split("%")[0])
        if not address.is_global or address.is_multicast:
            raise DocumentError("private_dns_answer_refused")
    return addresses


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address, timeout):
        super().__init__(host, 443, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        sock = socket.create_connection((self.address, 443), self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except Exception:
            sock.close()
            raise


def _fetch(url, timeout, max_bytes, addresses):
    parts = urlsplit(url)
    connection = _PinnedHTTPS(parts.hostname, addresses[0], timeout)
    deadline = time.monotonic() + timeout
    try:
        connection.request("GET", urlunsplit(("", "", parts.path, parts.query, "")), headers={"User-Agent": "legends-grant/0.2 public-evidence", "Accept-Encoding": "identity"})
        response = connection.getresponse()
        header_items = response.getheaders()
        lengths = [value for key, value in header_items if key.lower() == "content-length"]
        if len(lengths) > 1:
            raise DocumentError("duplicate_content_length")
        headers = {key.lower(): value for key, value in header_items}
        if response.status in (301, 302, 303, 307, 308):
            return FetchResponse(response.status, headers, b"")
        length = headers.get("content-length")
        if length is not None:
            if not re.fullmatch(r"[0-9]+", length):
                raise DocumentError("invalid_content_length")
            if int(length) > max_bytes:
                raise DocumentError("response_too_large")
        chunks, count = [], 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise DocumentError("request_timeout")
            # read1 makes progress after one underlying read, preventing a slow
            # trickle from defeating our total body deadline.
            if connection.sock:
                connection.sock.settimeout(remaining)
            chunk = response.read1(min(65536, max_bytes + 1 - count))
            if not chunk:
                break
            chunks.append(chunk)
            count += len(chunk)
            if count > max_bytes:
                raise DocumentError("response_too_large")
        return FetchResponse(response.status, headers, b"".join(chunks))
    finally:
        connection.close()


class _HTMLText(HTMLParser):
    def __init__(self, base_url):
        super().__init__(convert_charrefs=True)
        self.base_url, self.parts, self.links, self.hidden = base_url, [], [], 0
        self.link_set, self.base_seen = set(), False
        self.link_details, self.active_link = [], None
        self.login_form = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "template"}:
            self.hidden += 1
        if self.hidden:
            return
        if tag in {"p", "div", "br", "li", "tr", "td", "th", "h1", "h2", "h3", "section"}:
            self.parts.append("\n")
        attrs = dict(attrs)
        if tag == "input" and (attrs.get("type") or "").lower() == "password":
            self.login_form = True
        if tag == "form":
            form_hints = " ".join(attrs.get(key) or "" for key in ("action", "id", "name", "class"))
            if re.search(r"(?:^|[^a-z])(?:log[-_]?in|sign[-_]?in|authenticate|authentication)(?:$|[^a-z])", form_hints, re.I):
                self.login_form = True
        if tag == "base" and attrs.get("href") and not self.base_seen:
            self.base_seen = True
            try:
                self.base_url = public_url(urljoin(self.base_url, attrs["href"]))
            except DocumentError:
                pass
        # Stylesheets/preload assets are not notice attachments.
        href = attrs.get("href") if tag == "a" else attrs.get("src") if tag in {"iframe", "embed"} else attrs.get("data") if tag == "object" else None
        if href:
            try:
                url = public_url(urljoin(self.base_url, href))
            except DocumentError:
                return
            if url not in self.link_set:
                self.links.append(url)
                self.link_set.add(url)
            detail = {"url": url, "label": attrs.get("title", ""), "element": tag}
            self.link_details.append(detail)
            if tag == "a":
                self.active_link = detail

    def handle_endtag(self, tag):
        if tag == "a":
            self.active_link = None
        if tag in {"script", "style", "noscript", "template"} and self.hidden:
            self.hidden -= 1
        if tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "section"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)
            if self.active_link is not None:
                self.active_link["label"] = (self.active_link["label"] + " " + data.strip()).strip()


def _text_links(text):
    links = []
    for value in re.findall(r'https://[^\s<>"\x00-\x20]+', text):
        try:
            url = public_url(value.rstrip(".,;)]}"))
        except DocumentError:
            continue
        if url not in links:
            links.append(url)
    return links


def _pdf_worker():
    """Isolated parser, with bounded page count and emitted text size."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(sys.stdin.buffer.read(50_000_001)), strict=False)
        if reader.is_encrypted:
            result = {"text": "", "status": "blocked_encrypted_pdf"}
        elif len(reader.pages) > 200:
            result = {"text": "", "status": "blocked_pdf_page_limit"}
        else:
            parts, count = [], 0
            for page in reader.pages:
                text = page.extract_text() or ""
                count += len(text)
                if count > 2_000_000:
                    raise DocumentError("blocked_pdf_text_limit")
                parts.append(text)
            text = "\n".join(parts)
            result = {"text": text, "status": "extracted" if text.strip() else "blocked_scan_requires_ocr"}
    except Exception as exc:
        result = {"text": "", "status": str(exc) if isinstance(exc, DocumentError) else "blocked_pdf_parse"}
    sys.stdout.write(json.dumps(result, ensure_ascii=True))


def _extract(body, content_type, final_url):
    mime = content_type.split(";", 1)[0].strip().lower()
    if body.startswith(b"%PDF-") or mime == "application/pdf":
        try:
            import pypdf  # noqa: F401 - only probe availability in this process
        except ImportError:
            return "", [], "blocked_pdf_dependency", "pdf", []
        try:
            result = subprocess.run([sys.executable, "-c", "from grant_engine.documents import _pdf_worker; _pdf_worker()"],
                input=body, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=15,
                cwd=str(Path(__file__).resolve().parent.parent),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=True)
            value = json.loads(result.stdout)
            links = _text_links(value["text"])
            return value["text"], links, value["status"], "pdf", [{"url": url, "label": "", "element": "visible_text"} for url in links]
        except subprocess.TimeoutExpired:
            return "", [], "blocked_pdf_timeout", "pdf", []
        except Exception:
            return "", [], "blocked_pdf_parse", "pdf", []
    if mime not in {"text/html", "application/xhtml+xml", "text/plain", "text/csv", "application/json", "application/xml", "text/xml"}:
        return "", [], "blocked_unsupported_format", mime or "unknown", []
    charset = re.search(r"charset\s*=\s*[\"']?([a-zA-Z0-9._-]+)", content_type, re.I)
    try:
        text = body.decode(charset.group(1) if charset else "utf-8", errors="strict")
    except (UnicodeError, LookupError):
        return "", [], "blocked_text_encoding", mime, []
    if mime in {"text/html", "application/xhtml+xml"}:
        parser = _HTMLText(final_url)
        parser.feed(text)
        text = "\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip())
        status = "extracted"
        if parser.login_form or (len(text) < 1500 and any(marker in text.lower() for marker in ("sign in to view", "log in to view", "login required", "authentication required", "sign in to continue", "log in to continue"))):
            status = "blocked_login_html"
        elif len(re.sub(r"\s", "", text)) < 40:
            status = "blocked_insufficient_html_text"
        elif len(text) < 500 and any(marker in text.lower() for marker in ("enable javascript", "javascript is required", "access denied", "verify you are human", "checking your browser")):
            status = "blocked_interactive_html"
        return text, parser.links, status, "html", parser.link_details
    links = _text_links(text)
    return text, links, "extracted" if text.strip() else "blocked_empty_text", "text", [{"url": url, "label": "", "element": "visible_text"} for url in links]


def _artifact(root, body, folder, suffix):
    root = root.resolve()
    checksum = hashlib.sha256(body).hexdigest()
    relative = f"{folder}/{checksum}{suffix}"
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise DocumentError("artifact_outside_bundle")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Never silently repair corruption or overwrite user evidence.
    try:
        with path.open("xb") as stream:
            stream.write(body)
    except FileExistsError:
        if path.read_bytes() != body:
            raise DocumentError("existing_artifact_corrupt")
    return {"path": relative, "sha256": checksum, "bytes": len(body)}


def collect_document(url, bundle_dir, *, transport=None, resolver=socket.getaddrinfo,
                     max_bytes=10_000_000, timeout=20, max_redirects=5):
    """Collect one URL and persist a receipt, including for failed attempts.

    Injected transport(url, timeout, max_bytes) -> FetchResponse must not follow
    redirects. Tests inject resolver too. `ok` means bytes AND extractable text;
    `retrieved` distinguishes usable raw evidence from blocked extraction.
    Authority, notice completeness and eligibility always remain unassessed.
    """
    if type(max_bytes) is not int or not 1 <= max_bytes <= 50_000_000 or not 0 < timeout <= 120 or type(max_redirects) is not int or not 0 <= max_redirects <= 10:
        raise ValueError("Invalid collection bounds")
    root = Path(bundle_dir)
    receipt = {"schema_version": 1, "fetched_at": now(), "ok": False, "retrieved": False,
               "document": None, "errors": [], "redirects": [], "notice_complete": False,
               "authority": "unassessed", "eligibility": "unassessed", "content_review_required": True,
               "limits": {"max_bytes": max_bytes, "timeout_seconds": timeout, "max_redirects": max_redirects},
               "limitations": ["Only the explicit URL was collected", "Links are unreviewed inventory, not fetched attachments", "HTML login and challenge detection is conservative and incomplete; extraction success never confirms a grant notice", "PDF links use visible extracted URLs only; annotations, embedded files and line-wrapped URLs may be absent", "Extraction is not notice review; scanned PDFs need OCR", "DNS resolution uses the operating system resolver timeout", "PDF extraction: separate 15-second process timeout, 200-page and 2-million-character limits; no hard process memory limit"]}
    try:
        current = public_url(url)
        receipt["requested_url"] = current
        started = time.monotonic()
        seen = set()
        for hop in range(max_redirects + 1):
            if current in seen:
                raise DocumentError("redirect_loop")
            seen.add(current)
            addresses = _addresses(current, resolver)
            remaining = timeout - (time.monotonic() - started)
            if remaining <= 0:
                raise DocumentError("request_timeout")
            response = transport(current, remaining, max_bytes) if transport else _fetch(current, remaining, max_bytes, addresses)
            headers = {key.lower(): value for key, value in response.headers.items()}
            if response.status in (301, 302, 303, 307, 308):
                if hop == max_redirects:
                    raise DocumentError("redirect_limit")
                target = public_url(urljoin(current, headers.get("location", "")))
                receipt["redirects"].append({"from": current, "to": target, "status": response.status})
                current = target
                continue
            if response.status != 200:
                raise DocumentError("http_status_" + str(response.status))
            if headers.get("content-encoding", "identity").lower() not in {"", "identity"}:
                raise DocumentError("compressed_response_refused")
            if not isinstance(response.body, bytes) or not response.body:
                raise DocumentError("empty_or_invalid_body")
            if len(response.body) > max_bytes:
                raise DocumentError("response_too_large")
            length = headers.get("content-length")
            if length is not None:
                if not re.fullmatch(r"[0-9]+", length):
                    raise DocumentError("invalid_content_length")
                if int(length) != len(response.body):
                    raise DocumentError("content_length_mismatch")
            if time.monotonic() - started > timeout:
                raise DocumentError("request_timeout")
            raw = _artifact(root, response.body, "artifacts", ".bin")
            receipt["retrieved"] = True
            content_type = headers.get("content-type", "")
            receipt["document"] = {"url": current, "content_type": content_type,
                "raw": raw, "text": None, "extraction_status": "blocked_extraction_error",
                "links": [], "link_details": [], "links_fetched": False}
            text, links, status, kind, link_details = _extract(response.body, content_type, current)
            extracted = _artifact(root, text.encode("utf-8"), "artifacts", ".txt") if text else None
            receipt["document"] = {"url": current, "content_type": content_type, "format": kind,
                "raw": raw, "text": extracted, "extraction_status": status,
                "links": links, "link_details": link_details, "links_fetched": False}
            receipt["ok"] = status == "extracted"
            if not receipt["ok"]:
                receipt["errors"].append({"error_type": "ExtractionBlocked", "code": status})
            break
    except Exception as exc:
        receipt["errors"].append({"error_type": type(exc).__name__, "code": str(exc) if isinstance(exc, DocumentError) else "collection_failed"})
    manifest = _artifact(root, canonical(receipt).encode("utf-8"), "receipts", ".json")
    return {**receipt, "receipt_path": manifest["path"]}


def verify_bundle(bundle_dir):
    """Verify receipt names, artifact hashes and path confinement; no network."""
    root = Path(bundle_dir).resolve()
    errors, artifacts, count = [], set(), 0
    for path in sorted((root / "receipts").glob("*.json")):
        count += 1
        try:
            if not path.resolve().is_relative_to(root):
                raise DocumentError("receipt_outside_bundle")
            data = path.read_bytes()
            if path.stem != hashlib.sha256(data).hexdigest():
                raise DocumentError("receipt_checksum_mismatch")
            receipt = json.loads(data)
            if receipt.get("schema_version") != 1 or type(receipt.get("ok")) is not bool:
                raise DocumentError("invalid_receipt")
            document = receipt.get("document")
            if receipt["ok"] and (not document or document.get("extraction_status") != "extracted" or not document.get("raw") or not document.get("text")):
                raise DocumentError("invalid_success_receipt")
            for artifact in (document.get("raw"), document.get("text")) if document else ():
                if not artifact:
                    continue
                relative = artifact["path"]
                if not re.fullmatch(r"artifacts/[a-f0-9]{64}\.(bin|txt)", relative):
                    raise DocumentError("invalid_artifact_path")
                target = (root / relative).resolve()
                if not target.is_relative_to(root):
                    raise DocumentError("artifact_outside_bundle")
                raw = target.read_bytes()
                checksum = hashlib.sha256(raw).hexdigest()
                if checksum != artifact["sha256"] or target.stem != checksum or len(raw) != artifact["bytes"]:
                    raise DocumentError("artifact_checksum_mismatch")
                artifacts.add(relative)
        except Exception as exc:
            errors.append({"receipt": path.name, "code": str(exc) if isinstance(exc, DocumentError) else "invalid_or_missing_evidence"})
    if not count:
        errors.append({"code": "no_receipts"})
    return {"ok": not errors, "receipts": count, "artifacts": len(artifacts), "errors": errors}
