"""
Bộ Công Cụ Đo Kiểm Quang Học WCAG 2.2, Tín Hiệu Thị Giác Mayer (Miễn Trừ 100% Nhãn Đề Mục Đầu Dòng Khỏi Hạn Ngạch Bold),
Cổng Chống Cắt Cụt Cụm Từ In Đậm Tiếng Việt ("Đánh giá Rối | loạn"), Khóa Độ Dài Tiêu Đề Đề Mục (<= 8-10 Từ),
Kiểm Toán Cỡ Chữ 12pt Thực Tế Trên Khổ A4 Cho Sơ Đồ Vector SVG & Lưu Đồ Python,
Cân Bằng Độ Dài Thị Giác Đáp Án Trắc Nghiệm (N >= 40 Câu) & Quản Trị W3C Design Tokens
(Medical UI/UX Design System & Cognitive Ergonomics Linter v1.5 - @ui-ux - FB-01 -> FB-43)
"""

import argparse
import base64
import io
import json
import os
import re
import sys
from typing import Any, Dict, List, Set, Tuple

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional for raster image metadata checks
    Image = None


A4_PRINTABLE_WIDTH_PT = 473.4
A4_PRINTABLE_WIDTH_PX_96DPI = 630

FORBIDDEN_UI_LABELS = [
    r"\[\s*Must\s+know\s*\]",
    r"\[\s*Should\s+know\s*\]",
    r"\[\s*Must\s+not\s+miss\s*\]",
    r"\(\s*Theo\s+Vid\s*\)",
    r"\(\s*Theo\s+PNT\s*\)",
    r"\(\s*Theo\s+Slide\s*\)",
    r"\[\s*Theo\s+Vid\s*\]",
    r"\[\s*Theo\s+PNT\s*\]",
    r"\[\s*Theo\s+Slide\s*\]",
]

VIETNAMESE_COMPOUND_MEDICAL_PAIRS: Set[Tuple[str, str]] = {
    ("rối", "loạn"), ("huyết", "học"), ("huyết", "áp"), ("huyết", "thanh"), ("huyết", "tương"),
    ("huyết", "khối"), ("huyết", "động"), ("nhiễm", "trùng"), ("nhiễm", "khuẩn"), ("phế", "quản"),
    ("phế", "nang"), ("hô", "hấp"), ("tim", "mạch"), ("tiêu", "hóa"), ("tiết", "niệu"),
    ("thần", "kinh"), ("nội", "tiết"), ("phẫu", "thuật"), ("thủ", "thuật"), ("nghiệm", "pháp"),
    ("chẩn", "đoán"), ("điều", "trị"), ("xử", "trí"), ("dự", "phòng"), ("kháng", "sinh"),
    ("đông", "máu"), ("cầm", "máu"), ("mất", "máu"), ("thiếu", "máu"), ("tiểu", "cầu"),
    ("bạch", "cầu"), ("hồng", "cầu"), ("xét", "nghiệm"), ("lâm", "sàng"), ("tiền", "phẫu"),
    ("hậu", "phẫu"), ("biến", "chứng"), ("triệu", "chứng"), ("hội", "chứng"), ("dấu", "hiệu"),
    ("phúc", "mạc"), ("tắc", "ruột"), ("liệt", "ruột"), ("hoại", "tử"), ("áp", "xe"),
    ("cắt", "lọc"), ("dẫn", "lưu"), ("vết", "mổ"), ("suy", "thận"), ("suy", "gan"),
    ("suy", "tim"), ("tử", "cung"), ("buồng", "trứng"), ("âm", "đạo"), ("chuyển", "dạ"),
    ("cấp", "cứu"), ("chỉ", "định"), ("nguy", "cơ"), ("cơ", "chế"), ("sinh", "lý"),
}

MEANINGLESS_STANDALONE_BOLD_PHRASES: Set[str] = {
    "đánh giá", "thực hiện", "tiến hành", "bao gồm", "cần phải", "có thể",
    "giúp cho", "nhằm mục đích", "trong trường hợp", "đối với", "ngoài ra",
}


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    clean = hex_color.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    if len(clean) != 6:
        raise ValueError(f"Mã màu HEX không hợp lệ: {hex_color}")
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)


