-- =============================================================
-- Bảng lưu lịch sử hồ sơ nhân viên đã trích xuất
-- Chạy file này trong Supabase → SQL Editor → New query → Run
-- =============================================================

create table if not exists public.ho_so_nhan_vien (
  id                uuid primary key default gen_random_uuid(),
  ten_file          text,
  loai_tai_lieu     text,
  ho_ten            text,
  ngay_sinh         text,
  so_cccd           text,
  thong_tin_ca_nhan jsonb,
  hoc_van           jsonb default '[]'::jsonb,
  chung_chi         jsonb default '[]'::jsonb,
  ghi_chu           text,
  du_lieu           jsonb,          -- toàn bộ kết quả trích xuất (bản gốc)
  created_at        timestamptz not null default now()
);

-- Index để tìm nhanh theo tên và sắp xếp theo thời gian
create index if not exists idx_ho_so_ho_ten   on public.ho_so_nhan_vien (ho_ten);
create index if not exists idx_ho_so_so_cccd  on public.ho_so_nhan_vien (so_cccd);
create index if not exists idx_ho_so_created  on public.ho_so_nhan_vien (created_at desc);

-- Bật Row Level Security. App gọi bằng service_role key nên vẫn ghi/đọc bình thường,
-- còn anon/public key sẽ KHÔNG truy cập được (an toàn).
alter table public.ho_so_nhan_vien enable row level security;

-- (Không tạo policy cho anon => mặc định chặn mọi truy cập bằng anon key.)
