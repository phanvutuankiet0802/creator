# Chuẩn Công Thái Học Nhận Thức Đa Phương Tiện, Nén `80%-90% Key & Mệnh Đề Cốt Lõi`, Tương Phản Quang Học WCAG 2.2 & Cân Bằng Thị Giác Đáp Án (`references/cognitive_ergonomics_and_wcag.md` v1.3)

## 1. Toán Học Tương Phản Quang Học Theo Chuẩn W3C WCAG 2.2 (`SC 1.4.3` & `SC 1.4.6`)

- **Độ chói tương đối (`Relative Luminance - L` trong hệ màu sRGB):**
  $$L = 0.2126 \times r + 0.7152 \times g + 0.0722 \times b$$
- **Tỷ lệ tương phản (`Contrast Ratio - CR`):**
  $$CR = \frac{L_{\text{sáng hơn}} + 0.05}{L_{\text{tối hơn}} + 0.05}$$
- **Ngưỡng cưỡng chế:**
  1. **Văn bản thân bài (`Body Text 12pt`):** Đạt **WCAG AAA (`CR >= 7.0 : 1`)** (`#111111` trên `#FFFFFF` đạt `18.88 : 1`).
  2. **Chữ trong bảng biểu, nhãn sơ đồ & thẻ Flashcard:** Đạt tối thiểu **WCAG AA (`CR >= 4.5 : 1`)**.

## 2. Ứng Dụng 12 Nguyên Lý Học Tập Đa Phương Tiện Của Mayer, Nén `80%-90% Key & Mệnh Đề Cốt Lõi` & Cân Bằng Độ Dài Thị Giác Đáp Án (`FB-19` -> `FB-32`)

| Nhóm Quá Trình Nhận Thức | Nguyên lý Mayer & NN/g | Quy chuẩn Thiết kế Giao diện Cụ thể (`UI/UX Rule`) |
| :--- | :--- | :--- |
| **1. Giảm Tải Ngoại Lai (`Reducing Extraneous Processing`)** | **Coherence Principle** | Ẩn 100% các nhãn huấn luyện nội bộ (`[Must know]`, `[Should know]`, `[Must not miss]`, `[Theo Vid]`, `[Theo PNT]`, `[Theo Slide]`) khỏi mặt chữ (`FB-19`, `FB-20`). |
| **2. Nén `80%-90% Key & Mệnh Đề Cốt Lõi` Mà Vẫn Giữ Mắt Đọc Thoáng (`Signaling & High-Density Layout - FB-27, FB-32`)** | **Signaling Principle** | Bài giảng PDF (`4–12 trang A4 (khung trang động chống phình trang)`) gói **`70% mệnh đề học thuật cốt lõi`** đi kèm `30%` mạch văn nối nhân – quả súc tích bằng bảng biểu (`<table>`), chuỗi mũi tên (`→`) và danh sách phân tầng (`<ul>`), nhưng **chỉ tô đậm `<b>` / `<strong>` từ khóa hạt nhân ở mức `8% – 15%` tổng số từ** (trần cứng `<= 18%`, mỗi cụm `1 – 6 từ`). |
| **3. Chống Lộ Tín Hiệu Thị Giác Sai Lệch Trên Đề Thi (`Anti-Visual Salience Bias - FB-30, FB-32`)** | **Visual Homogeneity Principle** | Trên giao diện thẻ trắc nghiệm (`.option`) với quy mô linh hoạt `N >= 40 câu`, 4 lựa chọn A, B, C, D phải có độ dài ký tự tương đương nhau (`key_to_avg_char_ratio <= 1.35`, `key_to_max_distractor_char_ratio <= 1.20`, `max_to_min_char_spread <= 1.65`, tỷ lệ câu đúng dài nhất toàn đề `<= 35%` tổng số câu `N`) để mắt người làm bài không thể nhìn thoáng qua chọn ngay khối văn bản dài nhất (`audit_mcq_visual_option_balance`). |
| **4. Giảm Tải Ngoại Lai (`Spatial Alignment`)** | **Spatial Contiguity Principle** | Ảnh cắt tọa độ `x:y` từ trang JPEG gốc của Slide/PNT và sơ đồ SVG (`build_medical_svg_diagram`) đặt ngay trong khối nội dung đang giải thích cơ chế đó kèm `Click-to-Zoom`. |
| **5. Quản Lý Tải Bản Chất (`Managing Essential Processing`)** | **Segmenting Principle** | Chia đề mục thân bài linh hoạt theo mạch bệnh học tự nhiên, kết thúc bài giảng bằng **Lưu đồ tổng kết Python (`1150px`) + Bảng chốt số liệu quan trọng** (`FB-21`). |
