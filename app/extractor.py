"""Gọi ChatGPT (OpenAI) vision API để đọc tài liệu và trả về dữ liệu có cấu trúc."""
import json
import os

from openai import OpenAI

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


class ExtractorError(Exception):
    """Lỗi khi trích xuất."""


def _lay_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ExtractorError(
            "Chưa cấu hình OPENAI_API_KEY. Hãy tạo file .env từ .env.example và điền key."
        )
    return OpenAI(api_key=api_key)


def trich_xuat_tai_lieu(danh_sach_anh: list[str]) -> dict:
    """Gửi các ảnh của MỘT tài liệu cho model, trả về dict theo schema.

    danh_sach_anh: danh sách data URL base64 (mỗi phần tử một trang/ảnh).
    """
    if not danh_sach_anh:
        raise ExtractorError("Không có ảnh nào để đọc.")

    client = _lay_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o")

    noi_dung: list[dict] = [
        {
            "type": "text",
            "text": (
                "Đây là các trang của một tài liệu nhân viên. "
                "Hãy trích xuất thông tin theo schema."
            ),
        }
    ]
    for anh in danh_sach_anh:
        noi_dung.append({"type": "image_url", "image_url": {"url": anh, "detail": "high"}})

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": noi_dung},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": EXTRACTION_JSON_SCHEMA,
            },
        )
    except Exception as e:  # noqa: BLE001 - trả lỗi thân thiện cho người dùng
        raise ExtractorError(f"Lỗi gọi OpenAI API: {e}") from e

    noi_dung_tra = resp.choices[0].message.content
    if not noi_dung_tra:
        raise ExtractorError("Model không trả về nội dung.")

    try:
        return json.loads(noi_dung_tra)
    except json.JSONDecodeError as e:
        raise ExtractorError(f"Không đọc được JSON từ model: {e}") from e
