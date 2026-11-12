---
tags: [java, core, exception]
---

# Exception handling

## 1. Bản chất

Exception biểu diễn đường đi thất bại. Lựa chọn checked/unchecked phụ thuộc hợp đồng API;
tránh `catch (Exception)` chỉ để trả về giá trị mặc định và che mất lỗi thật.

## 2. Tình huống: validate yêu cầu thanh toán

```java
import java.math.BigDecimal;
import java.util.Objects;

public final class PaymentValidator {
    private PaymentValidator() {}

    public static void requirePositive(BigDecimal amount) {
        Objects.requireNonNull(amount, "amount");
        if (amount.signum() <= 0) {
            throw new IllegalArgumentException("amount must be positive");
        }
    }
}
```

## 3. Nguyên tắc production

- **Validate tại boundary** (API/input) và giữ invariant bên trong domain.
- Khi wrap exception, giữ `cause`: `throw new ServiceException("...", ex);`.
- Không log và rethrow cùng một lỗi ở mọi layer (dễ tạo log trùng).
- Nếu `InterruptedException` bị bắt nhưng không ném tiếp, thường cần `Thread.currentThread().interrupt()`.

**Nguồn:** [Java Exceptions tutorial](https://docs.oracle.com/javase/tutorial/essential/exceptions/).
