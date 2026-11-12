---
tags: [java, troubleshooting, best-practices]
---

# Template ghi chép sự cố

Sao chép mẫu sau vào một file Markdown mới trong `docs/troubleshooting/`.

```markdown
---
tags: [java, troubleshooting]
---

# [Triệu chứng / Exception]

## 1. Bối cảnh
- JDK version:
- Môi trường:
- Mức độ ảnh hưởng:

## 2. Triệu chứng và cách tái hiện
- Input, log (đã ẩn dữ liệu nhạy cảm), stacktrace
- Steps to reproduce

## 3. Giả thuyết và kiểm chứng
| Giả thuyết | Bằng chứng | Kết quả |
| --- | --- | --- |
| ... | ... | ... |

## 4. Root cause
- ...

## 5. Cách khắc phục
- Thay đổi:
- Kiểm thử:
- Rollback plan:

## 6. Prevention
- Guardrail / alert / test

## Nguồn
- Official docs / issue / PR
```

!!! tip "Quy tắc lưu trữ"
    Tên file dùng kebab-case theo sự cố, ví dụ `thread-pool-starvation.md`.
    Sau khi ghi chép, thêm vào menu `Troubleshooting` và liên kết sang trang lý thuyết.
