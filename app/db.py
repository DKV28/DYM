"""Kết nối Supabase (qua PostgREST API) để lưu & đọc lịch sử hồ sơ.

Dùng httpx gọi thẳng REST API của Supabase — nhẹ, hợp môi trường serverless,
không cần thêm thư viện SDK nặng.

Cấu hình qua biến môi trường:
    SUPABASE_URL          : ví dụ https://xxxx.supabase.co
    SUPABASE_SERVICE_KEY  : service_role key (chỉ dùng phía server, KHÔNG lộ ra web)
    SUPABASE_TABLE        : tên bảng (mặc định 'ho_so_nhan_vien')
"""
import os

import httpx

TABLE_MAC_DINH = "ho_so_nhan_vien"


class DBError(Exception):
    """Lỗi khi thao tác với database."""


def co_database() -> bool:
    """True nếu đã cấu hình đủ thông tin Supabase."""
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"))


def _cau_hinh() -> tuple[str, str, str]:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    table = os.getenv("SUPABASE_TABLE", TABLE_MAC_DINH)
    if not url or not key:
        raise DBError("Chưa cấu hình SUPABASE_URL / SUPABASE_SERVICE_KEY.")
    return url, key, table


def _headers(key: str, extra: dict | None = None) -> dict:
    h = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _endpoint(url: str, table: str) -> str:
    return f"{url}/rest/v1/{table}"


def luu_ho_so(ban_ghi: dict) -> dict | None:
    """Lưu MỘT bản ghi kết quả vào Supabase.

    ban_ghi: {ten_file, du_lieu, loi}. Chỉ lưu khi đọc thành công (có du_lieu).
    Trả về dòng vừa lưu, hoặc None nếu bỏ qua / chưa cấu hình DB.
    """
    if not co_database():
        return None
    d = ban_ghi.get("du_lieu")
    if not d:  # không lưu bản ghi lỗi
        return None

    url, key, table = _cau_hinh()
    ca_nhan = d.get("thong_tin_ca_nhan") or {}
    row = {
        "ten_file": ban_ghi.get("ten_file"),
        "loai_tai_lieu": d.get("loai_tai_lieu"),
        "ho_ten": ca_nhan.get("ho_ten"),
        "ngay_sinh": ca_nhan.get("ngay_sinh"),
        "so_cccd": ca_nhan.get("so_cccd"),
        "thong_tin_ca_nhan": ca_nhan,
        "hoc_van": d.get("hoc_van") or [],
        "chung_chi": d.get("chung_chi") or [],
        "ghi_chu": d.get("ghi_chu"),
        "du_lieu": d,
    }
    try:
        with httpx.Client(timeout=15) as client:
            r = client.post(
                _endpoint(url, table),
                headers=_headers(key, {"Prefer": "return=representation"}),
                json=row,
            )
            r.raise_for_status()
            data = r.json()
            return data[0] if isinstance(data, list) and data else data
    except httpx.HTTPError as e:
        raise DBError(f"Lỗi lưu Supabase: {e}") from e


def lay_lich_su(gioi_han: int = 200) -> list[dict]:
    """Lấy danh sách hồ sơ đã lưu, mới nhất trước."""
    if not co_database():
        return []
    url, key, table = _cau_hinh()
    try:
        with httpx.Client(timeout=15) as client:
            r = client.get(
                _endpoint(url, table),
                headers=_headers(key),
                params={
                    "select": "*",
                    "order": "created_at.desc",
                    "limit": str(gioi_han),
                },
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        raise DBError(f"Lỗi đọc Supabase: {e}") from e


def xoa_ho_so(ho_so_id: str) -> None:
    """Xoá một hồ sơ theo id."""
    if not co_database():
        raise DBError("Chưa cấu hình database.")
    url, key, table = _cau_hinh()
    try:
        with httpx.Client(timeout=15) as client:
            r = client.delete(
                _endpoint(url, table),
                headers=_headers(key),
                params={"id": f"eq.{ho_so_id}"},
            )
            r.raise_for_status()
    except httpx.HTTPError as e:
        raise DBError(f"Lỗi xoá Supabase: {e}") from e


def ban_ghi_tu_dong_db(row: dict) -> dict:
    """Chuyển 1 dòng DB về định dạng bản ghi mà exporter/frontend dùng."""
    return {
        "id": row.get("id"),
        "ten_file": row.get("ten_file"),
        "created_at": row.get("created_at"),
        "loi": None,
        "du_lieu": row.get("du_lieu")
        or {
            "loai_tai_lieu": row.get("loai_tai_lieu"),
            "thong_tin_ca_nhan": row.get("thong_tin_ca_nhan") or {},
            "hoc_van": row.get("hoc_van") or [],
            "chung_chi": row.get("chung_chi") or [],
            "ghi_chu": row.get("ghi_chu") or "",
        },
    }
