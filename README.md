# 📄 App đọc hồ sơ nhân viên (bằng cấp / CV / chứng chỉ hành nghề)

Web app trích xuất thông tin từ **file scan** (PDF/ảnh) của nhân viên bằng **ChatGPT API** (model vision).
Kết quả xem trực tiếp trên web và tải về dưới dạng **Excel** hoặc **JSON**.

## Tính năng

- Upload **nhiều file cùng lúc** (kéo–thả), hỗ trợ **PDF scan** và **ảnh JPG/PNG/…**
- Tự động chuyển PDF thành ảnh và gửi cho ChatGPT đọc
- Trích xuất:
  - **Thông tin cá nhân**: họ tên, ngày sinh, giới tính, số CCCD, quê quán, email, SĐT
  - **Học vấn / bằng cấp**: trường, chuyên ngành, bậc đào tạo, xếp loại, năm tốt nghiệp, hình thức
  - **Chứng chỉ hành nghề**: tên, số hiệu, nơi cấp, ngày cấp, ngày hết hạn, lĩnh vực
- Xuất **Excel** (3 sheet: Tổng hợp, Học vấn, Chứng chỉ) và **JSON**
- Giao diện tiếng Việt

## Yêu cầu

- Python 3.10+
- Một API key OpenAI: https://platform.openai.com/api-keys

## Cài đặt

```bash
# 1. Tạo môi trường ảo (khuyến nghị)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Cài thư viện
pip install -r requirements.txt

# 3. Cấu hình API key
cp .env.example .env
# Mở file .env và điền OPENAI_API_KEY của bạn
```

## Chạy app

```bash
uvicorn app.main:app --reload --port 8000
```

Mở trình duyệt: http://localhost:8000

## Cách dùng

1. Kéo–thả (hoặc chọn) các file bằng cấp / CV / chứng chỉ.
2. Bấm **🔍 Bắt đầu đọc** — chờ ChatGPT xử lý.
3. Xem kết quả từng tài liệu, rồi bấm **Tải Excel** hoặc **Tải JSON**.

## Cấu hình (file `.env`)

| Biến | Ý nghĩa | Mặc định |
|------|---------|----------|
| `OPENAI_API_KEY` | API key OpenAI (bắt buộc) | — |
| `OPENAI_MODEL` | Model vision dùng để đọc | `gpt-4o` |
| `MAX_PDF_PAGES` | Số trang PDF tối đa mỗi file | `10` |

## Cấu trúc dự án

```
app/
  main.py       # FastAPI: các API endpoint + phục vụ web
  extractor.py  # Gọi ChatGPT vision, ép JSON theo schema
  schema.py     # Định nghĩa trường dữ liệu + nhãn tiếng Việt
  utils.py      # Chuyển PDF/ảnh → ảnh base64
  exporter.py   # Xuất Excel + JSON
static/
  index.html    # Giao diện
  style.css
  app.js
```

## Lưu ý bảo mật

- API key chỉ nằm trong file `.env` phía server, **không lộ ra trình duyệt**.
- File upload **không lưu** trên server, chỉ xử lý trong bộ nhớ.
- Nội dung tài liệu được gửi tới OpenAI để đọc — cân nhắc với dữ liệu nhạy cảm.
```
