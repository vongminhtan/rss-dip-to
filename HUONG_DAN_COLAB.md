# 📓 Hướng dẫn chạy Shark Crypto Analyzer trên Google Colab

Để chạy dự án này trên Google Colab (nền tảng đám mây), bạn hãy thực hiện theo các bước sau đây.

### Bước 1: Truy cập Google Colab

Mở trình duyệt và truy cập: [colab.research.google.com](https://colab.research.google.com/)

### Bước 2: Tạo Notebook mới và Clone code

Trong một cell mới, hãy copy và chạy lệnh này để tải code từ GitHub của bạn về:

```python
# 1. Tải code từ GitHub
!git clone https://github.com/vongminhtan/rss-dip-to.git
%cd rss-dip-to
```

### Bước 3: Cài đặt các thư viện cần thiết

Hệ thống Colab chưa có sẵn các thư viện dự án yêu cầu, hãy chạy cell này:

```python
# 2. Cài đặt thư viện (Bao gồm cả Playwright cho môi trường Linux của Colab)
!pip install -r requirements.txt
!pip install playwright
!playwright install chromium
```

### Bước 4: Cấu hình API Key

Bạn có thể sửa trực tiếp file `config.yaml` trong giao diện thư mục của Colab (biểu tượng thư mục bên trái), hoặc chạy lệnh này để thay thế nhanh:

```python
import yaml

# Đọc file cấu hình
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# THAY API KEY CỦA BẠN VÀO ĐÂY
config['google_api_key'] = 'AIzaSyC7AMlX-Bn1PZKrqFEItrWX9RwXNow3sJs'

# Lưu lại file cấu hình
with open('config.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(config, f, allow_unicode=True)

print("✅ Đã cập nhật API Key thành công!")
```

### Bước 5: Chạy hệ thống

Vì Colab chạy trên môi trường không có màn hình, chúng ta cần di chuyển vào folder `code` để thực thi:

```python
# 3. Khởi chạy
%cd code
import asyncio
from chay_he_thong import thuc_thi_he_thong

# Chạy hệ thống (Colab hỗ trợ await trực tiếp trong cell)
await thuc_thi_he_thong()
```

### Bước 6: Tải kết quả về máy

Sau khi chạy xong, kết quả sẽ nằm trong folder `ket_qua/`. Bạn có thể tải về bằng lệnh:

```python
from google.colab import files
import os

# Đường dẫn quay lại folder kết quả
file_path = '../ket_qua/ket_qua_cuoi_cung.json'
if os.path.exists(file_path):
    files.download(file_path)
else:
    print("❌ Chưa tìm thấy file kết quả.")
```

---

### ⚠️ Lưu ý quan trọng trên Colab:

1. **Reset dữ liệu:** Sau khi bạn đóng trình duyệt hoặc ngắt kết nối quá lâu, Colab sẽ xóa toàn bộ dữ liệu bạn đã clone. Lần sau chạy bạn phải làm lại từ Bước 2.
2. **Playwright trên Cloud:** Đôi khi việc bóc tách nội dung chi tiết trên Colab có thể bị chặn bởi một số trang web bảo mật cao. Tuy nhiên, bước lọc tin FUD bằng Gemini vẫn sẽ hoạt động cực kỳ tốt.
