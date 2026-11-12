"""CLI entry point to start the Zensical Admin web interface."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from admin_app.server import create_server


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Khởi chạy trang quản trị mục và bài viết cho Zensical."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Địa chỉ bind (mặc định: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8001, help="Cổng trang quản trị (mặc định: 8001)")
    parser.add_argument(
        "--docs-url",
        default="http://localhost:8000",
        help="URL trang tài liệu Zensical để mở xem nhanh",
    )
    parser.add_argument(
        "--with-docs",
        action="store_true",
        help="Chạy kèm `zensical serve` song song trên cổng 8000",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Tự động mở trình duyệt khi khởi động",
    )
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent
    docs_proc: subprocess.Popen[bytes] | None = None

    if args.with_docs:
        exe_name = "zensical.exe" if os.name == "nt" else "zensical"
        zensical_exe = Path(sys.executable).resolve().parent / exe_name
        cmd = [str(zensical_exe) if zensical_exe.is_file() else "zensical", "serve"]
        docs_proc = subprocess.Popen(cmd, cwd=str(root_dir))

    server = create_server(root_dir, host=args.host, port=args.port, docs_url=args.docs_url)
    admin_url = f"http://{args.host}:{args.port}/"
    print(f"Zensical Admin đang chạy tại: {admin_url}")
    if args.with_docs:
        print(f"Zensical Docs đang chạy tại: {args.docs_url}")

    if args.open:
        webbrowser.open(admin_url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang dừng server quản trị...")
    finally:
        server.server_close()
        if docs_proc is not None and docs_proc.poll() is None:
            docs_proc.terminate()
            docs_proc.wait(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
