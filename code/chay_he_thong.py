import feedparser
import json
import os
import ssl
import asyncio
import time
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from utils_gemini import loc_tin_voi_gemini

# Thiết lập SSL để tránh lỗi chứng chỉ khi tải RSS
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

# Đường dẫn các file (Quay lại thư mục gốc)
FILE_CAU_HINH = '../config.json'
FILE_NGUON_RSS = '../rss_links.json'
THU_MUC_KET_QUA = '../ket_qua'
FILE_KET_QUA_CUOI = os.path.join(THU_MUC_KET_QUA, 'ket_qua_cuoi_cung.json')
FILE_THEO_NGAY = os.path.join(THU_MUC_KET_QUA, f"ngay_{datetime.now().strftime('%Y-%m-%d')}.json")

async def lay_noi_dung_chi_tiet(duong_dan_url, ngu_canh_trinh_duyet):
    trang = None
    try:
        trang = await ngu_canh_trinh_duyet.new_page()
        await trang.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })
        
        print(f"--- Đang bóc tách: {duong_dan_url}")
        # Chờ trang load xong (không dùng networkidle để tránh treo lâu)
        await trang.goto(duong_dan_url, wait_until="load", timeout=30000)
        
        noi_dung_tho = await trang.evaluate("""() => {
            const rac = ['nav', 'footer', 'script', 'style', 'header', 'aside', '.ads', '#ads', '.comments'];
            rac.forEach(the => {
                document.querySelectorAll(the).forEach(el => el.remove());
            });
            return document.body.innerText;
        }""")
        
        return noi_dung_tho.strip()
    except Exception as loi:
        print(f"!!! Lỗi khi bóc tách {duong_dan_url}: {loi}")
        return None
    finally:
        if trang:
            await trang.close()

async def thuc_thi_he_thong():
    print("====================================================")
    print("BẮT ĐẦU CHẠY HỆ THỐNG PHÂN TÍCH TIN TỨC")
    print("====================================================")

    # 1. Đọc cấu hình và nguồn RSS
    if not os.path.exists(FILE_CAU_HINH) or not os.path.exists(FILE_NGUON_RSS):
        print("!!! Thiếu file config.json hoặc rss_links.json")
        return

    with open(FILE_CAU_HINH, 'r', encoding='utf-8') as f:
        cau_hinh = json.load(f)
    
    with open(FILE_NGUON_RSS, 'r', encoding='utf-8') as f:
        danh_sach_url_rss = json.load(f)

    kho_du_lieu_tam = []
    so_ngay_gioi_han = cau_hinh.get('limit_days', 7) # Mặc định 7 ngày nếu không có config
    thoi_diem_hien_tai = time.time()
    giay_gioi_han = so_ngay_gioi_han * 24 * 60 * 60

    # 2. Tải tin từ RSS
    print(f"\n>>> Bước 1: Đang tải tin từ {len(danh_sach_url_rss)} nguồn RSS (Giới hạn: {so_ngay_gioi_han} ngày qua)...")
    for url in danh_sach_url_rss:
        print(f"Tải: {url}")
        kenh_tin = feedparser.parse(url)
        for tin in kenh_tin.entries:
            # Lọc theo thời gian
            ngay_dang_struct = tin.get('published_parsed')
            if ngay_dang_struct:
                thoi_diem_dang = time.mktime(ngay_dang_struct)
                if thoi_diem_hien_tai - thoi_diem_dang > giay_gioi_han:
                    continue
            
            kho_du_lieu_tam.append({
                'tieu_de': tin.get('title', ''),
                'mo_ta': tin.get('summary', tin.get('description', '')),
                'duong_dan': tin.get('link', ''),
                'ngay_dang': tin.get('published', '')
            })
    
    print(f"--- Đã lấy được {len(kho_du_lieu_tam)} tin phù hợp với thời gian.")

    # 3. Lọc tin bằng AI thật thông qua Gemini SDK
    print(f"\n>>> Bước 2: AI (Gemini) đang phân tích FUD & Cá mập Crypto...")
    ngu_canh_ai = cau_hinh.get('shark_context', '')
    muc_tieu = cau_hinh.get('target_sentiment', 'negative')
    
    # Chia nhỏ danh sách tin để gửi (Gemini 2.5 Flash cân được 100+ tin mỗi lần)
    danh_sach_loc = kho_du_lieu_tam[:100] 
    ket_qua_ai = loc_tin_voi_gemini(danh_sach_loc, ngu_canh_ai, muc_tieu)
    
    tin_da_loc = []
    if ket_qua_ai and isinstance(ket_qua_ai, list):
        for phan_hoi in ket_qua_ai:
            if phan_hoi.get('phu_hop'):
                idx = phan_hoi.get('index')
                if idx is not None and idx < len(danh_sach_loc):
                    tin_phu_hop = danh_sach_loc[idx]
                    tin_phu_hop['y_do_ca_map'] = phan_hoi.get('y_do_ca_map', 'N/A')
                    tin_da_loc.append(tin_phu_hop)
    
    if not tin_da_loc:
        print("--- Gemini không tìm thấy tin nào phù hợp với yêu cầu.")
        # Nếu muốn demo khi không có kết quả AI, bạn có thể fallback về filter từ khóa cũ
    else:
        print(f"--- Gemini đã lọc được {len(tin_da_loc)} tin phù hợp.")

    # 4. Cào nội dung chi tiết
    print(f"\n>>> Bước 3: Đang truy cập và lấy nội dung chi tiết cho {len(tin_da_loc)} tin đã lọc...")
    
    async with async_playwright() as p:
        trinh_duyet = await p.chromium.launch(headless=True)
        ngu_canh = await trinh_duyet.new_context()
        
        ket_qua_cuoi = []
        for tin in tin_da_loc:
            noi_dung_full = await lay_noi_dung_chi_tiet(tin['duong_dan'], ngu_canh)
            if noi_dung_full:
                tin['noi_dung_chi_tiet'] = noi_dung_full
                ket_qua_cuoi.append(tin)
        
        # Lưu kết quả
        if not os.path.exists(THU_MUC_KET_QUA):
            os.makedirs(THU_MUC_KET_QUA)
            
        with open(FILE_KET_QUA_CUOI, 'w', encoding='utf-8') as f:
            json.dump(ket_qua_cuoi, f, ensure_ascii=False, indent=2)
            
        # Lưu thêm file lọc theo ngày (overwrite mỗi lần chạy)
        with open(FILE_THEO_NGAY, 'w', encoding='utf-8') as f:
            json.dump(ket_qua_cuoi, f, ensure_ascii=False, indent=2)
            
        await trinh_duyet.close()

    print("\n====================================================")
    print(f"HOÀN TẤT! Đã lưu {len(ket_qua_cuoi)} bài viết.")
    print(f"- Tổng hợp: {FILE_KET_QUA_CUOI}")
    print(f"- Theo ngày: {FILE_THEO_NGAY}")
    print("====================================================")

if __name__ == "__main__":
    asyncio.run(thuc_thi_he_thong())
