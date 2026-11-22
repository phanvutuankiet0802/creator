# Sổ Tay Quy Chuẩn Học Liệu & Xuất Bản Tài Liệu (Lazy-Loaded Archive)

> Chỉ nạp tệp này khi người dùng yêu cầu **soạn bài giảng PDF A4, bộ Flashcard, ngân hàng câu hỏi MCQ/MEQ hoặc tổng hợp học liệu đa nguồn**. Tệp này bảo toàn 100% tinh hoa quy chuẩn xuất bản học liệu từ các phiên bản trước mà không làm nhiễu các dự án phần mềm/ứng dụng thông thường.

## 1. Quy Cách Tách Dòng Ngắn & Phân Cấp 4 Tầng Đầu Dòng (Bài Giảng A4)
- Mỗi gạch đầu dòng bắt buộc **dưới 4 dòng** trên khổ A4 cỡ chữ 12pt (`<= 42–45 từ`), mục tiêu lý tưởng **`1–2 dòng` (`10–28 từ`)**.
- Khi ý dài hoặc có ý con, hạ cấp theo đúng **4 tầng ký hiệu giảm dần**:
  1. Tầng 1 (`ul.lvl1`): Gạch đầu dòng (`– `)
  2. Tầng 2 (`ul.lvl2`): Chấm đen (`•` / `disc`)
  3. Tầng 3 (`ul.lvl3`): Chấm trắng (`○` / `circle`)
  4. Tầng 4 (`ul.lvl4`): Chấm vuông (`▪` / `square`)

## 2. Kiểm Toán Cỡ Chữ 2 Chiều & Tái Bố Cục Sơ Đồ Zigzag 2 Cột
- Kiểm toán đồng thời tỷ lệ thu phóng ngang và dọc: `scale_eff = min(1.0, 480 / W_px, 390 / H_px)` (ứng với khung A4 và `max-height: 390pt`).
- Khi lưu đồ tổng kết có `>= 4` bước hoặc `H_px > 580px`, chuyển sang **Lưới Zigzag 2 Cột Gọn (`W = 920px, H <= 560px`)** để chữ hiển thị thực tế trên giấy A4 luôn đạt `>= 12pt` rõ nét và giữ trọn bài giảng gọn trong `4–9 trang A4`.

## 3. Kiến Trúc Flashcard Kép 2 Chế Độ Chống Ngộp Nhận Thức
- Kết hợp 2 nhóm thẻ kèm thanh lọc chuyển đổi trực tiếp (`#fcModeBar`):
  - **Thuộc bài nhanh (`core_recall`, Bloom 1–2, `30%–45%`):** Câu hỏi 1 dòng trực diện về định nghĩa, mốc số liệu, phân loại, tam chứng/tứ chứng, liều thuốc để ôn trong 5 giây.
  - **Tư duy & Cơ chế (`clinical_reasoning`, Bloom 3–4, `55%–70%`):** Tình huống hạt nhân, giải thích cơ chế nhân–quả và phân biệt bẫy *Near-Miss*.

## 4. Hợp Nhất Đa Nguồn, Đề Thi & Trình Bày Học Thuật
- **Đồ thị Giải thích Nhân–Quả:** `85%–90%` dung lượng tập trung kiến thức cốt lõi (`P0/P1`), không đặt lịch sử y học mở đầu trang 1; chốt cuối bài bằng sơ đồ tổng kết + bảng tóm lược thực hành.
- **Lọc nhiễu nguồn đầu vào:** Loại bỏ mục tài liệu tham khảo/metadata trước khi đếm mệnh đề kiến thức; báo cáo độ phủ nguồn khách quan khi hợp nhất nhiều tài liệu.
- **Cân bằng độ dài phương án MCQ 2 đầu:** Tránh lộ đáp án đúng qua độ dài (`longest_is_key_rate <= 10%`, `shortest_is_key_rate <= 25%`); giữ đúng thứ tự 1-1 giữa đề và lời giải (`Kendall's tau == 1.0`).
- **Tín hiệu thị giác & Tối ưu tệp HTML:** Tô đậm có kỷ luật `8%–15%` (miễn trừ nhãn đề mục `<li><b>Nhãn:</b>`); không lặp dữ liệu Base64 gây phình HTML (`< 450 KB` cho gói thẻ/quiz độc lập); không để rò rỉ cây ASCII (`│├└─`) hoặc nhãn nội bộ ra bản in.
- **Mô hình điều phối sản xuất học liệu đa thành phẩm (4 Milestones):**
  - *Milestone 1:* Đồng bộ đa nguồn, lập đồ thị nhân–quả và trích xuất hình ảnh gốc.
  - *Milestone 2 (+ nhánh tái bố cục sơ đồ):* Biên soạn bài giảng PDF A4, tách dòng 4 cấp, đảm bảo cỡ chữ sơ đồ `>= 12pt`.
  - *Milestone 3:* Sản xuất song song bộ học liệu lượng giá (Flashcard / Quiz / Tự luận MEQ).
  - *Milestone 4:* Kiểm định độc lập đa chiều (Nội dung / UI-UX / Chuyên môn / QA-QC) và xuất bản sạch.
