#!/bin/bash

# Lấy đường dẫn tuyệt đối của thư mục chứa script này
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "------------------------------------------------"
echo " Đang kiểm tra môi trường ảo (venv)..."
if [ ! -d "venv" ]; then
    echo " [!] Chưa tìm thấy môi trường ảo. Đang tạo venv mới..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium
else
    source venv/bin/activate
fi

echo " >>> Đang khởi chạy hệ thống phân tích tin..."
echo "------------------------------------------------"

# Chuyển vào folder code và chạy code
cd code
python3 chay_he_thong.py

echo "------------------------------------------------"
echo " Xong! Nhấn phím bất kỳ để thoát."
read -n 1
