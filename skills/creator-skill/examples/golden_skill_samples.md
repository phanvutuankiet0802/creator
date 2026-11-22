> **Beta 1.19 supersession (current):** The old `<=10% correct option longest` mandate is withdrawn. Do not game option lengths or insert filler. Use the live builder/QA checks for per-option conspicuous cues and gross batch skew, plus counterfactual patient-dependence and expert distractor review. Older FB-44/LOCK-14 text below is retained as historical record only.

# Kho Mẫu Đối Chứng Chuẩn Vàng - @creator-skill v8.1 (`examples/golden_skill_samples.md`)

Minh họa cách thiết kế quy tắc sư phạm, kết nối khoang dữ liệu thay nóng `@nap-data`, vận hành Chuỗi Bàn Giao Đối Kháng 5 Agent (`@thau-hieu` $\rightarrow$ `@creator-skill` [PM/Dev/Meta-Auditor] $\rightarrow$ `@ui-ux` $\rightarrow$ `@tham-dinh-su-pham` $\rightarrow$ `@qa-qc`) và kiểm toán tự động bằng Python theo chuẩn **`FB-19` -> `FB-46 / LOCK-15`**:

- **Mẫu 1 (`FB-22`, `FB-27`, `FB-43` - Khử Trùng Lặp 3 Nguồn `Vid ∪ Slide ∪ PNT` & Nén Nhân–Quả Trong Ngoặc Đơn Trong Bài Giảng PDF 4–9 Trang A4).**
- **Mẫu 2 (`FB-21`, `FB-23`, `FB-30`, `FB-32`, `FB-44`, `FB-46 / LOCK-15` - Kiến Trúc 2 Tầng Nguồn, Ma Trận 2 Chiều NBME `90–100% Khung Tình Huống Lâm Sàng + Lồng Ghép 50-30-20` & Cổng Đếm Ký Tự Đáp Án `<= 10%`):**
  - **Tầng 1:** Phủ kín 100% nội dung và 4 Nhóm Nguyên Liệu Gốc của Bài giảng vừa biên soạn làm nền tảng bắt buộc.
  - **Tầng 2:** Quét trực tiếp `_Vid.md` $\rightarrow$ `_Slide.md` $\rightarrow$ `_PNT.md` trong `@nap-data` theo thứ tự ưu tiên **`Vid >> Slide >> PNT`** (khóa Vòng 3 `<= 15%`).
  - **Kiến trúc 2 Chiều NBME:** Lấy Tình huống lâm sàng 6 bước tuyến tính làm khung bao chứa cho `90% – 100%` câu hỏi toàn đề, lồng ghép `50%` Quyết định/Pivot Point + `30%` Điểm bản lề/Phân độ + `20%` Cơ chế sâu 2–3 bước & Đọc hình ảnh vào bên trong ca bệnh, đồng thời chạy `audit_mcq_option_length_parity` (`longest_is_key_rate <= 10%`) và 5 cổng kiểm toán IWF.
- **Mẫu 3 (`FB-25`, `FB-26`, `FB-31` - Động Cơ Kép `@nap-data` + `NotebookLM API` & Cặp đôi `@ocr-text` ⇄ `@import-md`).**
- **Mẫu 4 (`FB-28 -> FB-46` - Chuỗi Bàn Giao Đối Kháng 5 Agent & Kiểm Toán Chéo PM Meta-Audit):** Chạy `audit_rule_to_code_parity_and_qa_blindspots` và `run_team_agent_handoff_pipeline` kèm Pre-Mortem Fuzzing 18 kịch bản lỗi trước khi ghi vào Sổ cái Phiên bản (`LOCK-01..15`).
