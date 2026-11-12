---
tags: [java, jdk, maven]
---

# Cài đặt JDK & Maven

## 1. Kiểm tra môi trường

```bash
java -version
javac -version
mvn -version
```

Bạn nên thấy `java` và `javac` cùng major version, ví dụ 17.
`mvn -version` cũng hiển thị JDK mà Maven sử dụng.

## 2. Cấu hình trong WSL Ubuntu

Nếu JDK đã được cài, xác định vị trí:

```bash
readlink -f "$(command -v java)"
echo "$JAVA_HOME"
```

!!! note "Không cài trùng"
    Nếu WSL đã có JDK 17 và Maven phù hợp, chỉ kiểm tra `JAVA_HOME`, `PATH` và `mvn -version`;
    không cần cài lại mọi công cụ.

## 3. Chạy file Java đơn giản

Tạo `HelloJava.java`:

```java
public class HelloJava {
    public static void main(String[] args) {
        System.out.println("Java docs ready");
    }
}
```

```bash
javac HelloJava.java
java HelloJava
```

## 4. Lưu ý

- Môi trường build Zensical chỉ cần **Python**, không phụ thuộc Maven/JDK.
- Nếu dùng Maven Toolchains, kiểm tra cấu hình toolchain riêng với `JAVA_HOME`.

**Nguồn:** [JDK Tool Guides](https://docs.oracle.com/en/java/javase/17/docs/specs/man/).
