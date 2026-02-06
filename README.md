# Hướng dẫn sử dụng Hệ thống Thao túng Truyền thông (Shark Analyzer)

Hệ thống này giúp bạn tự động lấy tin tức từ các nguồn RSS, lọc các tin bài "tiêu cực" hoặc "tích cực" dựa trên bối cảnh bị cá mập thao túng, cào toàn bộ nội dung và thống kê tần suất các từ khóa nhạy cảm.

## 1. Các file cấu hình chính

- **`config.json`**: Nơi bạn chỉnh sửa chế độ lọc (`positive`/`negative`), ngữ cảnh (`shark_context`) và danh sách các từ khóa tiêu cực cần thống kê.
- **`rss_links.json`**: Danh sách các link RSS bạn muốn theo dõi.

## 2. Cách vận hành

Bạn chỉ cần chạy file tổng hợp:

```bash
python3 run_all.py
```

## 3. Các bước hệ thống thực hiện:

1. **Lấy tin RSS**: Tải tiêu đề và mô tả ngắn từ các link trong `rss_links.json`.
2. **Lọc nội dung (AI Filter)**: AI sẽ phân tích xem tin nào mang ý đồ "thao túng" theo bối cảnh bạn thiết lập.
3. **Cào dữ liệu (Scraping)**: Truy cập trực tiếp vào bài báo (vượt qua các trang chỉ load bằng Javascript) để lấy toàn bộ nội dung.
4. **Phân tích tần suất**: Đếm số lần xuất hiện của các từ khóa như "sụp đổ", "khủng hoảng"... trong bài viết.

## 4. Kết quả nhận được

Kết quả cuối cùng nằm trong file **`final_results.json`**. Mỗi bài viết sẽ có:

- `title`: Tiêu đề.
- `shark_intent`: AI phân tích ý đồ phía sau.
- `full_content`: Toàn bộ nội dung bài báo.
- `negative_word_frequency`: Bảng thống kê số lần xuất hiện của từ khóa tiêu cực.

## Lưu ý cho người dùng:

- Nếu bạn muốn thay đổi "Bối cảnh cá mập", hãy sửa mục `shark_context` trong `config.json`.
- Danh sách từ khóa tiêu cực có thể thêm bớt tùy ý trong mục `negative_word_groups`.
