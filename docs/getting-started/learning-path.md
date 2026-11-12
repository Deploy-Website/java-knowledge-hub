---
tags: [java, learning]
---

# Lộ trình học Java

## 1. Bản chất

Học Java hiệu quả nên đi từ **mô hình dữ liệu → xử lý dữ liệu → xử lý đồng thời → quan sát hiệu năng**, thay vì học API rời rạc.

## 2. Thứ tự đề xuất

1. [Java Core](../core/index.md): kiểu dữ liệu, object, record và exception.
2. [Collections](../collections/index.md): List, Set, Map, độ phức tạp.
3. [Stream API](../collections/stream-api.md): transform, filter, group.
4. [Thread Pool](../concurrency/thread-pool.md): quản lý concurrency có giới hạn.
5. [JVM & GC](../jvm/memory-gc.md): hiểu latency/memory.
6. [Best Practices](../best-practices/index.md): áp dụng vào production.

## 3. Bài tập thực tế

Từ danh sách đơn hàng, thử: lọc trạng thái thanh toán, nhóm theo customerId, tính tổng tiền,
và chạy kiểm tra độc lập qua thread pool có giới hạn.

!!! warning "Đừng bỏ qua dữ liệu"
    Với Java, cấu trúc dữ liệu và ranh giới mutability thường quan trọng hơn cú pháp ngắn gọn.
