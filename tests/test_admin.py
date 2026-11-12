"""Tests for Zensical Admin NavManager and HTTP API."""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace

from admin_app.nav_manager import NavError, NavManager, slugify_vi
from admin_app.server import AdminRequestHandler, create_server

SAMPLE_TOML = """\
# Header comment must survive
[project]
site_name = "Test Docs"
docs_dir = "docs"
site_dir = "site"

nav = [
  { "Trang chủ" = "index.md" },
  { "Java Core" = [
    { "Tổng quan" = "core/index.md" },
  ] },
]

[project.theme]
variant = "modern"
"""


class NavManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="zensical-admin-test-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        (self.tmp / "zensical.toml").write_text(SAMPLE_TOML, encoding="utf-8")
        (self.tmp / "docs" / "core").mkdir(parents=True)
        (self.tmp / "docs" / "index.md").write_text("# Trang chủ\n\nNội dung.\n", encoding="utf-8")
        (self.tmp / "docs" / "core" / "index.md").write_text("# Tổng quan\n", encoding="utf-8")
        self.manager = NavManager(self.tmp)

    def test_slugify_vi(self) -> None:
        self.assertEqual(slugify_vi("Đa luồng & Đồng bộ"), "da-luong-dong-bo")
        self.assertEqual(slugify_vi("   "), "bai-viet")

    def test_add_edit_delete_section_preserves_comments(self) -> None:
        self.manager.add_section("Design Patterns")
        tree = self.manager.get_tree()["tree"]
        self.assertEqual(tree[-1]["title"], "Design Patterns")
        self.assertEqual(tree[-1]["type"], "section")

        self.manager.update_section([2], "Mẫu thiết kế")
        tree = self.manager.get_tree()["tree"]
        self.assertEqual(tree[-1]["title"], "Mẫu thiết kế")

        toml_text = (self.tmp / "zensical.toml").read_text(encoding="utf-8")
        self.assertIn("# Header comment must survive", toml_text)
        self.assertIn('[project.theme]\nvariant = "modern"', toml_text)

        self.manager.delete_section([2])
        tree = self.manager.get_tree()["tree"]
        self.assertEqual(len(tree), 2)

    def test_add_page_creates_empty_file_with_title_only_and_builds_strict(self) -> None:
        self.manager.add_page("Generics cơ bản", "core/generics-co-ban.md", parent_path=[1])
        created = self.tmp / "docs" / "core" / "generics-co-ban.md"
        self.assertTrue(created.is_file())
        self.assertEqual(created.read_text(encoding="utf-8"), "# Generics cơ bản\n")

        tree = self.manager.get_tree()["tree"]
        added = tree[1]["children"][-1]
        self.assertEqual(added["title"], "Generics cơ bản")
        self.assertEqual(added["path"], "core/generics-co-ban.md")
        self.assertTrue(added["is_stub"])

        build_res = self.manager.run_build_check()
        self.assertTrue(build_res["ok"], build_res["output"])

    def test_update_page_rename_move_and_sync_h1(self) -> None:
        self.manager.add_page("Bài nháp", "core/nhap.md", parent_path=[1])
        self.manager.update_page(
            index_path=[1, 1],
            new_title="Bài chính thức",
            new_rel_path="patterns/chinh-thuc.md",
            sync_heading=True,
            target_parent_path=[],
        )
        old_file = self.tmp / "docs" / "core" / "nhap.md"
        new_file = self.tmp / "docs" / "patterns" / "chinh-thuc.md"
        self.assertFalse(old_file.exists())
        self.assertTrue(new_file.is_file())
        self.assertEqual(new_file.read_text(encoding="utf-8"), "# Bài chính thức\n")

        tree = self.manager.get_tree()["tree"]
        self.assertEqual(tree[-1]["title"], "Bài chính thức")
        self.assertEqual(tree[-1]["path"], "patterns/chinh-thuc.md")

    def test_delete_page_and_cleanup_empty_dirs(self) -> None:
        self.manager.add_page("Tạm", "extra/sub/tam.md")
        target = self.tmp / "docs" / "extra" / "sub" / "tam.md"
        self.assertTrue(target.is_file())

        self.manager.delete_page([2], delete_file=True)
        self.assertFalse(target.exists())
        self.assertFalse((self.tmp / "docs" / "extra").exists())

    def test_rejects_path_traversal_and_protects_index(self) -> None:
        with self.assertRaises(NavError):
            self.manager.add_page("Hack", "../secret.md")
        with self.assertRaises(NavError):
            self.manager.delete_page([0], delete_file=True)

    def test_move_item_and_valid_toml(self) -> None:
        self.manager.add_section("Mục mới")
        self.manager.move_item([2], "up")
        parsed = tomllib.loads((self.tmp / "zensical.toml").read_text(encoding="utf-8"))
        titles = [next(iter(item.keys())) for item in parsed["project"]["nav"]]
        self.assertEqual(titles, ["Trang chủ", "Mục mới", "Java Core"])


