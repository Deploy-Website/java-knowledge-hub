"""Manage Zensical navigation in zensical.toml and Markdown article files in docs/."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tomllib
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class NavError(ValueError):
    """Raised when a navigation or file operation is invalid."""


def slugify_vi(text: str) -> str:
    """Convert Vietnamese or ASCII text into a clean URL/file slug."""
    replaced = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFKD", replaced)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "bai-viet"


def format_toml_string(value: str) -> str:
    """Format a Python string as a valid TOML basic string."""
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\b", "\\b")
        .replace("\f", "\\f")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def serialize_nav(nav: list[dict[str, Any]], indent: int = 0) -> str:
    """Serialize a Zensical nav list into cleanly formatted TOML."""
    pad = "  " * indent
    inner_pad = "  " * (indent + 1)
    lines = ["["]
    for entry in nav:
        if not isinstance(entry, dict) or len(entry) != 1:
            raise NavError(f"Mục điều hướng không hợp lệ: {entry!r}")
        title, target = next(iter(entry.items()))
        key_str = format_toml_string(str(title))
        if isinstance(target, str):
            val_str = format_toml_string(target)
            lines.append(f"{inner_pad}{{ {key_str} = {val_str} }},")
        elif isinstance(target, list):
            nested = serialize_nav(target, indent + 1)
            lines.append(f"{inner_pad}{{ {key_str} = {nested} }},")
        else:
            raise NavError(f"Giá trị nav không hợp lệ cho '{title}': {target!r}")
    lines.append(f"{pad}]")
    return "\n".join(lines)


def _find_nav_value_span(toml_text: str) -> tuple[int, int]:
    """Locate the `[...]` byte/char span of `nav = [...]` inside zensical.toml."""
    i = 0
    n = len(toml_text)
    in_project = True  # root keys before any [table] also count, though [project] is expected

    while i < n:
        ch = toml_text[i]
        # Skip whitespace
        if ch in " \t\r\n":
            i += 1
            continue
        # Skip comments
        if ch == "#":
            nl = toml_text.find("\n", i)
            i = n if nl == -1 else nl + 1
            continue
        # Check table header [section]
        if ch == "[":
            nl = toml_text.find("\n", i)
            line_end = n if nl == -1 else nl
            header = toml_text[i:line_end].split("#", 1)[0].strip()
            in_project = header == "[project]"
            i = line_end + 1
            continue
        # Check key = value at line start
        if in_project and toml_text.startswith("nav", i):
            after_nav = i + 3
            if after_nav < n and (toml_text[after_nav] in " \t="):
                j = after_nav
                while j < n and toml_text[j] in " \t":
                    j += 1
                if j < n and toml_text[j] == "=":
                    j += 1
                    while j < n and toml_text[j] in " \t\r\n":
                        j += 1
                    if j < n and toml_text[j] == "[":
                        end_idx = _find_matching_bracket(toml_text, j)
                        return j, end_idx + 1
        # Advance to next line
        nl = toml_text.find("\n", i)
        i = n if nl == -1 else nl + 1

    raise NavError("Không tìm thấy cấu hình `nav = [...]` trong zensical.toml")


def _find_matching_bracket(text: str, start_idx: int) -> int:
    """Find the matching closing `]` for the `[` at start_idx, ignoring strings & comments."""
    depth = 0
    i = start_idx
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "#":
            nl = text.find("\n", i)
            i = n if nl == -1 else nl + 1
            continue
        if ch in ('"', "'"):
            if text.startswith(ch * 3, i):
                quote = ch * 3
                i += 3
                while i < n:
                    if ch == '"' and text[i] == "\\":
                        i += 2
                        continue
                    if text.startswith(quote, i):
                        i += 3
                        break
                    i += 1
            else:
                quote = ch
                i += 1
                while i < n:
                    if quote == '"' and text[i] == "\\":
                        i += 2
                        continue
                    if text[i] == quote:
                        i += 1
                        break
                    i += 1
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise NavError("Cấu trúc `nav = [...]` trong zensical.toml bị thiếu dấu đóng `]`.")


@dataclass
class PageStatus:
    """Metadata about a Markdown file on disk."""

    exists: bool
    is_stub: bool
    size_bytes: int
    line_count: int
    h1_title: str | None


class NavManager:
    """Read, validate, and mutate Zensical navigation and Markdown stub files."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir.resolve()
        self.config_path = self.root_dir / "zensical.toml"

    def _load_config(self) -> tuple[str, dict[str, Any]]:
        if not self.config_path.is_file():
            raise NavError(f"Không tìm thấy {self.config_path}")
        raw_text = self.config_path.read_text(encoding="utf-8")
        try:
            data = tomllib.loads(raw_text)
        except tomllib.TOMLDecodeError as exc:
            raise NavError(f"Lỗi cú pháp zensical.toml: {exc}") from exc
        return raw_text, data

    def _get_docs_dir(self, data: dict[str, Any]) -> Path:
        project = data.get("project", {})
        docs_rel = project.get("docs_dir", "docs")
        docs_dir = (self.root_dir / docs_rel).resolve()
        if not docs_dir.exists():
            docs_dir.mkdir(parents=True, exist_ok=True)
        return docs_dir

    def _get_nav_raw(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        project = data.get("project", {})
        nav = project.get("nav")
        if not isinstance(nav, list):
            raise NavError("`project.nav` trong zensical.toml phải là một danh sách.")
        return nav

    def _save_nav(self, raw_text: str, nav: list[dict[str, Any]]) -> None:
        start, end = _find_nav_value_span(raw_text)
        serialized = serialize_nav(nav, indent=0)
        updated_text = raw_text[:start] + serialized + raw_text[end:]
        try:
            tomllib.loads(updated_text)
        except tomllib.TOMLDecodeError as exc:
            raise NavError(f"Lỗi tạo TOML hợp lệ: {exc}") from exc
        self.config_path.write_text(updated_text, encoding="utf-8")

    def normalize_rel_path(self, rel_path: str) -> str:
        """Validate and normalize a Markdown path relative to docs/."""
        cleaned = rel_path.strip().replace("\\", "/").lstrip("/")
        if not cleaned:
            raise NavError("Đường dẫn file không được để trống.")
        if not cleaned.endswith(".md"):
            cleaned = f"{cleaned}.md"
        parts = [p for p in cleaned.split("/") if p]
        if any(p in (".", "..") for p in parts):
            raise NavError("Đường dẫn file không hợp lệ (không được chứa '..' hoặc '.').")
        normalized = "/".join(parts)
        return normalized

    def resolve_doc_path(self, docs_dir: Path, rel_path: str) -> Path:
        """Resolve a relative doc path and ensure it stays inside docs_dir."""
        normalized = self.normalize_rel_path(rel_path)
        target = (docs_dir / normalized).resolve()
        try:
            target.relative_to(docs_dir)
        except ValueError as exc:
            raise NavError("Đường dẫn vượt ra ngoài thư mục docs/.") from exc
        return target

    def _inspect_file(self, docs_dir: Path, rel_path: str) -> PageStatus:
        try:
            target = self.resolve_doc_path(docs_dir, rel_path)
        except NavError:
            return PageStatus(False, False, 0, 0, None)
        if not target.is_file():
            return PageStatus(False, False, 0, 0, None)

        content = target.read_text(encoding="utf-8")
        size_bytes = target.stat().st_size
        lines = content.splitlines()
        h1_title = self._extract_h1(lines)
        body_lines = self._strip_frontmatter(lines)
        non_empty = [ln.strip() for ln in body_lines if ln.strip()]
        is_stub = len(non_empty) == 0 or (
            len(non_empty) == 1 and non_empty[0].startswith("# ")
        )
        return PageStatus(True, is_stub, size_bytes, len(lines), h1_title)

    @staticmethod
    def _strip_frontmatter(lines: list[str]) -> list[str]:
        if lines and lines[0].strip() == "---":
            for idx in range(1, len(lines)):
                if lines[idx].strip() == "---":
                    return lines[idx + 1 :]
        return lines

    @classmethod
    def _extract_h1(cls, lines: list[str]) -> str | None:
        for ln in cls._strip_frontmatter(lines):
            stripped = ln.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return None

    @classmethod
    def _replace_or_set_h1(cls, content: str, new_title: str) -> str:
        if not content.strip():
            return f"# {new_title}\n"
        lines = content.splitlines(keepends=True)
        start_idx = 0
        if lines and lines[0].strip() == "---":
            for idx in range(1, len(lines)):
                if lines[idx].strip() == "---":
                    start_idx = idx + 1
                    break
        for idx in range(start_idx, len(lines)):
            if lines[idx].lstrip().startswith("# "):
                newline = "\n" if lines[idx].endswith("\n") else ""
                lines[idx] = f"# {new_title}{newline}"
                return "".join(lines)
        prefix = "".join(lines[:start_idx])
        suffix = "".join(lines[start_idx:]).lstrip("\r\n")
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        if suffix:
            return f"{prefix}# {new_title}\n\n{suffix}"
        return f"{prefix}# {new_title}\n"

    def _collect_linked_paths(self, nav: list[dict[str, Any]], out: set[str]) -> None:
        for entry in nav:
            _, target = next(iter(entry.items()))
            if isinstance(target, str):
                try:
                    out.add(self.normalize_rel_path(target))
                except NavError:
                    pass
            elif isinstance(target, list):
                self._collect_linked_paths(target, out)

    def _serialize_tree(
        self,
        nav: list[dict[str, Any]],
        docs_dir: Path,
        prefix: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        prefix = prefix or []
        result: list[dict[str, Any]] = []
        for idx, entry in enumerate(nav):
            title, target = next(iter(entry.items()))
            index_path = [*prefix, idx]
            if isinstance(target, str):
                status = self._inspect_file(docs_dir, target)
                result.append(
                    {
                        "type": "page",
                        "title": str(title),
                        "path": target,
                        "index_path": index_path,
                        "exists": status.exists,
                        "is_stub": status.is_stub,
                        "size_bytes": status.size_bytes,
                        "line_count": status.line_count,
                        "h1_title": status.h1_title,
                    }
                )
            elif isinstance(target, list):
                children = self._serialize_tree(target, docs_dir, index_path)
                result.append(
                    {
                        "type": "section",
                        "title": str(title),
                        "index_path": index_path,
                        "suggested_dir": self._infer_section_dir(str(title), target),
                        "children": children,
                    }
                )
        return result

    @staticmethod
    def _infer_section_dir(title: str, children: list[dict[str, Any]]) -> str:
        for child in children:
            _, target = next(iter(child.items()))
            if isinstance(target, str) and "/" in target:
                return target.rsplit("/", 1)[0]
        return slugify_vi(title)

    def get_tree(self) -> dict[str, Any]:
        """Return full navigation tree, stats, and unlinked Markdown files."""
        raw_text, data = self._load_config()
        _ = raw_text
        docs_dir = self._get_docs_dir(data)
        nav = self._get_nav_raw(data)
        tree = self._serialize_tree(nav, docs_dir)

        linked: set[str] = set()
        self._collect_linked_paths(nav, linked)

        unlinked_files: list[dict[str, Any]] = []
        for md_file in sorted(docs_dir.rglob("*.md")):
            rel = md_file.relative_to(docs_dir).as_posix()
            if rel not in linked:
                status = self._inspect_file(docs_dir, rel)
                unlinked_files.append(
                    {
                        "path": rel,
                        "is_stub": status.is_stub,
                        "size_bytes": status.size_bytes,
                        "line_count": status.line_count,
                        "h1_title": status.h1_title,
                    }
                )

        project = data.get("project", {})
        return {
            "site_name": project.get("site_name", "Documentation"),
            "docs_dir": str(docs_dir.relative_to(self.root_dir).as_posix()),
            "tree": tree,
            "unlinked_files": unlinked_files,
        }

    def _get_container_and_index(
        self, nav: list[dict[str, Any]], index_path: list[int]
    ) -> tuple[list[dict[str, Any]], int]:
        if not index_path:
            raise NavError("Thiếu vị trí mục (`index_path`).")
        current = nav
        for pos in index_path[:-1]:
            if pos < 0 or pos >= len(current):
                raise NavError("Vị trí mục không tồn tại (dữ liệu đã thay đổi, hãy tải lại).")
            _, target = next(iter(current[pos].items()))
            if not isinstance(target, list):
                raise NavError("Mục cha không phải là một nhóm mục.")
            current = target
        last = index_path[-1]
        if last < 0 or last >= len(current):
            raise NavError("Vị trí mục không tồn tại (dữ liệu đã thay đổi, hãy tải lại).")
        return current, last

    def _get_target_list(
        self, nav: list[dict[str, Any]], parent_path: list[int] | None
    ) -> list[dict[str, Any]]:
        if not parent_path:
            return nav
        container, idx = self._get_container_and_index(nav, parent_path)
        _, target = next(iter(container[idx].items()))
        if not isinstance(target, list):
            raise NavError("Mục đích không phải là một nhóm mục.")
        return target

    @staticmethod
    def _cleanup_empty_dirs(file_path: Path, docs_dir: Path) -> None:
        parent = file_path.parent
        while parent != docs_dir and parent.exists():
            try:
                next(parent.iterdir())
                break
            except StopIteration:
                parent.rmdir()
                parent = parent.parent

    def add_section(
        self,
        title: str,
        parent_path: list[int] | None = None,
        position: int | None = None,
    ) -> dict[str, Any]:
        """Add a new navigation section."""
        clean_title = title.strip()
        if not clean_title:
            raise NavError("Tên nhóm mục không được để trống.")
        raw_text, data = self._load_config()
        nav = self._get_nav_raw(data)
        target_list = self._get_target_list(nav, parent_path)
        new_entry: dict[str, Any] = {clean_title: []}
        if position is None or position < 0 or position > len(target_list):
            target_list.append(new_entry)
        else:
            target_list.insert(position, new_entry)
        self._save_nav(raw_text, nav)
        return self.get_tree()

    def update_section(self, index_path: list[int], new_title: str) -> dict[str, Any]:
        """Rename an existing navigation section."""
        clean_title = new_title.strip()
        if not clean_title:
            raise NavError("Tên nhóm mục không được để trống.")
        raw_text, data = self._load_config()
        nav = self._get_nav_raw(data)
        container, idx = self._get_container_and_index(nav, index_path)
        _, children = next(iter(container[idx].items()))
        if not isinstance(children, list):
            raise NavError("Mục được chọn không phải là nhóm mục.")
        container[idx] = {clean_title: children}
        self._save_nav(raw_text, nav)
        return self.get_tree()

    def delete_section(
        self, index_path: list[int], delete_files: bool = False
    ) -> dict[str, Any]:
        """Delete a navigation section and optionally delete its Markdown files."""
        raw_text, data = self._load_config()
        docs_dir = self._get_docs_dir(data)
        nav = self._get_nav_raw(data)
        container, idx = self._get_container_and_index(nav, index_path)
        _, children = next(iter(container[idx].items()))
        if not isinstance(children, list):
            raise NavError("Mục được chọn không phải là nhóm mục.")

        paths_to_check: list[str] = []
        self._collect_section_page_paths(children, paths_to_check)

        if delete_files and "index.md" in paths_to_check:
            raise NavError("Không cho phép xóa file trang chủ index.md.")

        container.pop(idx)
        self._save_nav(raw_text, nav)

        if delete_files:
            remaining: set[str] = set()
            self._collect_linked_paths(nav, remaining)
            for rel_path in paths_to_check:
                if rel_path in remaining:
                    continue
                target_file = self.resolve_doc_path(docs_dir, rel_path)
                if target_file.is_file():
                    target_file.unlink()
                    self._cleanup_empty_dirs(target_file, docs_dir)

        return self.get_tree()

    def _collect_section_page_paths(
        self, items: list[dict[str, Any]], out: list[str]
    ) -> None:
        for entry in items:
            _, target = next(iter(entry.items()))
            if isinstance(target, str):
                out.append(self.normalize_rel_path(target))
            elif isinstance(target, list):
                self._collect_section_page_paths(target, out)

    def add_page(
        self,
        title: str,
        rel_path: str,
        parent_path: list[int] | None = None,
        position: int | None = None,
        link_existing: bool = False,
    ) -> dict[str, Any]:
        """Add an article to nav and create an empty Markdown file with only the title."""
        clean_title = title.strip()
        if not clean_title:
            raise NavError("Tiêu đề bài viết không được để trống.")

        raw_text, data = self._load_config()
        docs_dir = self._get_docs_dir(data)
        nav = self._get_nav_raw(data)

        normalized = self.normalize_rel_path(rel_path)
        target_file = self.resolve_doc_path(docs_dir, normalized)

        linked: set[str] = set()
        self._collect_linked_paths(nav, linked)
        if normalized in linked:
            raise NavError(f"Đường dẫn '{normalized}' đã tồn tại trong menu điều hướng.")

        if link_existing:
            if not target_file.is_file():
                raise NavError(f"Không tìm thấy file có sẵn: docs/{normalized}")
        else:
            if target_file.exists():
                raise NavError(
                    f"File docs/{normalized} đã tồn tại trên ổ đĩa. "
                    "Hãy chọn đường dẫn khác hoặc bật tùy chọn liên kết file có sẵn."
                )

        target_list = self._get_target_list(nav, parent_path)
        new_entry = {clean_title: normalized}
        if position is None or position < 0 or position > len(target_list):
            target_list.append(new_entry)
        else:
            target_list.insert(position, new_entry)

        if not link_existing:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(f"# {clean_title}\n", encoding="utf-8")

        try:
            self._save_nav(raw_text, nav)
        except Exception:
            if not link_existing and target_file.exists():
                target_file.unlink()
                self._cleanup_empty_dirs(target_file, docs_dir)
            raise

        return self.get_tree()

    def update_page(
        self,
        index_path: list[int],
        new_title: str,
        new_rel_path: str | None = None,
        sync_heading: bool = True,
        target_parent_path: list[int] | None = None,
    ) -> dict[str, Any]:
        """Rename an article, optionally sync its H1 heading, move file path, or change section."""
        clean_title = new_title.strip()
        if not clean_title:
            raise NavError("Tiêu đề bài viết không được để trống.")

        raw_text, data = self._load_config()
        docs_dir = self._get_docs_dir(data)
        nav = self._get_nav_raw(data)

        container, idx = self._get_container_and_index(nav, index_path)
        _, old_target = next(iter(container[idx].items()))
        if not isinstance(old_target, str):
            raise NavError("Mục được chọn không phải là bài viết.")

        old_norm = self.normalize_rel_path(old_target)
        old_file = self.resolve_doc_path(docs_dir, old_norm)

        final_norm = (
            self.normalize_rel_path(new_rel_path)
            if new_rel_path is not None and new_rel_path.strip()
            else old_norm
        )

        if final_norm != old_norm:
            linked: set[str] = set()
            self._collect_linked_paths(nav, linked)
            if final_norm in linked:
                raise NavError(f"Đường dẫn '{final_norm}' đã được sử dụng bởi bài khác.")
            new_file = self.resolve_doc_path(docs_dir, final_norm)
            if new_file.exists():
                raise NavError(f"File đích docs/{final_norm} đã tồn tại.")
            if old_file.is_file():
                new_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_file), str(new_file))
                self._cleanup_empty_dirs(old_file, docs_dir)
            else:
                new_file.parent.mkdir(parents=True, exist_ok=True)
                new_file.write_text(f"# {clean_title}\n", encoding="utf-8")
            active_file = new_file
        else:
            active_file = old_file

        if sync_heading:
            if active_file.is_file():
                current_content = active_file.read_text(encoding="utf-8")
                updated_content = self._replace_or_set_h1(current_content, clean_title)
                if updated_content != current_content:
                    active_file.write_text(updated_content, encoding="utf-8")
            else:
                active_file.parent.mkdir(parents=True, exist_ok=True)
                active_file.write_text(f"# {clean_title}\n", encoding="utf-8")

        updated_entry = {clean_title: final_norm}
        current_parent_path = index_path[:-1]
        if target_parent_path is not None and target_parent_path != current_parent_path:
            dest_list = self._get_target_list(nav, target_parent_path)
            container.pop(idx)
            dest_list.append(updated_entry)
        else:
            container[idx] = updated_entry

        self._save_nav(raw_text, nav)
        return self.get_tree()

    def delete_page(
        self, index_path: list[int], delete_file: bool = False
    ) -> dict[str, Any]:
        """Remove an article from nav and optionally delete its Markdown file."""
        raw_text, data = self._load_config()
        docs_dir = self._get_docs_dir(data)
        nav = self._get_nav_raw(data)

        container, idx = self._get_container_and_index(nav, index_path)
        _, target = next(iter(container[idx].items()))
        if not isinstance(target, str):
            raise NavError("Mục được chọn không phải là bài viết.")

        norm_path = self.normalize_rel_path(target)
        if delete_file and norm_path == "index.md":
            raise NavError("Không cho phép xóa file trang chủ index.md.")

        container.pop(idx)
        self._save_nav(raw_text, nav)

        if delete_file:
            remaining: set[str] = set()
            self._collect_linked_paths(nav, remaining)
            if norm_path not in remaining:
                target_file = self.resolve_doc_path(docs_dir, norm_path)
                if target_file.is_file():
                    target_file.unlink()
                    self._cleanup_empty_dirs(target_file, docs_dir)

        return self.get_tree()

    def move_item(self, index_path: list[int], direction: str) -> dict[str, Any]:
        """Move a section or page up/down within its current container."""
        if direction not in ("up", "down"):
            raise NavError("Hướng di chuyển phải là 'up' hoặc 'down'.")
        raw_text, data = self._load_config()
        nav = self._get_nav_raw(data)
        container, idx = self._get_container_and_index(nav, index_path)
        new_idx = idx - 1 if direction == "up" else idx + 1
        if new_idx < 0 or new_idx >= len(container):
            return self.get_tree()
        container[idx], container[new_idx] = container[new_idx], container[idx]
        self._save_nav(raw_text, nav)
        return self.get_tree()

    def read_page_content(self, rel_path: str) -> dict[str, Any]:
        """Read Markdown file content for quick inspection in the admin UI."""
        _, data = self._load_config()
        docs_dir = self._get_docs_dir(data)
        norm = self.normalize_rel_path(rel_path)
        target_file = self.resolve_doc_path(docs_dir, norm)
        if not target_file.is_file():
            return {"path": norm, "exists": False, "content": ""}
        return {
            "path": norm,
            "exists": True,
            "content": target_file.read_text(encoding="utf-8"),
        }

    def run_build_check(self) -> dict[str, Any]:
        """Run `zensical build --strict` and return status + output."""
        zensical_exe = self._find_zensical_executable()
        if not zensical_exe:
            return {
                "ok": False,
                "returncode": -1,
                "output": "Không tìm thấy lệnh `zensical` trong môi trường hiện tại.",
            }
        proc = subprocess.run(
            [zensical_exe, "build", "--strict"],
            cwd=str(self.root_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        combined = "\n".join(
            part for part in (proc.stdout.strip(), proc.stderr.strip()) if part
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "output": combined or ("Build thành công" if proc.returncode == 0 else "Build lỗi"),
        }

    def _find_zensical_executable(self) -> str | None:
        exe_name = "zensical.exe" if os.name == "nt" else "zensical"
        py_bin_dir = Path(sys.executable).resolve().parent
        candidate = py_bin_dir / exe_name
        if candidate.is_file():
            return str(candidate)
        venv_bin = self.root_dir / ".venv" / ("Scripts" if os.name == "nt" else "bin") / exe_name
        if venv_bin.is_file():
            return str(venv_bin)
        return shutil.which("zensical")
