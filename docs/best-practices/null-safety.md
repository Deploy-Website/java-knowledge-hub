---
tags: [java, best-practices, "null"]
---

# Null safety và Optional

## 1. Bản chất

`Optional<T>` biểu diễn một kết quả có thể vắng mặt, đặc biệt hữu ích ở **return type**.
Không nên dùng `Optional` bừa bãi ở field/parameter chỉ để tránh `null`.

## 2. Tình huống: tìm đơn hàng theo ID

```java
import java.util.Map;
import java.util.Optional;

record Order(String id, String status) {}

class OrderRepository {
    private final Map<String, Order> orders;

    OrderRepository(Map<String, Order> orders) {
        this.orders = Map.copyOf(orders);
    }

    Optional<Order> findById(String id) {
        return Optional.ofNullable(orders.get(id));
    }
}
```

Cách sử dụng:

```java
Order order = repository.findById("O100")
        .orElseThrow(() -> new IllegalArgumentException("Order not found"));
```

## 3. Edge cases

- `Optional.of(null)` ném `NullPointerException` ngay; dùng `ofNullable` nếu có thể null.
- `orElse(fallback())` đánh giá `fallback()` ngay, còn `orElseGet(() -> fallback())` lazy.
- Không gọi `get()` khi chưa kiểm tra hiện diện.

**Nguồn:** [Optional API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/Optional.html).
