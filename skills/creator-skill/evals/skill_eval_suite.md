> **Beta 1.19 supersession (current):** The old `<=10% correct option longest` mandate is withdrawn. Do not game option lengths or insert filler. Use the live builder/QA checks for per-option conspicuous cues and gross batch skew, plus counterfactual patient-dependence and expert distractor review. Older FB-44/LOCK-14 text below is retained as historical record only.

# Bộ Đề Kiểm Định Hồi Quy Hệ Sinh Thái Skill & Team-Agent (`evals/skill_eval_suite.md` v8.1)

- **T01 -> T13:** Kiểm định toàn diện cấu trúc 6 trụ cột, đối chiếu chữ ký hàm Python (`inspect.signature`), kiểm tra cổng `master_audit_gate.py`, kiểm tra Unicode tiếng Việt + chữ Hy Lạp (`θ`).
- **T14 (`FB-19` -> `FB-21`):** Kiểm tra bài giảng chia đề mục linh hoạt theo mạch bài, chốt cuối bài bằng Lưu đồ tổng kết + Bảng số liệu quan trọng, và 0% lộ nhãn kỹ thuật prompt hay nhãn trích nguồn.
- **T15 (`FB-22`, `FB-23`, `FB-27`, `FB-32`, `FB-43`):** Kiểm tra bài giảng khử trùng lặp 3 nguồn (`Vid ∪ Slide ∪ PNT`) trong khung cứng `4–9 trang A4` với tỷ lệ chữ tô đậm `<b>` `8–15%` (trần cứng `<= 18%`, miễn trừ nhãn đề mục), và xác nhận Flashcard (`50–100 thẻ`) + Đề ôn tập (`tối thiểu >= 40 câu linh hoạt`) vận hành theo Kiến trúc 2 Tầng Nguồn.
- **T16 -> T19 (`FB-28` -> `FB-44`):** Kiểm tra Khóa An Toàn 2 Chìa (`Pre/Post AST Diff Guard` & `Proof-of-Improvement Gate`), Cổng Đếm Ký Tự Đáp Án (`<= 10%` câu đúng dài nhất).
- **T20 (`FB-46 / LOCK-15` - Kiểm định Kiến Trúc 2 Chiều NBME & 5 Cổng Kiểm Toán IWF):**
  - Kiểm tra `audit_rule_to_code_parity_and_qa_blindspots` xác nhận `@tao-de` và `@tham-dinh-su-pham` có đầy đủ 6 hàm mới (`audit_vignette_chronological_flow`, `audit_orth_2d_vignette_and_embedded_matrix`, `audit_forensic_distractor_profiling`, `audit_convergence_cues`, `audit_inter_item_cueing_matrix`, `audit_option_grammatical_and_category_homogeneity`) và `@qa-qc` bắt trúng `18/18` kịch bản Pre-Mortem Fuzzing.
