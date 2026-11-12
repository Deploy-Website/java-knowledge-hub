---
tags: [java, jvm, troubleshooting]
---

# Chẩn đoán ứng dụng Java

## 1. Bản chất

Diagnostic nên đi từ **triệu chứng → dữ liệu quan sát → giả thuyết → thay đổi nhỏ → đo lại**.
Tránh đổi đồng thời heap, pool và garbage collector vì sẽ mất khả năng kết luận.

## 2. Công cụ có sẵn trong JDK

```bash
jcmd -l
jcmd <PID> Thread.print
jcmd <PID> GC.heap_info
jcmd <PID> GC.class_histogram
```

`jcmd` thường cần chạy cùng user và quyền phù hợp với process đích.

!!! danger "Chú ý production"
    Một số lệnh diagnostic có ảnh hưởng hiệu năng hoặc tạo file lớn. Kiểm tra tài liệu của từng lệnh,
    dung lượng đĩa và chính sách bảo mật trước khi sử dụng trên production.

## 3. Checklist

- [ ] Thu thập timeline xảy ra lỗi, RPS/latency/error rate.
- [ ] Kiểm tra thread count, CPU, heap, GC pause.
- [ ] Liên hệ với deploy/change gần nhất.
- [ ] Đưa ra một giả thuyết có thể kiểm chứng.

**Nguồn:** [jcmd manual](https://docs.oracle.com/en/java/javase/17/docs/specs/man/jcmd.html).
