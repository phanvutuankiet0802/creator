# Quy Tắc Quét Độ Lệch Phiên Bản & Xung Đột Ngữ Cảnh Liên Skill (`references/cross_skill_drift_rules.md` v2.7)

## 1. Bảng Quy Tắc Quét Độ Lệch Phiên Bản Mở Rộng (`DRIFT-01 -> DRIFT-13`)

| Mã Quy Tắc | Quy chuẩn Hiện hành (`FB-19 -> FB-46 / LOCK-15`) | Dấu hiệu Tàn dư Quy chuẩn Cũ (`Legacy Drift Signature`) | Mức độ Cảnh báo |
| :--- | :--- | :--- | :--- |
| **DRIFT-01 (`FB-21`)** | Bố cục đề mục thân bài linh hoạt theo mạch bài học; chỉ cố định Lưu đồ tổng kết + Bảng số liệu ở cuối bài. | Bắt buộc cứng nhắc *"kết cấu 6 phần La Mã `I -> VI`"* cho mọi bài giảng/học liệu. | `S3 - Version Drift Warning` |
| **DRIFT-02 -> DRIFT-06** | Khung bài giảng `4–9 trang A4`, tỷ lệ chữ bôi đậm `<b>` `8–15%` (`<= 18%`, miễn trừ nhãn đề mục), ẩn nhãn nội bộ. | Cho phép tô đậm `10–25%` hoặc in nhãn `[Must know]` / `(Theo Vid)`. | `S2 - Ergonomics Drift` |
| **DRIFT-07 (`FB-30`, `FB-44`)** | Bắt buộc đếm ký tự 4 phương án A, B, C, D qua hàm `audit_mcq_option_length_parity` (`<= 1.35x` TB nhiễu, `<= 1.20x` nhiễu dài nhất, `longest_is_key_rate <= 10%`). | Thiếu hàm đếm ký tự thực tế `audit_mcq_option_length_parity`. | `S1 - Missing Quantitative Gate` |
| **DRIFT-08 -> DRIFT-12** | Khóa thứ tự giải đề 1-1 (`FB-32`), 2 tầng nguồn (`FB-33`), 12 lá WONCA (`FB-34`), `@tra-cuu` độc lập (`FB-40`), khử trùng lặp 3 nguồn & cỡ chữ 12pt SVG (`FB-43`). | Thiếu các cổng kiểm toán tương ứng trong code `.py`. | `S1 - Missing Gate` |
| **DRIFT-13 (`FB-46 / LOCK-15`)** | Kiến trúc 2 Chiều NBME (`90–100%` Khung Tình huống lâm sàng 6 bước lồng ghép `50% Quyết định/Pivot Point - 30% Điểm bản lề/Phân độ - 20% Cơ chế sâu & Hình ảnh`) + 5 cổng kiểm toán IWF. | Thiếu `audit_vignette_chronological_flow`, `audit_orth_2d_vignette_and_embedded_matrix`, `audit_forensic_distractor_profiling`, `audit_convergence_cues` hoặc `audit_inter_item_cueing_matrix` trong `@tao-de` / `@tham-dinh-su-pham`. | `S1 - Missing NBME 2D/IWF Gate` |

- **`DRIFT-14` (`S1` - `FB-52 / LOCK-20`):** `@import-md` thiếu `reconcile_and_normalize_cartridge_metadata`, `audit_post_mount_cartridge_integrity` hoặc `ensure_page_or_slide_markers_and_lock10`.


## DRIFT-15 & DRIFT-16 (LOCK-23 / FB-55)
- **DRIFT-15:** Kiểm tra đồng bộ `decolumnize_and_denoise_source_markdown`, `audit_sentence_completeness_and_syntax`, `audit_statistical_trivia_overload` và `extract_mandatory_procedural_and_clinical_figures` giữa `@soan-bai-giang` v8.0, `@tham-dinh-su-pham` v5.0 và `@giao-trinh-tong-hop` v5.3.
- **DRIFT-16:** Cấm bỏ qua `visual_anchor_audit` / `audit_rendered_diagrams_visual_and_geometry` trong `pdf_lecture_builder.py` và cấm để `lecture_html` rỗng trong `master_audit_gate.py`.
