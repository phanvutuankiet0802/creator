# Mô-Đun UX Lâm Sàng & Y Tế Số Chuẩn NHS / WCAG 2.2 (Clinical UX Pack)

> Chỉ nạp tệp này khi thiết kế giao diện, dashboard, biểu mẫu, cảnh báo hoặc tài liệu liên quan đến **Y khoa, Chăm sóc sức khỏe, Hồ sơ bệnh nhân hoặc Hỗ trợ quyết định lâm sàng (CDS)**.

## 1. Nguyên Tắc Thiết Kế Y Tế Lấy An Toàn Làm Trọng Tâm (NHS Digital Service Manual + WCAG 2.2)
1. **Tương phản cao cho môi trường ánh sáng khắc nghiệt (phòng khám, trực đêm, in trắng đen):**
   - Dùng bộ token từ `tokens/medical_design_tokens.json` (chữ chính `#111111` trên `#FFFFFF` đạt `18.88:1` — vượt xa WCAG 2.2 AAA).
   - **Không dùng màu sắc làm tín hiệu duy nhất:** Mọi trạng thái bất thường (giá trị xét nghiệm cao/thấp, dị ứng, chống chỉ định) phải kèm đồng thời **nhãn chữ rõ ràng + biểu tượng + phân biệt hình khối/viền**.
2. **Phân Tầng Cảnh Báo Lâm Sàng (Chống Mệt Mỏi Cảnh Báo — *Alert Fatigue*):**
   - **Cấp 1 — Cờ Đỏ / Nguy Hiểm Tức Thời (*Red-Flag / Critical*):** Chống chỉ định tuyệt đối, tương tác thuốc nguy hiểm, dấu hiệu sinh tồn nguy kịch → banner nổi bật cố định ở đầu vùng nhìn, yêu cầu xác nhận có ý thức.
   - **Cấp 2 — Cần Lưu Ý (*Warning / Caution*):** Cần hiệu chỉnh liều (suy thận, thai kỳ, người cao tuổi), giá trị cận biên → callout hổ phách rõ ràng nhưng không chặn luồng đọc.
   - **Cấp 3 — Thông Tin Hỗ Trợ (*Info / Guideline Context*):** Tham chiếu phác đồ, nguồn bằng chứng → hiển thị gọn, có thể mở rộng khi cần (*progressive disclosure*).
3. **Hiển Thị Định Lượng & Liều Dùng Không Mơ Hồ (ISMP / NHS Medication Safety):**
   - Luôn ghi đơn vị chuẩn rõ ràng (`mg`, `mcg` thay vì ký hiệu dễ nhầm `µg` hoặc `u`, `mmol/L`, `mg/dL`), căn phải cột số trong bảng để mắt so sánh nhanh theo hàng dọc.
   - Ghi rõ **khoảng tham chiếu bình thường** ngay cạnh kết quả xét nghiệm và tách rõ giá trị ngoài ngưỡng.
   - Luôn tách biệt trực quan giữa **Dữ kiện bệnh nhân** (Fact), **Suy luận/Gợi ý của AI** (AI Draft — gắn nhãn minh bạch) và **Quyết định/Y lệnh của bác sĩ** (Clinician Action).
4. **Biểu Mẫu & Luồng Nhập Liệu Giảm Sai Sót (NHS One Thing Per Page / Chunking):**
   - Chia nhóm thông tin lâm sàng mạch lạc (Hành chính → Lý do/Bệnh sử → Khám & Dấu hiệu sinh tồn → Cận lâm sàng → Đánh giá & Kế hoạch).
   - Xác thực dữ liệu ngay tại trường nhập với thông báo lỗi cụ thể, nêu rõ định dạng hoặc dải sinh lý hợp lệ.
   - Mọi màn hình hỗ trợ lâm sàng cần có liên kết/chú thích ngắn chỉ rõ **nguồn guideline & thời điểm cập nhật** để bác sĩ tin cậy và kiểm chứng được.
