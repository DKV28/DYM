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

## 🗄️ Lưu lịch sử với Supabase

App tự động **lưu mỗi hồ sơ đã đọc** vào Supabase và có tab **Lịch sử** để xem lại,
tìm kiếm, xoá, và xuất Excel/JSON. Nếu không cấu hình, app vẫn chạy bình thường
(chỉ không lưu lịch sử).

**Thiết lập:**

1. Tạo project tại https://supabase.com (miễn phí).
2. Vào **SQL Editor → New query**, dán nội dung file [`supabase/schema.sql`](supabase/schema.sql) và bấm **Run** để tạo bảng.
3. Vào **Project Settings → API**, lấy:
   - **Project URL** → `SUPABASE_URL`
   - **service_role key** (mục *Project API keys*) → `SUPABASE_SERVICE_KEY`
4. Điền vào `.env` (chạy local) hoặc **Environment Variables** trên Vercel.

> ⚠️ **Bảo mật:** `service_role` key có toàn quyền, chỉ dùng phía server (backend).
> App không bao giờ gửi key này ra trình duyệt. Bảng đã bật RLS nên `anon` key
> không truy cập được dữ liệu.

**Dữ liệu lưu:** thông tin cá nhân, học vấn, chứng chỉ, tên file, thời gian —
*không lưu file scan gốc*.

## 🚀 Deploy lên Vercel

App đã cấu hình sẵn để chạy trên Vercel (serverless Python).

**Các bước:**

1. Push code lên GitHub (đã xong nếu bạn thấy repo này).
2. Vào https://vercel.com → **Add New… → Project** → chọn repo này.
3. Vercel tự nhận diện (`vercel.json` + `api/index.py`). Bấm **Deploy**.
4. Vào **Settings → Environment Variables**, thêm:
   - `OPENAI_API_KEY` = key của bạn *(bắt buộc)*
   - `OPENAI_MODEL` = `gpt-4o` *(tuỳ chọn)*
   - `MAX_PDF_PAGES` = `10` *(tuỳ chọn)*
   - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` = nếu dùng lịch sử *(tuỳ chọn)*
5. Bấm **Redeploy** để nạp biến môi trường.

> **Quan trọng về giới hạn thời gian (timeout):**
> Vercel giới hạn thời gian mỗi request. Vì ChatGPT đọc ảnh khá lâu, app được
> thiết kế để **xử lý từng file một** (frontend gọi API lần lượt) nên mỗi request
> chỉ đọc 1 tài liệu → an toàn hơn nhiều.
> - **Hobby (miễn phí):** tối đa **60 giây/request**. Đủ cho hầu hết 1 tài liệu,
>   nhưng PDF nhiều trang có thể vẫn quá lâu.
> - **Pro:** có thể nâng `maxDuration` trong `vercel.json` lên tới **300 giây**.
>
> Nếu gặp timeout với file nhiều trang, hãy giảm `MAX_PDF_PAGES`, hoặc cắt bớt trang.

**Deploy bằng CLI (tuỳ chọn):**
```bash
npm i -g vercel
vercel            # deploy preview
vercel --prod     # deploy production
```

## Cấu hình (file `.env`)

| Biến | Ý nghĩa | Mặc định |
|------|---------|----------|
| `OPENAI_API_KEY` | API key OpenAI (bắt buộc) | — |
| `OPENAI_MODEL` | Model vision dùng để đọc | `gpt-4o` |
| `MAX_PDF_PAGES` | Số trang PDF tối đa mỗi file | `10` |
| `SUPABASE_URL` | URL project Supabase (tuỳ chọn) | — |
| `SUPABASE_SERVICE_KEY` | service_role key (tuỳ chọn) | — |
| `SUPABASE_TABLE` | Tên bảng | `ho_so_nhan_vien` |

## Cấu trúc dự án

```
api/
  index.py      # Điểm vào cho Vercel (ASGI)
app/
  main.py       # FastAPI: các API endpoint + phục vụ web
  extractor.py  # Gọi ChatGPT vision, ép JSON theo schema
  schema.py     # Định nghĩa trường dữ liệu + nhãn tiếng Việt
  utils.py      # Chuyển PDF/ảnh → ảnh base64
  exporter.py   # Xuất Excel + JSON
  db.py         # Lưu/đọc lịch sử qua Supabase
supabase/
  schema.sql    # SQL tạo bảng lịch sử
static/
  index.html    # Giao diện
  style.css
  app.js
vercel.json     # Cấu hình deploy Vercel
```

## Lưu ý bảo mật

- API key chỉ nằm trong file `.env` phía server, **không lộ ra trình duyệt**.
- File upload **không lưu** trên server, chỉ xử lý trong bộ nhớ.
- Nội dung tài liệu được gửi tới OpenAI để đọc — cân nhắc với dữ liệu nhạy cảm.
```
