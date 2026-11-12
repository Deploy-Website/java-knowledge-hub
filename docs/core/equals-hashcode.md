---
tags: [java, core, collections]
---

# equals() và hashCode()

## 1. Bản chất

`equals` xác định hai object có bằng nhau về logic hay không; `hashCode` hỗ trợ các collection dạng hash.
**Hai object `equals` bằng nhau bắt buộc có cùng `hashCode`**.

## 2. Lỗi thực tế với HashSet

```java
import java.util.Set;

record CustomerId(String value) {}

class Example {
    public static void main(String[] args) {
        Set<CustomerId> ids = Set.of(new CustomerId("C001"));
        System.out.println(ids.contains(new CustomerId("C001"))); // true
    }
}
```

Dùng `record` cho value object giúp tránh viết tay cặp phương thức dễ sai.

## 3. Edge cases

- Không dùng field mutable để tính hash của key đang nằm trong `HashMap`.
- `BigDecimal("1.0")` và `BigDecimal("1.00")` khác nhau theo `equals`, dù `compareTo` trả `0`.
- Với entity có ID được sinh sau khi persist, cần thiết kế equality theo lifecycle rõ ràng.

**Nguồn:** [Object.equals/hashCode](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Object.html).
