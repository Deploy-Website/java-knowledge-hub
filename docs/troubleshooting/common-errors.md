---
tags: [java, troubleshooting, debugging]
---

# Các lỗi Java thường gặp

## 1. `NullPointerException`

**Bản chất:** dereference reference null. Kiểm tra stacktrace và ranh giới nhận dữ liệu.

**Ưu tiên:** validate tại API boundary, thiết lập invariant và dùng `Optional` cho kết quả có thể vắng mặt.

## 2. `ConcurrentModificationException`

**Bản chất:** một số iterator fail-fast nếu collection bị thay đổi cấu trúc sai cách trong khi đang lặp.

```java
import java.util.ArrayList;
import java.util.List;

List<String> ids = new ArrayList<>(List.of("A", "B", "C"));
ids.removeIf("B"::equals); // thay vì ids.remove(...) trong enhanced for
```

Fail-fast không phải cơ chế đồng bộ thread; nó là phát hiện bug theo best-effort.

## 3. `OutOfMemoryError: Java heap space`

Thu thập GC log và heap dump khi được phép, quan sát retained objects; cân nhắc batch streaming,
cache limit và memory sizing trước khi chỉ tăng `-Xmx`.

## 4. `RejectedExecutionException`

Xảy ra khi executor không thể nhận task mới (ví dụ đã shutdown hoặc queue/pool đang saturated).
Cần quan sát queue, giới hạn concurrency và định nghĩa chính sách backpressure.

## 5. Mẫu chẩn đoán

Xem [Template ghi chép sự cố](incident-template.md) để lưu lại nguyên nhân và bước tái hiện.

**Nguồn:** [Java API docs](https://docs.oracle.com/en/java/javase/17/docs/api/).
