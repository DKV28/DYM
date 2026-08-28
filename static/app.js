// Trạng thái ứng dụng
let danhSachFile = []; // File[]
let ketQua = [];       // kết quả trích xuất trả về từ server

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
    if (d.co_api_key) {
      el.innerHTML = `<span class="badge">✅ Đã cấu hình API · model: ${d.model}</span>`;
    } else {
      el.innerHTML = `<span class="badge err">⚠️ Chưa cấu hình OPENAI_API_KEY trong file .env</span>`;
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

// ---------- Gọi API đọc ----------
async function b_atDauDoc() {
  if (danhSachFile.length === 0) return;
  $("khuTienTrinh").classList.remove("hidden");
  $("khuKetQua").classList.add("hidden");
  $("btnDoc").disabled = true;
  $("tienTrinhText").textContent =
    `Đang đọc ${danhSachFile.length} tài liệu bằng ChatGPT… (có thể mất vài chục giây)`;

  const fd = new FormData();
  for (const f of danhSachFile) fd.append("files", f);

  try {
    const r = await fetch("/api/trich-xuat", { method: "POST", body: fd });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || `Lỗi ${r.status}`);
    }
    const d = await r.json();
    ketQua = d.ket_qua || [];
    veKetQua();
  } catch (e) {
    alert("Có lỗi khi đọc tài liệu: " + e.message);
  } finally {
    $("khuTienTrinh").classList.add("hidden");
    $("btnDoc").disabled = false;
  }
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

function veKetQua() {
  const khu = $("bangKetQua");
  khu.innerHTML = "";
  if (ketQua.length === 0) {
    khu.innerHTML = `<p class="empty">Không có kết quả.</p>`;
  }
  ketQua.forEach((bg) => {
    const block = document.createElement("div");
    block.className = "doc-block";
    const d = bg.du_lieu;
    if (bg.loi) {
      block.innerHTML = `
        <div class="doc-head">
          <span>${escapeHtml(bg.ten_file)}</span>
          <span class="tag err">Lỗi</span>
        </div>
        <div class="doc-body"><p class="err-msg">${escapeHtml(bg.loi)}</p></div>`;
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
    khu.appendChild(block);
  });
  $("khuKetQua").classList.remove("hidden");
}

// ---------- Tải file kết quả ----------
async function taiFile(url, tenMacDinh) {
  if (ketQua.length === 0) return;
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ket_qua: ketQua }),
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
  $("btnTaiExcel").addEventListener("click", () => taiFile("/api/xuat-excel", "ho_so_nhan_vien.xlsx"));
  $("btnTaiJson").addEventListener("click", () => taiFile("/api/xuat-json", "ho_so_nhan_vien.json"));
}

ganSuKien();
kiemTraTrangThai();
