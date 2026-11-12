---
tags: [java, best-practices, clean-code]
---

# Best Practices Java

## 1. Nguyên tắc

Code tốt là code có **invariant rõ ràng, phụ thuộc tối thiểu, dễ test và có hành vi lỗi dự đoán được**.

## 2. Cách tổ chức giải pháp chung

- Dùng tên mô tả domain (`OrderSummary`, `CustomerId`) thay vì `Utils` cho mọi hành vi.
- Giữ pure functions cho tính toán thuần, tách I/O ra boundary.
- Validate input ở boundary; không biến tất cả `null` thành một giá trị mặc định tùy tiện.
- Không tối ưu vi mô trước khi có profiler/benchmark.
- Đặt tên exception và thông báo có ngữ cảnh; giữ cause.

## 3. Checklist review

- [ ] Có kiểm thử happy path và edge case?
- [ ] Tài nguyên (file, executor, DB) được đóng đúng lifecycle?
- [ ] Collections/DTO có tránh rò rỉ mutable state?
- [ ] Độ phức tạp có phù hợp kích thước input thực tế?
- [ ] Log có tránh lộ dữ liệu nhạy cảm?

## Đọc thêm

- [Null safety](null-safety.md)
- [Resource management](resource-management.md)

**Nguồn:** [Effective Java, 3rd Edition](https://www.pearson.com/en-us/subject-catalog/p/effective-java/P200000000935/9780134685991).
