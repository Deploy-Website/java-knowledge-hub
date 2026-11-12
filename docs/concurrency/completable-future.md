---
tags: [java, concurrency, completablefuture]
---

# CompletableFuture

## 1. Bản chất

`CompletableFuture` giúp mô hình hóa phép tính hoàn thành trong tương lai và kết hợp các phép tính bất đồng bộ.
Nó **không tự bảo đảm non-blocking I/O**; `supplyAsync` vẫn chạy logic của bạn trên thread.

## 2. Tình huống: lấy dữ liệu từ hai nguồn độc lập

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

record Profile(String name, int points) {}

class ProfileService {
    private final Executor ioExecutor;

    ProfileService(Executor ioExecutor) {
        this.ioExecutor = ioExecutor;
    }

    CompletableFuture<Profile> load(String customerId) {
        var name = CompletableFuture.supplyAsync(
                () -> fetchName(customerId), ioExecutor);
        var points = CompletableFuture.supplyAsync(
                () -> fetchPoints(customerId), ioExecutor);
        return name.thenCombine(points, Profile::new);
    }

    private String fetchName(String id) { return "Customer-" + id; }
    private Integer fetchPoints(String id) { return 100; }
}
```

## 3. Lưu ý production

- Truyền `Executor` được quản lý thay vì phụ thuộc ngầm vào common pool khi làm I/O.
- Đặt timeout ở **HTTP client/DB client**; `orTimeout` chỉ hoàn tất future lỗi, không bảo đảm dừng tác vụ nền.
- Dùng `handle/exceptionally` để quy định fallback; không bỏ qua thất bại im lặng.

**Nguồn:** [CompletableFuture](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CompletableFuture.html).
