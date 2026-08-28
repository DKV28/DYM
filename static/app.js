// Trạng thái ứng dụng
let danhSachFile = []; // File[]
let ketQua = [];       // kết quả phiên đọc hiện tại
let lichSu = [];       // hồ sơ đã lưu (từ Supabase)
let coDatabase = false;

const $ = (id) => document.getElementById(id);

const NHAN_CA_NHAN = {
  ho_ten: "Họ tên", ngay_sinh: "Ngày sinh", gioi_tinh: "Giới tính",
  so_cccd: "Số CCCD/CMND", que_quan: "Quê quán", email: "Email", so_dien_thoai: "Số điện thoại",
};
const NHAN_HOC_VAN = {
  truong: "Trường", chuyen_nganh: "Chuyên ngành", bac_dao_tao: "Bậc đào tạo",
  xep_loai: "Xếp loại", nam_tot_nghiep: "Năm TN", hinh_thuc_dao_tao: "Hình thức",
};
const NHAN_CHUNG_CHI = {
  ten_chung_chi: "Tên chứng chỉ", so_hieu: "Số hiệu", noi_cap: "Nơi cấp",
  ngay_cap: "Ngày cấp", ngay_het_han: "Ngày hết hạn", linh_vuc: "Lĩnh vực",
};
const NHAN_LOAI = {
  bang_cap: "Bằng cấp", cv: "CV / Sơ yếu lý lịch",
  chung_chi_hanh_nghe: "Chứng chỉ hành nghề", khac: "Khác",
};

// ---------- Kiểm tra trạng thái API key ----------
async function kiemTraTrangThai() {
  try {
    const r = await fetch("/api/trang-thai");
    const d = await r.json();
    const el = $("trangThai");
    coDatabase = !!d.co_database;
    const dbBadge = coDatabase
      ? `<span class="badge">🗄️ Đã kết nối Supabase</span>`
      : `<span class="badge err">🗄️ Chưa cấu hình Supabase (không lưu lịch sử)</span>`;
    if (d.co_api_key) {
      el.innerHTML = `<span class="badge">✅ API · ${d.model}</span> ${dbBadge}`;
    } else {
      el.innerHTML =
        `<span class="badge err">⚠️ Chưa cấu hình OPENAI_API_KEY</span> ${dbBadge}`;
    }
  } catch (e) {
    $("trangThai").innerHTML = `<span class="badge err">Không kết nối được server</span>`;
  }
}

// ---------- Quản lý file ----------
function themFile(files) {
  for (const f of files) danhSachFile.push(f);
  veDanhSach();
}

function xoaFile(i) {
  danhSachFile.splice(i, 1);
  veDanhSach();
}

function dinhDangKichThuoc(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + " KB";
  return (bytes / 1024 / 1024).toFixed(1) + " MB";
}