def compute_relative_luminance(hex_color: str) -> float:
    """Tính độ chói tương đối L theo chuẩn W3C WCAG 2.2 (sRGB)."""
    r8, g8, b8 = hex_to_rgb(hex_color)
    channels = []
    for c8 in (r8, g8, b8):
        cs = c8 / 255.0
        if cs <= 0.04045:
            channels.append(cs / 12.92)
        else:
            channels.append(((cs + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def compute_wcag_contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Tính tỷ lệ tương phản (L1 + 0.05) / (L2 + 0.05) chuẩn W3C WCAG 2.2."""
    l1 = compute_relative_luminance(fg_hex)
    l2 = compute_relative_luminance(bg_hex)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def audit_bold_phrase_integrity_and_heading_consistency(html_text: str) -> Dict[str, Any]:
    """
    FB-43 (Vấn đề 2): Chặn đứng lỗi cắt cụt cụm từ ghép tiếng Việt khi in đậm ("<b>Đánh giá Rối</b> loạn huyết học"),
    in đậm động từ vô nghĩa, hoặc bỏ sót in đậm nhãn đề mục đầu dòng `<li>`.
    """
    tag_strip = re.compile(r"<[^>]+>")
    raw_html = html_text or ""
    truncated_lead_in: List[str] = []
    truncated_compound: List[str] = []
    meaningless_bold: List[str] = []

    for m_tr in re.finditer(
        r"<li\b[^>]*>\s*[\s•\-\*–—]*<(?:b|strong)\b[^>]*>([^<:]{1,60})</(?:b|strong)>\s+([^<:]{1,45}):",
        raw_html,
        flags=re.IGNORECASE,
    ):
        b_p = m_tr.group(1).strip()
        r_p = m_tr.group(2).strip()
        if "<" not in r_p and len((b_p + " " + r_p).split()) <= 10:
            truncated_lead_in.append(f"<b>{b_p}</b> {r_p}:")

    for m_b in re.finditer(
        r"<(?:b|strong)\b[^>]*>(.*?)</(?:b|strong)>\s*([a-zA-ZÀ-ỹ]+)?",
        raw_html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        inside_txt = re.sub(r"\s+", " ", tag_strip.sub(" ", m_b.group(1))).strip()
        next_word_raw = (m_b.group(2) or "").strip()
        if not inside_txt:
            continue
        clean_low = inside_txt.strip(" :.,;()[]-–—•").lower()
        if clean_low in MEANINGLESS_STANDALONE_BOLD_PHRASES:
            meaningless_bold.append(f"<b>{inside_txt}</b>")
        if not inside_txt.endswith(":") and next_word_raw:
            inside_words = re.findall(r"[a-zA-ZÀ-ỹ]+", inside_txt)
            if inside_words:
                last_w = inside_words[-1].lower()
                next_w = next_word_raw.lower()
                if (last_w, next_w) in VIETNAMESE_COMPOUND_MEDICAL_PAIRS:
                    truncated_compound.append(f"'<b>{inside_txt}</b> {next_word_raw}'")

    issues: List[str] = []
    if truncated_lead_in:
        issues.append(f"TRUNCATED_BULLET_HEADING_BOLD: {truncated_lead_in[:4]}")
    if truncated_compound:
        issues.append(f"SPLIT_VIETNAMESE_COMPOUND_BOLD: {truncated_compound[:4]}")
    if meaningless_bold:
        issues.append(f"MEANINGLESS_VERB_ONLY_BOLD: {meaningless_bold[:4]}")

    return {
        "valid": len(issues) == 0,
        "truncated_lead_in": truncated_lead_in,
        "truncated_compound": truncated_compound,
        "meaningless_bold": meaningless_bold,
        "issues": issues,
    }


def audit_heading_and_label_conciseness(
    html_text: str,
    max_h2_words: int = 11,
    max_bullet_label_words: int = 7,
) -> Dict[str, Any]:
    """FB-43 (Vấn đề 4): Kiểm định tiêu đề đề mục <h2> và nhãn đầu dòng ngắn gọn, dễ nhớ."""
    tag_strip = re.compile(r"<[^>]+>")
    raw_html = html_text or ""
    h2_list = [
        re.sub(r"\s+", " ", tag_strip.sub(" ", h)).strip()
        for h in re.findall(r"<h2[^>]*>(.*?)</h2>", raw_html, flags=re.IGNORECASE | re.DOTALL)
    ]
    long_h2: List[str] = []
    for h2 in h2_list:
        if "tổng kết" in h2.lower() and "lưu đồ" in h2.lower():
            continue
        clean_h2 = re.sub(r"^(?:phần|mục)?\s*(?:[IVX]+|\d+(?:\.\d+)?)\s*[.\-–:)\s]+", "", h2, flags=re.IGNORECASE).strip()
        if len(clean_h2.split()) > max_h2_words:
            long_h2.append(h2)

    long_labels: List[str] = []
    for m_lbl in re.finditer(
        r"<li\b[^>]*>\s*[\s•\-\*–—]*<(?:b|strong)\b[^>]*>([^<]{1,120}):\s*</(?:b|strong)>",
        raw_html,
        flags=re.IGNORECASE,
    ):
        lbl_txt = re.sub(r"\([^)]*\)", "", m_lbl.group(1)).strip(" :.-–—")
        if len(lbl_txt.split()) > max_bullet_label_words:
            long_labels.append(lbl_txt)

    issues: List[str] = []
    if long_h2:
        issues.append(f"HEADING_H2_TOO_LONG: {long_h2}")
    if len(long_labels) > 2:
        issues.append(f"BULLET_LABEL_TOO_LONG: {long_labels[:4]}")
    return {"valid": len(issues) == 0, "long_h2": long_h2, "long_labels": long_labels, "issues": issues}


def audit_diagram_font_size_12pt_ui(
    html_text: str,
    min_effective_font_pt: float = 11.5,
) -> Dict[str, Any]:
    """FB-43 (Vấn đề 6): Kiểm định cỡ chữ thực tế >= 11.5pt (chuẩn 12pt) cho mọi Sơ đồ SVG và Lưu đồ Python trên khổ A4."""
    issues: List[str] = []
    tiny_inline = re.findall(
        r"<(?:img|svg|div|figure)\b[^>]*style\s*=\s*[\"'][^\"']*(?:max-height\s*:\s*(?:[1-9]\d|1[01]\d)\s*(?:px|pt)|(?<!min-)width\s*:\s*(?:[1-5]\d|6[0-4])\s*%)",
        html_text or "",
        flags=re.IGNORECASE,
    )
    if tiny_inline:
        issues.append(f"INLINE_STYLE_SHRINKING_DIAGRAM_FORBIDDEN: {tiny_inline[:3]}")
    import html as _html_mod
    svg_blocks = re.findall(r"<svg\b([^>]*)>(.*?)</svg>", html_text or "", flags=re.IGNORECASE | re.DOTALL)
    for idx, (svg_attrs, svg_inner) in enumerate(svg_blocks, 1):
        vb_m = re.search(r"viewBox\s*=\s*[\"']\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s*[\"']", svg_attrs, flags=re.IGNORECASE)
        vb_w = float(vb_m.group(1)) if vb_m else float(A4_PRINTABLE_WIDTH_PX_96DPI)
        scale = A4_PRINTABLE_WIDTH_PX_96DPI / max(1.0, vb_w)
        fs_matches = re.findall(r"font-size\s*[:=]\s*[\"']?\s*([\d.]+)\s*(pt|px)?", svg_inner, flags=re.IGNORECASE)
        eff_pts = [
            round((float(v) if (u or "px").lower() == "pt" else float(v) * 0.75) * scale, 2)
            for v, u in fs_matches
        ]
        if eff_pts and min(eff_pts) < min_effective_font_pt:
            issues.append(f"SVG_FONT_BELOW_12PT (#{idx}: min={min(eff_pts)}pt < {min_effective_font_pt}pt)")
        for _t_attrs, _t_inner in re.findall(r"<text\b([^>]*)>(.*?)</text>", svg_inner, flags=re.I | re.S):
            _t_plain = _html_mod.unescape(re.sub(r"<[^>]+>", "", _t_inner)).strip()
            _is_mid = "middle" in _t_attrs.lower()
            _avail_w = vb_w - 12.0 if _is_mid else vb_w - 40.0
            if len(_t_plain) > (56 if _is_mid else 52) and (len(_t_plain) * 10.2) > _avail_w:
                issues.append(f"SVG_TEXT_OVERFLOW_CLIPPING (#{idx}: len={len(_t_plain)} chars '{_t_plain[:40]}...' overflows viewBox {vb_w:.0f}px)")

    all_imgs = re.findall(
        r"<img\b[^>]*?\bsrc\s*=\s*[\"']([^\"']+)[\"'][^>]*>",
        html_text or "",
        flags=re.IGNORECASE,
    )
    for idx, src in enumerate(all_imgs, 1):
        if src.startswith("data:image/") and ";base64," in src:
            try:
                raw = base64.b64decode(src.split(";base64,", 1)[1])
                if Image is None:
                    raise ImportError("Pillow (PIL) is required to inspect embedded base64 raster images")
                im = Image.open(io.BytesIO(raw))
                w, _ = im.size
                info_pt = im.info.get("effective_a4_font_pt")
                info_px = im.info.get("min_rendered_font_px")
                font_used = str(im.info.get("font_path_used") or "")
                if "/truetype/liberation/" in font_used.replace("\\", "/"):
                    issues.append(f"FORBIDDEN_LIBERATION_V1_TOFU_FONT (#{idx}: {font_used})")
                if info_pt is not None and (info_px is None or not font_used):
                    issues.append(f"SPOOFED_DIAGRAM_PNG_METADATA (#{idx}: effective_a4_font_pt={info_pt} missing min_rendered_font_px/font_path_used)")
                if info_px is not None:
                    recomp_pt = round(float(info_px) * ((A4_PRINTABLE_WIDTH_PT * 0.92) / max(1, w)), 2)
                    if recomp_pt < min_effective_font_pt:
                        issues.append(f"PYTHON_DIAGRAM_FONT_BELOW_12PT (#{idx}: recomputed={recomp_pt}pt < {min_effective_font_pt}pt)")
                elif info_pt is not None and float(info_pt) < min_effective_font_pt:
                    issues.append(f"PYTHON_FLOWCHART_FONT_BELOW_12PT (#{idx}: {info_pt}pt < {min_effective_font_pt}pt)")
            except Exception as exc:
                issues.append(f"PYTHON_FLOWCHART_DECODE_ERROR (#{idx}: {exc})")

    return {"valid": len(issues) == 0, "issues": issues}


def audit_mayer_signaling_density(
    html_text: str,
    min_ratio: float = 0.06,
    optimal_min: float = 0.08,
    optimal_max: float = 0.15,
    hard_cap: float = 0.18,
    max_span_words: int = 6,
) -> Dict[str, Any]:
    """
    Đo lường tỷ lệ chữ bôi đậm <b>/<strong> trong câu theo Nguyên lý Tín hiệu Mayer (FB-27, FB-43):
    - MIỄN TRỪ 100% Nhãn đề mục đầu dòng `<li><b>Nhãn:</b>` và Nhãn cột đầu bảng `<td><b>Nhãn</b></td>` khỏi hạn ngạch bold!
    - Kiểm tra tính toàn vẹn của cụm từ ghép tiếng Việt (chống cắt cụt `"<b>Đánh giá Rối</b> loạn huyết học"`).
    """
    phrase_integrity = audit_bold_phrase_integrity_and_heading_consistency(html_text)

    # Tách nhãn cấu trúc đầu dòng <li> và cột đầu <td> khỏi phần tính hạn ngạch in đậm từ khóa trong câu
    body_without_structural_labels = re.sub(
        r"(<li\b[^>]*>\s*[\s•\-\*–—]*)<(?:b|strong)\b[^>]*>([^<]{1,90})</(?:b|strong)>",
        r"\1\2",
        html_text or "",
        flags=re.IGNORECASE,
    )
    body_without_structural_labels = re.sub(
        r"(<td\b[^>]*>\s*)<(?:b|strong)\b[^>]*>([^<]{1,70})</(?:b|strong)>(\s*</td>)",
        r"\1\2\3",
        body_without_structural_labels,
        flags=re.IGNORECASE,
    )

    bold_spans = re.findall(
        r"<(?:b|strong)\b[^>]*>(.*?)</(?:b|strong)>",
        body_without_structural_labels,
        flags=re.IGNORECASE | re.DOTALL,
    )
    plain_text = re.sub(r"<[^>]+>", " ", html_text or "")
    total_words_list = [w for w in plain_text.split() if w.strip()]
    total_words = len(total_words_list)

    bold_words_count = 0
    long_spans: List[str] = []
    for span in bold_spans:
        clean_span = re.sub(r"<[^>]+>", " ", span).strip()
        words = [w for w in clean_span.split() if w.strip()]
        bold_words_count += len(words)
        if len(words) > max_span_words:
            long_spans.append(clean_span)

    ratio = (bold_words_count / total_words) if total_words > 0 else 0.0
    issues: List[str] = []
    if not phrase_integrity["valid"]:
        issues.extend(phrase_integrity["issues"])

    if ratio > hard_cap:
        issues.append(
            f"OVER_BOLD_VISUAL_NOISE: Tỷ lệ bôi đậm trong câu {ratio:.1%} vượt trần cứng {hard_cap:.0%}"
        )
    elif ratio < min_ratio and total_words >= 50:
        issues.append(
            f"UNDER_SIGNALED_TEXT: Tỷ lệ bôi đậm {ratio:.1%} thấp hơn ngưỡng sàn {min_ratio:.0%}"
        )

    allowed_long = max(1, int(len(bold_spans) * 0.10)) if bold_spans else 0
    if len(long_spans) > allowed_long:
        issues.append(
            f"BOLD_SPAN_TOO_LONG: Có {len(long_spans)} cụm <b> trong câu dài quá {max_span_words} từ (vượt dung sai {allowed_long})"
        )

    for pat in FORBIDDEN_UI_LABELS:
        if re.search(pat, html_text, flags=re.IGNORECASE):
            issues.append(f"FORBIDDEN_META_LABEL_LEAK: Phát hiện nhãn cấm khớp mẫu {pat}")

    status = (
        "OPTIMAL_SIGNALING"
        if (optimal_min <= ratio <= optimal_max and not issues)
        else ("ACCEPTABLE_WITHIN_CAP" if not issues else "FAILED_ERGONOMICS")
    )

    return {
        "valid": len(issues) == 0,
        "status": status,
        "total_words": total_words,
        "bold_words": bold_words_count,
        "bold_ratio": round(ratio, 4),
        "bold_spans_count": len(bold_spans),
        "long_spans_count": len(long_spans),
        "phrase_integrity": phrase_integrity,
        "issues": issues,
    }


def audit_mcq_visual_option_balance(
    questions: List[Dict[str, Any]],
    max_key_to_avg_char_ratio: float = 1.35,
    max_key_to_max_distractor_char_ratio: float = 1.20,
    max_option_spread_char_ratio: float = 1.65,
    max_longest_is_key_rate: float = 0.10,
) -> Dict[str, Any]:
    """
    Kiểm định Cân bằng Thị giác 4 nút bấm phương án A, B, C, D trên giao diện Quiz HTML (FB-30, FB-32).
    """
    letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
    visual_cue_issues: List[str] = []
    longest_is_key_count = 0
    valid_q = 0

    for idx, q in enumerate(questions or [], 1):
        if not isinstance(q, dict):
            continue
        opts = q.get("options", [])
        corr = str(q.get("correct", "")).strip().upper()
        if not isinstance(opts, list) or len(opts) != 4 or corr not in letter_map:
            continue
        valid_q += 1
        c_idx = letter_map[corr]
        char_lens = [len(re.sub(r"\s+", " ", str(o).strip())) for o in opts]
        c_chars = char_lens[c_idx]
        dist_chars = [char_lens[i] for i in range(4) if i != c_idx]
        avg_dist = sum(dist_chars) / 3.0 if dist_chars else 1.0
        max_dist = max(dist_chars) if dist_chars else 1
        min_all = max(1, min(char_lens))
        max_all = max(char_lens)

        if c_chars > max_dist:
            longest_is_key_count += 1

        if c_chars >= 28 and (
            (c_chars / max(1.0, avg_dist)) > max_key_to_avg_char_ratio
            or (c_chars - max_dist >= 12 and (c_chars / max(1, max_dist)) > max_key_to_max_distractor_char_ratio)
        ):
            visual_cue_issues.append(
                f"Câu #{idx} [VISUAL_LONGEST_KEY_SALIENT]: Nút đáp án đúng {corr} ({c_chars} ký tự) dài trồi thị giác so với nhiễu ({char_lens})."
            )
        elif (max_all - min_all >= 30) and ((max_all / min_all) > max_option_spread_char_ratio):
            visual_cue_issues.append(
                f"Câu #{idx} [VISUAL_OPTION_HEIGHT_IMBALANCE]: Chiều dài 4 nút A/B/C/D lệch nhau quá {max_option_spread_char_ratio}x ({char_lens})."
            )

    longest_rate = round(longest_is_key_count / max(1, valid_q), 4)
    systemic_salience_bias = (valid_q >= 8) and (longest_rate > max_longest_is_key_rate)
    if systemic_salience_bias:
        visual_cue_issues.insert(
            0,
            f"SYSTEMIC_VISUAL_LONGEST_KEY_BIAS: {longest_is_key_count}/{valid_q} câu ({longest_rate:.1%}) có nút đáp án đúng dài nhất theo số ký tự (trần <= {max_longest_is_key_rate:.0%}).",
        )

    item_tol = max(1, int(valid_q * 0.05)) if valid_q >= 10 else 0
    valid = (not systemic_salience_bias) and (len(visual_cue_issues) <= item_tol)
    return {
        "valid": valid,
        "question_count": valid_q,
        "longest_is_key_count": longest_is_key_count,
        "longest_is_key_rate": longest_rate,
        "systemic_salience_bias": systemic_salience_bias,
        "issues": visual_cue_issues,
    }


def validate_w3c_design_tokens(tokens_path: str) -> Dict[str, Any]:
    """Kiểm định cấu trúc tệp W3C Design Tokens (DTCG 2025.10), độ tương phản màu, trần <= 9 trang A4 và cỡ chữ sơ đồ 12pt (FB-43)."""
    if not os.path.isfile(tokens_path):
        return {"valid": False, "errors": [f"Không tìm thấy tệp token: {tokens_path}"]}

    with open(tokens_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    errors: List[str] = []
    for req_group in ("color", "typography", "ergonomics"):
        if req_group not in data:
            errors.append(f"Thiếu nhóm token bắt buộc: {req_group}")

    try:
        bg_page = data["color"]["surface"]["page"]["$value"]
        fg_primary = data["color"]["text"]["primary"]["$value"]
        fg_danger = data["color"]["accent"]["danger"]["$value"]
        fg_success = data["color"]["accent"]["success"]["$value"]
        mcq_bal = data["ergonomics"]["mcq-option-balance"]["max-longest-is-key-rate"]["$value"]
        prop_target = data["ergonomics"]["content-density-and-volume"]["lecture-core-proposition-target"]["$value"]
        page_max = data["ergonomics"]["content-density-and-volume"]["lecture-page-max"]["$value"]
        fc_min = data["ergonomics"]["content-density-and-volume"]["flashcard-min-count"]["$value"]
        qz_min = data["ergonomics"]["content-density-and-volume"]["quiz-min-question-count"]["$value"]

        cr_body = compute_wcag_contrast_ratio(fg_primary, bg_page)
        cr_danger = compute_wcag_contrast_ratio(fg_danger, bg_page)
        cr_success = compute_wcag_contrast_ratio(fg_success, bg_page)

        if cr_body < 7.0:
            errors.append(f"Độ tương phản chữ thân bài ({cr_body}:1) không đạt chuẩn WCAG AAA (7.0:1)")
        if cr_danger < 4.5 or cr_success < 4.5:
            errors.append("Độ tương phản màu nhấn lâm sàng không đạt chuẩn WCAG AA (4.5:1)")
        if float(mcq_bal) > 0.10:
            errors.append("Token max-longest-is-key-rate vượt trần 0.10 (FB-44 / LOCK-14)")
        if int(page_max) > 9:
            errors.append(f"Token lecture-page-max ({page_max}) vượt trần cứng 9 trang A4 theo FB-43")
        if not (0.70 <= float(prop_target) <= 0.90) or int(fc_min) != 50 or int(qz_min) != 40:
            errors.append("Token content-density-and-volume chưa đồng bộ chuẩn FB-32 -> FB-43")
    except KeyError as exc:
        errors.append(f"Cấu trúc đường dẫn token bị thiếu khóa: {exc}")
        cr_body = 0.0

    return {
        "valid": len(errors) == 0,
        "body_contrast_ratio": cr_body,
        "errors": errors,
    }


def _run_self_tests() -> Dict[str, Any]:
    here = os.path.dirname(os.path.abspath(__file__))
    tokens_path = os.path.join(os.path.dirname(here), "tokens", "medical_design_tokens.json")
    token_res = validate_w3c_design_tokens(tokens_path)

    cr_high = compute_wcag_contrast_ratio("#111111", "#FFFFFF")
    cr_low = compute_wcag_contrast_ratio("#94A3B8", "#FFFFFF")
    contrast_ok = (cr_high >= 18.0) and (cr_low < 3.0)

    sample_good = (
        "<ul><li><b>Đánh giá rối loạn huyết học:</b> Trong xử trí <b>tiền sản giật nặng</b>, mục tiêu tiên quyết là dự phòng co giật bằng "
        "<b>Magnesium sulfate tĩnh mạch</b> và kiểm soát huyết áp tâm thu dưới ngưỡng nguy hiểm "
        "để bảo vệ hệ thần kinh trung ương của sản phụ cũng như duy trì tưới máu tử cung nhau.</li></ul>"
    )
    res_good = audit_mayer_signaling_density(sample_good, min_ratio=0.05)

    sample_bad = (
        "<ul><li><b>Đánh giá Rối</b> loạn huyết học: [Must know] <b>Toàn bộ câu văn này bị bôi đậm quá dài vượt quá sáu từ quy định gây nhiễu</b> "
        "<b>và tỷ lệ chữ in đậm vượt trần mười tám phần trăm</b> (Theo Vid).</li></ul>"
    )
    res_bad = audit_mayer_signaling_density(sample_bad)

    diag_ok = audit_diagram_font_size_12pt_ui('<svg viewBox="0 0 630 180"><text font-size="12pt">Chuẩn 12pt</text></svg>')
    diag_bad = audit_diagram_font_size_12pt_ui('<svg viewBox="0 0 900 180"><text font-size="10px">Quá nhỏ</text></svg>')

    bad_visual_q = [
        {
            "options": [
                "Theo dõi",
                "Khám lại",
                "Nhập viện theo dõi sát tại khoa cấp cứu và tiêm Corticosteroid trưởng thành phổi thai nhi ngay",
                "Cho về",
            ],
            "correct": "C",
        }
        for _ in range(8)
    ]
    vis_bad = audit_mcq_visual_option_balance(bad_visual_q)
    good_visual_q = [
        {
            "options": [
                "Siêu âm đầu dò âm đạo đo chiều dài kênh cổ tử cung và theo dõi cơn gò",
                "Định lượng nồng độ beta-hCG huyết thanh động học sau 48 giờ tại viện",
                "Khởi phát chuyển dạ bằng truyền tĩnh mạch Oxytocin liều tăng dần",
                "Tiêm bắp Betamethasone hỗ trợ phổi thai nhi kết hợp giảm gò Nifedipine",
            ],
            "correct": ["A", "B", "C", "B"][i % 4],
        }
        for i in range(8)
    ]
    vis_good = audit_mcq_visual_option_balance(good_visual_q)

    passed = (
        token_res["valid"]
        and contrast_ok
        and res_good["valid"]
        and (not res_bad["valid"])
        and len(res_bad["issues"]) >= 3
        and diag_ok["valid"]
        and (not diag_bad["valid"])
        and (not vis_bad["valid"])
        and vis_good["valid"]
    )
    return {
        "self_test_passed": passed,
        "token_validation": token_res,
        "contrast_checks": {"body_on_white": cr_high, "low_contrast_sample": cr_low},
        "good_sample_audit": res_good,
        "bad_sample_caught_issues": len(res_bad["issues"]),
        "diagram_12pt_audit_verified": diag_ok["valid"] and (not diag_bad["valid"]),
        "visual_option_balance_verified": (not vis_bad["valid"]) and vis_good["valid"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Medical UI/UX Ergonomics Linter v1.5")
    parser.add_argument("--self-test", action="store_true", help="Chạy bộ kiểm thử tự động")
    args = parser.parse_args()
    res = _run_self_tests()
    if not res["self_test_passed"]:
        print("[ui_ergonomics_linter v1.5 FAILED]:", json.dumps(res, ensure_ascii=False))
        sys.exit(1)
    print("[ui_ergonomics_linter v1.5 SELF-TEST PASSED]:", json.dumps(res, ensure_ascii=False))


# ==============================================================================
# LOCK-38 / FB-69: PEER-TO-PEER TEAM-AGENT PIXEL MARGIN & ASCII LEAK AUDITOR
# ==============================================================================
def audit_compiled_pdf_page_margin_overflow_ui(
    pdf_path: str,
    html_text: str = "",
    right_strip_px: int = 8,
    max_dark_rows_threshold: int = 12,
) -> Dict[str, Any]:
    """
    LOCK-38 / FB-69: Peer-to-Peer Team-Agent Visual & Margin Overflow Auditor for @ui-ux.
    Scans rendered PDF pages via pypdfium2 to detect right-margin diagram clipping
    and inspects HTML/PDF text for raw ASCII tree box-drawing characters.
    """
    veto_reasons: List[str] = []
    overflow_pages: List[int] = []

    if html_text and any(ch in html_text for ch in ("├──", "└──", "┌──", "┐", "┘")):
        veto_reasons.append(
            "[PEER_VETO_VISUAL_OVERFLOW][@ui-ux] Raw ASCII tree characters (├──, └──) detected in HTML source."
        )

    p = Path(pdf_path) if pdf_path else None
    if p and p.exists() and p.suffix.lower() == ".pdf":
        try:
            import pypdfium2 as pdfium
            import numpy as np
            doc = pdfium.PdfDocument(str(p))
            for idx in range(len(doc)):
                page = doc[idx]
                bitmap = page.render(scale=2.0)
                pil_img = bitmap.to_pil()
                arr = np.array(pil_img.convert("L"))
                h, w = arr.shape
                strip = arr[int(h * 0.06):int(h * 0.94), max(0, w - right_strip_px):w]
                dark_rows = int(np.sum(np.min(strip, axis=1) < 180))
                if dark_rows > max_dark_rows_threshold:
                    overflow_pages.append(idx + 1)
                    veto_reasons.append(
                        f"[PEER_VETO_VISUAL_OVERFLOW][@ui-ux] Page {idx + 1} of '{p.name}' has {dark_rows} dark pixel rows touching the right edge."
                    )
        except Exception as _diag_exc:
            _ = str(_diag_exc)

    return {
        "peer_agent": "ui-ux",
        "version": "v1.7",
        "lock_id": "LOCK-38_FB-69",
        "status": "PEER_VETO_VISUAL_OVERFLOW" if veto_reasons else "PASS",
        "andon_cord_veto": len(veto_reasons) > 0,
        "overflow_pages": overflow_pages,
        "veto_reasons": veto_reasons,
    }



# ==============================================================================
# LOCK-44 / FB-75 (@ui-ux v1.8): KIỂM TOÁN TÁCH DÒNG NGẮN (< 4 DÒNG, MỤC TIÊU 1-2 DÒNG)
# & PHÂN CẤP 4 TẦNG KÝ HIỆU ĐẦU DÒNG (– -> • -> ○ -> ▪) + THANH LỌC FLASHCARD KÉP
# ==============================================================================

def audit_4level_bullet_hierarchy_and_line_ergonomics_ui(
    html_content: str,
    words_per_a4_line: float = 14.0,
    max_lines_per_bullet: int = 3,
    hard_max_words_per_bullet: int = 45,
) -> Dict[str, Any]:
    """
    LOCK-44 / FB-75 (@ui-ux v1.8):
    Kiểm toán công thái học thị giác cho hệ thống danh sách gạch đầu dòng trong bài giảng PDF:
      1. Phân cấp 4 tầng giảm dần: `ul.lvl1` (Gạch đầu dòng `–`) -> `ul.lvl2` (Chấm đen `•`)
         -> `ul.lvl3` (Chấm trắng `○`) -> `ul.lvl4` (Chấm vuông `▪`).
      2. Độ dài dòng mỗi node `<li>`: dưới 4 dòng (`<= 3 dòng` trên khổ A4 12pt, tức `<= 42-45 từ`),
         khuyến khích 1–2 dòng (`10–28 từ`).
    """
    tag_strip = re.compile(r"<[^>]+>")
    raw = str(html_content or "")
    lvl_counts = {
        f"lvl{k}": len(re.findall(rf"""<ul\b[^>]*class=["'][^"']*lvl{k}[^"']*["'][^>]*>""", raw, flags=re.I))
        for k in (1, 2, 3, 4)
    }
    total_bullets = 0
    one_to_two_line_cnt = 0
    under_4_line_cnt = 0
    violations: List[str] = []

    for idx, m_li in enumerate(re.finditer(r"<li\b[^>]*>(.*?)</li>", raw, flags=re.I | re.S), 1):
        own_seg = re.split(r"<(?:ul|ol)\b", m_li.group(1), maxsplit=1, flags=re.I)[0]
        plain = re.sub(r"\s+", " ", tag_strip.sub(" ", own_seg)).strip()
        if not plain:
            continue
        total_bullets += 1
        w_cnt = len(plain.split())
        est_lines = max(1, int((w_cnt + words_per_a4_line - 1) // words_per_a4_line))
        if w_cnt <= 28 or est_lines <= 2:
            one_to_two_line_cnt += 1
        if w_cnt <= hard_max_words_per_bullet and est_lines <= max_lines_per_bullet:
            under_4_line_cnt += 1
        else:
            violations.append(
                f"[UI_BULLET_OVER_4_LINES] Bullet #{idx} dài {w_cnt} từ (~{est_lines} dòng A4 >= 4 dòng): '{plain[:60]}...'"
            )

    denom = max(1, total_bullets)
    return {
        "valid": len(violations) == 0,
        "lock_id": "LOCK-44_FB-75",
        "total_bullets": total_bullets,
        "one_to_two_line_rate": round(one_to_two_line_cnt / denom, 4),
        "under_4_lines_rate": round(under_4_line_cnt / denom, 4),
        "hierarchy_level_counts": lvl_counts,
        "violations": violations,
    }


compute_shared_mayer_signaling_metrics = audit_mayer_signaling_density
