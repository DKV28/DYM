"""Điểm vào cho Vercel Python runtime.

Vercel nhận diện biến ASGI tên `app` trong file thuộc thư mục /api và phục vụ nó.
Toàn bộ request được rewrite về đây (xem vercel.json).
"""
import sys
from pathlib import Path

# Đảm bảo import được package `app` ở thư mục gốc dự án
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402  (phải nằm sau khi chỉnh sys.path)

# Vercel dùng biến `app` này làm ASGI application
__all__ = ["app"]
