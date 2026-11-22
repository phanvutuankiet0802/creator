# Context Intelligence — hợp đồng xuyên 26 skill v0.1

## Vì sao cần
"Đúng định dạng" và "có từ khóa trong nguồn" không đồng nghĩa với **hiểu ngữ cảnh**. Bản làm việc phải hiểu nhiệm vụ thật, người dùng, môn học, kiểu bài, hoàn cảnh dùng, nguồn và những lần người dùng sửa yêu cầu. Không tạo sản phẩm khuôn mẫu, khô khan, liệt kê đều các mục, hoặc biến mọi bài thành câu hỏi điều trị.

## Context trước Content — bắt buộc ở chat thường lẫn Task
1. **Ý định thật:** người dùng muốn đọc để hiểu, ôn thi, chuẩn bị khám, thực hành thao tác, phân tích số liệu hay đánh giá chất lượng? Phân biệt yêu cầu chính và chi tiết phụ; giữ các quyết định trước trong cuộc hội thoại (không yêu cầu hỏi lại điều đã biết).
2. **Đối tượng và thời điểm:** sinh viên, bác sĩ, giảng viên, người bệnh hay người làm quản lý; trình độ, kiến thức nền, áp lực thời gian, kiểu kiểm tra, giới hạn môi trường, năng lực dùng công cụ. Khi chưa biết thì ghi `unknown`, không bịa tiểu sử.
3. **Bối cảnh chuyên môn:** môn và loại bài có thể đa nhãn. Một *định nghĩa* có thể là P0 trong nguyên lý Y học gia đình/Y học môi trường, nhưng là nền ngắn trong bài cấp cứu ngoại khoa, **trừ khi nó quyết định chẩn đoán hoặc xử trí**. Không quy tắc cứng theo tên môn.
4. **Bối cảnh học liệu:** đọc đủ nguồn người dùng chọn, phân biệt nguồn gốc, quan điểm giảng viên, chỗ mâu thuẫn, ảnh và bảng không thể lược bỏ. Không tự thêm kiến thức ngoài nguồn vào phần mô tả bài giảng; nếu có mở rộng thì phân tầng riêng.
5. **Quyết định nội dung (per LO):** `LO → dạy sâu / giải thích ngắn / sơ đồ / kiểm tra / hoãn review`, kèm lý do riêng của môn + loại bài + nhu cầu hiện tại, trích nguồn và đánh đổi khi giới hạn độ dài. Không làm mỗi LO một độ dài bằng nhau.
6. **Cách giải thích:** dùng trình tự *tại sao → diễn biến/cơ chế → dấu hiệu/nhận biết → hệ quả/quyết định*, hoặc trình tự hợp ngữ cảnh khác. Giải thích các mắt xích dễ nhầm; đừng nhảy bước, trưng các thuật ngữ trừu tượng mà không nối nghĩa; tránh chữ nhiều mà ít ý. Ảnh/sơ đồ phải thực sự giúp hiểu và đủ độ lớn.
7. **Thích ứng đầu ra:** bài giảng PDF trắng đen, font 12 pt, tối đa 9 A4, đúng 4 tệp khi qua `giao-trinh-tong-hop`, bảng chốt tất cả LO P0/P1, không đưa phần luyện tập hay tài liệu tham khảo hiển thị vào PDF học tập; dữ liệu provenance vẫn nằm nội bộ. MCQ có sức phân hóa và phương án nhiễu hợp lý; MEQ phát triển dữ kiện thật; flashcard bao phủ điểm trọng tâm; các skill khác áp dụng định dạng phù hợp mục tiêu riêng.
8. **Chống quên ngữ cảnh lúc bàn giao:** truyền `context_fingerprint`, mục đích, đối tượng, loại bài, source snapshot, yêu cầu cấm/bắt buộc, LO và lý do của từng quyết định. Bản subtask không được tự đổi phạm vi, bài, số trang, định dạng hoặc độ sâu.
9. **Phản chứng:** dùng cặp tình huống chỉ thay *một biến ngữ cảnh* (môn/loại bài/mục đích/người học) và đánh giá liệu độ sâu, trình tự, loại câu hỏi **thay đổi hợp lý**. Dùng cặp đối chứng đảo phủ định, đổi chỉ định, thiếu bảng, giả mạo nguồn, kết luận chung chung. Người đánh giá phải kiểm tra kết quả thực chứ không tin mỗi dòng tự đánh giá.
10. **Không lạm dụng checklist:** Khi người dùng yêu cầu trả lời đơn giản, không bắt họ điền 10 mục; khai thác bối cảnh hiện có và chỉ hỏi nếu một thiếu sót thực sự chặn nhiệm vụ. Các trường JSON là hồ sơ nội bộ cho công cụ, không ép chat thường sinh JSON dài.