function veDanhSach() {
  const khu = $("khuDanhSach");
  const ul = $("danhSachFile");
  $("soFile").textContent = danhSachFile.length;
  ul.innerHTML = "";
  danhSachFile.forEach((f, i) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div>
        <div class="fname">${escapeHtml(f.name)}</div>
        <div class="fmeta">${dinhDangKichThuoc(f.size)}</div>
      </div>
      <button class="rm" title="Xoá" data-i="${i}">✕</button>`;
    ul.appendChild(li);
  });
  ul.querySelectorAll(".rm").forEach((b) =>
    b.addEventListener("click", () => xoaFile(parseInt(b.dataset.i, 10)))
  );
  khu.classList.toggle("hidden", danhSachFile.length === 0);
  $("btnDoc").disabled = danhSachFile.length === 0;
}

// ---------- Gọi API đọc (từng file một — hợp với serverless/Vercel) ----------
async function b_atDauDoc() {
  if (danhSachFile.length === 0) return;
  $("khuTienTrinh").classList.remove("hidden");
  $("btnDoc").disabled = true;

  // Chuẩn bị khu kết quả (xoá cũ, hiện ra để append dần)
  ketQua = [];
  $("bangKetQua").innerHTML = "";
  $("khuKetQua").classList.remove("hidden");

  const tong = danhSachFile.length;
  for (let i = 0; i < tong; i++) {
    const f = danhSachFile[i];
    $("tienTrinhText").textContent =
      `Đang đọc bằng ChatGPT… (${i + 1}/${tong}): ${f.name}`;

    const fd = new FormData();
    fd.append("file", f);

    let bg;
    try {
      const r = await fetch("/api/trich-xuat-mot", { method: "POST", body: fd });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || `Lỗi ${r.status}`);
      }
      bg = await r.json();
    } catch (e) {
      bg = { ten_file: f.name, du_lieu: null, loi: "Lỗi khi gọi máy chủ: " + e.message };
    }
    ketQua.push(bg);
    $("bangKetQua").appendChild(veMotBlock(bg)); // hiện ngay từng kết quả
  }

  $("khuTienTrinh").classList.add("hidden");
  $("btnDoc").disabled = false;
}

// ---------- Hiển thị kết quả ----------
function veBangDoiTuong(nhan, obj) {
  const rows = Object.entries(nhan)
    .map(([k, label]) => {
      const v = (obj && obj[k]) ? escapeHtml(obj[k]) : "—";
      return `<div class="k">${label}</div><div class="v">${v}</div>`;
    })
    .join("");
  return `<div class="kv">${rows}</div>`;
}

function veBangMang(nhan, arr) {
  if (!arr || arr.length === 0) return `<p class="empty">Không có dữ liệu.</p>`;
  const keys = Object.keys(nhan);
  const thead = keys.map((k) => `<th>${nhan[k]}</th>`).join("");
  const tbody = arr
    .map((item) => "<tr>" + keys.map((k) => `<td>${item[k] ? escapeHtml(item[k]) : "—"}</td>`).join("") + "</tr>")
    .join("");
  return `<table class="mini"><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>`;
}

// Tạo 1 block hiển thị cho một bản ghi kết quả
function veMotBlock(bg) {
  const block = document.createElement("div");
  block.className = "doc-block";
  const d = bg.du_lieu;
  if (bg.loi || !d) {
    block.innerHTML = `
      <div class="doc-head">
        <span>${escapeHtml(bg.ten_file)}</span>
        <span class="tag err">Lỗi</span>
      </div>
      <div class="doc-body"><p class="err-msg">${escapeHtml(bg.loi || "Không có dữ liệu.")}</p></div>`;
  } else {
    const loai = NHAN_LOAI[d.loai_tai_lieu] || d.loai_tai_lieu || "Khác";
    block.innerHTML = `
      <div class="doc-head">
        <span>${escapeHtml(bg.ten_file)}</span>
        <span class="tag">${loai}</span>
      </div>
      <div class="doc-body">
        <div class="subh">Thông tin cá nhân</div>
        ${veBangDoiTuong(NHAN_CA_NHAN, d.thong_tin_ca_nhan)}
        <div class="subh">Học vấn / bằng cấp</div>
        ${veBangMang(NHAN_HOC_VAN, d.hoc_van)}
        <div class="subh">Chứng chỉ hành nghề</div>
        ${veBangMang(NHAN_CHUNG_CHI, d.chung_chi)}
        ${d.ghi_chu ? `<div class="subh">Ghi chú</div><p>${escapeHtml(d.ghi_chu)}</p>` : ""}
      </div>`;
  }
  return block;
}

// ---------- Tải file kết quả ----------
async function taiFile(url, tenMacDinh, duLieu) {
  if (!duLieu || duLieu.length === 0) {
    alert("Không có dữ liệu để tải.");
    return;
  }
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ket_qua: duLieu }),
  });
  if (!r.ok) {
    alert("Không tải được file.");
    return;
  }
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = tenMacDinh;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}

// ---------- Tab ----------
function chuyenTab(ten) {
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.tab === ten)
  );
  $("tabDoc").classList.toggle("hidden", ten !== "doc");
  $("tabLichSu").classList.toggle("hidden", ten !== "lichSu");
  if (ten === "lichSu") napLichSu();
}

// ---------- Lịch sử ----------
async function napLichSu() {
  const khu = $("bangLichSu");
  if (!coDatabase) {
    khu.innerHTML =
      `<p class="empty">Chưa cấu hình Supabase. Thêm SUPABASE_URL và SUPABASE_SERVICE_KEY để lưu lịch sử.</p>`;
    $("soLichSu").textContent = "0";
    return;
  }
  khu.innerHTML = `<p class="empty">Đang tải…</p>`;
  try {
    const r = await fetch("/api/lich-su");
    const d = await r.json();
    lichSu = d.ket_qua || [];
    veLichSu();
  } catch (e) {
    khu.innerHTML = `<p class="err-msg">Không tải được lịch sử: ${escapeHtml(e.message)}</p>`;
  }
}

function locLichSu() {
  const tu = ($("timLichSu").value || "").trim().toLowerCase();
  if (!tu) return lichSu;
  return lichSu.filter((bg) => {
    const ca = (bg.du_lieu && bg.du_lieu.thong_tin_ca_nhan) || {};
    return [bg.ten_file, ca.ho_ten, ca.so_cccd]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(tu));
  });
}

function veLichSu() {
  const khu = $("bangLichSu");
  const ds = locLichSu();
  $("soLichSu").textContent = lichSu.length;
  khu.innerHTML = "";
  if (ds.length === 0) {
    khu.innerHTML = `<p class="empty">Chưa có hồ sơ nào.</p>`;
    return;
  }
  ds.forEach((bg) => {
    const block = veMotBlock(bg);
    // thêm thời gian + nút xoá vào tiêu đề
    const head = block.querySelector(".doc-head");
    if (bg.created_at) {
      const t = new Date(bg.created_at).toLocaleString("vi-VN");
      const span = document.createElement("span");
      span.className = "ls-time";
      span.textContent = t;
      head.insertBefore(span, head.lastElementChild);
    }
    if (bg.id) {
      const btn = document.createElement("button");
      btn.className = "btn ghost mini";
      btn.textContent = "🗑️ Xoá";
      btn.addEventListener("click", () => xoaLichSu(bg.id));
      head.appendChild(btn);
    }
    khu.appendChild(block);
  });
}

async function xoaLichSu(id) {
  if (!confirm("Xoá hồ sơ này khỏi lịch sử?")) return;
  try {
    const r = await fetch(`/api/lich-su/${id}`, { method: "DELETE" });
    if (!r.ok) throw new Error("Lỗi máy chủ");
    lichSu = lichSu.filter((x) => x.id !== id);
    veLichSu();
  } catch (e) {
    alert("Không xoá được: " + e.message);
  }
}

// ---------- Tiện ích ----------
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// ---------- Gắn sự kiện ----------
function ganSuKien() {
  const dz = $("khuUpload");
  const input = $("inputFile");

  $("btnChon").addEventListener("click", (e) => { e.stopPropagation(); input.click(); });
  dz.addEventListener("click", () => input.click());
  dz.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") input.click(); });
  input.addEventListener("change", () => { themFile(input.files); input.value = ""; });

  ["dragenter", "dragover"].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("drag"); })
  );
  ["dragleave", "drop"].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("drag"); })
  );
  dz.addEventListener("drop", (e) => { if (e.dataTransfer?.files) themFile(e.dataTransfer.files); });

  $("btnXoaHet").addEventListener("click", () => { danhSachFile = []; veDanhSach(); });
  $("btnDoc").addEventListener("click", b_atDauDoc);
  $("btnTaiExcel").addEventListener("click", () => taiFile("/api/xuat-excel", "ho_so_nhan_vien.xlsx", ketQua));
  $("btnTaiJson").addEventListener("click", () => taiFile("/api/xuat-json", "ho_so_nhan_vien.json", ketQua));

  // Tabs
  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => chuyenTab(t.dataset.tab))
  );

  // Lịch sử
  $("btnLamMoiLS").addEventListener("click", napLichSu);
  $("timLichSu").addEventListener("input", veLichSu);
  $("btnLSExcel").addEventListener("click", () => taiFile("/api/xuat-excel", "lich_su_ho_so.xlsx", locLichSu()));
  $("btnLSJson").addEventListener("click", () => taiFile("/api/xuat-json", "lich_su_ho_so.json", locLichSu()));
}

ganSuKien();
kiemTraTrangThai();
