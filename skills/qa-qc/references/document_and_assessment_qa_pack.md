# Cổng Kiểm Định Tài Liệu PDF A4, Sơ Đồ SVG & Học Liệu Tương Tác (Document & Assessment QA Pack)

> Chỉ nạp tệp này khi chạy `qa-qc` với profile `document_publishing` (xuất bản bài giảng PDF A4, sơ đồ học thuật, Flashcard HTML, Quiz MCQ/MEQ). Tệp này bảo toàn 100% các cổng kiểm định thành phẩm chuyên sâu từ `qa-qc v3.8–v3.9.2`.

## 1. Cổng Chặn Lỗi Hiển Thị PDF & Đồ Họa
1. **Chặn lỗi font ô vuông tofu (`Liberation v1.x`):** Quét tĩnh đường dẫn font trong script sinh PDF/SVG, chặn font thiếu glyph tiếng Việt (như `/truetype/liberation/` cũ); yêu cầu font hỗ trợ Unicode tiếng Việt đầy đủ (`Noto Serif`, `DejaVu`, `Times New Roman` hợp lệ).
2. **Quét pixel tràn lề phải từng trang PDF thật (`audit_compiled_pdf_page_margin_overflow_qa`):** Kiểm tra biên phải mỗi trang PDF sau biên dịch để phát hiện chữ/bảng/sơ đồ bị cắt xén ngoài vùng in.
3. **Chặn rò rỉ cây ASCII & lỗi tách thực thể HTML:** Không để ký tự vẽ cây thô (`│├└─`) lọt ra PDF/HTML; khi tách câu bằng dấu `;`, không được chém ngang thực thể HTML (`&lt;`, `&gt;`, `&amp;`) bằng negative lookbehind `(?<!&lt)(?<!&gt)(?<!&amp);`.
4. **Kiểm chứng metadata ảnh sơ đồ & chống tràn chữ tiêu đề SVG:** Không ghi khống kích thước/nguồn ảnh sơ đồ; kiểm tra cỡ chữ thực tế trên giấy A4 đạt `>= 12pt` ở cả 2 chiều `W × H`.

## 2. Cổng Kiểm Định Công Thái Học Bài Giảng, Flashcard & MCQ
1. **Tách dòng ngắn & Phân cấp 4 tầng đầu dòng:** Mỗi gạch đầu dòng `< 4` dòng trên A4 `12pt` (`<= 42–45 từ`, mục tiêu `1–2 dòng`) và đúng thứ tự ký hiệu 4 cấp (`–` → `•` → `○` → `▪`).
2. **Kiểm định Flashcard kép 2 chế độ (`#fcModeBar`):** Xác nhận có đủ 2 nhóm `core_recall` (`30%–45%`) và `clinical_reasoning` (`55%–70%`), thanh chuyển chế độ `#fcModeBar` hoạt động thật và `0%` ký tự emoji gây lỗi font.
3. **Bộ giải mã JSON Flashcard/Quiz bền vững với chuỗi `];` nội dòng:** Khi trích xuất mảng JSON nhúng trong script HTML, dùng bộ tách cân bằng ngoặc/JSON parser chuẩn thay vì regex cắt sớm tại chuỗi `];` xuất hiện bên trong nội dung câu hỏi.
4. **Khử nhân lặp Base64 & tối ưu dung lượng HTML:** Không lặp cùng một chuỗi ảnh Base64 nhiều lần trong tệp HTML tự chứa (mục tiêu `< 450 KB` cho gói thẻ/quiz không nhúng ảnh nặng).
5. **Kiểm định cân bằng đề trắc nghiệm & chống cắt cụt:** Kiểm tra không có phương án bị cắt cụt cơ học (`opt[:65]`), cân bằng độ dài đáp án đúng ở 2 đầu (`longest_is_key_rate <= 10%`, `shortest_is_key_rate <= 25%`) và giữ đúng thứ tự 1-1 giữa đề và lời giải.

## 3. Thực Thi Kiểm Định Tự Động
- Gọi các hàm tương ứng trong `scripts/qa_test_harness.py` (gồm 28 hàm kiểm định tĩnh, hợp đồng, kiểm định PDF/HTML/Flashcard, săn lỗi tiên đoán và `compute_pass_at_k_and_verdict`).
