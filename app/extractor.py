"""Gọi Google Gemini API để đọc tài liệu và trả về dữ liệu có cấu trúc.

Dùng REST API qua httpx (nhẹ, hợp serverless). Gemini có bậc miễn phí
(lấy key tại https://aistudio.google.com/apikey).
"""
import json
import os

import httpx

from .schema import EXTRACTION_JSON_SCHEMA

SYSTEM_PROMPT = """Bạn là trợ lý trích xuất dữ liệu nhân sự.
Nhiệm vụ: đọc kỹ ảnh scan tài liệu của nhân viên (bằng cấp, CV, chứng chỉ hành nghề)
và trích xuất thông tin thành JSON theo đúng schema được yêu cầu.

Nguyên tắc:
- Chỉ ghi thông tin THỰC SỰ có trong tài liệu. Không bịa, không suy đoán.
- Nếu một trường không tìm thấy, để chuỗi rỗng "".
- Giữ nguyên dấu tiếng Việt, viết hoa/thường đúng như tài liệu.
- Ngày tháng chuẩn hoá về dd/mm/yyyy khi có thể.
- Nhiều trang có thể thuộc cùng một người: gộp lại thành một kết quả.
- Với bằng cấp, mỗi bằng là một phần tử trong 'hoc_van'.
- Với chứng chỉ hành nghề, mỗi chứng chỉ là một phần tử trong 'chung_chi'.
"""

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class ExtractorError(Exception):
    """Lỗi khi trích xuất."""


def _to_gemini_schema(node: dict) -> dict:
    """Chuyển JSON Schema (kiểu OpenAI) sang schema Gemini chấp nhận.

    - Kiểu chữ HOA (OBJECT/STRING/ARRAY...)
    - Bỏ các khoá Gemini không hỗ trợ (additionalProperties, strict).
    """
    out: dict = {}
    if "type" in node:
        out["type"] = node["type"].upper()
    if "description" in node:
        out["description"] = node["description"]
    if "enum" in node:
        out["enum"] = node["enum"]
    if "properties" in node:
        out["properties"] = {k: _to_gemini_schema(v) for k, v in node["properties"].items()}
        # giữ thứ tự trường ổn định
        out["propertyOrdering"] = list(node["properties"].keys())
    if "required" in node:
        out["required"] = node["required"]
    if "items" in node:
        out["items"] = _to_gemini_schema(node["items"])
    return out


GEMINI_SCHEMA = _to_gemini_schema(EXTRACTION_JSON_SCHEMA["schema"])


def _tach_data_url(data_url: str) -> tuple[str, str]:
    """Từ 'data:image/png;base64,XXXX' -> ('image/png', 'XXXX')."""
    if data_url.startswith("data:") and ";base64," in data_url:
        header, b64 = data_url.split(";base64,", 1)
        mime = header[len("data:"):] or "image/png"
        return mime, b64
    return "image/png", data_url


def trich_xuat_tai_lieu(danh_sach_anh: list[str]) -> dict:
    """Gửi các ảnh của MỘT tài liệu cho Gemini, trả về dict theo schema.

    danh_sach_anh: danh sách data URL base64 (mỗi phần tử một trang/ảnh).
    """
    if not danh_sach_anh:
        raise ExtractorError("Không có ảnh nào để đọc.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ExtractorError(
            "Chưa cấu hình GEMINI_API_KEY. Lấy key miễn phí tại "
            "https://aistudio.google.com/apikey rồi thêm vào .env."
        )
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    parts: list[dict] = [
        {
            "text": (
                "Đây là các trang của một tài liệu nhân viên. "
                "Hãy trích xuất thông tin theo schema."
            )
        }
    ]
    for anh in danh_sach_anh:
        mime, b64 = _tach_data_url(anh)
        parts.append({"inline_data": {"mime_type": mime, "data": b64}})

    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": GEMINI_SCHEMA,
        },
    }

    url = f"{API_BASE}/{model}:generateContent"
    try:
        with httpx.Client(timeout=120) as client:
            r = client.post(url, params={"key": api_key}, json=body)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        chi_tiet = ""
        try:
            chi_tiet = e.response.json().get("error", {}).get("message", "")
        except Exception:  # noqa: BLE001
            chi_tiet = e.response.text[:300]
        raise ExtractorError(f"Lỗi gọi Gemini API ({e.response.status_code}): {chi_tiet}") from e
    except httpx.HTTPError as e:
        raise ExtractorError(f"Lỗi kết nối Gemini API: {e}") from e

    # Kiểm tra bị chặn hoặc không có kết quả
    feedback = data.get("promptFeedback") or {}
    if feedback.get("blockReason"):
        raise ExtractorError(f"Tài liệu bị Gemini chặn: {feedback.get('blockReason')}")

    candidates = data.get("candidates") or []
    if not candidates:
        raise ExtractorError("Gemini không trả về kết quả.")

    parts_out = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts_out)
    if not text:
        raise ExtractorError("Gemini trả về nội dung rỗng.")

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ExtractorError(f"Không đọc được JSON từ Gemini: {e}") from e
