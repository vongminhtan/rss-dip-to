import feedparser
import json
import os
import ssl
import asyncio
import time
import random
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from utils_gemini import loc_tin_voi_gemini

# Load environment variables từ file .env
load_dotenv()

# Mã màu ANSI cho Console
BLUE = "\033[34m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Danh sách cấu hình giả lập thiết bị (User-Agent + Viewport)
THIET_BI_GIA_LAP = [
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36", "vp": {"width": 1920, "height": 1080}, "is_mobile": False},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36", "vp": {"width": 1440, "height": 900}, "is_mobile": False},
    {"ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1", "vp": {"width": 390, "height": 844}, "is_mobile": True},
    {"ua": "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36", "vp": {"width": 360, "height": 800}, "is_mobile": True},
    {"ua": "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", "vp": {"width": 820, "height": 1180}, "is_mobile": True}
]

# Thiết lập SSL để tránh lỗi chứng chỉ khi tải RSS
if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
    getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

# Đường dẫn các file (Xác định dựa trên vị trí của script)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_NGUON_RSS = os.path.join(BASE_DIR, 'rss_links.json')
FILE_NGUON_RSS_TEST = os.path.join(BASE_DIR, 'rss_links_test.json')
THU_MUC_KET_QUA = os.path.join(BASE_DIR, 'ket_qua')

async def quet_rss_async(url, session, sem):
    """Tải và parse RSS bất đồng bộ với giới hạn luồng và cơ chế Retry cho lỗi DNS."""
    async with sem:
        max_retries = 2
        for i in range(max_retries + 1):
            try:
                # Staggered delay để không dồn dập DNS query
                await asyncio.sleep(random.uniform(0.5, 1.5))
                async with session.get(url, timeout=15, ssl=False) as response:
                    html = await response.text()
                    return feedparser.parse(html)
            except Exception as e:
                error_msg = str(e)
                # Nếu là lỗi DNS (gaierror), thử lại sau khi nghỉ
                if "gaierror" in error_msg or "nodename nor servname" in error_msg:
                    if i < max_retries:
                        await asyncio.sleep(2 * (i + 1))
                        continue
                
                if "Header value is too long" in error_msg:
                    print(f"{YELLOW}--- Nguồn {url} phản hồi header quá dài (Bỏ qua RSS này/Yahoo)...{RESET}")
                else:
                    print(f"{RED}!!! Lỗi khi quét {url}: {error_msg[:100]}{RESET}")
                return None

async def lay_noi_dung_chi_tiet(url, trinh_duyet):
    """Bóc tách nội dung với logic Human-like và xử lý Redirect Google News"""
    ngu_canh = None
    trang = None
    try:
        # Chọn ngẫu nhiên thiết bị
        thiet_bi = random.choice(THIET_BI_GIA_LAP)
        
        # Tạo context mới cho mỗi trang để có User-Agent riêng
        ngu_canh = await trinh_duyet.new_context(
            user_agent=thiet_bi['ua'],
            viewport=thiet_bi['vp'],
            is_mobile=thiet_bi['is_mobile']
        )
        trang = await ngu_canh.new_page()
        
        # --- Human Behavior Simulator ---
        # 1. Random delay trước khi truy cập
        await asyncio.sleep(random.uniform(1, 4))
        
        # 2. Truy cập (Google News cần timeout lâu hơn một chút)
        timeout_val = 60000 if "news.google.com" in url else 45000
        # Sử dụng domcontentloaded thay vì networkidle để tránh bị treo bởi trackers
        response = await trang.goto(url, wait_until="domcontentloaded", timeout=timeout_val)
        
        # 3. Xử lý đặc biệt cho Google News redirect
        if "news.google.com" in url:
            # Đợi thêm vài giây để trang đích load hẳn sau redirect
            await asyncio.sleep(random.uniform(3, 5))
            # Đợi đến khi URL không còn chứa google.com (nếu có thể)
            try:
                await trang.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass

        if response and response.status == 200:
            # 4. Giả lập cuộn trang (Human scroll)
            for _ in range(random.randint(1, 3)):
                await trang.mouse.wheel(0, random.randint(300, 700))
                await asyncio.sleep(random.uniform(0.5, 1.2))
            
            noi_dung_tho = await trang.evaluate("() => document.body.innerText")
            
            # Kiểm tra xem có thực sự lấy được nội dung không
            if noi_dung_tho and len(noi_dung_tho.strip()) > 500:
                return noi_dung_tho.strip()
        
        return "Không thể bóc tách nội dung."
    except Exception as e:
        # print(f"Lỗi khi bóc {url}: {str(e)}") # Có thể bật khi cần debug sâu
        return "Không thể bóc tách nội dung."
    finally:
        if trang: await trang.close()
        if ngu_canh: await ngu_canh.close()

