import feedparser
import json
import os
import ssl
import asyncio
import time
import yaml
import aiohttp
from datetime import datetime
from playwright.async_api import async_playwright
from utils_gemini import loc_tin_voi_gemini

# Mã màu ANSI cho Console
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Thiết lập SSL để tránh lỗi chứng chỉ khi tải RSS
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

# Đường dẫn các file (Xác định dựa trên vị trí của script)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_CAU_HINH = os.path.join(BASE_DIR, 'config.yaml')
FILE_NGUON_RSS = os.path.join(BASE_DIR, 'rss_links.json')
THU_MUC_KET_QUA = os.path.join(BASE_DIR, 'ket_qua')

async def quet_rss_async(url, session):
    """Tải và parse RSS bất đồng bộ."""
    try:
        async with session.get(url, timeout=15, ssl=False) as response:
            html = await response.text()
            return feedparser.parse(html)
    except Exception as e:
        # Nếu gặp lỗi tiêu đề quá dài (Yahoo Finance) hoặc các lỗi khác, thông báo nhẹ nhàng
        error_msg = str(e)
        if "Header value is too long" in error_msg:
            print(f"{YELLOW}--- Nguồn {url} phản hồi header quá dài (Bỏ qua RSS này/Yahoo)...{RESET}")
        else:
            print(f"{RED}!!! Lỗi khi quét {url}: {error_msg[:100]}{RESET}")
        return None

async def lay_noi_dung_chi_tiet(duong_dan_url, ngu_canh_trinh_duyet):
    trang = None
    try:
        trang = await ngu_canh_trinh_duyet.new_page()
        await trang.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })
        
        await trang.goto(duong_dan_url, wait_until="load", timeout=20000)
        noi_dung_tho = await trang.evaluate("() => document.body.innerText")
        return noi_dung_tho.strip()
    except Exception:
        return None
    finally:
        if trang:
            await trang.close()

