# Academic Intelligence — Hợp đồng tiền kiểm v0.1

## Mục đích và giới hạn
Quy trình này phải diễn ra **trước khi** tạo PDF/flashcard/MCQ/MEQ hoặc bài học tương tác. Đích đến là hiểu đúng môn, kiểu bài và P0/P1 từ **toàn bộ nguồn được chọn**. **Không** dùng tên môn một mình để tự suy ra rằng định nghĩa, dịch tễ hoặc xử trí luôn P0 hoặc P3. Hệ thống Python kiểm tra **cấu trúc, neo bằng chứng, tỷ lệ ánh xạ LO trong inventory đã khai báo**; nó KHÔNG phân loại ý nghĩa y khoa hoặc bảo đảm điểm thi.

## Quy trình bắt buộc (dùng được trong Gemini Chat không chạy script)
1. Đọc toàn bộ Vid, Slide, PNT được người dùng chọn hoặc nguồn trực tiếp. Đánh dấu văn bản nào không có, chưa đọc hết, thiếu ảnh/biểu đồ. Đừng giả vờ đã lấy NotebookLM chỉ vì có UUID. Vid là nguồn ưu tiên phản ánh bài giảng, Slide/PNT bổ trợ; bất đồng phải ghi riêng, không tự sửa nguồn.
2. Xác định `domains` **đa nhãn** (có `environmental_medicine`, `family_medicine`), `lesson_type` (foundations/concepts/mechanisms/clinical_diagnosis/clinical_management/procedure/prevention/population_health/research_methods/interpretation/mixed) và biện minh dựa vào nội dung và đề thi/bối cảnh đã được cung cấp.
3. Lập bảng **concept inventory**: mã ý, trích dẫn nguyên văn đủ ngắn từ nguồn, vị trí trang/đoạn, loại thông tin (định nghĩa/cơ chế/số liệu/quy tắc quyết định/hình bắt buộc...), P0..P4, lý do, rủi ro nếu bỏ qua. Không tự tạo trích dẫn hoặc ảnh. Không loại P0/P1 chỉ vì thiếu chỗ: nếu không thể trình bày trong 9 trang thì `SCOPE_CONFLICT`.
4. Từ inventory lập LO; **AI đề xuất P0**, sau đó phản biện mức ưu tiên theo **cả môn lẫn loại bài cụ thể**. Ngoại khoa cấp cứu: đánh giá nguy cơ, phân tầng, chẩn đoán/phân biệt và quyết định thời gian thường trọng tâm. Y học môi trường: định nghĩa phơi nhiễm, ngưỡng, quan hệ liều-đáp ứng, phòng ngừa có thể rất trọng tâm. Y học gia đình: nguyên lý chăm sóc, dự phòng, liên tục/toàn diện, quản lý nguy cơ có thể trọng tâm. Đây chỉ là ví dụ; đối chiếu mục tiêu bài và nguồn thật.
5. Lập mapping `concept_id -> LO_id -> {lecture,flashcard,mcq,meq}`; phân bổ **hình/sơ đồ** có vai trò quyết định ở bước LO. Không ép tất cả LO thành một ca lâm sàng hay MEQ chọn điều trị; các dạng cơ chế, số liệu, dân số cũng có đường đánh giá.
6. Chỉ số `declared_core_coverage` = số ý P0/P1 trong inventory có LO hợp lệ / số ý P0/P1 **đã khai báo**. Yêu cầu >= 90% ở bước tiền kiểm; mọi P0 quan trọng phải có đường tới sản phẩm tương ứng. Chỉ số này **KHÔNG** là chứng minh đã lấy 90% toàn văn nguồn. Muốn nói bao phủ nguồn cần reviewer soát độc lập toàn bộ nguồn và đối chiếu những ý bị bỏ.
7. Thử phản biện: câu mất phủ định, đổi chỉ định thành chống chỉ định; định nghĩa quan trọng bị coi thứ yếu trong môn khái niệm; bệnh ngoại khoa bị nhồi dịch tễ không cần thiết; hai trang nguồn khác quan điểm; hình ECG/bảng phân độ mất; câu hỏi trả lời được không cần ca.
8. Trạng thái chỉ có `BLOCKED` hoặc `STRUCTURE_PASS_SEMANTIC_REVIEW_REQUIRED` cho đến khi có kiểm định chuyên môn độc lập. KHÔNG tự đánh dấu đạt học thuật vì từ khóa trùng hoặc metadata reviewer tự ghi.

## Hợp đồng đầu ra người dùng (khi gọi `giao-trinh-tong-hop`)
- **ĐÚNG 4 tệp:** PDF bài giảng (tối đa 9 A4), flashcard HTML, MCQ HTML, MEQ HTML. Bài giảng trắng đen, phông Times New Roman 12pt nếu dùng được hợp pháp hoặc font tương thích khai báo rõ; bảng/sơ đồ đọc được; có hình thiết yếu; không hiện luyện tập hoặc danh mục tài liệu tham khảo trong PDF học tập nhưng vẫn lưu nguồn riêng trong manifest nội bộ; cuối bài có Kết luận để nhớ và **bảng chốt phủ đủ LO trọng tâm**.
- Số thẻ/câu/ca co giãn theo nguồn và LO. Không nhồi câu để đủ quota. Không hứa bài giảng bảo đảm điểm 9+.
- Nếu không chạy script: dùng bảng kiểm và bằng chứng bằng văn bản; không được tuyên bố đã chạy `academic_preflight.py`.

## Máy có Python
- `scripts/academic_preflight.py --input preflight.json --out preflight_report.json` trong các skill kỹ thuật có script tương ứng. Bằng chứng JSON cần `full_text` và `sha256` của từng nguồn, `read_complete=true`, `inventory_scope_reviewed=true` (tự khai, vẫn cần thẩm định độc lập), `profile`, `inventory`, `objectives`. Không dùng `inventory_scope_reviewed=true` như chứng nhận reviewer độc lập.
- Cổng `master_audit_gate.audit_adaptive_academic_deliverables` nhận đường dẫn `source_evidence_path=` để kiểm tra; khi làm Quad-Pack mà không có preflight sẽ phải báo thiếu và không được phát hành.
