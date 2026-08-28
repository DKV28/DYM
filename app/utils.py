"""Tiện ích xử lý file: chuyển PDF/ảnh thành danh sách ảnh PNG base64
để gửi cho ChatGPT vision API.
"""
import base64
import io

import fitz  # PyMuPDF
from PIL import Image

# Các đuôi file được hỗ trợ
ANH_HO_TRO = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
PDF_HO_TRO = {".pdf"}

# Giới hạn cạnh dài nhất của ảnh gửi lên (giảm dung lượng, tăng tốc)
MAX_CANH = 2200


def _nen_anh_base64(img: Image.Image) -> str:
    """Chuẩn hoá ảnh về RGB, thu nhỏ nếu quá lớn, trả về data URL base64 (PNG)."""
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    w, h = img.size
    canh_dai = max(w, h)
    if canh_dai > MAX_CANH:
        ty_le = MAX_CANH / canh_dai
        img = img.resize((int(w * ty_le), int(h * ty_le)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def pdf_sang_anh(du_lieu: bytes, so_trang_toi_da: int = 10) -> list[str]:
    """Render từng trang PDF thành ảnh base64. Zoom 2x cho nét chữ scan."""
    anh: list[str] = []
    doc = fitz.open(stream=du_lieu, filetype="pdf")
    try:
        ma_tran = fitz.Matrix(2, 2)  # phóng to 2x để OCR rõ hơn
        for i, trang in enumerate(doc):
            if i >= so_trang_toi_da:
                break
            pix = trang.get_pixmap(matrix=ma_tran)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            anh.append(_nen_anh_base64(img))
    finally:
        doc.close()
    return anh


def anh_sang_base64(du_lieu: bytes) -> list[str]:
    """Đọc file ảnh thành 1 ảnh base64."""
    img = Image.open(io.BytesIO(du_lieu))
    return [_nen_anh_base64(img)]


def file_sang_danh_sach_anh(
    ten_file: str, du_lieu: bytes, so_trang_toi_da: int = 10
) -> list[str]:
    """Từ tên file + nội dung, trả về danh sách ảnh base64 để gửi cho model.

    Ném ValueError nếu định dạng không hỗ trợ.
    """
    duoi = "." + ten_file.rsplit(".", 1)[-1].lower() if "." in ten_file else ""
    if duoi in PDF_HO_TRO:
        return pdf_sang_anh(du_lieu, so_trang_toi_da)
    if duoi in ANH_HO_TRO:
        return anh_sang_base64(du_lieu)
    raise ValueError(f"Định dạng không hỗ trợ: {duoi or ten_file}")
