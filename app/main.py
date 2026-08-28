"""App đọc dữ liệu bằng cấp / CV / chứng chỉ hành nghề của nhân viên.

Backend FastAPI:
- POST /api/trich-xuat : nhận nhiều file, đọc bằng ChatGPT, trả JSON kết quả
- POST /api/xuat-excel : nhận JSON kết quả, trả file .xlsx
- POST /api/xuat-json  : nhận JSON kết quả, trả file .json
- GET  /               : giao diện web
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from . import db
from .exporter import xuat_excel, xuat_json
from .extractor import ExtractorError, trich_xuat_tai_lieu
from .utils import file_sang_danh_sach_anh

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Đọc hồ sơ nhân viên", version="1.0.0")

MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "10"))
# Giới hạn dung lượng mỗi file: 20 MB
MAX_FILE_BYTES = 20 * 1024 * 1024


@app.get("/", response_class=HTMLResponse)
def trang_chu() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/api/trang-thai")
def trang_thai() -> dict:
    """Cho frontend biết đã cấu hình API key hay chưa."""
    return {
        "co_api_key": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
        "co_database": db.co_database(),
    }


async def _doc_mot_file(f: UploadFile) -> dict:
    """Đọc MỘT file, trả về bản ghi {ten_file, du_lieu, loi}, tự lưu DB nếu có."""
    ban_ghi: dict = {"ten_file": f.filename, "du_lieu": None, "loi": None}
    try:
        du_lieu = await f.read()
        if len(du_lieu) > MAX_FILE_BYTES:
            raise ValueError("File vượt quá 20 MB.")
        anh = file_sang_danh_sach_anh(f.filename, du_lieu, MAX_PDF_PAGES)
        ban_ghi["du_lieu"] = trich_xuat_tai_lieu(anh)
    except (ValueError, ExtractorError) as e:
        ban_ghi["loi"] = str(e)
    except Exception as e:  # noqa: BLE001
        ban_ghi["loi"] = f"Lỗi không xác định: {e}"

    # Tự lưu vào Supabase (không chặn kết quả nếu lưu lỗi)
    if ban_ghi["du_lieu"]:
        try:
            luu = db.luu_ho_so(ban_ghi)
            if luu and luu.get("id"):
                ban_ghi["id"] = luu["id"]
                ban_ghi["da_luu"] = True
        except db.DBError as e:
            ban_ghi["canh_bao_db"] = str(e)
    return ban_ghi


@app.post("/api/trich-xuat-mot")
async def trich_xuat_mot(file: UploadFile = File(...)) -> dict:
    """Đọc MỘT file — dùng cho môi trường serverless (Vercel) để tránh timeout.

    Frontend gọi endpoint này lần lượt cho từng file và hiện tiến trình.
    """
    return await _doc_mot_file(file)


@app.post("/api/trich-xuat")
async def trich_xuat(files: list[UploadFile] = File(...)) -> dict:
    """Đọc nhiều file trong một request (tiện khi chạy local, không giới hạn thời gian)."""
    if not files:
        raise HTTPException(status_code=400, detail="Chưa chọn file nào.")
    ket_qua = [await _doc_mot_file(f) for f in files]
    return {"ket_qua": ket_qua}


@app.post("/api/xuat-excel")
async def api_xuat_excel(payload: dict) -> Response:
    ket_qua = payload.get("ket_qua")
    if not isinstance(ket_qua, list) or not ket_qua:
        raise HTTPException(status_code=400, detail="Không có dữ liệu để xuất.")
    data = xuat_excel(ket_qua)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="ho_so_nhan_vien.xlsx"'},
    )


@app.post("/api/xuat-json")
async def api_xuat_json(payload: dict) -> Response:
    ket_qua = payload.get("ket_qua")
    if not isinstance(ket_qua, list) or not ket_qua:
        raise HTTPException(status_code=400, detail="Không có dữ liệu để xuất.")
    data = xuat_json(ket_qua)
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="ho_so_nhan_vien.json"'},
    )


@app.get("/api/lich-su")
def lich_su() -> dict:
    """Lấy danh sách hồ sơ đã lưu trong Supabase."""
    if not db.co_database():
        return {"co_database": False, "ket_qua": []}
    try:
        rows = db.lay_lich_su()
    except db.DBError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {
        "co_database": True,
        "ket_qua": [db.ban_ghi_tu_dong_db(r) for r in rows],
    }


@app.delete("/api/lich-su/{ho_so_id}")
def xoa_lich_su(ho_so_id: str) -> dict:
    """Xoá một hồ sơ đã lưu."""
    if not db.co_database():
        raise HTTPException(status_code=400, detail="Chưa cấu hình database.")
    try:
        db.xoa_ho_so(ho_so_id)
    except db.DBError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True}


# Phục vụ file tĩnh (JS/CSS)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
