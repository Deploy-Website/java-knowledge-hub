# Java Knowledge Base — Zensical

Project mẫu **chỉ cho tài liệu Java**, không có Spring, PostgreSQL hay chủ đề khác.
Nội dung tiếng Việt, code ví dụ Java 17+, cấu hình Zensical 0.1.1.

## 1. Yêu cầu

- Python >= 3.11 và module `venv`.
- Java JDK 17+ để chạy ví dụ Java; **không bắt buộc** để build trang docs.
- WSL Ubuntu / Linux / macOS; trên Windows có thể dùng PowerShell tương ứng.

## 2. Chạy local (WSL Ubuntu)

```bash
cd java-zensical-docs
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
zensical serve
```

Mở http://127.0.0.1:8000/ trên Windows/browser (WSL thường forward localhost).

## 2.1. Trang quản trị mục & bài viết

Chạy trang quản trị bằng Python (không cần cài thêm thư viện ngoài):

```bash
python admin.py --with-docs
```

- Trang quản trị: http://127.0.0.1:8001/ (thêm, sửa, xóa, sắp xếp nhóm mục/bài viết trong `zensical.toml` và tự tạo file `.md` rỗng chỉ có dòng tiêu đề `# Tiêu đề` trong `docs/`).
- Trang tài liệu Zensical: http://localhost:8000/ (chỉ cần bỏ `--with-docs` nếu chỉ muốn chạy riêng trang quản trị).

## 3. Build production

```bash
zensical build --strict
# static output: site/
```

> `site/` là output, không commit vào Git. Trước khi publish,
> thêm `site_url = "https://<domain>/<path>/"` (URL thực tế) vào phần `[project]`
> của `zensical.toml`. Sau đó có thể bật `navigation.instant` nếu cần.

## 4. Đổi giao diện

Chỉnh trong `[project.theme]`:

```toml
variant = "modern"   # hoặc "classic" để gần Material for MkDocs
language = "vi"
```

## 5. Thêm tài liệu mới

1. Tạo Markdown trong `docs/`, ví dụ `docs/core/generics.md`.
2. Ghi front matter `tags` và bài viết.
3. Bổ sung đường dẫn vào `nav` trong `zensical.toml`.
4. Chạy `zensical build --strict` để phát hiện lỗi build.

Mỗi bài nên có: **Bản chất → Cơ chế → Ví dụ thực tế → Best Practice/Edge cases → Nguồn**.

## 6. Kiểm tra phiên bản

`python -m pip index versions zensical` để kiểm tra có bản mới hơn.
Project pin `zensical==0.1.1` nhằm giúp build có thể lặp lại; nâng cấp có kiểm soát
bằng cách sửa `requirements.txt`, kiểm tra changelog rồi chạy lại build.

## Nguồn tài liệu Zensical chính thức

- https://zensical.org/docs/get-started/
- https://zensical.org/docs/setup/navigation/
- https://zensical.org/docs/setup/colors/
- https://zensical.org/docs/authoring/code-blocks/
- https://zensical.org/docs/compatibility/markdown/python-markdown-extensions/

## Ghi chú

- Mermaid, tabs, admonitions, syntax highlight và tags được cấu hình theo Zensical.
- Các đoạn Java sử dụng API Java 17 trở xuống, ngoại trừ phần nhắc đến version mới.
- CI chạy test, build kiểm tra (`zensical build --clean --strict`) và tự động deploy lên GitHub Pages khi push lên nhánh `main` (cần bật **Settings → Pages → Source: GitHub Actions** trên repository).
