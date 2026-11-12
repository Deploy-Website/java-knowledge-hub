"""HTTP server and JSON API for the Zensical Admin UI."""

from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from admin_app.nav_manager import NavError, NavManager

STATIC_DIR = Path(__file__).resolve().parent / "static"


class AdminHTTPServer(ThreadingHTTPServer):
    """Threading HTTP server holding shared NavManager and lock."""

    def __init__(
        self,
        server_address: tuple[str, int],
        manager: NavManager,
        docs_url: str = "http://localhost:8000",
    ) -> None:
        self.manager = manager
        self.lock = threading.Lock()
        self.docs_url = docs_url
        super().__init__(server_address, AdminRequestHandler)


class AdminRequestHandler(BaseHTTPRequestHandler):
    """Handle admin UI static page and REST-like JSON API endpoints."""

    server: AdminHTTPServer

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_bytes: bytes) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html_bytes)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(html_bytes)

    def _read_json_body(self) -> dict[str, Any]:
        length_str = self.headers.get("Content-Length", "0")
        try:
            length = int(length_str)
        except ValueError as exc:
            raise NavError("Header Content-Length không hợp lệ.") from exc
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise NavError("Dữ liệu JSON gửi lên không hợp lệ.") from exc
        if not isinstance(data, dict):
            raise NavError("Payload JSON phải là object.")
        return data

    def _run_api(self, fn: Any) -> None:
        try:
            with self.server.lock:
                result = fn()
            self._send_json(HTTPStatus.OK, {"ok": True, "data": result})
        except NavError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
        except Exception as exc:  # pragma: no cover - defensive fallback
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "error": f"Lỗi hệ thống: {exc}"},
            )

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            index_file = STATIC_DIR / "index.html"
            self._send_html(index_file.read_bytes())
            return

        if parsed.path == "/api/tree":
            def _action() -> dict[str, Any]:
                tree = self.server.manager.get_tree()
                tree["docs_url"] = self.server.docs_url
                return tree

            self._run_api(_action)
            return

        if parsed.path == "/api/page-preview":
            qs = parse_qs(parsed.query)
            rel_path = qs.get("path", [""])[0]
            self._run_api(lambda: self.server.manager.read_page_content(rel_path))
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Không tìm thấy đường dẫn."})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/sections":
            def _action() -> dict[str, Any]:
                body = self._read_json_body()
                return self.server.manager.add_section(
                    title=str(body.get("title", "")),
                    parent_path=body.get("parent_path"),
                    position=body.get("position"),
                )

            self._run_api(_action)
            return

        if parsed.path == "/api/pages":
            def _action() -> dict[str, Any]:
                body = self._read_json_body()
                return self.server.manager.add_page(
                    title=str(body.get("title", "")),
                    rel_path=str(body.get("path", "")),
                    parent_path=body.get("parent_path"),
                    position=body.get("position"),
                    link_existing=bool(body.get("link_existing", False)),
                )

            self._run_api(_action)
            return

        if parsed.path == "/api/move":
            def _action() -> dict[str, Any]:
                body = self._read_json_body()
                return self.server.manager.move_item(
                    index_path=body.get("index_path", []),
                    direction=str(body.get("direction", "")),
                )

            self._run_api(_action)
            return

        if parsed.path == "/api/build":
            self._run_api(self.server.manager.run_build_check)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Không tìm thấy endpoint."})

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/sections":
            def _action() -> dict[str, Any]:
                body = self._read_json_body()
                return self.server.manager.update_section(
                    index_path=body.get("index_path", []),
                    new_title=str(body.get("title", "")),
                )

            self._run_api(_action)
            return

        if parsed.path == "/api/pages":
            def _action() -> dict[str, Any]:
                body = self._read_json_body()
                return self.server.manager.update_page(
                    index_path=body.get("index_path", []),
                    new_title=str(body.get("title", "")),
                    new_rel_path=body.get("path"),
                    sync_heading=bool(body.get("sync_heading", True)),
                    target_parent_path=body.get("target_parent_path"),
                )

            self._run_api(_action)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Không tìm thấy endpoint."})

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/sections":
            def _action() -> dict[str, Any]:
                body = self._read_json_body()
                return self.server.manager.delete_section(
                    index_path=body.get("index_path", []),
                    delete_files=bool(body.get("delete_files", False)),
                )

            self._run_api(_action)
            return

        if parsed.path == "/api/pages":
            def _action() -> dict[str, Any]:
                body = self._read_json_body()
                return self.server.manager.delete_page(
                    index_path=body.get("index_path", []),
                    delete_file=bool(body.get("delete_file", False)),
                )

            self._run_api(_action)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Không tìm thấy endpoint."})


def create_server(
    root_dir: Path,
    host: str = "127.0.0.1",
    port: int = 8001,
    docs_url: str = "http://localhost:8000",
) -> AdminHTTPServer:
    """Create a configured AdminHTTPServer for the given repository root."""
    manager = NavManager(root_dir)
    return AdminHTTPServer((host, port), manager, docs_url=docs_url)
