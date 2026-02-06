import json
import os
from google import genai
from google.genai import types
from pydantic import BaseModel

# Định nghĩa Schema bằng Pydantic
class TinPhanTich(BaseModel):
    index: int
    phu_hop: bool
    y_do_ca_map: str

def goi_gemini(noi_dung_prompt, api_key, format_json=True):
    """
    Sử dụng Google GenAI SDK mới nhất (google-genai) cho Gemini 2.5 Flash.
    Khởi tạo client với api_key được truyền vào.
    """
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
        print(f"!!! Lỗi hệ thống khi gọi Gemini (GenAI Client): {e}")
        return None

def loc_tin_voi_gemini(danh_sach_tin, ngu_canh, sentiment="negative", api_key=None):
    """
    Truyền danh sách tin để Gemini lọc dựa trên bối cảnh cá mập.
    """
    prompt = f"""
Ngữ cảnh: {ngu_canh}
Mục tiêu: Tìm các bài viết có sắc thái {sentiment}.

Hãy phân tích danh sách các bài viết dưới đây.
Phân tích theo góc nhìn: Liệu có sự thao túng của 'cá mập' truyền thông ở đây không?

Danh sách bài viết:
"""
    for i, tin in enumerate(danh_sach_tin):
        prompt += f"--- Bài {i} ---\nTiêu đề: {tin['tieu_de']}\nMô tả: {tin['mo_ta']}\n"

    return goi_gemini(prompt, api_key, format_json=True)
