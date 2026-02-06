# 🦈 Shark Crypto Analyzer 🦈

Hệ thống tự động phát hiện **FUD** và dấu hiệu **thao túng thị trường Crypto** từ các nguồn tin tức (RSS) sử dụng sức mạnh của **Gemini 2.5 Flash**.

## 🚀 Tính năng vượt trội (Version 2026)

- **Gemini 2.5 Flash SDK**: Sử dụng SDK mới nhất (`google-genai`), tốc độ xử lý cực nhanh (Sub-second).
- **JSON Schema Control**: Đảm bảo đầu ra AI luôn là JSON chuẩn 100%, không lỗi parse.
- **Crypto Focus**: Quét tin từ VnExpress, VietNamNet và các báo quốc tế lớn (CoinTelegraph, CoinDesk, CryptoSlate).
- **Automation**: Tự động hóa từ khâu lấy tin -> AI lọc tin FUD -> Bóc tách nội dung chuyên sâu.
- **Ghi nhật ký ngày**: Tự động lưu file kết quả riêng cho từng ngày chạy.

## 📁 Cấu trúc dự án

- `run.sh`: Script "một chạm" để khởi chạy toàn bộ hệ thống.
- `config.yaml`: Nơi chỉnh sửa Model, Bối cảnh (Shark Context) và mục tiêu lọc.
- `rss_links.json`: Danh sách các nguồn tin RSS (Việt Nam & Quốc tế).
- `code/`: Thư mục chứa mã nguồn cốt lõi.
  - `chay_he_thong.py`: Logic vận hành chính.
  - `utils_gemini.py`: Tương tác với Gemini 2.5 SDK.
- `ket_qua/`: Thư mục chứa kết quả phân tích JSON.

## 🛠 Hướng dẫn cài đặt & Chạy

1. **Chuẩn bị API Key**: Lấy Google API Key từ [Google AI Studio](https://aistudio.google.com/).
2. **Kích hoạt & Chạy**:
   Mở Terminal tại thư mục dự án và chạy:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
   _Script sẽ tự động tạo môi trường ảo (venv), cài đặt thư viện và khởi chạy._

## ⚙️ Tùy chỉnh bối cảnh Cá Mập

Sửa file `config.yaml`:

- `ai_model`: `gemini-2.5-flash` (Mặc định).
- `shark_context`: Bạn có thể thay đổi cách AI định nghĩa thế nào là "thao túng" hoặc "FUD" tại đây.
- `limit_days`: Số ngày tin tức cũ nhất muốn quét.

---

_Phát triển bởi Antigravity AI - 2026_
