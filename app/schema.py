"""Định nghĩa cấu trúc dữ liệu cần trích xuất từ tài liệu nhân viên.

Cấu trúc này được dùng cho:
- Prompt gửi cho model (mô tả các trường cần đọc)
- JSON Schema ép model trả về đúng định dạng (chuyển sang responseSchema của Gemini)
- Xuất Excel (tên cột tiếng Việt)
"""

# JSON Schema mô tả kết quả trích xuất cho một tài liệu.
# extractor.py sẽ chuyển schema này sang định dạng responseSchema của Gemini.
EXTRACTION_JSON_SCHEMA = {
    "name": "ho_so_nhan_vien",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "loai_tai_lieu": {
                "type": "string",
                "description": (
                    "Phân loại tài liệu: một trong "
                    "'bang_cap', 'cv', 'chung_chi_hanh_nghe', 'khac'."
                ),
                "enum": ["bang_cap", "cv", "chung_chi_hanh_nghe", "khac"],
            },
            "thong_tin_ca_nhan": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "ho_ten": {"type": "string"},
                    "ngay_sinh": {"type": "string", "description": "Định dạng dd/mm/yyyy nếu có."},
                    "gioi_tinh": {"type": "string"},
                    "so_cccd": {"type": "string", "description": "Số CCCD/CMND/hộ chiếu."},
                    "que_quan": {"type": "string"},
                    "email": {"type": "string"},
                    "so_dien_thoai": {"type": "string"},
                },
                "required": [
                    "ho_ten",
                    "ngay_sinh",
                    "gioi_tinh",
                    "so_cccd",
                    "que_quan",
                    "email",
                    "so_dien_thoai",
                ],
            },
            "hoc_van": {
                "type": "array",
                "description": "Danh sách bằng cấp / quá trình học tập.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "truong": {"type": "string"},
                        "chuyen_nganh": {"type": "string"},
                        "bac_dao_tao": {
                            "type": "string",
                            "description": "Ví dụ: Trung cấp, Cao đẳng, Đại học, Thạc sĩ, Tiến sĩ.",
                        },
                        "xep_loai": {"type": "string", "description": "Ví dụ: Giỏi, Khá, Xuất sắc."},
                        "nam_tot_nghiep": {"type": "string"},
                        "hinh_thuc_dao_tao": {
                            "type": "string",
                            "description": "Ví dụ: Chính quy, Tại chức, Từ xa.",
                        },
                    },
                    "required": [
                        "truong",
                        "chuyen_nganh",
                        "bac_dao_tao",
                        "xep_loai",
                        "nam_tot_nghiep",
                        "hinh_thuc_dao_tao",
                    ],
                },
            },
            "chung_chi": {
                "type": "array",
                "description": "Danh sách chứng chỉ hành nghề / chứng chỉ chuyên môn.",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "ten_chung_chi": {"type": "string"},
                        "so_hieu": {"type": "string", "description": "Số hiệu/số chứng chỉ."},
                        "noi_cap": {"type": "string"},
                        "ngay_cap": {"type": "string", "description": "Định dạng dd/mm/yyyy nếu có."},
                        "ngay_het_han": {
                            "type": "string",
                            "description": "Định dạng dd/mm/yyyy, để trống nếu vô thời hạn.",
                        },
                        "linh_vuc": {"type": "string", "description": "Lĩnh vực/phạm vi hành nghề."},
                    },
                    "required": [
                        "ten_chung_chi",
                        "so_hieu",
                        "noi_cap",
                        "ngay_cap",
                        "ngay_het_han",
                        "linh_vuc",
                    ],
                },
            },
            "ghi_chu": {
                "type": "string",
                "description": "Thông tin khác đáng chú ý, hoặc lý do nếu không đọc được.",
            },
        },
        "required": [
            "loai_tai_lieu",
            "thong_tin_ca_nhan",
            "hoc_van",
            "chung_chi",
            "ghi_chu",
        ],
    },
}

# Nhãn tiếng Việt cho các cột khi xuất Excel.
NHAN_CA_NHAN = {
    "ho_ten": "Họ tên",
    "ngay_sinh": "Ngày sinh",
    "gioi_tinh": "Giới tính",
    "so_cccd": "Số CCCD/CMND",
    "que_quan": "Quê quán",
    "email": "Email",
    "so_dien_thoai": "Số điện thoại",
}

NHAN_HOC_VAN = {
    "truong": "Trường",
    "chuyen_nganh": "Chuyên ngành",
    "bac_dao_tao": "Bậc đào tạo",
    "xep_loai": "Xếp loại",
    "nam_tot_nghiep": "Năm tốt nghiệp",
    "hinh_thuc_dao_tao": "Hình thức đào tạo",
}

NHAN_CHUNG_CHI = {
    "ten_chung_chi": "Tên chứng chỉ",
    "so_hieu": "Số hiệu",
    "noi_cap": "Nơi cấp",
    "ngay_cap": "Ngày cấp",
    "ngay_het_han": "Ngày hết hạn",
    "linh_vuc": "Lĩnh vực",
}

NHAN_LOAI_TAI_LIEU = {
    "bang_cap": "Bằng cấp",
    "cv": "CV / Sơ yếu lý lịch",
    "chung_chi_hanh_nghe": "Chứng chỉ hành nghề",
    "khac": "Khác",
}
