# Tháp Kiểm Thử Chủ Động 6 Tầng, Săn Lỗi Tiên Đoán 18 Kịch Bản, Kiến Trúc 2 Chiều NBME, Cổng Đếm Ký Tự Đáp Án & Kiểm Chứng Tri Thức A/B (`references/testing_pyramid_and_bug_taxonomy.md` v2.7)

## 1. Phân Loại Mức Độ Nghiêm Trọng Của Lỗi (`Defect Severity Taxonomy - FB-28 -> FB-46 / LOCK-15`)

| Cấp độ | Định danh | Tiêu chí Kỹ thuật, Sư phạm & Giao diện | Hành động Cưỡng chế (`Gate Action`) |
| :--- | :--- | :--- | :--- |
| **S1** | **Blocker (Chặn đứng)** | Lỗi cú pháp Python (`SyntaxError`), thiếu tệp `SKILL.md` (`ERR-07`), rò rỉ mẫu IOC 4 chấm `A.B.C.D` (`ERR-21`), rơi rớt bất kỳ hàm/tính năng cũ nào khi nâng cấp (`LOCK-01..15`), tỷ lệ đáp án đúng dài nhất toàn đề `> 10%` (`SYSTEMIC_LONGEST_KEY_BIAS_FB30`), **tỷ lệ Khung Tình huống lâm sàng `< 85–90%` (`LOCK15_UNIVERSAL_VIGNETTE_SHELL_LOW`), đảo kết quả xét nghiệm lên trước khám thực thể (`LOCK15_VIGNETTE_CHRONOLOGY_INVERSION`), dùng câu hỏi âm tính (`LOCK15_ZERO_NEGATIVE_PHRASING_VIOLATION`) hoặc tự bịa chỉ số tâm trắc học giả (`LOCK15_PSYCHOMETRIC_HALLUCINATION`)**. | **NỔ DÂY BẪY (`TRIPWIRE_TRIGGERED - NO-GO`):** Cấm gọi `skills:save_skill` / `skills:update_skill` hoặc `google:show_file`. Bắt buộc quay vòng lặp sửa lỗi (`Loopback`). |
| **S2** | **Critical (Nghiêm trọng)** | Tri thức mới làm giảm điểm chất lượng (`Candidate < Baseline`), đáp án đúng dài vượt ngưỡng ký tự (`> 1.35x` TB nhiễu hoặc `> 1.20x` nhiễu dài nhất), **lỗi hội tụ thành phần (`LOCK15_CONVERGENCE_CUE_DETECTED`) hoặc lộ thông tin liên câu (`INTER_ITEM_CUEING`)**, lộ nhãn `[Must know]` / `(Theo Vid)`. | **CHẶN NGHIỆM THU (`NO-GO`):** Xuất phiếu `Loopback Remediation Ticket` kèm số liệu định lượng chính xác. |
| **S3** | **Major (Đáng kể)** | Độ lệch phiên bản tiềm ẩn (`Version Drift`) ở các skill vệ tinh đang khóa bảo vệ (`DRIFT-01`). | **CHO PHÉP CÓ ĐIỀU KIỆN (`CONDITIONAL GO`).** |
| **S4** | **Minor (Nhỏ / Tối ưu)** | Gợi ý rút gọn docstring, tối ưu hóa tốc độ chạy script. | **ĐẠT (`GO`).** |