def thong_ke_loi(tin_phu_hop):
    error_links = []
    for entry in tin_phu_hop:
        content = entry.get("noi_dung")
        if not content or content == "Không thể bóc tách nội dung." or content.strip() == "":
            error_links.append(entry.get("duong_dan"))
    
    # Luôn lưu file link lỗi nếu có thư mục kết quả
    if os.path.exists(THU_MUC_KET_QUA):
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_error = os.path.join(THU_MUC_KET_QUA, f"error_links_{timestamp}.txt")
        with open(file_error, 'w', encoding='utf-8') as f:
            for link in error_links:
                f.write(f"{link}\n")
        print(f"{CYAN}--- Đã lưu danh sách link lỗi tại: {RESET}{YELLOW}{file_error}{RESET}")

    if error_links:
        print(f"\n{RED}{BOLD}⚠️ THỐNG KÊ LỖI BÓC TÁCH:{RESET}")
        print(f"Tổng số link lỗi: {len(error_links)} / {len(tin_phu_hop)}")
        
        # Thống kê theo domain
        from collections import Counter
        domains = [link.split('/')[2] if '://' in link else link for link in error_links]
        domain_counts = Counter(domains)
        
        print(f"{YELLOW}Chi tiết theo domain:{RESET}")
        for domain, count in domain_counts.items():
            print(f"  - {domain}: {count}")
        
        print(f"\n{YELLOW}Danh sách link lỗi (Xem chi tiết trong file error_links_list.txt){RESET}")
    else:
        print(f"\n{GREEN}✅ Chúc mừng! Không có link nào bị lỗi bóc tách.{RESET}")

