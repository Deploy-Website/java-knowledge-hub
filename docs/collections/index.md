---
tags: [java, collections, performance]
---

# Chọn Collection phù hợp

## 1. Bản chất

Collection quyết định cách dữ liệu được truy cập và mức chi phí thao tác. Không có cấu trúc nào tối ưu cho mọi nghiệp vụ.

| Nhu cầu | Chọn thông thường | Chi phí trung bình |
| --- | --- | --- |
| Duyệt theo thứ tự, truy cập bằng index | `ArrayList` | `get(i)` O(1), tìm O(n) |
| Không trùng phần tử | `HashSet` | `contains` O(1) kỳ vọng |
| Tra cứu theo ID | `HashMap` | `get` O(1) kỳ vọng |
| Cần key có thứ tự | `TreeMap` | `get/put` O(log n) |
| Duyệt map theo insertion order | `LinkedHashMap` | `get` O(1) kỳ vọng |

!!! note "O(1) kỳ vọng không phải bảo đảm mọi input"
    Hash collisions, resize, hash function và memory overhead vẫn có thể ảnh hưởng hiệu năng.

## 2. Tình huống: kiểm tra ID tồn tại

Nếu kiểm tra một tập `allowedIds` nhiều lần, chuyển từ `List` sang `HashSet` một lần:

```java
import java.util.HashSet;
import java.util.List;
import java.util.Set;

List<String> allowedIds = List.of("A001", "A002", "A003");
Set<String> lookup = new HashSet<>(allowedIds); // O(n) để khởi tạo
boolean found = lookup.contains("A002");       // O(1) kỳ vọng
```

Với dữ liệu rất nhỏ hoặc tra cứu một lần, `List` có thể đơn giản và đủ nhanh.

**Nguồn:** [Java Collections Framework](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/doc-files/coll-overview.html).
