# Mẫu Báo Cáo Nghiệm Thu QA/QC 6 Tầng, Kiến Trúc 2 Chiều NBME, Đếm Ký Tự Đáp Án & Phiếu Phản Hồi Vòng Lặp (`assets/qa_defect_and_verdict_template.md` v2.7)

## 1. Bảng Tóm Tắt Phán Quyết Nghiệm Thu Chủ Động 6 Tầng (`Proactive QA Gatekeeper & A/B Verdict Summary`)

| Hạng mục Kiểm thử (`Test Layer`) | Công cụ / Phương pháp (`Grader`) | Kết quả (`Pass/Fail`) | Số lỗi (`S1 / S2 / S3 / S4`) |
| :--- | :--- | :--- | :--- |
| **Tầng 1: Phân tích Tĩnh `AST`, Chống Nuốt Lỗi & Bảo mật Sandbox** | `ast.parse`, Unicode `NFC`, Quét mẫu IOC 4 chấm | `PASS / FAIL` | `0 / 0 / 0 / 0` |
| **Tầng 2: Hợp đồng Liên Skill & Radar Độ lệch (`DRIFT-01..13`)** | `inspect.signature`, `detect_cross_skill_version_drift` | `PASS / WARN` | `0 / 0 / X / 0` |
| **Tầng 3: Kiểm định Thành phẩm HTML/PDF, Kiến trúc 2 Chiều NBME & Đếm Ký Tự (`FB-30 -> FB-46`)** | `audit_html_deliverable_predictive` + `audit_nbme_2d_and_iwf_gates_qa` + `audit_mcq_option_length_parity_qa` (`<= 10%` câu đúng dài nhất) | `PASS / FAIL` | `0 / 0 / 0 / 0` |
| **Tầng 4: Săn lỗi Tiên đoán 18 Kịch bản (`Pre-Mortem Fuzzing`)** | `run_predictive_premortem_fuzzing` (`18/18 scenarios caught`) | `PASS / FAIL` | `0 / 0 / 0 / 0` |
| **Tầng 5: Cổng Kiểm chứng Tri thức Mới (`A/B Proof Gate`)** | `evaluate_knowledge_improvement_gate` (`Baseline` vs `Candidate`) | `APPROVED / REJECTED` | `0 / 0 / 0 / 0` |
| **Tầng 6: Độ tin cậy Đa lượt (`pass@3` / `pass^3`)** | `compute_pass_at_k_and_verdict` | **`VERDICT: GO / NO-GO`** | **Tổng điểm tin cậy: `XX%`** |
