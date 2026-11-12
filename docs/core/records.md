---
tags: [java, core, record, immutability]
---

# Record và immutable data

## 1. Bản chất

`record` (Java 16+) phù hợp cho **data carrier**: Java tự tạo constructor, accessor,
`equals`, `hashCode` và `toString` dựa vào record components.

!!! warning "Record không đảm bảo deep immutability"
    Nếu component là `List` mutable, phần tử trong list vẫn có thể thay đổi nếu không defensive copy.

## 2. Tình huống: DTO đơn hàng

```java
import java.math.BigDecimal;
import java.util.List;
import java.util.Objects;

public record OrderSummary(String orderId, List<BigDecimal> itemPrices) {
    public OrderSummary {
        Objects.requireNonNull(orderId, "orderId");
        itemPrices = List.copyOf(Objects.requireNonNull(itemPrices, "itemPrices"));
    }

    public BigDecimal total() {
        return itemPrices.stream()
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}
```

`List.copyOf` tạo danh sách **không thể sửa** và không cho phép phần tử null.
Trong ví dụ, `BigDecimal` là immutable nên không cần copy sâu phần tử.

## 3. Khi nào không nên dùng?

- Entity cần lifecycle, identity và trạng thái thay đổi liên tục.
- Đối tượng phải tương thích với framework yêu cầu no-arg constructor/setter (xác minh theo framework cụ thể).

**Nguồn:** [JEP 395](https://openjdk.org/jeps/395), [List.copyOf API](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/List.html#copyOf(java.util.Collection)).
