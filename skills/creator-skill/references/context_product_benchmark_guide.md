# Kiểm thử sản phẩm theo ngữ cảnh — A/B evidence gate v0.2

Mục tiêu: làm lộ trường hợp skill chỉ *khai* hiểu ngữ cảnh nhưng sinh ra sản phẩm không thay đổi hợp lý, hoặc bị mất nguồn khi chuyển giữa các skill.

## Hai kiểu so sánh phải tách bạch
1. `layout_revision`: Hai sản phẩm cùng nguồn **và cùng ngữ cảnh**, chỉ khác cách trình bày; không được gọi là chứng minh AI thích nghi ngữ cảnh. Trường hợp thực: hai PDF thử bài 4 (mỗi tệp 5 trang).
2. `context_adaptation`: Hai sản phẩm dùng **cùng các tệp nguồn nguyên byte**, chỉ nên đổi *một* biến ngữ cảnh (môn, loại bài, trình độ, mục đích). Phải chứng minh sự thay đổi cách giải thích, phân bổ nội dung, thứ tự suy luận và dạng câu hỏi **có lý do học thuật**; không đủ nếu chỉ đổi tên môn trong tiêu đề.

## Chuẩn vào và quy trình
- Cung cấp tệp đầu ra thật A/B và SHA-256 từ byte tệp; cung cấp *tệp nguồn thực*, SHA-256 từng nguồn, nguồn Vid/Slide/PNT đã chọn. Không chấp nhận UUID trơ hoặc hash tự khai không đối chiếu file.
- Cung cấp danh mục LO P0/P1 đã được phản biện. Mỗi LO có ít nhất một bản ghi `gold_checks`: `objective_id`, `source_id`, `source_quote` nguyên văn, và `artifact_quotes.A/B` là đoạn thật của từng sản phẩm. Bật `require_full_gold_witnesses=true` để **chặn** thiếu mục tiêu.
- Chạy `contextual_product_benchmark.py` và lưu JSON report. Khớp quote/hash là bằng chứng về sự có mặt, **không chứng minh paraphrase đúng nghĩa**, tính đủ toàn nguồn, hay một người đã thực sự học hiểu.
- Review mù với hai người độc lập (khi thực sự có reviewer). Review các mục: source fidelity, reasoning coherence, context selectivity, readability, objective coverage, visual relevance. Mỗi tiêu chí chấm 1–5 và dẫn 2 đoạn văn *có thật* trong sản phẩm. Lời tự khai reviewer ID không chứng minh danh tính; cần xác nhận thực bằng quy trình ngoài công cụ.
- Nếu còn điểm mù, gắn `BLOCKED` / `AWAITING_BLIND_REVIEW` / `REVIEW_RECORDS_COMPLETE_VERIFICATION_REQUIRED`; công cụ không cấp quyền phát hành theo điểm tự báo.

## Bẫy học thuật bắt buộc
- Đảo định nghĩa: mốc <2 tuần để *phân loại* không cho phép trì hoãn cấp cứu.
- Câu 'chống chỉ định' bị đảo thành 'chỉ định'. Tương tự với phủ định, so sánh, điều kiện, ngưỡng, chỉ định từng phân độ.
- 'Ngoại khoa' không đồng nghĩa mọi định nghĩa đều P3; 'Y học môi trường' không đồng nghĩa mọi định nghĩa đều P0. Lý do phải gắn mục tiêu bài và tài liệu thực.
- Bài giảng không được lấp đầy bằng thông tin ngoài trọng tâm để đạt độ dài. Bảng chốt cuối bài phủ đủ LO trọng tâm. PDF trắng đen, Times New Roman 12pt nếu bản quyền font/môi trường cho phép; không vượt 9 A4; hình/sơ đồ phải có giá trị giải thích.
- Flashcards không bỏ ý P0/P1; MCQ có phương án nhiễu phân biệt; MEQ có dữ kiện mới thực sự theo từng giai đoạn, không chỉ tách một câu dài thành nhiều ô.
- Không có dữ liệu reviewer/người học hoặc kiểm định đủ nguồn thì tuyệt đối không nói “bảo đảm 9+” hay “bao phủ 90% toàn bài”.

## Khả năng vận hành
- Chat-first `hoc-y`, `mcq`, `thau-hieu` thực hiện quy trình đánh giá và yêu cầu người dùng đọc A/B bằng ngôn ngữ; **không đòi chạy script**.
- Task/script mode: QA/QC, CreatorSkill, Thẩm định sư phạm và điều phối gọi tool khi có file thực. Script là *phép kiểm độc lập*, không thay thế tư duy và phản biện học thuật.

## Hiện trạng bài số 4
Hai PDF bài 4 hiện có là `layout_revision`, không phải A/B ngữ cảnh. Kết quả 2/4 LO minh chứng đối chiếu source/output, thiếu hai LO → `BLOCKED` ở chế độ nghiêm ngặt; review mù chưa có. Đây là báo cáo trung thực về phạm vi kiểm định, không phải kết luận nội dung còn thiếu trong PDF.


## Bản v0.3 — kiểm chứng nội dung người học có thể nhìn thấy (ACTIVE)
- **Không đọc script JSON/JS làm chứng cứ học tập.** `static` HTML chỉ trích văn bản HTML khả kiến sơ bộ; không nhận diện đủ CSS, DOM động hoặc câu trả lời nằm sau nút. Trong benchmark nghiêm ngặt, HTML có script/style/link **phải** dùng `html_evidence_mode: "browser"`.
- Nếu MCQ, flashcard, MEQ có nội dung/đáp án/phản hồi hiển thị sau thao tác, kèm `html_interactions: [{"action":"click","selector":"..."}]` cho từng bản A/B; bật `require_interaction_evidence: true` để chặn thiếu thao tác. Browser chạy isolated, chặn mọi network request. Chứng cứ chỉ gồm phần thực sự hiện trong `body.innerText` qua các trạng thái đã kiểm tra, không gồm mã JS/JSON.
- Để chứng minh *thay đổi chiến lược dạy theo ngữ cảnh* (chứ không chỉ khác chữ), bật `require_pedagogical_contrasts: true` trong manifest A/B `context_adaptation`. Mỗi LO Critical khai một bản ghi `pedagogical_contrasts` gồm: `objective_id`, `context_field` thực sự thay đổi, `source_id`, `source_quote` nguyên văn, `A_quote`, `B_quote` là trích đoạn thực sự thấy, `why_this_change` nêu lý do theo người học và mục tiêu.
- Trường `critical_objectives` phải được xác định từ inventory thực, không tự kê vài LO cho vừa test. Dù đủ trích dẫn, không chấm PASS về tính đúng nghĩa, đủ bài hay tự nhiên; vẫn **AWAITING_BLIND_REVIEW**. Reviewer thực cần phản biện độ chính xác, tính mạch lạc, vai trò từng ý, và khả năng vận dụng.
- Chạy `python scripts/contextual_product_benchmark.py PATH/MANIFEST.json --out REPORT.json`. Với HTML động bắt buộc có Chromium + Playwright; nếu thiếu môi trường, ghi NOT VERIFIED chứ không đổi sang đọc JSON thô.
