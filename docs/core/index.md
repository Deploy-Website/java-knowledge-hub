---
tags: [java, core]
---

# Java Core

## 1. Bản chất

Java là ngôn ngữ kiểu tĩnh, hướng đối tượng và có quản lý bộ nhớ tự động thông qua JVM.
Trong backend, điều quan trọng là **thiết kế dữ liệu và hợp đồng API rõ ràng**.

## 2. Những khái niệm cần phân biệt

| Khái niệm | Ý nghĩa thực tế |
| --- | --- |
| `record` | DTO/value data ngắn gọn, shallowly immutable |
| `class` | Đối tượng có trạng thái/hành vi, có thể mutable |
| `interface` | Hợp đồng giữa các thành phần |
| `checked exception` | Compiler yêu cầu xử lý hoặc khai báo |
| `equals/hashCode` | Định danh logic khi dùng Set/Map |

## 3. Đọc tiếp

- [Record và immutable data](records.md)
- [equals() và hashCode()](equals-hashcode.md)
- [Exception handling](exceptions.md)

**Nguồn:** [Java SE 17 Language Specification](https://docs.oracle.com/javase/specs/jls/se17/html/).
