> **Beta 1.19 supersession (current):** The old `<=10% correct option longest` mandate is withdrawn. Do not game option lengths or insert filler. Use the live builder/QA checks for per-option conspicuous cues and gross batch skew, plus counterfactual patient-dependence and expert distractor review. Older FB-44/LOCK-14 text below is retained as historical record only.

# Danh Mục Thư Viện Tham Chiếu Chuẩn Y Khoa & Quy Chuẩn Học Thuật (`references/medical_ebm_standards.md` v8.1)

## 1. Hệ Thống Sách Giáo Khoa Y Khoa Chuẩn Thế Giới (Core Textbooks)
- **Nội khoa:** *Harrison's Principles of Internal Medicine (22e)*; *CMDT*
- **Ngoại khoa:** *Sabiston Textbook of Surgery*; *Schwartz's Principles of Surgery*
- **Sản Phụ khoa:** *Williams Obstetrics (26e)*; *Williams Gynecology (4e)*
- **Nhi khoa:** *Nelson Textbook of Pediatrics (22e)*
- **Sinh lý - Giải phẫu bệnh - Dược lý:** *Guyton and Hall Medical Physiology (15e)*; *Robbins & Kumar Basic Pathology (11e)*; *Goodman & Gilman's Pharmacology*

## 2. Hệ Thống Phác Đồ & Guidelines Thực Hành Lâm Sàng
- **Cấp độ Quốc gia (Việt Nam):** Bộ Y tế Việt Nam (`kcb.vn`), các Thông tư/QCVN hiện hành, Phác đồ BV Từ Dũ, BV Hùng Vương, BV Chợ Rẫy, BV Bạch Mai, BV Nhi Đồng 1 & 2.
- **Cấp độ Quốc tế:** WHO, NICE, CDC/NIOSH, UpToDate, AMBOSS, AHA/ACC, ESC, GOLD, GINA, ADA, KDIGO, ACOG, FIGO, RCOG.

## 3. Tiêu Chuẩn Khảo Thí Y Khoa Quốc Tế NBME/USMLE & Liên Minh Team-Agent Đối Kháng (`FB-19` -> `FB-46 / LOCK-15`)
- **Chuẩn Khảo thí Quốc tế:** *NBME Item-Writing Guide (Case, Swanson, Paniagua & Swygert)*, *Haladyna, Downing & Rodriguez (2002)*, *Tarrant & Ware (2006/2008)*, *Tavakol & Dennick (AMEE Guide No. 66 & No. 72)*, *Wiggins & McTighe Understanding by Design (3 Concentric Circles)*.
- **Kiến trúc 2 Chiều NBME (`audit_orth_2d_vignette_and_embedded_matrix` & `audit_vignette_chronological_flow` - `FB-46 / LOCK-15`):** Lấy Tình huống lâm sàng 6 bước tuyến tính làm khung bao chứa cho `90% – 100%` câu hỏi toàn đề, lồng ghép `50%` Quyết định/Pivot Point + `30%` Điểm bản lề/Phân độ + `20%` Cơ chế sâu 2–3 bước & Đọc hình ảnh vào bên trong ca bệnh.
- **5 Cổng Kiểm Toán IWF & Cổng Đếm Ký Tự Đáp Án (`<= 10%` Câu Đúng Dài Nhất):** Chạy `audit_forensic_distractor_profiling`, `audit_convergence_cues`, `audit_inter_item_cueing_matrix`, `audit_option_grammatical_and_category_homogeneity` và `audit_mcq_option_length_parity` (`longest_is_key_rate <= 10%`).
