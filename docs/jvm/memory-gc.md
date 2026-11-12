---
tags: [java, jvm, gc, performance]
---

# JVM Memory & Garbage Collection

## 1. Bản chất

JVM quản lý object trên heap và giải phóng object không còn reachable bằng garbage collector.
Lỗi `OutOfMemoryError` không đồng nghĩa luôn có memory leak; có thể do heap nhỏ, dữ liệu bùng nổ hoặc native memory.

## 2. Những vùng cần quan sát

| Vùng | Vai trò |
| --- | --- |
| Heap | Object và array |
| Stack mỗi thread | Frame, local variables, operand stack |
| Metaspace | Metadata của class (HotSpot) |
| Direct/native memory | Direct buffer và các vùng native khác |

## 3. Ví dụ startup flags cho Java 17

```bash
java -Xms512m -Xmx2g       -Xlog:gc*:file=gc.log:time,uptime,level,tags       -jar app.jar
```

!!! note "Không dùng -Xmx = RAM máy"
    Trong container, JVM, OS và native memory đều cần RAM. Đặt resource limit và đo RSS,
    GC logs, heap usage trước khi quyết định.

## 4. Triệu chứng phổ biến

- CPU tăng + GC liên tục: kiểm tra allocation rate và live set.
- Heap tăng đến max rồi OOM: heap dump, retained objects, cache eviction.
- RSS tăng nhưng heap ổn định: kiểm tra native/direct memory, số thread, metaspace.

**Nguồn:** [Java 17 HotSpot VM Options](https://docs.oracle.com/en/java/javase/17/docs/specs/man/java.html), [JDK GC Tuning Guide](https://docs.oracle.com/en/java/javase/17/gctuning/).
