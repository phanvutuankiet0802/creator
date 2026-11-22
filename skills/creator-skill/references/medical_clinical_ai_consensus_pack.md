# Mô-Đun Đồng Thuận AI Y Khoa & Lâm Sàng (Medical Clinical AI Consensus Pack)

> Chỉ nạp tệp này khi thiết kế, xây dựng hoặc kiểm toán sản phẩm, phần mềm, quy trình hoặc skill có liên quan đến **Y khoa, Chăm sóc sức khỏe, Dữ liệu lâm sàng hoặc Giáo dục y khoa**.

## 1. Kiến Trúc Hệ Thống AI Y Khoa Đa Mô-Đun (Glass-Box Modularity)
Tổng hợp từ **Microsoft Healthcare Agent Orchestrator**, **Oxford TrustedMDT**, **Google DeepMind AMIE / G-AMIE & MedGemma** và **OpenClinAI Med Agent Hub**:

1. **Tách lớp Điều phối khỏi lớp Chuyên khoa & Dữ liệu:**
   - Lớp điều phối (*Orchestrator*) quản lý trạng thái phiên, định tuyến và hợp đồng dữ liệu chặt (ví dụ JSON Schema / Pydantic).
   - Lớp tri thức chuyên khoa (*Clinical Guidelines / EBM*) và lớp truy xuất dữ liệu (*FHIR / EHR / Document Store*) phải là mô-đun rời để thêm/bớt chuyên khoa mà không sửa lõi.
2. **Giám sát Lấy Bác Sĩ Làm Trung Tâm (*Physician-Centered Oversight — G-AMIE*):**
   - AI tổng hợp bệnh sử, tóm lược dữ kiện, đề xuất chẩn đoán phân biệt kèm mức độ tin cậy và cảnh báo cờ đỏ (*red flags*).
   - Quyết định chẩn đoán xác định, kê đơn và can thiệp luôn thuộc về nhân viên y tế có chuyên môn; hệ thống bắt buộc thể hiện rõ nguồn dẫn chứng để bác sĩ kiểm chứng nhanh (*Glass-Box*, không hộp đen).
3. **Chuẩn Tương Tác Dữ Liệu Y Tế (khi xây dựng phần mềm / API y tế):**
   - Ưu tiên mô hình hóa theo chuẩn **HL7 FHIR R4** (`Patient`, `Observation`, `Condition`, `MedicationRequest`, `DiagnosticReport`) và hệ mã hóa chuẩn quốc tế **LOINC** (xét nghiệm), **SNOMED CT** (thuật ngữ lâm sàng), **ICD-10 / ICD-11** (mã bệnh), **RxNorm / ATC** (thuốc).
   - Tuyệt đối tách biệt dữ liệu mẫu tổng hợp (*synthetic data*) khỏi dữ liệu định danh bệnh nhân thật (**PHI/PII**).

## 2. Chuẩn Đánh Giá Chất Lượng & An Toàn (HealthBench + GRADE/CEBM)
1. **Đánh giá theo Rubric Hành Vi Có Trọng Số (cảm hứng OpenAI HealthBench):**
   - Không chỉ chấm đúng/sai đơn lẻ; đánh giá tối thiểu 5 trục độc lập:
     - **Độ chính xác lâm sàng (*Clinical Accuracy*):** Đúng sinh lý bệnh, liều lượng, ngưỡng cắt và chống chỉ định.
     - **An toàn & Cờ đỏ (*Safety & Red-Flag Escalation*):** Không bỏ sót dấu hiệu đe dọa tính mạng; cảnh báo kịp thời khi cần cấp cứu.
     - **Ràng buộc bằng chứng (*Guideline Grounding*):** Mọi khuyến nghị quan trọng phải đối chiếu được về guideline uy tín (WHO, NICE, BMJ Best Practice, AHA/ACC, ESC, Bộ Y tế) hoặc tài liệu nguồn do người dùng cung cấp.
     - **Nhận thức ngữ cảnh & Độ bất định (*Context Awareness & Uncertainty*):** Nhận diện dữ kiện còn thiếu (tuổi, thai kỳ, suy gan/thận, thuốc đang dùng) và nói rõ khi thiếu bằng chứng.
     - **Chất lượng truyền đạt (*Communication Clarity*):** Tránh biệt ngữ rối rắm khi viết cho bệnh nhân; ngắn gọn, chuẩn thuật ngữ chuyên ngành khi viết cho bác sĩ/sinh viên y khoa.
2. **Phân Tầng Bằng Chứng & Chống Trôi Nghĩa Khi Diễn Giải (`FActScore / ClaimVer`):**
   - Khi diễn giải mệnh đề y khoa cho dễ hiểu, giữ nguyên **4 bất biến suy diễn**: không nâng khống mức độ chắc chắn (*có thể* ≠ *chắc chắn*), không đảo chiều quan hệ nhân–quả, không làm sai lệch ngưỡng cắt/liều lượng, không tự bịa nhóm bệnh nhân ngoài phạm vi nguồn.
   - Phân tầng nhận thức đa môn (NLM SemRep / EBM):
     - *Kênh 1 — Cơ chế nhân–quả:* Trình bày chuỗi giải thích bản chất (*Tại sao / Như thế nào*).
     - *Kênh 2 — Ngưỡng quyết định & hành động:* Đưa vào bảng cấu trúc rõ ràng (tiêu chuẩn chẩn đoán, phân độ, xử trí).
     - *Kênh 3 — Số liệu mô tả ngoại vi:* Tách gọn, không che lấp cốt lõi lâm sàng.