## Trạng thái minh bạch
- `CONTEXT_STRUCTURAL_PASS`: đã đủ dữ liệu bối cảnh, nguồn/LO và quyết định có neo rõ; **chưa nói là quyết định đúng**.
- `CONTEXT_SEMANTIC_REVIEW_REQUIRED`: chưa kiểm tra hiểu đúng nghĩa và chất lượng diễn đạt.
- `CONTEXT_FAIL`: sai phạm vi/đối tượng/đề xuất trái yêu cầu, mất nguồn/handoff hoặc ép template không hợp mục tiêu.

## Kiểm thử nền (bắt buộc bổ sung theo từng skill)
- **C01** Hai môn khác nhau, cùng một loại khái niệm nhưng độ ưu tiên khác phù hợp.
- **C02** Cùng môn nhưng bài định nghĩa vs cấp cứu xử trí cho cấu trúc khác.
- **C03** Người mới học vs người cần lập luận thi MEQ: giải thích sâu khác nhưng không sai nguồn.
- **C04** Trộn nguồn Vid/Slide với kết luận khác nhau: giữ hai quan điểm và nêu xung đột.
- **C05** Yêu cầu người dùng sửa sau: không còn xuất phần họ đã loại bỏ; không đổi yêu cầu bốn tệp.
- **C06** Giới hạn 9 trang: P0 không biến mất, báo scope conflict nếu không chứa được.
- **C07** Không chế thêm bệnh cảnh lâm sàng vào bài khái niệm hoặc ép một quota chung.
- **C08** Khi không có nguồn, không bịa từ NotebookLM UUID.
- **C09** Mỗi lần chuyển skill giữ context fingerprint và snapshot nguồn.
- **C10** Blind A/B review với người học/giảng viên: câu có dễ hiểu hơn, đúng ý, không khô khan, không thừa so với bản cũ? Yêu cầu bằng chứng nhận xét, chưa tự động xác nhận.

## Triển khai
- Skill chat-first (`hoc-y`, `mcq`, `thau-hieu`): dùng quy trình bằng ngôn ngữ, không được phụ thuộc script.
- Skill kỹ thuật có Python: gọi `scripts/context_intelligence.py::audit_context` để kiểm tra *tính nhất quán* của hồ sơ. Tool không phán quyết sự phù hợp học thuật.
- Điều phối: lập `context` cùng lúc lập LO và trước khi tạo sản phẩm; có thể dùng file `context.json`. Các skill con không tự thay thế context mà phải trả `SCOPE_CONFLICT` khi bất đồng.

## Kiểm định ngữ cảnh trên sản phẩm thật (bổ sung 2026-11)
Đừng chỉ chấm hợp đồng JSON; phải chạy cặp A/B trên tệp đã xuất. Phân biệt
`layout_revision` và `context_adaptation`; không dùng thay đổi font/bố cục để
chứng minh hiểu ngữ cảnh. Mỗi LO P0/P1 đòi nguồn gốc, câu gốc từ nguồn thật,
và chứng cứ trong sản phẩm. Nhận xét về độ mạch lạc, tự nhiên, tính chọn lọc
và đúng trọng tâm cần đánh giá sản phẩm bằng con người; việc khớp hash/quote
không chứng nhận ý nghĩa hoặc chất lượng sư phạm. Giữ provenance nội bộ,
không bắt PDF học tập phải hiện tài liệu tham khảo. Thiếu dữ liệu → BLOCKED/
REVIEW_REQUIRED, không suy đoán điểm thi 9+ hoặc bao phủ 90%.
Tham khảo trong môi trường có công cụ: `CONTEXT_PRODUCT_BENCHMARK_GUIDE.md`
ở gói kiểm toán. Chat thường: dùng trực tiếp rubric và trích dẫn đoạn thật.
