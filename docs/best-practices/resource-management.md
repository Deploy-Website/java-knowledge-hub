---
tags: [java, best-practices, io]
---

# Resource management

## 1. Bản chất

File streams và nhiều tài nguyên I/O cần được đóng; GC không thay thế cơ chế đóng tài nguyên.
Dùng `try-with-resources` khi object triển khai `AutoCloseable`.

## 2. Tình huống: đọc CSV theo dòng

```java
import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

public class CsvReader {
    public static long countRows(Path path) throws IOException {
        long count = 0;
        try (BufferedReader reader = Files.newBufferedReader(
                path, StandardCharsets.UTF_8)) {
            while (reader.readLine() != null) {
                count++;
            }
        }
        return count;
    }
}
```

Thao tác này dùng O(1) memory bổ sung theo số dòng, nhưng không xử lý CSV có newline bên trong quoted fields.
Với CSV chuẩn RFC 4180, dùng parser chuyên biệt nếu cần xử lý đầy đủ.

## 3. Chú ý

- Exception lúc `close()` có thể được gắn thành suppressed exception.
- Không đọc toàn file vào RAM chỉ để đếm dòng với tập tin lớn.
- `ExecutorService` trong Java 17 **không** là `AutoCloseable`; shutdown theo lifecycle riêng.

**Nguồn:** [Try-with-resources](https://docs.oracle.com/javase/tutorial/essential/exceptions/tryResourceClose.html), [Files.newBufferedReader](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/nio/file/Files.html#newBufferedReader(java.nio.file.Path,java.nio.charset.Charset)).
