# International Evidence Reconciliation v0.1 — Quy tắc đang thử nghiệm

## Scope
Áp dụng khi học liệu y khoa có khuyến cáo chẩn đoán, xử trí, thuốc, chống chỉ định, ngưỡng số liệu hoặc mục tiêu học tập đáng ngờ. Đây **không phải** hệ thống xác nhận tự động mọi sự thật y khoa; tính đúng đắn ngữ nghĩa và cập nhật vẫn cần kiểm chứng độc lập có chuyên môn.

## Không đảo ngược thứ tự học liệu bằng một bảng xếp hạng cứng
- Đọc toàn bộ Vid / Slide / PNT được chọn và giữ nguyên byte, đường dẫn, hash.
- `Vid` thường là bản ghi giảng đường; là nguồn **tường thuật nội dung đã được giảng**, không tự động là chuẩn khoa học ưu tiên hơn guideline.
- Với riêng bài 4, Vid ghi "Nhóm sinh viên phối hợp giảng dạy cùng Giảng viên Phẫu thuật Mạch máu". Theo thông tin người dùng, buổi đó sinh viên thuyết trình; không suy diễn mỗi câu đều do giảng viên phê duyệt. Đây là ngoại lệ theo **buổi**, không hạ mức tin cậy của mọi Vid.
- Phân biệt `who_presented`, `who_authored`, `who_reviewed`, `approval_evidence`, `teaching_primary`, `scientific_verification_status`.
- Mục tiêu học tập trong source do sinh viên tự đặt chỉ là ứng viên: phải đối chiếu với cấu trúc môn, mục tiêu chương trình (nếu có), mức rủi ro, hướng dẫn chuyên ngành, và đề đánh giá thực tế.

## Retrieval / Evidence hierarchy by QUESTION TYPE
1. Xác định câu hỏi cần kiểm chứng và phạm vi PICO/đối tượng, mức độ nặng, thời điểm, tuyến điều trị, khu vực áp dụng.
2. Dựa vào nguồn phù hợp với loại vấn đề: guideline hội chuyên ngành mới nhất có liên quan và tài liệu chính thống; WHO/national guidance cho chính sách, y tế công cộng; systematic review/Cochrane cho hiệu quả can thiệp; nghiên cứu gốc khi thiếu tổng quan; sách chuyên ngành cho khái niệm nền.
3. Kiểm tra ngày và phiên bản guideline; hỏi liệu có bản cập nhật/thay thế. Không coi một web snippet là đầy đủ guideline.
4. Đánh giá chất lượng: độ trực tiếp, thiết kế nghiên cứu, nguy cơ thiên lệch, tính nhất quán, độ chính xác, phù hợp đối tượng, mức độ khuyến cáo (GRADE/AGREE II khi thực sự thực hành phương pháp), xung đột lợi ích, sự khác biệt điều kiện Việt Nam.
5. Ghi `agrees`, `contradiction`, `context_dependent`, `outdated`, hoặc `insufficient_evidence`; tách "điều được dạy" khỏi "điều có thể khẳng định từ chứng cứ".
6. Với mâu thuẫn Critical, CreatorSkill tạo issue, yêu cầu reviewer y khoa và chặn phê duyệt cho tới khi giải quyết. Không âm thầm sửa source. Hạn chế lạm dụng khẩu hiệu "tuyệt đối", "luôn", "không bao giờ" khi guideline có phân tầng.
7. Không cho hệ thống tự báo đã dùng GRADE/AGREE II chỉ vì gắn nhãn; yêu cầu hồ sơ đánh giá thật.

## Phân tách sản phẩm và hồ sơ QA
- **PDF bài giảng xuất cho người học**: trắng đen, cỡ chữ khoảng 12 pt, tối đa 9 trang, không in trích dẫn, link nguồn, thư mục tài liệu, quy trình đối chiếu hoặc nhãn QA. Giữ bảng chốt mục tiêu học tập và sơ đồ rõ ràng.
- **Hồ sơ kiểm định nội bộ**: URL, DOI, tác giả/tổ chức, ngày hiệu lực, phiên bản, snapshot, SHA-256, ghi chú xung đột, ngữ cảnh áp dụng, và trạng thái người duyệt; nằm ngoài bốn tệp sản phẩm của `giao-trinh-tong-hop`.
- Bộ kiểm tra offline `creator-skill/scripts/international_evidence_gate.py` chỉ xác minh tệp, hash, đoạn trích, cấu trúc và nhắc thiếu reviewer. Nó KHÔNG kiểm chứng truth, tính cập nhật hoặc quyền reviewer.

## Ca thực: Tắc động mạch cấp — CTA
Vid có nhận định `"TUYỆT ĐỐI KHÔNG"` chỉ định CTA trong trường hợp tắc cấp hoàn toàn vì mất thời gian vàng. ESC 2024 trình bày DSA, CTA, DUS, CE-MRA như các phương án hình ảnh tùy chuyên môn, khả năng có sẵn và ưu tiên điều trị; ALI cần đánh giá nhanh và can thiệp kịp thời. **Chưa thể suy từ sự khác biệt câu chữ rằng mọi chụp CTA đều đúng hay sai**. Kết luận giáo dục cần phân tầng chi đe dọa, chậm trễ do chụp và sự sẵn có của tái thông. Nhận định Vid phải được gắn cờ `context_dependent`, chưa tự sửa nội dung nguồn, chưa tự chấm PASS.

## Tài liệu gốc tham chiếu trong QA (không in PDF)
- ESC 2024 Peripheral Arterial and Aortic Diseases: https://academic.oup.com/eurheartj/article/45/36/3538/7738955
- CDC ACIP GRADE Handbook: https://www.cdc.gov/acip-grade-handbook/hcp/chapter-2-creating-trusting-guidelines/index.html
- Cochrane Handbook: https://www.cochrane.org/handbook

## Definition of done
Các claim P0/P1/high-risk được đối chiếu bằng bằng chứng thực sự, không còn khuyến cáo tuyệt đối chưa giải quyết; QA xác định xung đột theo bối cảnh, có bản ghi reviewer được xác minh từ hệ thống đáng tin (hiện chưa có); PDF sạch citation; MCQ/MEQ không biến nội dung tranh cãi thành một đáp án duy nhất mà không khai báo ngữ cảnh; test hồi quy đạt.
