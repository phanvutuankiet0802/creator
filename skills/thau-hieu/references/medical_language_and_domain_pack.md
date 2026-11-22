# Mô-Đun Y Khoa & Chuẩn Ngôn Ngữ Lâm Sàng Tiếng Việt (Medical Domain Pack)

Chỉ nạp tài liệu này khi dự án, sản phẩm hoặc câu hỏi có yếu tố **Y khoa, Y tế số, Dữ liệu lâm sàng hoặc Giáo dục y khoa**.

## 1. Nguyên Tắc An Toàn Lâm Sàng & Bằng Chứng (Đồng Thuận HealthBench + G-AMIE + EBM)
- **Giám sát bởi Bác sĩ / Con người (*Clinician-in-the-Loop / G-AMIE*):** Hệ thống AI đóng vai trò tổng hợp, suy luận hỗ trợ và cảnh báo cờ đỏ (*red flags*); quyết định chẩn đoán, kê đơn và can thiệp cuối cùng thuộc về nhân viên y tế có thẩm quyền.
- **Ràng buộc nguồn bằng chứng (*Guideline Grounding*):** Ưu tiên phác đồ/hướng dẫn uy tín (WHO, NICE, BMJ Best Practice, AHA/ACC, ESC, Bộ Y tế Việt Nam, sách giáo khoa kinh điển). Khi có xung đột giữa nguồn quốc tế và nguồn địa phương, nêu rõ bối cảnh áp dụng thay vì tự ý gộp mù.
- **Chuyển dịch thống kê sang ý nghĩa lâm sàng:** Không ném thô các chỉ số nghiên cứu (`LR+`, `LR-`, `95% CI`, `p-value`) vào giao diện thực hành hay tài liệu người dùng nếu không đi kèm ý nghĩa hành động thực tế (khi trừ khi người dùng đang phân tích thống kê/nghiên cứu).
- **Minh bạch độ bất định & Cờ đỏ:** Nếu thiếu dữ kiện lâm sàng quan trọng (tuổi, thai kỳ, chức năng thận, dị ứng, dấu hiệu sinh tồn), chủ động hỏi hoặc gắn cờ giới hạn phạm vi; luôn đẩy các dấu hiệu nguy hiểm (*red flags*) lên vị trí dễ thấy nhất.
- **Bảo mật dữ liệu bệnh nhân (PHI/PII Hygiene):** Tuyệt đối không ghi cứng thông tin định danh bệnh nhân thật vào mã nguồn, log, ví dụ hay tệp mẫu.

## 2. Chống Dịch Máy Triệu Chứng Học & Thuật Ngữ Y Khoa Tiếng Việt
Khi viết giao diện, tài liệu, cảnh báo hoặc phản hồi y khoa tiếng Việt, bắt buộc dùng thuật ngữ lâm sàng chuẩn thay cho cụm dịch máy từ tiếng Anh:

| Cụm dịch máy cần tránh | Thuật ngữ lâm sàng tiếng Việt chuẩn |
| :--- | :--- |
| đau nhọn (*sharp pain*) | **đau chói / đau nhói** |
| đau cùn (*dull pain*) | **đau âm ỉ** |
| nhạy cảm dội (*rebound tenderness*) | **phản ứng dội (Blumberg dương tính)** |
| bảo vệ thành bụng (*abdominal guarding*) | **đề kháng thành bụng** |
| tử cung gỗ (*woody uterus*) | **tử cung co cứng như gỗ** |
| đau lan ra / bức xạ (*radiating pain*) | **đau lan (lên vai, ra sau lưng...)** |
| ngắn hơi (*shortness of breath*) | **khó thở** |
| đánh trống ngực chạy đua (*racing heart*) | **hồi hộp đánh trống ngực / nhịp tim nhanh** |

## 3. Phân Tầng Nội Dung Y Khoa Khi Thiết Kế Sản Phẩm / Tài Liệu
- **Kênh Cơ chế Nhân–Quả (`Causal Mechanism`):** Giải thích *Tại sao / Sinh lý bệnh → Biểu hiện → Nguyên tắc xử trí* bằng câu ngắn mạch lạc.
- **Kênh Ngưỡng Quyết Định & Hành Động (`Decision Thresholds & Actions`):** Đưa mốc chẩn đoán, phân độ, liều dùng, chống chỉ định vào bảng cấu trúc rõ ràng, dễ quét nhanh.
- **Kênh Ngoại vi / Mô tả (`Descriptive Satellite`):** Tách dịch tễ chi tiết, lịch sử y học hoặc số liệu phụ ra phần tham khảo bổ sung để không che khuất phần cốt lõi lâm sàng.