async def thuc_thi_he_thong():
    print(f"\n{BLUE}{BOLD}====================================================")
    print("   BẮT ĐẦU CHẠY HỆ THỐNG PHÂN TÍCH TIN TỨC (LOCAL)")
    print(f"===================================================={RESET}")

    # 1. Đọc cấu hình
    if not os.path.exists(FILE_CAU_HINH) or not os.path.exists(FILE_NGUON_RSS):
        print(f"!!! Thiếu file cấu hình")
        return

    with open(FILE_CAU_HINH, 'r', encoding='utf-8') as f:
        cau_hinh = yaml.safe_load(f)
    
    with open(FILE_NGUON_RSS, 'r', encoding='utf-8') as f:
        danh_sach_url_rss = json.load(f)
        # CHẾ ĐỘ TEST: Lấy từ cấu hình config.yaml
        if cau_hinh.get('test_mode', False):
            danh_sach_url_rss = danh_sach_url_rss[:3]
            print(f"{YELLOW}--- [TEST MODE] Chỉ sử dụng 3 nguồn RSS đầu tiên.{RESET}")

    kho_tin_tho = []
    tieu_de_da_lay = set()
    so_ngay_gioi_han = cau_hinh.get('limit_days', 2)
    thoi_diem_hien_tai = time.time()
    giay_gioi_han = so_ngay_gioi_han * 24 * 60 * 60

    # 2. Tải và Lọc trùng (NÂNG CẤP ĐA LUỒNG)
    print(f"\n{CYAN}{BOLD}>>> Bước 1: Đang quét RSS từ {len(danh_sach_url_rss)} nguồn (Đồng thời)...{RESET}")
    
    # Cấu hình Connector để bỏ qua SSL và tăng giới hạn Header (Tránh lỗi Yahoo)
    connector = aiohttp.TCPConnector(ssl=False)
    # Lưu ý: aiohttp mặc định giới hạn header 8KB, một số trang như Yahoo gửi lớn hơn. 
    # Ta sẽ giả lập trình duyệt để tránh bị chặn.
    async with aiohttp.ClientSession(
        connector=connector, 
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"},
        trust_env=True
    ) as session:
        tasks = [quet_rss_async(url, session) for url in danh_sach_url_rss]
        results = await asyncio.gather(*tasks)
        
        for feed in results:
            if not feed: continue
            for tin in feed.entries:
                tieu_de = tin.get('title', '').strip()
                if not tieu_de or tieu_de in tieu_de_da_lay: continue
                
                ngay_dang_struct = tin.get('published_parsed')
                if ngay_dang_struct:
                    thoi_diem_dang = time.mktime(ngay_dang_struct)
                    if thoi_diem_hien_tai - thoi_diem_dang > giay_gioi_han: continue
                
                kho_tin_tho.append({
                    'tieu_de': tieu_de,
                    'mo_ta': tin.get('summary', ''),
                    'duong_dan': tin.get('link', '')
                })
                tieu_de_da_lay.add(tieu_de)
    
    tong_so_tin = len(kho_tin_tho)
    print(f"{GREEN}--- Đã lấy và lọc trùng: {tong_so_tin} tin Crypto mới.{RESET}")

    # LƯU FILE TẤT CẢ TIN ĐÃ TẢI (SAU BƯỚC 1)
    if kho_tin_tho:
        if not os.path.exists(THU_MUC_KET_QUA): os.makedirs(THU_MUC_KET_QUA)
        file_tat_ca = os.path.join(THU_MUC_KET_QUA, f"tat_ca_tin_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")
        with open(file_tat_ca, 'w', encoding='utf-8') as f:
            json.dump(kho_tin_tho, f, ensure_ascii=False, indent=2)
        print(f"{GREEN}--- Đã lưu danh sách tất cả tin đã tải: {RESET}{YELLOW}{file_tat_ca}{RESET}")

    if not kho_tin_tho: return

    # 3. Lọc đợt (Batching) bằng AI
    print(f"\n{CYAN}{BOLD}>>> Bước 2: AI (Gemini) đang lọc tin...{RESET}")
    ngu_canh_ai = cau_hinh.get('shark_context', '')
    api_key = cau_hinh.get('google_api_key')
    
    BATCH_SIZE = 150
    tin_phu_hop = []
    
    for start_idx in range(0, tong_so_tin, BATCH_SIZE):
        end_idx = min(start_idx + BATCH_SIZE, tong_so_tin)
        batch = kho_tin_tho[start_idx:end_idx]
        print(f"  > Xử lý đợt: {start_idx} đến {end_idx}...")
        
        ket_qua_ai = loc_tin_voi_gemini(batch, ngu_canh_ai, api_key=api_key)
        if ket_qua_ai:
            for phan_hoi in ket_qua_ai:
                if phan_hoi.get('phu_hop'):
                    idx = phan_hoi.get('index')
                    if idx is not None and idx < len(batch):
                        tin_phu_hop.append(batch[idx])
        
        if end_idx < tong_so_tin:
            # Nghỉ cố định 2s để tránh 429 cho Key Free
            print(f"  {YELLOW}...Đang nghỉ 2s giữa các đợt AI...{RESET}")
            time.sleep(2)

    # LƯU FILE TIN ĐÃ LỌC SAU KHI AI XỬ LÝ
    if tin_phu_hop:
        if not os.path.exists(THU_MUC_KET_QUA): os.makedirs(THU_MUC_KET_QUA)
        file_loc = os.path.join(THU_MUC_KET_QUA, f"tin_da_loc_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")
        with open(file_loc, 'w', encoding='utf-8') as f:
            json.dump(tin_phu_hop, f, ensure_ascii=False, indent=2)
        print(f"\n{GREEN}--- Đã lưu danh sách tin đã lọc (chưa bóc nội dung): {RESET}{YELLOW}{file_loc}{RESET}")

    # 4. Cào chi tiết và Xuất kết quả (ĐƠN LUỒNG TUẦN TỰ)
    if tin_phu_hop:
        print(f"\n{CYAN}{BOLD}>>> Bước 3: Đang bóc tách chi tiết {len(tin_phu_hop)} tin (Đơn luồng)...{RESET}")
        
        async with async_playwright() as p:
            trinh_duyet = await p.chromium.launch(headless=True)
            ngu_canh = await trinh_duyet.new_context()
            
            # Chạy tuần tự từng tin một
            for i, tin in enumerate(tin_phu_hop):
                print(f"  {YELLOW}[{i+1}/{len(tin_phu_hop)}] --- Đang bóc:{RESET} {tin['tieu_de'][:60]}...")
                tin['noi_dung'] = await lay_noi_dung_chi_tiet(tin['duong_dan'], ngu_canh)
            
            await trinh_duyet.close()

        if not os.path.exists(THU_MUC_KET_QUA): os.makedirs(THU_MUC_KET_QUA)
        
        # Xuất file TXT và JSON
        file_base = f"bao_cao_{datetime.now().strftime('%Y-%m-%d')}"
        file_txt = os.path.join(THU_MUC_KET_QUA, f"{file_base}.txt")
        file_json = os.path.join(THU_MUC_KET_QUA, f"{file_base}.json")
        
        # Xuất file JSON
        with open(file_json, 'w', encoding='utf-8') as f:
            json.dump(tin_phu_hop, f, ensure_ascii=False, indent=2)
            
        # Xuất file TXT nhưng nội dung là JSON (Theo yêu cầu user)
        with open(file_txt, 'w', encoding='utf-8') as f:
            json.dump(tin_phu_hop, f, ensure_ascii=False, indent=2)

        print(f"\n{GREEN}{BOLD}====================================================")
        print(f"HOÀN TẤT! Đã lưu báo cáo tại: {THU_MUC_KET_QUA}")
        print(f"===================================================={RESET}")

if __name__ == "__main__":
    asyncio.run(thuc_thi_he_thong())
