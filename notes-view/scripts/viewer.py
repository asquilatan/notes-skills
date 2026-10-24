#!/usr/bin/env python3
"""Serve a directory of Markdown notes as a mobile-friendly web reader.

Usage:
    python viewer.py --directory ./notes
    python viewer.py --directory ./notes --port 8080

The server binds to 0.0.0.0 by default so other devices on the same
network can open the printed URL. It uses only the Python standard library.
Page assets live in ../static/ (index.html, styles.css, app.js) and are
read per request, so edits appear on a browser refresh without a restart.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import socket
import sys
import tempfile
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

MARKDOWN_SUFFIXES = {".md", ".markdown"}
IGNORED_DIRS = {"node_modules", "__pycache__", "venv"}

DEFAULT_WRITABLE = "questions.md"
MAX_ANSWER_CHARS = 200
MAX_REQUEST_BYTES = 8192

TASK_CHECKBOX_RE = re.compile(r"^ {0,3}[-*+][ \t]+\[([ xX])\](?=[ \t]|$)")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)*?\1", re.DOTALL)
BLANK_RE = re.compile(r"(?<!_)_{3}(?!_)")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATIC_ROUTES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/static/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


def natural_key(value: str) -> list:
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", value)]


def scan_tree(directory: Path, root: Path) -> list[dict]:
    directories: list[dict] = []
    files: list[dict] = []
    try:
        entries = sorted(directory.iterdir(), key=lambda entry: natural_key(entry.name))
    except OSError:
        return []

    for entry in entries:
        if entry.name.startswith(".") or entry.name in IGNORED_DIRS:
            continue
        try:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                children = scan_tree(entry, root)
                if children:
                    directories.append({
                        "type": "dir",
                        "name": entry.name,
                        "path": entry.relative_to(root).as_posix(),
                        "children": children,
                    })
            elif entry.is_file() and entry.suffix.lower() in MARKDOWN_SUFFIXES:
                files.append({
                    "type": "file",
                    "name": entry.name,
                    "path": entry.relative_to(root).as_posix(),
                })
        except OSError:
            continue

    return directories + files


def resolve_within(root: Path, raw: str) -> Path | None:
    raw = unquote(raw).replace("\\", "/")
    if "\x00" in raw:
        return None
    parts = [part for part in raw.split("/") if part not in ("", ".")]
    if not parts or any(part == ".." or part.startswith(".") for part in parts):
        return None
    target = root.joinpath(*parts).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


def fence_mask(lines: list[str]) -> list[bool]:
    """Mark lines that belong to a fenced code block so their contents are ignored."""
    mask: list[bool] = []
    fence: tuple[str, int] | None = None
    for line in lines:
        body = line.rstrip("\r\n")
        if fence is None:
            match = FENCE_RE.match(body)
            if match:
                fence = (match.group(1)[0], len(match.group(1)))
                mask.append(True)
            else:
                mask.append(False)
            continue
        mask.append(True)
        stripped = body.strip()
        if stripped and set(stripped) == {fence[0]} and len(stripped) >= fence[1]:
            fence = None
    return mask


def inline_code_spans(line: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in INLINE_CODE_RE.finditer(line)]


def task_checkbox_lines(lines: list[str], mask: list[bool]) -> list[int]:
    return [
        index for index, line in enumerate(lines)
        if not mask[index] and TASK_CHECKBOX_RE.match(line.rstrip("\r\n"))
    ]


def blank_slots(lines: list[str], mask: list[bool]) -> list[tuple[int, int, int]]:
    slots: list[tuple[int, int, int]] = []
    for index, line in enumerate(lines):
        if mask[index]:
            continue
        spans = inline_code_spans(line)
        for match in BLANK_RE.finditer(line):
            if any(start <= match.start() < end for start, end in spans):
                continue
            slots.append((index, match.start(), match.end()))
    return slots


def toggle_checkbox(text: str, index: int, checked: bool) -> tuple[str, bool] | None:
    lines = text.splitlines(keepends=True)
    targets = task_checkbox_lines(lines, fence_mask(lines))
    if not 0 <= index < len(targets):
        return None
    line_index = targets[index]
    match = TASK_CHECKBOX_RE.match(lines[line_index].rstrip("\r\n"))
    if match is None:
        return None
    desired = "x" if checked else " "
    if match.group(1).casefold() == desired:
        return text, False
    start, end = match.span(1)
    line = lines[line_index]
    lines[line_index] = line[:start] + desired + line[end:]
    return "".join(lines), True


def fill_blank(text: str, index: int, value: str) -> tuple[str, bool] | None:
    lines = text.splitlines(keepends=True)
    slots = blank_slots(lines, fence_mask(lines))
    if not 0 <= index < len(slots):
        return None
    line_index, start, end = slots[index]
    line = lines[line_index]
    lines[line_index] = line[:start] + value + line[end:]
    return "".join(lines), True


def validate_answer(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    answer = value.strip()
    if not answer or len(answer) > MAX_ANSWER_CHARS:
        return None
    if "\n" in answer or "\r" in answer or "___" in answer:
        return None
    if any(ord(character) < 32 for character in answer):
        return None
    return answer


def fingerprint(payload: bytes) -> str:
    """FNV-1a of the raw file, matching the browser so stale pages can be rejected."""
    value = 2166136261
    for byte in payload:
        value = ((value ^ byte) * 16777619) & 0xFFFFFFFF
    return f"{value:08x}"


def write_atomic(target: Path, payload: bytes, expected: bytes) -> bool:
    """Replace the file only if it still holds the bytes this edit was based on."""
    try:
        if target.read_bytes() != expected:
            return False
    except OSError:
        return False
    handle, temp_name = tempfile.mkstemp(dir=target.parent, prefix=".notes-view-", suffix=".tmp")
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
        os.replace(temp_name, target)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return True


class NotesRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    root: Path = Path(".").resolve()
    verbose: bool = False
    writable: frozenset[str] = frozenset({DEFAULT_WRITABLE})

    def log_message(self, fmt: str, *args) -> None:
        if self.verbose:
            super().log_message(fmt, *args)

    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _send_text(self, status: HTTPStatus, message: str) -> None:
        self._send(status, message.encode("utf-8"), "text/plain; charset=utf-8")

    def _send_static(self, route: str) -> None:
        name, content_type = STATIC_ROUTES[route]
        try:
            body = (STATIC_DIR / name).read_bytes()
        except OSError as exc:
            self._send_text(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not read {name}: {exc}")
            return
        self._send(HTTPStatus.OK, body, content_type)

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        route = parsed.path

        if route in STATIC_ROUTES:
            self._send_static(route)
            return

        if route == "/api/tree":
            self._send_json(HTTPStatus.OK, {
                "root": self.root.name or str(self.root),
                "tree": scan_tree(self.root, self.root),
                "writable": sorted(self.writable),
            })
            return

        if route == "/api/file":
            requested = parse_qs(parsed.query).get("path", [""])[0]
            target = resolve_within(self.root, requested)
            if target is None or not target.is_file() or target.suffix.lower() not in MARKDOWN_SUFFIXES:
                self._send_text(HTTPStatus.NOT_FOUND, "Markdown file not found.")
                return
            try:
                text = target.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                self._send_text(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "File is not valid UTF-8.")
                return
            except OSError as exc:
                self._send_text(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not read file: {exc}")
                return
            self._send(HTTPStatus.OK, text.encode("utf-8"), "text/markdown; charset=utf-8")
            return

        if route.startswith("/files/"):
            target = resolve_within(self.root, route[len("/files/"):])
            if target is None or not target.is_file():
                self._send_text(HTTPStatus.NOT_FOUND, "File not found.")
                return
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if content_type.startswith("text/"):
                content_type += "; charset=utf-8"
            try:
                payload = target.read_bytes()
            except OSError as exc:
                self._send_text(HTTPStatus.INTERNAL_SERVER_ERROR, f"Could not read file: {exc}")
                return
            self._send(HTTPStatus.OK, payload, content_type)
            return

        if route == "/favicon.ico":
            self._send(HTTPStatus.NO_CONTENT, b"", "image/x-icon")
            return

        self._send_text(HTTPStatus.NOT_FOUND, "Not found.")

    def _same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        host = self.headers.get("Host")
        try:
            return bool(host) and urlsplit(origin).netloc == host
        except ValueError:
            return False

    def _is_json_request(self) -> bool:
        return self.headers.get("Content-Type", "").split(";")[0].strip().lower() == "application/json"

    def _read_body(self) -> bytes | None:
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.close_connection = True
            return None
        if not 0 < length <= MAX_REQUEST_BYTES:
            self.close_connection = True
            return None
        return self.rfile.read(length)

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/answer":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found."})
            return
        if not self._same_origin():
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "Cross-origin answer rejected."})
            return

        body = self._read_body()
        if body is None:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Expected a small JSON answer body."})
            return
        if not self._is_json_request():
            self._send_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "Expected application/json."})
            return
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Malformed JSON answer body."})
            return
        if not isinstance(payload, dict):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Expected a JSON object."})
            return

        requested = payload.get("path")
        kind = payload.get("kind")
        index = payload.get("index")
        if not isinstance(requested, str) or not isinstance(index, int) or isinstance(index, bool):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Missing answer path, kind, or index."})
            return
        if index < 0:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Index must be zero or positive."})
            return

        target = resolve_within(self.root, requested)
        if target is None or not target.is_file() or target.suffix.lower() not in MARKDOWN_SUFFIXES:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Markdown file not found."})
            return
        if target.name.casefold() not in self.writable:
            self._send_json(HTTPStatus.FORBIDDEN, {"error": "This file is not open for answers."})
            return

        if kind == "checkbox":
            checked = payload.get("checked")
            if not isinstance(checked, bool):
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "A checkbox answer needs true or false."})
                return
            value = None
        elif kind == "blank":
            value = validate_answer(payload.get("value"))
            if value is None:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": f"Blank answers need 1-{MAX_ANSWER_CHARS} characters on one line, without ___."},
                )
                return
        else:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Unknown answer kind."})
            return

        with self.server.write_lock:
            try:
                raw = target.read_bytes()
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                self._send_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "File is not valid UTF-8."})
                return
            except OSError as exc:
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": f"Could not read file: {exc}"})
                return

            source = payload.get("source")
            if source is not None and source != fingerprint(raw):
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {"error": "The file changed since this page loaded. Reload and try again."},
                )
                return

            if kind == "checkbox":
                result = toggle_checkbox(text, index, checked)
            else:
                result = fill_blank(text, index, value)
            if result is None:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {"error": "That answer is no longer in the file. Reload the page and try again."},
                )
                return

            updated, changed = result
            saved = updated.encode("utf-8")
            if changed and not write_atomic(target, saved, raw):
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {"error": "The file changed while saving. Reload the page and try again."},
                )
                return
            if not changed:
                saved = raw

        self._send_json(HTTPStatus.OK, {"ok": True, "changed": changed, "source": fingerprint(saved)})


class NotesServer(ThreadingHTTPServer):
    write_lock = threading.Lock()

    def handle_error(self, request, client_address) -> None:
        error = sys.exc_info()[1]
        if isinstance(error, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


def lan_address() -> str | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Serve a Markdown notes directory to devices on your local network."
    )
    parser.add_argument(
        "--directory", "-d", default="notes",
        help="Directory containing the notes (default: ./notes)",
    )
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument("--host", default="0.0.0.0", help="Address to bind (default: 0.0.0.0)")
    parser.add_argument(
        "--writable", nargs="+", default=[], metavar="FILENAME",
        help=f"Extra files whose task checkboxes and ___ blanks may be answered "
             f"({DEFAULT_WRITABLE} is always writable)",
    )
    parser.add_argument("--verbose", action="store_true", help="Log every HTTP request")
    args = parser.parse_args()

    if not 0 <= args.port <= 65535:
        print("error: --port must be between 0 and 65535", file=sys.stderr)
        return 2

    writable = {DEFAULT_WRITABLE}
    for name in args.writable:
        if Path(name).name != name or not name:
            print(f"error: --writable takes plain filenames, not paths: {name}", file=sys.stderr)
            return 2
        writable.add(name.casefold())

    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        print(f"error: directory not found: {root}", file=sys.stderr)
        return 2

    for name in sorted({name for name, _ in STATIC_ROUTES.values()}):
        if not (STATIC_DIR / name).is_file():
            print(f"error: static asset missing: {STATIC_DIR / name}", file=sys.stderr)
            return 2

    handler = type(
        "BoundNotesHandler",
        (NotesRequestHandler,),
        {"root": root, "verbose": args.verbose, "writable": frozenset(writable)},
    )
    try:
        server = NotesServer((args.host, args.port), handler)
    except OSError as exc:
        print(f"error: could not start the server on {args.host}:{args.port} ({exc})", file=sys.stderr)
        print("Try a different port, for example: --port 8081", file=sys.stderr)
        return 1

    port = server.server_address[1]

    print()
    print("  Notes viewer")
    print(f"  Serving   {root}")
    print(f"  Answers   {', '.join(sorted(writable))}")
    print(f"  Local     http://localhost:{port}")
    if args.host in ("0.0.0.0", ""):
        ip = lan_address()
        if ip:
            print(f"  Network   http://{ip}:{port}")
        else:
            print("  Network   use your computer's LAN IP")
    else:
        print(f"  Network   http://{args.host}:{port}")
    print()
    print("  Open the Network URL on your phone (same Wi-Fi). Press Ctrl+C to stop.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