class _FakeSocket:
    def __init__(self, raw_request: bytes) -> None:
        self._in = io.BytesIO(raw_request)
        self._out = io.BytesIO()

    def makefile(self, mode: str, *args: object, **kwargs: object) -> io.BytesIO:
        return self._in if "r" in mode else self._out

    def sendall(self, data: bytes) -> None:
        self._out.write(data)

    def raw_response(self) -> bytes:
        return self._out.getvalue()


class AdminHttpApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="zensical-admin-http-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        (self.tmp / "zensical.toml").write_text(SAMPLE_TOML, encoding="utf-8")
        (self.tmp / "docs" / "core").mkdir(parents=True)
        (self.tmp / "docs" / "index.md").write_text("# Trang chủ\n", encoding="utf-8")
        (self.tmp / "docs" / "core" / "index.md").write_text("# Tổng quan\n", encoding="utf-8")
        self.server = create_server(self.tmp, host="127.0.0.1", port=0)
        self.addCleanup(self.server.server_close)

    def _req(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        payload = json.dumps(body).encode("utf-8") if body is not None else b""
        raw = (
            f"{method} {path} HTTP/1.1\r\n"
            f"Host: 127.0.0.1\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(payload)}\r\n"
            f"\r\n"
        ).encode("utf-8") + payload
        sock = _FakeSocket(raw)
        handler = AdminRequestHandler(sock, ("127.0.0.1", 12345), self.server)
        _ = handler
        resp_bytes = sock.raw_response()
        header_part, body_part = resp_bytes.split(b"\r\n\r\n", 1)
        status_line = header_part.splitlines()[0].decode("utf-8")
        status_code = int(status_line.split()[1])
        return status_code, json.loads(body_part.decode("utf-8"))

    def test_http_html_and_crud_flow(self) -> None:
        raw_get = b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n"
        sock = _FakeSocket(raw_get)
        AdminRequestHandler(sock, ("127.0.0.1", 12345), self.server)
        self.assertIn(b"200 OK", sock.raw_response())
        self.assertIn(b"<!DOCTYPE html>", sock.raw_response())

        status, res = self._req("GET", "/api/tree")
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])

        status, res = self._req("POST", "/api/sections", {"title": "Collections"})
        self.assertEqual(status, 200)
        self.assertEqual(res["data"]["tree"][-1]["title"], "Collections")

        status, res = self._req(
            "POST",
            "/api/pages",
            {"title": "HashMap nội bộ", "path": "collections/hashmap.md", "parent_path": [2]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            (self.tmp / "docs" / "collections" / "hashmap.md").read_text(encoding="utf-8"),
            "# HashMap nội bộ\n",
        )

        status, res = self._req(
            "PUT",
            "/api/pages",
            {"index_path": [2, 0], "title": "HashMap & Equals"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(
            (self.tmp / "docs" / "collections" / "hashmap.md").read_text(encoding="utf-8"),
            "# HashMap & Equals\n",
        )

        status, res = self._req(
            "DELETE",
            "/api/pages",
            {"index_path": [2, 0], "delete_file": True},
        )
        self.assertEqual(status, 200)
        self.assertFalse((self.tmp / "docs" / "collections" / "hashmap.md").exists())


if __name__ == "__main__":
    unittest.main()
