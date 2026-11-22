# Bộ Đề Kiểm Định Công Thái Học & Hệ Thống Thiết Kế (`evals/ui_ux_eval_suite.md` v1.3)

| Mã Test | Kịch bản Kiểm định Thiết kế (`Test Scenario`) | Đầu vào Giả lập (`Input`) | Kỳ vọng Đầu ra từ `ui_ergonomics_linter.py` (`Expected Outcome`) |
| :--- | :--- | :--- | :--- |
| **UX-01** | Kiểm định tương phản quang học WCAG 2.2 AAA cho chữ thân bài | Foreground `#111111` trên Background `#FFFFFF` | `contrast_ratio >= 18.8`, đạt chuẩn `WCAG_AAA_PASS` (`>= 7.0:1`). |
| **UX-02** | Bắt lỗi tương phản thấp gây mỏi mắt | Chữ xám nhạt `#94A3B8` trên nền trắng `#FFFFFF` | `contrast_ratio < 3.0`, báo lỗi `WCAG_CONTRAST_FAIL`. |
| **UX-03** | Kiểm định Nguyên lý Tín hiệu Mayer (`8% - 15%` bold, trần `<= 18%`) trên bài giảng nén `70% mệnh đề cốt lõi` | Đoạn văn học thuật có `11.5%` số từ nằm trong thẻ `<b>` và mọi cụm `<b>` đều dài `<= 6 từ` | `signaling_status = "OPTIMAL_SIGNALING"`, `valid = True`. |
| **UX-04** | Bắt lỗi "Bão chữ in đậm" (`Over-Bold Noise > 18%`) hoặc cụm `<b>` quá dài | Đoạn văn tô đậm `28%` số từ hoặc có thẻ `<b>` chứa câu dài 12 từ | Báo lỗi `OVER_BOLD_VISUAL_NOISE` hoặc `BOLD_SPAN_TOO_LONG`. |
| **UX-05** | Bắt lỗi rò rỉ nhãn huấn luyện nội bộ lên giao diện (`FB-19`, `FB-20`) | HTML chứa chuỗi `[Must know]` hoặc `(Theo Vid)` | Báo lỗi `FORBIDDEN_META_LABEL_LEAK`. |
| **UX-06 (`FB-32`)** | Kiểm định tính toàn vẹn của tệp `tokens/medical_design_tokens.json` theo W3C DTCG | Đọc và phân giải toàn bộ cây JSON Token | Xác nhận đầy đủ `color`, `typography`, `ergonomics` (kèm `content-density-and-volume`: `70%` mệnh đề, `50-80` thẻ, `>= 40` câu và `mcq-option-balance`). |
| **UX-07 (`FB-30`)** | Kiểm định Cân bằng Độ dài Thị giác 4 Đáp án Trắc nghiệm (`audit_mcq_visual_option_balance`) | Bộ câu hỏi có đáp án đúng dài gấp `> 1.35x` số ký tự các phương án nhiễu hoặc `longest_is_key_rate > 35%` | Báo lỗi `SYSTEMIC_VISUAL_LONGEST_KEY_BIAS` / `VISUAL_LONGEST_KEY_SALIENT` (`valid = False`). |
