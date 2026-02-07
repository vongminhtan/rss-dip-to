import json
import os
import time
import re
from google import genai
from google.genai import types
from pydantic import BaseModel

# Định nghĩa Schema bằng Pydantic
class TinPhanTich(BaseModel):
    index: int
    phu_hop: bool

def goi_gemini(noi_dung_prompt, api_key, format_json=True):
    """
    Sử dụng Google GenAI SDK mới nhất (google-genai) cho Gemini 2.5 Flash.
    Bổ sung cơ chế tự động chờ (Retry) khi gặp lỗi Quota (429).
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if not api_key:
                print("!!! Thiếu API Key trong cấu hình.")
                return None
                
            client = genai.Client(api_key=api_key)
            model_name = "gemini-2.5-flash"
            
            # Cấu hình phản hồi dạng JSON với Schema Pydantic
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[TinPhanTich] if format_json else None,
            )
            
            # Gọi Gemini qua Client mới
            response = client.models.generate_content(
                model=model_name,
                contents=noi_dung_prompt,
                config=config
            )
            
            if not response.text:
                print("!!! Gemini không trả về nội dung.")
                return None

            if format_json:
                return json.loads(response.text)
            
            return response.text

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                # Tìm số giây cần chờ từ lỗi (nếu có), mặc định 60s
                wait_time = 60
                seconds_match = re.search(r'(\d+\.?\d*)s', error_msg)
                if seconds_match:
                    wait_time = max(60, float(seconds_match.group(1)) + 5)
                
                print(f"⚠️ Gặp lỗi Quota (429). Đang nghỉ giải lao {wait_time} giây trước khi thử lại (Lần {attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print(f"!!! Lỗi hệ thống khi gọi Gemini: {e}")
                if attempt == max_retries - 1: return None
                time.sleep(5)
    return None

def loc_tin_voi_gemini(danh_sach_tin, ngu_canh, sentiment="negative", api_key=None):
    """
    Truyền danh sách tin để Gemini lọc.
    """
    prompt = f"Ngữ cảnh phân tích: {ngu_canh}\n\n"
    prompt += "Hãy lọc ra các tin tức THỰC SỰ liên quan đến thị trường CRYPTO trong danh sách này (Chỉ trả về những tin phù hợp):\n"
    for i, tin in enumerate(danh_sach_tin):
        prompt += f"- Bài {i}: {tin['tieu_de']}\n"

    return goi_gemini(prompt, api_key, format_json=True)
