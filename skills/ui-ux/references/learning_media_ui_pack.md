# Quy Chuẩn UI/UX Học Liệu PDF A4 & Thẻ Nhớ Tương Tác (Learning Media UI Pack)

> Chỉ nạp tệp này khi thiết kế hoặc kiểm toán **bài giảng PDF A4, sơ đồ học thuật, Flashcard tương tác hoặc ứng dụng trắc nghiệm/tự luận**. Tệp này bảo toàn 100% các quy chuẩn công thái học học liệu chuyên sâu từ các phiên bản trước.

## 1. Công Thái Học Tách Dòng Ngắn & Phân Cấp 4 Tầng Ký Hiệu Đầu Dòng (A4 12pt)
- Mỗi gạch đầu dòng bắt buộc **dưới 4 dòng** trên khổ A4 cỡ chữ `12pt` (`<= 42–45 từ`), khuyến khích **`1–2 dòng` (`10–28 từ`)**.
- Hệ thống phân cấp 4 tầng giảm dần trong CSS ấn phẩm A4:
  - **Tầng 1 (`ul.lvl1 > li`):** `list-style-type: "–  "` (Gạch đầu dòng)
  - **Tầng 2 (`ul.lvl2 > li`):** `list-style-type: disc` (Chấm đen `•`)
  - **Tầng 3 (`ul.lvl3 > li`):** `list-style-type: circle` (Chấm trắng `○`)
  - **Tầng 4 (`ul.lvl4 > li`):** `list-style-type: square` (Chấm vuông `▪`)

## 2. Tín Hiệu Thị Giác Mayer & Cỡ Chữ Sơ Đồ 2 Chiều
- **Tô đậm có kỷ luật:** Giữ tỷ lệ từ tô đậm trong khoảng `8%–15%` (`<= 18%`), cụm ngắn `1–6 từ`, **miễn trừ 100%** nhãn đề mục `<li><b>Nhãn:</b>` khỏi hạn ngạch tô đậm.
- **Kiểm toán cỡ chữ sơ đồ 2 chiều (`W × H`):** Tính đồng thời tỷ lệ co ngang (`480pt / W_px`) và co dọc (`390pt / H_px`) để bảo đảm cỡ chữ hiển thị thực tế trên mặt giấy A4 `>= 12pt`. Sơ đồ `>= 4` bước hoặc `H_px > 580px` chuyển sang lưới Zigzag 2 cột (`W = 920px, H <= 560px`).
- **Ấn phẩm sạch:** Không xuất nhãn kỹ thuật nội bộ, không để rò rỉ cây ASCII (`│├└─`), và sử dụng font hỗ trợ tiếng Việt đầy đủ (tránh lỗi ô vuông tofu của `Liberation v1.x`).

## 3. Vi Tương Tác Flashcard Kép 2 Chế Độ (`#fcModeBar`)
- Cấu trúc bộ thẻ gồm 2 nhóm thẻ cân đối với thanh lọc chuyển đổi trực tiếp `#fcModeBar` (`Tất cả thẻ` | `Thuộc bài nhanh` | `Tư duy & Cơ chế`):
  1. **Thuộc bài nhanh (`card_mode = "core_recall"`, Bloom 1–2, `30%–45%`):** Câu hỏi 1 dòng hỏi trực diện định nghĩa, mốc số liệu, ngưỡng cắt, phân loại, tam chứng/tứ chứng, liều thuốc; mặt sau gọn, dễ nhẩm trong 5 giây.
  2. **Tư duy & Cơ chế (`card_mode = "clinical_reasoning"`, Bloom 3–4, `55%–70%`):** Tình huống ngắn hạt nhân hỏi cơ chế nhân–quả hoặc phân biệt bẫy gần đúng (*Near-Miss*).
- Không dùng emoji gây lỗi hiển thị font khi xuất PDF/HTML; dùng ký hiệu Unicode cơ bản hoặc SVG sạch.
- Khi làm mới/cập nhật từng câu hỏi trong ngân hàng câu hỏi JSON, cập nhật cục bộ theo ID câu hỏi và cân bằng độ dài phương án ở cả 2 đầu (tránh lộ đáp án bằng độ dài).