async def thuc_thi_he_thong():
    print(f"\n{BLUE}{BOLD}====================================================")
    print("   BẮT ĐẦU CHẠY HỆ THỐNG PHÂN TÍCH TIN TỨC (LOCAL)")
    print(f"===================================================={RESET}")

    # 1. Đọc cấu hình từ .env
    if not os.path.exists(FILE_NGUON_RSS):
        print(f"!!! Thiếu file nguồn RSS ({FILE_NGUON_RSS})")
        return

    # Hàm hỗ trợ lấy config: Ưu tiên ENV > Default
    def get_conf(key, default=None):
        env_key = key.upper()
        val = os.getenv(env_key)
        if val is not None:
            # Chuyển đổi kiểu dữ liệu cho phù hợp
            if isinstance(default, bool):
                return val.lower() in ('true', '1', 'yes')
            if isinstance(default, int):
                try: return int(val)
                except: return default
            return val
        return default

    test_mode = get_conf('test_mode', False)
    
    # CHẾ ĐỘ TEST: Ưu tiên đọc từ file rss_links_test.json
    if test_mode:
        if os.path.exists(FILE_NGUON_RSS_TEST):
            with open(FILE_NGUON_RSS_TEST, 'r', encoding='utf-8') as f:
                danh_sach_url_rss = json.load(f)
            print(f"{YELLOW}--- [TEST MODE] Đã tải {len(danh_sach_url_rss)} nguồn từ {FILE_NGUON_RSS_TEST}{RESET}")
        else:
            with open(FILE_NGUON_RSS, 'r', encoding='utf-8') as f:
                danh_sach_url_rss = json.load(f)[:3]
            print(f"{YELLOW}--- [TEST MODE] Không tìm thấy file test, lấy 3 nguồn đầu tiên.{RESET}")
    else:
        with open(FILE_NGUON_RSS, 'r', encoding='utf-8') as f:
            danh_sach_url_rss = json.load(f)

    kho_tin_tho = []
    tieu_de_da_lay = set()
    so_ngay_gioi_han = get_conf('limit_days', 2)
    thoi_diem_hien_tai = time.time()
    giay_gioi_han = so_ngay_gioi_han * 24 * 60 * 60

    # 2. Tải và Lọc trùng (Lấy tuần tự để tránh lỗi mạng/DNS)
    print(f"\n{CYAN}{BOLD}>>> Bước 1: Đang quét RSS từ {len(danh_sach_url_rss)} nguồn (Tuần tự)...{RESET}")
    
    # Cấu hình Connector tối ưu cho Mac: Bật DNS Cache và bỏ SSL
    connector = aiohttp.TCPConnector(ssl=False, use_dns_cache=True, ttl_dns_cache=300)
    sem_rss = asyncio.Semaphore(1) # Chế độ tuần tự (Semaphore=1)
    
    async with aiohttp.ClientSession(
        connector=connector, 
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"},
        trust_env=True
    ) as session:
        for i, url in enumerate(danh_sach_url_rss):
            print(f"  [{i+1}/{len(danh_sach_url_rss)}] Quét nguồn: {url[:60]}...", end=" ", flush=True)
            feed = await quet_rss_async(url, session, sem_rss)
            
            if not feed:
                print(f"{RED}Thất bại{RESET}")
                continue
            
            so_tin_moi_nguon = 0
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
                so_tin_moi_nguon += 1
            
            if so_tin_moi_nguon > 0:
                print(f"{GREEN}Thành công ({so_tin_moi_nguon} tin mới){RESET}")
            else:
                print(f"{YELLOW}Thành công (0 tin mới){RESET}")
    
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
    ngu_canh_ai = get_conf('shark_context', '')
    
    api_key = get_conf('google_api_key', 'NHAP_KEY_O_DAY')
    if not api_key or api_key == "NHAP_KEY_O_DAY":
        print(f"{RED}!!! Lỗi: Chưa cấu hình GOOGLE_API_KEY trong file .env hoặc config.yaml{RESET}")
        return
    
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

    # 4. Cào chi tiết và Xuất kết quả (ĐA LUỒNG TỐI ƯU)
    if tin_phu_hop:
        so_luong_luong = get_conf('crawl_concurrency', 5)
        print(f"\n{CYAN}{BOLD}>>> Bước 3: Đang bóc tách chi tiết {len(tin_phu_hop)} tin (Sử dụng {so_luong_luong} luồng)...{RESET}")
        
        # Giới hạn số lượng luồng cào cùng lúc (Semaphore)
        limit = asyncio.Semaphore(so_luong_luong)

        async def cào_tin_với_limit(index, tin_obj, browser_instance):
            async with limit:
                # Thêm staggered delay để không khởi tạo tất cả cùng 1 lúc
                await asyncio.sleep(random.uniform(1, 3))
                
                print(f"  {YELLOW}[{index+1}/{len(tin_phu_hop)}] --- Đang bóc:{RESET} {tin_obj['tieu_de'][:60]}...")
                tin_obj['noi_dung'] = await lay_noi_dung_chi_tiet(tin_obj['duong_dan'], browser_instance)

        async with async_playwright() as p:
            # Chạy có giao diện hoặc không tùy headless
            trinh_duyet = await p.chromium.launch(headless=True)
            
            tasks = [cào_tin_với_limit(i, tin, trinh_duyet) for i, tin in enumerate(tin_phu_hop)]
            await asyncio.gather(*tasks)
            
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

        # Thống kê lỗi trực tiếp lên console
        thong_ke_loi(tin_phu_hop)

if __name__ == "__main__":
    asyncio.run(thuc_thi_he_thong())
