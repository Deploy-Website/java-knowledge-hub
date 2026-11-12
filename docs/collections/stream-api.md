---
tags: [java, collections, streams]
---

# Stream API thực chiến

## 1. Bản chất

`Stream` biểu diễn pipeline xử lý dữ liệu; intermediate operations như `filter/map` là lazy,
còn terminal operations như `toList/collect` mới chạy pipeline.

## 2. Tình huống: tổng tiền theo khách hàng

```java
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

record Order(String customerId, BigDecimal total, boolean paid) {}

class OrderReport {
    static Map<String, BigDecimal> totalPaidByCustomer(List<Order> orders) {
        return orders.stream()
                .filter(Order::paid)
                .collect(Collectors.groupingBy(
                        Order::customerId,
                        Collectors.reducing(
                                BigDecimal.ZERO,
                                Order::total,
                                BigDecimal::add
                        )
                ));
    }
}
```

**Độ phức tạp:** O(n) thao tác hash kỳ vọng, dùng O(k) bộ nhớ cho `k` khách hàng khác nhau.

## 3. Stream hay for-loop?

=== "Stream"
    Phù hợp cho pipeline `filter → transform → collect` rõ ràng, không cần side effect.

=== "for-loop"
    Phù hợp khi logic branch phức tạp, cần early exit, hoặc profiling chỉ ra hot path.

!!! warning "Tránh side effect trong stream"
    Không sửa một `ArrayList` dùng chung bên trong `parallelStream()` nếu không đồng bộ.
    Không mặc định dùng parallel stream cho workload I/O.

**Nguồn:** [Stream API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/stream/Stream.html).
