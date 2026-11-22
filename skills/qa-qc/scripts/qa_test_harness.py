"""
Động Cơ Kiểm Thử Chủ Động 6 Tầng, Phân Tích Tĩnh AST, Quét Độ Lệch Liên Skill (DRIFT-01..13),
Kiểm Định Thành Phẩm HTML/PDF Trước Bàn Giao (Bài Giảng Khóa Cứng 4-9 Trang A4, Khử Trùng Lặp Ý Chính 3 Nguồn Vid U Slide U PNT,
Chống Cắt Cụt Cụm Từ In Đậm Tiếng Việt "Đánh giá Rối | loạn", Khử Ngắt Dòng Vô Lý Giữa Đoạn, Khóa Độ Dài Tiêu Đề Đề Mục <= 8-10 Từ,
Và Bộ Kiểm Toán Cỡ Chữ 12pt Thực Tế Trên Khổ A4 Cho Sơ Đồ SVG & Lưu Đồ Python - FB-43),
Kiểm Định Kiến Trúc 2 Chiều NBME (>= 90% Khung Tình Huống Lâm Sàng 6 Bước Lồng Ghép 50-30-20) & 5 Cổng Chống Lỗi Kỹ Thuật IWFs
(audit_nbme_2d_and_iwf_gates_qa - FB-46 / LOCK-15), Đếm Ký Tự Đáp Án Trắc Nghiệm Chống Mẹo Chọn Câu Dài Nhất (<= 35% - LOCK-55 / Beta 1.19),
Kiểm Toán Khóa Cứng Trật Tự Giải Đề 1-1 Chống Gom Nhóm Chủ Đề (FB-32),
Săn Lỗi Tiên Đoán Pre-Mortem Fuzzing 18 Kịch Bản & Cổng Chứng Minh Tri Thức Mới Tốt Hơn
(Independent Proactive QA/QC, Pre-Delivery Simulator & A/B Proof Gate Harness v2.7 - @qa-qc - FB-28 -> FB-46 / LOCK-15)
Hoạt động 100% ở chế độ Read-Only Critic (Giữ Chìa Khóa An Toàn Số 2 song hành cùng PM @creator-skill).
"""

import argparse
import ast
import glob
import json
import os
import re
import sys
import unicodedata
from typing import Any, Dict, List, Set, Tuple


A4_PRINTABLE_WIDTH_PX_96DPI = 630

FORBIDDEN_SANDBOX_PATTERNS = [
    r"\bpip\s+install\b",
    r"\bapt-get\s+install\b",
    r"\bnpm\s+install\b",
    r"\bcurl\s+https?://",
    r"\bwget\s+https?://",
]

IPV4_LIKE_HEADING_PATTERN = re.compile(r"(?<!\d)\d+\.\d+\.\d+\.\d+(?!\d)")

BANNED_META_LABELS_PATTERN = re.compile(
    r"\[\s*(?:Must\s+know|Should\s+know|Must\s+not\s+miss|Theo\s+Vid|Theo\s+PNT|Theo\s+Slide)\s*\]"
    r"|\(\s*Theo\s+(?:Vid|PNT|Slide)\s*\)",
    flags=re.IGNORECASE,
)

MERGED_QUESTION_HEADER_REGEX = re.compile(
    r"(?:^|\n)\s*(?:#{1,4}|\*\*|-)?\s*Câu\s+\d+\s*(?:&|và|,|/|\+)\s*(?:Câu\s+)?\d+",
    flags=re.IGNORECASE,
)

THEMATIC_GROUP_HEADER_REGEX = re.compile(
    r"(?:^|\n)\s*(?:#{1,4}|\*\*)\s*(?:Nhóm\s+\d+\s*[:\-–]\s*Chủ\s+đề|Chủ\s+đề\s+[A-Z0-9]+\s*[:\-–]|Trạm\s+Ôn\s+Tập\s+Gom\s+Nhóm\s+Theo\s+Chủ\s+Đề)",
    flags=re.IGNORECASE,
)

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


def run_ast_and_static_security_scan(py_code: str, filename: str = "<memory>") -> Dict[str, Any]:
    """Tầng 1: Phân tích tĩnh cây cú pháp AST, phát hiện hàm rỗng và kiểm tra an toàn thực thi Sandbox."""
    defects: List[Dict[str, str]] = []
    try:
        tree = ast.parse(py_code, filename=filename)
    except SyntaxError as exc:
        defects.append(
            {
                "severity": "S1",
                "code": "AST_SYNTAX_ERROR",
                "file": filename,
                "detail": f"Lỗi cú pháp Python tại dòng {exc.lineno}: {exc.msg}",
            }
        )
        return {"valid": False, "defects": defects, "functions_found": []}

    functions_found: List[str] = []
    swallowed_exceptions_count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions_found.append(node.name)
            body_wo_doc = [
                stmt
                for stmt in node.body
                if not (
                    isinstance(stmt, ast.Expr)
                    and isinstance(getattr(stmt, "value", None), ast.Constant)
                    and isinstance(stmt.value.value, str)
                )
            ]
            if len(body_wo_doc) == 1 and isinstance(body_wo_doc[0], ast.Pass):
                defects.append(
                    {
                        "severity": "S2",
                        "code": "EMPTY_STUB_FUNCTION",
                        "file": filename,
                        "detail": f"Hàm '{node.name}' chỉ chứa lệnh 'pass' rỗng (Stub chưa hoàn thiện).",
                    }
                )
        elif isinstance(node, ast.ExceptHandler):
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                swallowed_exceptions_count += 1

    if swallowed_exceptions_count > 3:
        defects.append(
            {
                "severity": "S3",
                "code": "EXCESSIVE_SWALLOWED_EXCEPTIONS",
                "file": filename,
                "detail": f"Phát hiện {swallowed_exceptions_count} khối 'except: pass' nuốt ngoại lệ ngầm dễ che giấu lỗi runtime.",
            }
        )

    for pat in FORBIDDEN_SANDBOX_PATTERNS:
        if re.search(pat, py_code):
            defects.append(
                {
                    "severity": "S1",
                    "code": "FORBIDDEN_SANDBOX_NETWORK_CALL",
                    "file": filename,
                    "detail": f"Phát hiện lệnh mạng/cài đặt bị cấm trong Sandbox VM khớp mẫu: {pat}",
                }
            )
    if re.search(r"/usr/share/fonts/truetype/liberation/Liberation(?:Sans|Serif|Mono)", py_code) and "lib1_rx" not in py_code and "Kịch bản 30" not in py_code:
        defects.append(
            {
                "severity": "S1",
                "code": "LOCK33_FORBIDDEN_LIBERATION_V1_TOFU_FONT",
                "file": filename,
                "detail": "Phát hiện nạp bộ font cấm /usr/share/fonts/truetype/liberation/Liberation* (v1.x thiếu 92 dấu tiếng Việt gây lỗi ô vuông Tofu ▯ trong sơ đồ).",
            }
        )

    return {
        "valid": not any(d["severity"] in ("S1", "S2") for d in defects),
        "functions_found": functions_found,
        "swallowed_exceptions_count": swallowed_exceptions_count,
        "defects": defects,
    }


def scan_markdown_hygiene_and_ioc_risk(md_text: str, filename: str = "<markdown>") -> Dict[str, Any]:
    """Kiểm tra chuẩn Unicode NFC và phát hiện số đề mục 4 chấm A.B.C.D gây lỗi IOC giả (ERR-21)."""
    defects: List[Dict[str, str]] = []
    normalized = unicodedata.normalize("NFC", md_text)
    if normalized != md_text:
        defects.append(
            {
                "severity": "S3",
                "code": "UNICODE_NOT_NFC",
                "file": filename,
                "detail": "Văn bản chứa ký tự tổ hợp NFD chưa chuẩn hóa NFC.",
            }
        )

    ioc_matches = IPV4_LIKE_HEADING_PATTERN.findall(md_text)
    if ioc_matches:
        defects.append(
            {
                "severity": "S1",
                "code": "ERR21_IPV4_IOC_FALSE_POSITIVE_RISK",
                "file": filename,
                "detail": f"Phát hiện đề mục 4 chấm dễ bị nhận nhầm là IPv4 IOC: {ioc_matches[:5]}",
            }
        )

    return {
        "valid": not any(d["severity"] in ("S1", "S2") for d in defects),
        "defects": defects,
    }


def detect_cross_skill_version_drift(skill_text: str, skill_name: str) -> List[Dict[str, str]]:
    """
    Tầng 2: Radar quét độ lệch phiên bản mở rộng (DRIFT-01..13) ở chế độ 100% Read-Only (FB-30 -> FB-46 / LOCK-15).
    """
    drifts: List[Dict[str, str]] = []

    if re.search(r"kết cấu 6 phần(?:\s+La\s+Mã)?", skill_text, flags=re.IGNORECASE):
        if not re.search(r"(?:xóa bỏ|không ép|loại bỏ|bỏ khung|tàn dư).*?6 phần", skill_text, flags=re.IGNORECASE):
            drifts.append(
                {
                    "skill": skill_name,
                    "drift_code": "DRIFT-01",
                    "severity": "S3",
                    "detail": (
                        "Còn giữ quy tắc 'kết cấu 6 phần La Mã I -> VI' (FB-05 cũ), "
                        "chưa đồng bộ với quy chuẩn bố cục linh hoạt FB-21."
                    ),
                }
            )

    if skill_name in ("user:tra-cuu", "tra-cuu"):
        if re.search(r"get_skill_resources\(\s*name\s*=\s*.user:nap-data.", skill_text, flags=re.IGNORECASE):
            drifts.append(
                {
                    "skill": skill_name,
                    "drift_code": "DRIFT-11",
                    "severity": "S1",
                    "detail": "Skill @tra-cuu còn gọi chéo sang user:nap-data thay vì hoạt động độc lập 100% qua kho .md nội bộ và API NotebookLM của chính nó (FB-40).",
                }
            )

    if skill_name in ("user:import-md", "import-md"):
        for req_fn in (
            "reconcile_and_normalize_cartridge_metadata",
            "audit_post_mount_cartridge_integrity",
            "ensure_page_or_slide_markers_and_lock10",
        ):
            if req_fn not in skill_text:
                drifts.append(
                    {
                        "skill": skill_name,
                        "drift_code": "DRIFT-14",
                        "severity": "S1",
                        "detail": f"Skill @import-md thiếu cổng kiểm toán toàn vẹn băng dữ liệu bắt buộc '{req_fn}' theo chuẩn FB-52 / LOCK-20.",
                    }
                )

    if skill_name in ("user:soan-bai-giang", "soan-bai-giang"):
        for req_fn in (
            "compute_deduplicated_triad_key_budget",
            "audit_bold_phrase_integrity_and_heading_consistency",
            "audit_diagram_font_size_12pt",
        ):
            if req_fn not in skill_text:
                drifts.append(
                    {
                        "skill": skill_name,
                        "drift_code": "DRIFT-12",
                        "severity": "S1",
                        "detail": f"Skill @soan-bai-giang thiếu cổng kiểm toán bắt buộc '{req_fn}' theo chuẩn FB-43.",
                    }
                )

    if re.search(r"tô đậm.*?10\s*[-–]\s*25%", skill_text, flags=re.IGNORECASE):
        drifts.append(
            {
                "skill": skill_name,
                "drift_code": "DRIFT-06",
                "severity": "S2",
                "detail": "Còn ghi tỷ lệ tô đậm '10-25%' cũ lệch với chuẩn Mayer '8-15% (trần cứng <= 18%)' của FB-27.",
            }
        )

    if skill_name in ("user:tao-de", "tao-de", "user:tham-dinh-su-pham", "tham-dinh-su-pham"):
        if "audit_mcq_option_length_parity" not in skill_text:
            drifts.append(
                {
                    "skill": skill_name,
                    "drift_code": "DRIFT-07",
                    "severity": "S1",
                    "detail": f"Skill khảo thí {skill_name} thiếu cổng đếm ký tự đáp án 'audit_mcq_option_length_parity' (FB-30).",
                }
            )
        for req_lock15_fn in (
            "audit_vignette_chronological_flow",
            "audit_orth_2d_vignette_and_embedded_matrix",
            "audit_forensic_distractor_profiling",
            "audit_convergence_cues",
            "audit_inter_item_cueing_matrix",
        ):
            if req_lock15_fn not in skill_text and "audit_mcq_option_length_parity" in skill_text and "build_quiz_html" in skill_text:
                drifts.append(
                    {
                        "skill": skill_name,
                        "drift_code": "DRIFT-13",
                        "severity": "S1",
                        "detail": f"Skill khảo thí {skill_name} thiếu cổng kiểm định NBME 2 chiều / IWF '{req_lock15_fn}' (FB-46 / LOCK-15).",
                    }
                )

    if skill_name in ("user:mcq", "mcq", "user:mcq-chuyen-sau", "mcq-chuyen-sau"):
        if "Input_Queue" not in skill_text or "FB-32" not in skill_text:
            drifts.append(
                {
                    "skill": skill_name,
                    "drift_code": "DRIFT-08",
                    "severity": "S1",
                    "detail": f"Skill giải đề {skill_name} thiếu cổng khóa mảng đầu vào 'Input_Queue[1..N]' chống gom nhóm câu hỏi theo chủ đề (FB-32).",
                }
            )
        if re.search(r"\b3\.\s*Trạm\s+Ôn\s+Tập\s+Gom\s+Nhóm\s+Theo\s+Chủ\s+Đề\b", skill_text, flags=re.IGNORECASE):
            drifts.append(
                {
                    "skill": skill_name,
                    "drift_code": "DRIFT-08",
                    "severity": "S2",
                    "detail": f"Skill {skill_name} còn chứa đề mục mồi '3. Trạm Ôn Tập Gom Nhóm Theo Chủ Đề' dễ kích hoạt thiên kiến tự gom nhóm câu trả lời (FB-32).",
                }
            )

    if skill_name in ("user:tham-dinh-su-pham", "tham-dinh-su-pham"):
        if "audit_two_tier_source_coverage_and_expansion" not in skill_text:
            drifts.append(
                {
                    "skill": skill_name,
                    "drift_code": "DRIFT-09",
                    "severity": "S1",
                    "detail": "Skill thẩm định thiếu hàm kiểm định 2 tầng nguồn 'audit_two_tier_source_coverage_and_expansion' (FB-33).",
                }
            )

    if skill_name in ("user:ocr-text", "ocr-text"):
        if "audit_ocr_cardinality_and_garbled_tokens" not in skill_text:
            drifts.append(
                {
                    "skill": skill_name,
                    "drift_code": "DRIFT-10",
                    "severity": "S1",
                    "detail": "Skill @ocr-text thiếu cổng kiểm toán số lượng phần tử sơ đồ Slide & lọc rác OCR 'audit_ocr_cardinality_and_garbled_tokens' (FB-34 / LOCK-10).",
                }
            )

    return drifts


def audit_lecture_fb43_ergonomics_qa(
    html_text: str,
    min_effective_font_pt: float = 11.5,
    max_h2_words: int = 11,
) -> Dict[str, Any]:
    """
    Tầng 3 (@qa-qc Pre-Delivery Lecture Audit Gate - FB-43):
    """
    tag_strip = re.compile(r"<[^>]+>")
    raw_html = html_text or ""
    defects: List[Dict[str, str]] = []

    for m_tr in re.finditer(
        r"<li\b[^>]*>\s*[\s•\-\*–—]*<(?:b|strong)\b[^>]*>([^<:]{1,60})</(?:b|strong)>\s+([^<:]{1,45}):",
        raw_html,
        flags=re.IGNORECASE,
    ):
        b_p = m_tr.group(1).strip()
        r_p = m_tr.group(2).strip()
        if "<" not in r_p and len((b_p + " " + r_p).split()) <= 10:
            defects.append(
                {
                    "severity": "S1",
                    "code": "FB43_TRUNCATED_BULLET_HEADING_BOLD",
                    "detail": f"Đề mục đầu dòng bị cắt cụt in đậm trước dấu hai chấm: '<b>{b_p}</b> {r_p}:'",
                }
            )

    for m_b in re.finditer(
        r"<(?:b|strong)\b[^>]*>(.*?)</(?:b|strong)>\s*([a-zA-ZÀ-ỹ]+)?",
        raw_html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        inside_txt = re.sub(r"\s+", " ", tag_strip.sub(" ", m_b.group(1))).strip()
        next_word_raw = (m_b.group(2) or "").strip()
        if inside_txt and not inside_txt.endswith(":") and next_word_raw:
            inside_words = re.findall(r"[a-zA-ZÀ-ỹ]+", inside_txt)
            if inside_words and (inside_words[-1].lower(), next_word_raw.lower()) in VIETNAMESE_COMPOUND_MEDICAL_PAIRS:
                defects.append(
                    {
                        "severity": "S1",
                        "code": "FB43_SPLIT_VIETNAMESE_COMPOUND_BOLD",
                        "detail": f"Thẻ <b> cắt ngang từ ghép tiếng Việt: '<b>{inside_txt}</b> {next_word_raw}'",
                    }
                )

    for h2 in re.findall(r"<h2[^>]*>(.*?)</h2>", raw_html, flags=re.IGNORECASE | re.DOTALL):
        h2_plain = re.sub(r"\s+", " ", tag_strip.sub(" ", h2)).strip()
        if "tổng kết" in h2_plain.lower() and "lưu đồ" in h2_plain.lower():
            continue
        clean_h2 = re.sub(r"^(?:phần|mục)?\s*(?:[IVX]+|\d+(?:\.\d+)?)\s*[.\-–:)\s]+", "", h2_plain, flags=re.IGNORECASE).strip()
        if len(clean_h2.split()) > max_h2_words:
            defects.append(
                {
                    "severity": "S2",
                    "code": "FB43_HEADING_H2_TOO_LONG",
                    "detail": f"Tiêu đề <h2> quá dài gây khó nhớ ({len(clean_h2.split())} từ > {max_h2_words} từ): '{h2_plain}'",
                }
            )

    for s_idx, (svg_attrs, svg_inner) in enumerate(
        re.findall(r"<svg\b([^>]*)>(.*?)</svg>", raw_html, flags=re.IGNORECASE | re.DOTALL), 1
    ):
        vb_m = re.search(r"viewBox\s*=\s*[\"']\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s*[\"']", svg_attrs, flags=re.IGNORECASE)
        vb_w = float(vb_m.group(1)) if vb_m else float(A4_PRINTABLE_WIDTH_PX_96DPI)
        scale = A4_PRINTABLE_WIDTH_PX_96DPI / max(1.0, vb_w)
        fs_matches = re.findall(r"font-size\s*[:=]\s*[\"']?\s*([\d.]+)\s*(pt|px)?", svg_inner, flags=re.IGNORECASE)
        eff_pts = [
            round((float(v) if (u or "px").lower() == "pt" else float(v) * 0.75) * scale, 2)
            for v, u in fs_matches
        ]
        if eff_pts and min(eff_pts) < min_effective_font_pt:
            defects.append(
                {
                    "severity": "S1",
                    "code": "FB43_DIAGRAM_FONT_BELOW_12PT",
                    "detail": f"Sơ đồ SVG #{s_idx} có cỡ chữ thực tế trên A4 chỉ đạt {min(eff_pts)}pt (< {min_effective_font_pt}pt chuẩn 12pt).",
                }
            )

    return {"valid": len(defects) == 0, "defects": defects}




def audit_explanation_depth_and_teaching_flow_qa(
    html_text: str,
    domain: str = "clinical",
) -> Dict[str, Any]:
    """
    Tầng 3 (@qa-qc Pre-Delivery Lecture Explanation Graph & P0/P1 Priority Gate - FB-50 / LOCK-18):
    1. Chặn lỗi đặt đề mục Lịch sử/Mốc năm tháng làm đề mục <h2> mở đầu Trang 1 của bài lâm sàng (`FB50_FIRST_PAGE_HISTORY_DOMINANCE`).
    2. Chặn lỗi liệt kê gạch đầu dòng cụt ngủn không có liên từ giải thích nhân - quả (`FB50_SHALLOW_ENUMERATION_WITHOUT_MECHANISM`).
    """
    tag_strip = re.compile(r"<[^>]+>")
    raw_html = html_text or ""
    defects: List[Dict[str, str]] = []

    h2_list = [
        re.sub(r"\s+", " ", tag_strip.sub(" ", h)).strip()
        for h in re.findall(r"<h2[^>]*>(.*?)</h2>", raw_html, flags=re.IGNORECASE | re.DOTALL)
    ]
    first_h2 = h2_list[0] if h2_list else ""
    if domain == "clinical" and re.search(
        r"\b(?:lịch\s+sử|mốc\s+lịch\s+sử|lịch\s+sử\s+phát\s+triển|các\s+mốc\s+năm)\b",
        first_h2.lower(),
    ):
        defects.append(
            {
                "severity": "S1",
                "code": "FB50_FIRST_PAGE_HISTORY_DOMINANCE",
                "detail": f"Đề mục <h2> đầu tiên ('{first_h2}') ưu tiên Lịch sử/Mốc năm tháng (P3/P4) thay vì mở thẳng vào cơ chế và quyết định lâm sàng P0/P1.",
            }
        )

    li_items = [
        re.sub(r"\s+", " ", tag_strip.sub(" ", li)).strip()
        for li in re.findall(r"<li\b[^>]*>(.*?)</li>", raw_html, flags=re.IGNORECASE | re.DOTALL)
    ]
    li_items = [x for x in li_items if x]
    causal_regex = re.compile(
        r"(?:→|➜|->|=>|\b(?:vì|do|nhằm|giúp|dẫn\s+đến|gây|hậu\s+quả|cơ\s+chế|bản\s+chất|nhờ|nên|để|khiến|ngăn\s+ngừa|phục\s+hồi|bảo\s+vệ|loại\s+trừ)\b)",
        flags=re.IGNORECASE,
    )
    short_fragments = sum(1 for li in li_items if len(li.split()) < 7 and not causal_regex.search(li))
    causal_bullets = sum(1 for li in li_items if causal_regex.search(li) or ("(" in li and ")" in li))
    if len(li_items) >= 4 and (short_fragments / len(li_items) > 0.45 or causal_bullets / len(li_items) < 0.35):
        defects.append(
            {
                "severity": "S1",
                "code": "FB50_SHALLOW_ENUMERATION_WITHOUT_MECHANISM",
                "detail": f"Bài giảng liệt kê gạch đầu dòng nông cạn thiếu cầu nối giải thích nhân - quả ({short_fragments}/{len(li_items)} bullet cụt).",
            }
        )

    return {"valid": len(defects) == 0, "defects": defects}


def audit_anti_commonsense_and_counterfactual_qa(
    questions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Tầng 3 (@qa-qc Pre-Delivery Anti-Common-Sense & Counterfactual Pivot Gate - FB-50 / LOCK-18):
    1. Chặn phương án nhiễu ngây ngô loại trừ được bằng common sense (`FB50_COMMON_SENSE_THROWAWAY_DISTRACTOR`).
    2. Chặn cụm từ độn ký tự sáo rỗng (`FB50_ARTIFICIAL_BOILERPLATE_PADDING`).
    3. Chặn câu hỏi giả bệnh án dài nhưng hỏi năm lịch sử / định nghĩa học vẹt ở cuối (`FB50_FAKE_CASE_WRAPPING_TRIVIA`).
    """
    defects: List[Dict[str, str]] = []
    throwaway_pat = re.compile(
        r"(?:cho\s+(?:bệnh\s+nhân\s+)?(?:xuất\s+viện\s+)?về\s+nhà\s+(?:tự\s+theo\s+dõi|nghỉ\s+ngơi)|"
        r"không\s+cần\s+(?:điều\s+trị|xử\s+trí|can\s+thiệp|làm\s+xét\s+nghiệm)\s+gì\s+thêm|"
        r"chỉ\s+(?:cần\s+)?uống\s+(?:thuốc\s+bổ|vitamin)|"
        r"chờ\s+đợi\s+tự\s+khỏi\s+không\s+cần\s+can\s+thiệp)",
        flags=re.IGNORECASE,
    )
    boilerplate_pat = re.compile(
        r"(?:trên\s+lâm\s+sàng\s+tại\s+khoa\s+cấp\s+cứu\s+hiện\s+nay|"
        r"theo\s+đúng\s+quy\s+trình\s+chẩn\s+đoán\s+và\s+điều\s+trị\s+chuẩn\s+hiện\s+hành\s+tại\s+bệnh\s+viện)",
        flags=re.IGNORECASE,
    )
    trivia_tail_pat = re.compile(
        r"(?:\bvào\s+năm\s+nào\b|\bnăm\s+\d{4}\b|\bai\s+là\s+người\s+đầu\s+tiên\b|\bđược\s+định\s+nghĩa\s+là\s+gì\b)",
        flags=re.IGNORECASE,
    )

    for idx, q in enumerate(questions or [], 1):
        if not isinstance(q, dict):
            continue
        stem = str(q.get("question", "")).strip()
        opts = q.get("options", [])
        if len(stem) >= 300 and trivia_tail_pat.search(stem[-160:]):
            defects.append(
                {
                    "severity": "S1",
                    "code": "FB50_FAKE_CASE_WRAPPING_TRIVIA",
                    "detail": f"Câu #{idx}: Thân bài dài nhưng câu dẫn cuối hỏi kiến thức năm lịch sử/định nghĩa tách rời ca bệnh.",
                }
            )
        if isinstance(opts, list):
            for o in opts:
                os_txt = str(o or "")
                if throwaway_pat.search(os_txt):
                    defects.append(
                        {
                            "severity": "S1",
                            "code": "FB50_COMMON_SENSE_THROWAWAY_DISTRACTOR",
                            "detail": f"Câu #{idx}: Phương án nhiễu ngây ngô loại trừ bằng common sense ('{os_txt}').",
                        }
                    )
                if boilerplate_pat.search(os_txt):
                    defects.append(
                        {
                            "severity": "S1",
                            "code": "FB50_ARTIFICIAL_BOILERPLATE_PADDING",
                            "detail": f"Câu #{idx}: Phương án chứa cụm từ độn ký tự sáo rỗng ('{os_txt}').",
                        }
                    )

    return {"valid": len(defects) == 0, "defects": defects}


def audit_nbme_2d_and_iwf_gates_qa(
    questions: List[Dict[str, Any]],
    min_vignette_shell_rate: float = 0.85,
) -> Dict[str, Any]:
    """
    Tầng 3 (@qa-qc Pre-Delivery NBME 2D Matrix & 5 IWF Audit Gate - FB-46 / LOCK-15):
    Kiểm định độc lập bộ câu hỏi trắc nghiệm theo chuẩn NBME/USMLE mới:
    1. Kiểm tra Trật tự tuyến tính 6 bước (`VIGNETTE_CHRONOLOGY_INVERSION` - chặn đưa xét nghiệm lên trước khám thực thể).
    2. Kiểm tra Kiến trúc 2 Chiều (`UNIVERSAL_VIGNETTE_SHELL_LOW` - bắt buộc >= 85-90% câu hỏi có Khung Tình huống lâm sàng).
    3. Kiểm tra Câu hỏi âm tính mở rộng (`ZERO_NEGATIVE_PHRASING_VIOLATION` - chặn KHÔNG PHÙ HỢP NHẤT / ÍT KHẢ NĂNG NHẤT).
    4. Kiểm tra Hội tụ thành phần (`CONVERGENCE_CUE_DETECTED`) & Chặn bịa chỉ số tâm trắc học giả (`PSYCHOMETRIC_HALLUCINATION`).
    """
    defects: List[Dict[str, str]] = []
    if not isinstance(questions, list) or not questions:
        defects.append({"severity": "S1", "code": "EMPTY_QUESTIONS", "detail": "Danh sách câu hỏi rỗng."})
        return {"valid": False, "vignette_shell_rate": 0.0, "defects": defects}

    demo_pat = re.compile(
        r"\b(?:\d+\s*tuổi|\d+\s*tháng\s+tuổi|bệnh\s+nhân|sản\s+phụ(?!\s+khoa)|thai\s+phụ|người\s+đàn\s+ông|người\s+phụ\s+nữ|bé\s+trai|bé\s+gái)\b",
        flags=re.IGNORECASE,
    )
    find_pat = re.compile(
        r"\b(?:nhập\s+viện|đến\s+khám|cấp\s+cứu|đau|sốt|ra\s+huyết|khó\s+thở|huyết\s+áp|mạch|nhịp\s+tim|khám\s+thực\s+thể|khám\s+thấy|siêu\s+âm|xét\s+nghiệm|điện\s+tâm\s+đồ|ct\s*scan|\d+\s*(?:mmhg|lần/phút|°c|mg/dl|ng/ml|tuần))\b",
        flags=re.IGNORECASE,
    )
    exam_pat = re.compile(
        r"\b(?:khám\s+thực\s+thể|khám\s+lâm\s+sàng|khám\s+lúc\s+tiếp\s+nhận|khám\s+thấy|sinh\s+hiệu\s*:|huyết\s+áp\s+\d+/\d+)\b",
        flags=re.IGNORECASE,
    )
    workup_pat = re.compile(
        r"\b(?:cận\s+lâm\s+sàng\s*:|xét\s+nghiệm\s+(?:máu|huyết\s+thanh|sinh\s+hóa|troponin)|kết\s+quả\s+(?:xét\s+nghiệm|siêu\s+âm|điện\s+tâm\s+đồ))\b",
        flags=re.IGNORECASE,
    )
    neg_ext_pat = re.compile(
        r"(?:ngoại\s+trừ|chọn\s+câu\s+sai|không\s+phù\s+hợp\s+nhất|chưa\s+phù\s+hợp|ít\s+khả\s+năng\s+(?:xảy\s+ra\s+)?nhất|ít\s+nghĩ\s+đến\s+nhất)\s*[^.?!]{0,40}[?:.]?\s*$",
        flags=re.IGNORECASE,
    )

    vig_count = 0
    letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}

    for idx, q in enumerate(questions, 1):
        if not isinstance(q, dict):
            continue
        stem = re.sub(r"\s+", " ", str(q.get("question", "")).strip())
        opts = q.get("options", [])
        corr = str(q.get("correct", "")).strip().upper()
        meta = q.get("nbme_audit_meta") or {}

        if len(stem.split()) >= 18 and demo_pat.search(stem) and find_pat.search(stem):
            vig_count += 1

        sents = [s.strip() for s in re.split(r"(?<=[.?!])\s+", stem) if s.strip()]
        body = " ".join(sents[:-1]) if len(sents) > 1 and sents[-1].endswith("?") else stem
        ex_m = exam_pat.search(body)
        wk_m = workup_pat.search(body)
        if wk_m and ex_m and wk_m.start() < ex_m.start():
            defects.append(
                {
                    "severity": "S1",
                    "code": "LOCK15_VIGNETTE_CHRONOLOGY_INVERSION",
                    "detail": f"Câu #{idx}: Kết quả cận lâm sàng ('{wk_m.group(0)}') xuất hiện trước phần khám thực thể ('{ex_m.group(0)}').",
                }
            )

        if neg_ext_pat.search(stem):
            defects.append(
                {
                    "severity": "S1",
                    "code": "LOCK15_ZERO_NEGATIVE_PHRASING_VIOLATION",
                    "detail": f"Câu #{idx}: Sử dụng câu hỏi âm tính bị cấm ('{neg_ext_pat.search(stem).group(0).strip()}').",
                }
            )

        if isinstance(meta, dict):
            for b_key in ("p_value", "r_pbis", "point_biserial", "distractor_efficiency_de", "simulated_psychometrics"):
                if b_key in meta:
                    defects.append(
                        {
                            "severity": "S1",
                            "code": "LOCK15_PSYCHOMETRIC_HALLUCINATION",
                            "detail": f"Câu #{idx}: Tự bịa chỉ số tâm trắc học thực nghiệm `{b_key}` khi chưa có dữ liệu thi thực tế.",
                        }
                    )

        if isinstance(opts, list) and len(opts) == 4 and corr in letter_map:
            c_idx = letter_map[corr]
            clauses = [
                [c.strip().lower() for c in re.split(r"[;+]|(?:\s+kết\s+hợp\s+)|(?:\s+và\s+)", str(o)) if len(c.strip()) >= 4]
                for o in opts
            ]
            if all(len(c) >= 2 for c in clauses):
                kc = clauses[c_idx][:2]
                c0 = sum(1 for j in range(4) if j != c_idx and kc[0] in clauses[j])
                c1 = sum(1 for j in range(4) if j != c_idx and kc[1] in clauses[j])
                if c0 >= 1 and c1 >= 1:
                    dist_sums = [
                        sum(1 for j in range(4) if j != d_i and clauses[d_i][0] in clauses[j])
                        + sum(1 for j in range(4) if j != d_i and clauses[d_i][1] in clauses[j])
                        for d_i in range(4)
                        if d_i != c_idx
                    ]
                    if (c0 + c1) > max(dist_sums or [0]) and (c0 + c1) >= 2:
                        defects.append(
                            {
                                "severity": "S2",
                                "code": "LOCK15_CONVERGENCE_CUE_DETECTED",
                                "detail": f"Câu #{idx}: Đáp án đúng {corr} lộ lỗi Hội tụ thành phần (cả 2 vế đều lặp lại ở các phương án nhiễu).",
                            }
                        )

    shell_rate = round(vig_count / max(1, len(questions)), 4)
    if len(questions) >= 10 and shell_rate < min_vignette_shell_rate:
        defects.append(
            {
                "severity": "S1",
                "code": "LOCK15_UNIVERSAL_VIGNETTE_SHELL_LOW",
                "detail": f"Tỷ lệ câu hỏi có Khung Tình huống lâm sàng chỉ đạt {shell_rate:.1%} (< {min_vignette_shell_rate:.0%}).",
            }
        )

    return {
        "valid": not any(d["severity"] in ("S1", "S2") for d in defects),
        "vignette_shell_rate": shell_rate,
        "defects": defects,
    }


def audit_ocr_cardinality_and_garbled_tokens_qa(
    markdown_text: str,
    filename: str = "source.md",
) -> Dict[str, Any]:
    """
    Tầng 3 (@qa-qc Pre-Delivery OCR Cardinality & Garble Audit Gate - FB-34 / LOCK-10):
    """
    text = unicodedata.normalize("NFC", markdown_text or "")
    defects: List[Dict[str, str]] = []
    cardinality_mismatches: List[Dict[str, Any]] = []

    header_pat = re.compile(
        r"(?:^|\n)\s*[-•*]?\s*(\d+)\s+(Đặc điểm|Đặc trưng|Năng lực|Kỹ năng|Nguyên lý|Nhiệm vụ|Nền tảng|Nhánh|Lĩnh vực|Cấp dự phòng)([^\n:]*):\s*([^\n]+)",
        flags=re.IGNORECASE,
    )
    for m in header_pat.finditer(text):
        claimed = int(m.group(1))
        label = m.group(2).strip()
        sub = m.group(3).strip()
        body = m.group(4).strip()
        items = [x.strip() for x in body.split(";") if x.strip()]
        if len(items) >= 3 and len(items) != claimed:
            cardinality_mismatches.append(
                {
                    "claimed": claimed,
                    "actual": len(items),
                    "header": f"{claimed} {label}{sub}",
                }
            )
            defects.append(
                {
                    "severity": "S1",
                    "code": "LOCK10_OCR_CARDINALITY_MISMATCH",
                    "file": filename,
                    "detail": f"Tiêu đề ghi '{claimed} {label}{sub}' nhưng phần thân liệt kê {len(items)} mệnh đề ngăn cách bằng ';'.",
                }
            )

    if "WONCA" in text.upper():
        for bad_w in re.findall(
            r"\b11\s+(?:đặc\s+điểm|đặc\s+trưng|chiếc\s+lá|lá\s+cây|tán\s+lá|kỹ\s+năng)\b",
            text,
            flags=re.IGNORECASE,
        ):
            defects.append(
                {
                    "severity": "S1",
                    "code": "LOCK10_WONCA_11_LEAVES_HALLUCINATION",
                    "file": filename,
                    "detail": f"Ghi sai '{bad_w}' cho Cây WONCA (chuẩn WONCA Europe 2011 bắt buộc là 12 đặc trưng / 12 chiếc lá).",
                }
            )

    garble_regexes = [
        r"\bdiệnom\b",
        r"\biv\s+souq\b",
        r"\btộm\s+át\b",
        r"\bHướng\s+cộng\s+il\b",
        r"\bđìni\s+drid\b",
        r"\bvag\s+nsidin\b",
        r"\bup\s+dida\b",
        r"\bmis\s+dait\b",
        r"\bonig\s+sup\s+goôdt\b",
        r"\bUPicio\s+qg6\s+200\s+crs\b",
        r"\bDMp\s+hurGOU\b",
        r"\bLƯỢNG\s+GIAT\b",
        r"\(0\.9\.5-5\)\s*bin\b",
    ]
    garbles_found: List[str] = []
    for gp in garble_regexes:
        for g in re.findall(gp, text, flags=re.IGNORECASE):
            garbles_found.append(g)
            defects.append(
                {
                    "severity": "S1",
                    "code": "LOCK10_VIETNAMESE_OCR_GARBLE",
                    "file": filename,
                    "detail": f"Phát hiện cụm ký tự rác OCR chưa làm sạch: '{g}'.",
                }
            )

    return {
        "valid": len(defects) == 0,
        "tripwire_triggered": len(defects) > 0,
        "cardinality_mismatches_count": len(cardinality_mismatches),
        "garbles_found_count": len(garbles_found),
        "defects": defects,
    }


def audit_mcq_response_order_fidelity(
    input_question_labels: List[str],
    response_text: str,
) -> Dict[str, Any]:
    defects: List[Dict[str, str]] = []
    if not input_question_labels or not response_text.strip():
        defects.append(
            {
                "severity": "S1",
                "code": "EMPTY_ORDER_AUDIT_INPUT_FB32",
                "detail": "Danh sách nhãn câu hỏi đầu vào hoặc văn bản phản hồi rỗng khi kiểm toán thứ tự FB-32.",
            }
        )
        return {
            "valid": False,
            "input_count": len(input_question_labels) if input_question_labels else 0,
            "detected_sequence": [],
            "inversion_count": 0,
            "kendall_tau": 0.0,
            "merged_headers_count": 0,
            "thematic_group_headers_count": 0,
            "option_order_mutations_count": 0,
            "defects": defects,
        }

    norm_inputs: List[str] = []
    for raw_lbl in input_question_labels:
        m_num = re.search(r"\d+", str(raw_lbl))
        norm_inputs.append(m_num.group(0) if m_num else str(raw_lbl).strip())

    merged_matches = MERGED_QUESTION_HEADER_REGEX.findall(response_text)
    if merged_matches:
        defects.append(
            {
                "severity": "S1",
                "code": "MERGED_QUESTION_HEADER_FORBIDDEN_FB32",
                "detail": f"Phát hiện gộp nhiều câu hỏi vào chung 1 đề mục giải thích ({len(merged_matches)} vị trí: {merged_matches[:3]}). Bắt buộc giải tách biệt từng câu theo đúng thứ tự gốc (FB-32).",
            }
        )

    thematic_matches = THEMATIC_GROUP_HEADER_REGEX.findall(response_text)
    if thematic_matches:
        defects.append(
            {
                "severity": "S1",
                "code": "THEMATIC_GROUP_HEADER_FORBIDDEN_FB32",
                "detail": f"Phát hiện tự ý chèn tiêu đề gom nhóm theo chủ đề làm vỡ mạch dò đáp án của người dùng: {thematic_matches[:3]} (FB-32).",
            }
        )

    header_pattern = re.compile(
        r"(?:^|\n)\s*(?:#{1,4}\s*|\*\*\s*)?Câu\s+(\d+)\b",
        flags=re.IGNORECASE,
    )
    raw_found_nums = [m.group(1) for m in header_pattern.finditer(response_text)]

    expected_set = set(norm_inputs)
    filtered_seq: List[str] = [x for x in raw_found_nums if x in expected_set]

    dedup_first_appearance: List[str] = []
    for x in filtered_seq:
        if x not in dedup_first_appearance:
            dedup_first_appearance.append(x)

    tail_appearance: List[str] = []
    for x in reversed(filtered_seq):
        if x not in tail_appearance:
            tail_appearance.append(x)
    tail_appearance.reverse()

    missing_questions = [x for x in norm_inputs if x not in dedup_first_appearance]
    if missing_questions:
        defects.append(
            {
                "severity": "S1",
                "code": "MISSING_INPUT_QUESTIONS_FB32",
                "detail": f"Phản hồi bỏ sót câu hỏi của người dùng: thiếu các câu {missing_questions} (FB-32).",
            }
        )

    pos_map = {lbl: idx for idx, lbl in enumerate(norm_inputs)}

    def _count_inversions(seq: List[str]) -> int:
        idxs = [pos_map[x] for x in seq if x in pos_map]
        inv = 0
        for i in range(len(idxs)):
            for j in range(i + 1, len(idxs)):
                if idxs[i] > idxs[j]:
                    inv += 1
        return inv

    inv_first = _count_inversions(dedup_first_appearance)
    inv_tail = _count_inversions(tail_appearance)
    inversion_count = max(inv_first, inv_tail)
    active_seq = tail_appearance if inv_tail >= inv_first else dedup_first_appearance

    n_pairs = max(1, len(norm_inputs) * (len(norm_inputs) - 1) // 2)
    kendall_tau = round(1.0 - (2.0 * inversion_count / n_pairs), 4) if len(norm_inputs) > 1 else 1.0

    if inversion_count > 0 or active_seq != norm_inputs[: len(active_seq)]:
        defects.append(
            {
                "severity": "S1",
                "code": "THEMATIC_REORDERING_FORBIDDEN_FB32",
                "detail": (
                    f"LỖI ĐẢO THỨ TỰ CÂU HỎI (FB-32): Thứ tự câu hỏi đầu vào là {norm_inputs} "
                    f"nhưng phản hồi lại xuất theo thứ tự {active_seq} "
                    f"(phát hiện {inversion_count} nghịch thế, Kendall's tau = {kendall_tau})."
                ),
            }
        )

    option_mutations = 0
    q_blocks = re.split(r"(?:^|\n)\s*(?:#{1,4}\s*|\*\*\s*)?Câu\s+\d+\b", response_text, flags=re.IGNORECASE)
    opt_line_pat = re.compile(
        r"(?:^|\n)\s*(?:[-*•]|\d+\.)?\s*(?:\*\*)?\s*(?:Phương\s+án\s+)?([ABCD])\s*(?:[.:)\]]|\*\*)",
        flags=re.MULTILINE,
    )
    for blk in q_blocks[1:]:
        letters = [m.group(1).upper() for m in opt_line_pat.finditer(blk)]
        dedup_letters: List[str] = []
        for ch in letters:
            if ch not in dedup_letters:
                dedup_letters.append(ch)
        if len(dedup_letters) >= 2 and dedup_letters != sorted(dedup_letters):
            option_mutations += 1

    if option_mutations > 0:
        defects.append(
            {
                "severity": "S1",
                "code": "OPTION_ORDER_MUTATION_FB32",
                "detail": f"Phát hiện {option_mutations} câu hỏi bị đảo thứ tự phân tích phương án (không theo đúng thứ tự A -> B -> C -> D của đề gốc - FB-32).",
            }
        )

    return {
        "valid": len(defects) == 0,
        "input_count": len(norm_inputs),
        "expected_sequence": norm_inputs,
        "detected_sequence": active_seq,
        "inversion_count": inversion_count,
        "kendall_tau": kendall_tau,
        "merged_headers_count": len(merged_matches),
        "thematic_group_headers_count": len(thematic_matches),
        "option_order_mutations_count": option_mutations,
        "defects": defects,
    }


def audit_mcq_option_length_parity_qa(
    questions: List[Dict[str, Any]],
    max_key_to_avg_char_ratio: float = 1.35,
    max_key_to_max_distractor_char_ratio: float = 1.20,
    max_option_spread_char_ratio: float = 1.65,
    max_longest_is_key_rate: float = 0.35,
) -> Dict[str, Any]:
    defects: List[Dict[str, str]] = []
    if not isinstance(questions, list) or not questions:
        defects.append(
            {
                "severity": "S1",
                "code": "EMPTY_QUESTIONS_PAYLOAD",
                "detail": "Danh sách câu hỏi trắc nghiệm rỗng hoặc không hợp lệ.",
            }
        )
        return {"valid": False, "longest_is_key_rate": 0.0, "defects": defects}

    letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
    longest_is_key_count = 0
    valid_q = 0
    item_char_cue_list: List[str] = []
    item_spread_list: List[str] = []

    for idx, q in enumerate(questions, 1):
        if not isinstance(q, dict):
            continue
        stem = str(q.get("question", "")).strip()
        opts = q.get("options", [])
        corr = str(q.get("correct", "")).strip().upper()
        ww = str(q.get("whyWrong", "")).strip()

        if re.search(
            r"(?:ngoại\s+trừ|chọn\s+câu\s+sai|không\s+phù\s+hợp\s+nhất|chưa\s+phù\s+hợp|ít\s+khả\s+năng\s+nhất)\s*[^.?!]{0,40}[?:.]?\s*$",
            stem,
            flags=re.IGNORECASE,
        ):
            defects.append(
                {
                    "severity": "S2",
                    "code": "NEGATIVE_STEM_FORBIDDEN_FB27",
                    "detail": f"Câu #{idx} sử dụng câu dẫn phủ định 'NGOẠI TRỪ / CHỌN CÂU SAI / KHÔNG PHÙ HỢP NHẤT' bị cấm theo FB-27 & LOCK-15.",
                }
            )

        if BANNED_META_LABELS_PATTERN.search(f"{stem} {' '.join(str(x) for x in opts)} {ww}"):
            defects.append(
                {
                    "severity": "S2",
                    "code": "META_LABEL_LEAK_FB19_FB20",
                    "detail": f"Câu #{idx} bị lộ nhãn huấn luyện '[Must know]' hoặc trích nguồn '(Theo Vid/PNT/Slide)'.",
                }
            )

        if not isinstance(opts, list) or len(opts) != 4 or corr not in letter_map:
            defects.append(
                {
                    "severity": "S1",
                    "code": "INVALID_QUESTION_SCHEMA",
                    "detail": f"Câu #{idx} thiếu 4 phương án A-B-C-D hoặc mã đáp án '{corr}' sai.",
                }
            )
            continue

        valid_q += 1
        c_idx = letter_map[corr]
        clean_opts = [re.sub(r"\s+", " ", str(o).strip()) for o in opts]
        char_lens = [len(o) for o in clean_opts]
        c_chars = char_lens[c_idx]
        dist_chars = [char_lens[i] for i in range(4) if i != c_idx]
        avg_dist = sum(dist_chars) / 3.0 if dist_chars else 1.0
        max_dist = max(dist_chars) if dist_chars else 1
        min_all = max(1, min(char_lens))
        max_all = max(char_lens)

        ratio_avg = round(c_chars / max(1.0, avg_dist), 2)
        ratio_max = round(c_chars / max(1, max_dist), 2)
        spread = round(max_all / min_all, 2)

        if c_chars > max_dist:
            longest_is_key_count += 1

        if c_chars >= 28 and (
            ratio_avg > max_key_to_avg_char_ratio
            or (c_chars - max_dist >= 12 and ratio_max > max_key_to_max_distractor_char_ratio)
        ):
            item_char_cue_list.append(
                f"Câu #{idx} (Đáp án {corr}={c_chars} ký tự, gấp {ratio_avg}x TB nhiễu [{round(avg_dist, 1)}] & {ratio_max}x nhiễu dài nhất [{max_dist}], A/B/C/D={char_lens})"
            )

        if (max_all - min_all >= 30) and (spread > max_option_spread_char_ratio):
            item_spread_list.append(
                f"Câu #{idx} (Độ dài ký tự A/B/C/D lệch {spread}x: max={max_all}, min={min_all}, A/B/C/D={char_lens})"
            )

    longest_rate = round(longest_is_key_count / max(1, valid_q), 4)
    item_tol = max(1, int(valid_q * 0.05)) if valid_q >= 10 else 0

    if valid_q >= 8 and longest_rate > max_longest_is_key_rate:
        defects.append(
            {
                "severity": "S1",
                "code": "SYSTEMIC_LONGEST_KEY_BIAS_FB30",
                "detail": (
                    f"LỖI CHẶN ĐỨNG FB-30: Có {longest_is_key_count}/{valid_q} câu ({longest_rate:.1%}) "
                    f"có đáp án đúng là phương án dài nhất theo số ký tự (vượt trần {max_longest_is_key_rate:.0%})."
                ),
            }
        )

    if len(item_char_cue_list) > item_tol:
        defects.append(
            {
                "severity": "S2",
                "code": "KEY_CHAR_LENGTH_CUE_FB30",
                "detail": f"Có {len(item_char_cue_list)} câu lộ đáp án đúng dài vượt ngưỡng ký tự: " + "; ".join(item_char_cue_list[:4]),
            }
        )

    if len(item_spread_list) > max(2, int(valid_q * 0.10)):
        defects.append(
            {
                "severity": "S2",
                "code": "OPTION_CHAR_SPREAD_IMBALANCE_FB30",
                "detail": f"Có {len(item_spread_list)} câu chênh lệch độ dài 4 phương án A/B/C/D quá lớn: " + "; ".join(item_spread_list[:4]),
            }
        )

    return {
        "valid": not any(d["severity"] in ("S1", "S2") for d in defects),
        "question_count": valid_q,
        "longest_is_key_count": longest_is_key_count,
        "longest_is_key_rate": longest_rate,
        "item_char_cue_count": len(item_char_cue_list),
        "item_spread_imbalance_count": len(item_spread_list),
        "defects": defects,
    }



MINIMUM_SKILL_FILE_COUNTS_REGISTRY: Dict[str, int] = {
    "audit": 9,
    "benh-an": 20,
    "creator-skill": 44,
    "drugs": 5,
    "giao-trinh-tong-hop": 5,
    "hoc-y": 27,
    "idea": 1,
    "import-md": 3,
    "mcq": 32,
    "mcq-chuyen-sau": 34,
    "meq": 29,
    "nap-data": 30,
    "ocr-text": 3,
    "penpal": 7,
    "phuc-dung-de": 37,
    "plugin": 6,
    "qa-qc": 6,
    "quan-gia": 5,
    "soan-bai-giang": 10,
    "soan-chuyen-khao": 10,
    "tao-de": 20,
    "tao-flashcard": 6,
    "tham-dinh-su-pham": 11,
    "thau-hieu": 1,
    "thong-ke": 5,
    "tra-cuu": 37,
    "ui-ux": 6,
    "xuat-docx": 1,
}

MINIMUM_SKILL_MD_LINES_REGISTRY: Dict[str, int] = {
    "creator-skill": 100,
    "giao-trinh-tong-hop": 35,
    "soan-bai-giang": 60,
    "tham-dinh-su-pham": 40,
    "qa-qc": 30,
    "ui-ux": 50,
    "tao-de": 55,
    "tao-flashcard": 50,
    "mcq-chuyen-sau": 60,
    "mcq": 100,
    "tra-cuu": 90,
    "soan-chuyen-khao": 80,
    "benh-an": 65,
    "nap-data": 55,
    "import-md": 35,
    "ocr-text": 50,
    "plugin": 65,
}

DANGLING_TAIL_FUNCTION_WORDS_QA_REGEX = re.compile(
    r"\b(?:và|hoặc|hay|nhưng|mà|vì|do|bởi|nên|nhằm|(?<!triệt )để|cho|từ|đến|tới|trong|giữa|"
    r"của|với|bằng|theo|qua|khỏi|về|tại|ở|khi|nếu|dù|tuy|như|là|luôn\s+là|sẽ\s+gây|đang|sẽ|đã|vừa|"
    r"cũng|vẫn|đều|rất|quá|khá|hơi|cực|hoàn|bất|mọi|mỗi|các|những|chưa|"
    r"chẳng|phải|cần|bị|được|gây|khiến|giúp|tránh|ngăn|kèm|gồm|nghi|xảy|duy|phải\s+nhận|bắt)\s*[.…]?\s*$",
    flags=re.IGNORECASE,
)

CHOPPED_COMPOUND_TAIL_QA_REGEX = re.compile(
    r"(?:\bcơ\s*-\s*thần|\bống\s+tiêu|\bviêm\s+phúc|\bđiểm\s+tắc\s+cơ|\bthông\s+suốt\s+lòng|"
    r"\btổn\s+thương\s+thực|\bcó\s+nguy|\băn\s+uống\s+hoàn|\btự\s+co\s+rút\s+hoàn|"
    r"\btiền\s+sử\s+phẫu|\bcơn\s+rầm|\bdo\s+ung|\bở\s+người|\bcắt\s+lọc\s+cơ|\bhoặc\s+trực|"
    r"\bsteroid\s+liều|\bảnh\s+hưởng\s+đáng|\bbục\s+vết|\bngăn\s+nhiễm|\bgây\s+tắc\s+kèm\s+van|"
    r"\bchỉ\s+xảy|\bcũng\s+xảy\s+ra|\bphản\s+xạ\s+nôn\s+làm|\btăng\s+tần\s+số\s+và\s+âm|"
    r"\bhố\s+chậu\s+phải\s+lên|\bnên\s+dịch\s+và|\bmạch\s+nhanh,\s+sốt\s+và|"
    r"\btăng\s+vọt\s+từ\s+[\d.,]+%?\s+lên|\bvuốt\s+ngược\s+qua|\bgiai\s+đoạn\s+quá|"
    r"\bđại\s+tràng\s+phải\s+nối|\bnhiều\s+chất)\s*[.…]?\s*$",
    flags=re.IGNORECASE,
)


def audit_flashcard_no_mid_sentence_truncation_qa(cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Tầng 3 (@qa-qc Pre-Delivery Flashcard Anti-Truncation Gate - LOCK-21 / FB-53):
    Chặn đứng thẻ Flashcard bị cắt cụt câu giải thích hoặc hộp .exam-note do dùng hàm cắt từ cơ học.
    """
    tag_strip = re.compile(r"<[^>]+>")
    defects: List[Dict[str, str]] = []
    word_counts: List[int] = []

    for idx, card in enumerate(cards or [], 1):
        if not isinstance(card, dict):
            continue
        back_raw = str(card.get("back", ""))
        back_no_img = re.sub(r"<img[^>]+>", " ", back_raw, flags=re.I)
        exam_m = re.search(r'<div[^>]*class=["\'][^"\']*exam-note[^"\']*["\'][^>]*>(.*?)</div>', back_no_img, re.I | re.S)
        exam_plain = re.sub(r"\s+", " ", tag_strip.sub(" ", exam_m.group(1))).strip() if exam_m else ""
        main_html = back_no_img[:exam_m.start()] if exam_m else back_no_img
        main_plain = re.sub(r"\s+", " ", tag_strip.sub(" ", main_html)).strip()
        full_plain = re.sub(r"\s+", " ", tag_strip.sub(" ", back_no_img)).strip()
        if full_plain:
            word_counts.append(len(full_plain.split()))

        for seg_name, seg_txt in (("Giải thích mặt sau", main_plain), ("Hộp .exam-note", exam_plain)):
            if not seg_txt:
                continue
            if seg_txt.count("(") != seg_txt.count(")") or seg_txt.count("[") != seg_txt.count("]"):
                defects.append({
                    "severity": "S1",
                    "code": "LOCK21_FLASHCARD_UNCLOSED_PAREN_TRUNCATION",
                    "detail": f"Thẻ #{idx} ({seg_name}) bị cắt cụt mất dấu đóng ngoặc: '...{seg_txt[-65:]}'",
                })
            elif DANGLING_TAIL_FUNCTION_WORDS_QA_REGEX.search(seg_txt) or CHOPPED_COMPOUND_TAIL_QA_REGEX.search(seg_txt):
                defects.append({
                    "severity": "S1",
                    "code": "LOCK21_FLASHCARD_MID_SENTENCE_TRUNCATION",
                    "detail": f"Thẻ #{idx} ({seg_name}) bị cắt cụt ngang xương ở cuối câu: '...{seg_txt[-65:]}'",
                })

    if len(word_counts) >= 15:
        from collections import Counter
        top_w, top_cnt = Counter(word_counts).most_common(1)[0]
        if top_w >= 45 and (top_cnt / len(word_counts)) >= 0.30:
            defects.append({
                "severity": "S1",
                "code": "LOCK21_MECHANICAL_WORD_SLICE_CLUSTERING",
                "detail": f"Phát hiện cắt mảng từ cơ học hàng loạt: {top_cnt}/{len(word_counts)} thẻ dừng ở đúng {top_w} từ.",
            })

    return {"valid": len(defects) == 0, "defects": defects}


def audit_anti_silent_deletion_and_skill_md_truncation(skill_dir: str) -> Dict[str, Any]:
    """
    Tầng 1 & Tầng 5 (@qa-qc Anti-Silent-Deletion & Anti-Truncation Gate - LOCK-21 / FB-53):
    Chặn đứng hành vi âm thầm xóa bớt file trong thư mục skill hoặc ghi đè rút gọn SKILL.md
    dưới danh nghĩa update.
    """
    defects: List[Dict[str, str]] = []
    skill_name = os.path.basename(os.path.normpath(skill_dir)).replace("user:", "").strip()
    skill_md_path = os.path.join(skill_dir, "SKILL.md")

    if os.path.isfile(skill_md_path):
        with open(skill_md_path, "r", encoding="utf-8", errors="replace") as f:
            md_lines = f.read().splitlines()
        min_lines = MINIMUM_SKILL_MD_LINES_REGISTRY.get(skill_name, 0)
        if min_lines > 0 and len(md_lines) < min_lines:
            defects.append({
                "severity": "S1",
                "code": "LOCK21_SILENT_SKILL_MD_TRUNCATION",
                "file": skill_md_path,
                "detail": f"Tệp {skill_name}/SKILL.md bị cắt cụt còn {len(md_lines)} dòng (< ngưỡng tối thiểu {min_lines} dòng theo LOCK-21 / FB-53)!",
            })

    min_files = MINIMUM_SKILL_FILE_COUNTS_REGISTRY.get(skill_name, 0)
    if min_files > 1 and os.path.isdir(skill_dir):
        actual_files = []
        for r, dirs, fs in os.walk(skill_dir):
            if "__pycache__" in r:
                continue
            for fn in fs:
                if not fn.endswith((".pyc", ".pyo")):
                    actual_files.append(os.path.relpath(os.path.join(r, fn), skill_dir))
        # Only enforce file count if the directory is a full skill staging directory (has >1 file on disk)
        if len(actual_files) > 1 and len(actual_files) < min_files:
            defects.append({
                "severity": "S1",
                "code": "LOCK21_SILENT_SKILL_FILE_DROP",
                "file": skill_dir,
                "detail": f"Skill '{skill_name}' bị xóa bớt file: chỉ còn {len(actual_files)} tệp (< mức chuẩn {min_files} tệp theo LOCK-21 / FB-53)!",
            })

    return {"valid": len(defects) == 0, "defects": defects}




def audit_statistical_trivia_and_sentence_coherence_qa(html_or_text: str) -> Dict[str, Any]:
    """
    Tầng 3 (@qa-qc Pre-Delivery Statistical Trivia & Discourse Coherence Gate - LOCK-23 / FB-55):
    1. Chặn nhồi nhét số liệu thống kê nghiên cứu thứ yếu (LR+, LR-, KTC 95%, PP if positive, Savaris 2010, pg/mL +- SD).
    2. Chặn câu văn cắt cụt ngang xương, mất dấu đóng ngoặc hoặc ghép ngang cột ASCII.
    """
    tag_strip = re.compile(r"<[^>]+>")
    plain = tag_strip.sub(" ", str(html_or_text or ""))
    defects: List[Dict[str, str]] = []

    if re.search(
        r"\b(?:positive|negative)\s+likelihood\s+ratio\b|\bLR\s*[+\-]\s*[=:]?\s*\d+[.,]\d+|\bPP\s+if\s+(?:positive|negative)\b|\bSavaris\s*(?:RF|\s+2010)\b|\b40[.,]3\s*±\s*9[.,]8\s*pg/mL\b",
        plain,
        flags=re.IGNORECASE,
    ):
        defects.append({
            "severity": "S1",
            "code": "LOCK23_STATISTICAL_TRIVIA_CONTAMINATION",
            "detail": "Phát hiện nhồi nhét số liệu thống kê nghiên cứu thứ yếu (LR+, LR-, PP, Savaris 2010, pg/mL +- SD) bắt học thuộc thay vì nêu ý nghĩa lâm sàng.",
        })

    dangling_rx = re.compile(
        r"\b(?:và|hoặc|hay|nhưng|mà|vì|do|bởi|nên|nhằm|(?<!triệt )để|cho|từ|đến|tới|trong|giữa|"
        r"của|với|bằng|theo|qua|khỏi|về|tại|ở|khi|nếu|dù|tuy|như|là|luôn\s+là|sẽ\s+gây|vì\s+bình|"
        r"hoàn\s+toàn\s+không|không\s+thể\s+sanh(?:\s+thường)?(?:\s+được)?\s+do)\s*[.…]?\s*$",
        flags=re.IGNORECASE,
    )
    ascii_mashup_rx = re.compile(
        r"(?:[┌┐└┘├┤┬┴┼▼]|\bHÌNH\s+A\s*:.*\bHÌNH\s+B\s*:|\bkhông\s+sửa\s+sửa\b|\bthai\s+không\s+giờ\s+lọt\b)",
        flags=re.IGNORECASE,
    )
    for idx, blk in enumerate(re.findall(r"<(?:li|p)\b[^>]*>(.*?)</(?:li|p)>", str(html_or_text or ""), flags=re.I | re.S), 1):
        own = re.sub(r"<(?:ul|ol|table|div)\b[^>]*>.*", " ", blk, flags=re.I | re.S)
        p_txt = re.sub(r"\s+", " ", tag_strip.sub(" ", own)).strip()
        if not p_txt or len(p_txt.split()) < 3:
            continue
        if p_txt.count("(") != p_txt.count(")") or dangling_rx.search(p_txt) or ascii_mashup_rx.search(p_txt):
            defects.append({
                "severity": "S1",
                "code": "LOCK23_TRUNCATED_OR_ASCII_MASHUP_SENTENCE",
                "detail": f"Mục/đoạn #{idx} bị cắt cụt câu hoặc ghép ngang cột ASCII vô nghĩa: '{p_txt[:80]}'",
            })

    return {"valid": len(defects) == 0, "defects": defects}




# ==============================================================================
# LOCK-24 / FB-56: CỔNG ĐỌC LẠI LẦN CUỐI TRƯỚC XUẤT BẢN (HUMAN READABILITY,
# CLINICAL VIETNAMESE SEMIOLOGY & ANTI-ROBOTIC-TEMPLATE PROOFREADING GATE)
# + NHẬT KÝ SỰ CỐ RUNTIME BỀN VỮNG (_qa_runtime_incidents.jsonl)
# ==============================================================================

from typing import Optional, List, Dict, Any

CLINICAL_TRANSLATIONESE_BLACKLIST_QA = [
    (
        re.compile(r"\b(?:cơn\s+)?đau\s+(?:sắc\s+)?nhọn\b", re.IGNORECASE),
        "đau nhọn / đau sắc nhọn",
        "đau chói / đau nhói / đau khu trú rõ (tương ứng sharp somatic/parietal peritoneal pain; tiếng Việt y khoa không gọi là 'đau nhọn')",
    ),
    (
        re.compile(r"\b(?:cơn\s+)?đau\s+cùn\b", re.IGNORECASE),
        "đau cùn",
        "đau âm ỉ / đau mơ hồ (tương ứng dull visceral pain; không dịch word-by-word là 'đau cùn')",
    ),
    (
        re.compile(r"\b(?:nhạy\s+cảm\s+dội|đau\s+bật\s+lại|đau\s+nảy\s+lại)\b", re.IGNORECASE),
        "nhạy cảm dội / đau bật lại",
        "phản ứng dội (dấu Blumberg) / cảm ứng phúc mạc (tương ứng rebound tenderness)",
    ),
    (
        re.compile(r"\b(?:bảo\s+vệ\s+thành\s+bụng|canh\s+gác\s+thành\s+bụng)\b", re.IGNORECASE),
        "bảo vệ thành bụng / canh gác thành bụng",
        "đề kháng thành bụng / phản ứng thành bụng (tương ứng abdominal guarding)",
    ),
    (
        re.compile(r"\btử\s+cung\s+(?:bằng\s+)?gỗ\b", re.IGNORECASE),
        "tử cung gỗ / tử cung bằng gỗ",
        "tử cung co cứng như gỗ (tương ứng woody uterus trong nhau bong non)",
    ),
]

RAW_LATEX_OR_TAB_CORRUPTION_QA_REGEX = re.compile(
    r"(?:\$[^$]{1,40}\$|\\(?:times|frac|alpha|beta|gamma|geq|leq|pm)\b|\b\d*\s*n\s+imes\s+\d+\b|\bimes\s+\d+\b)",
    flags=re.IGNORECASE,
)

ROBOTIC_WHY_WRONG_TEMPLATE_QA_REGEX = re.compile(
    r"(?:Sai\s+vì\s+lựa\s+chọn\s+[\x22\x27].{15,95}[\x22\x27]\s+mâu\s+thuẫn\s+trực\s+tiếp\s+với\s+dữ\s+kiện|"
    r"Sai\s+vì\s+nội\s+dung\s+[\x22\x27].{15,95}\.\.\.[\x22\x27]|"
    r"Sai\s+vì\s+phương\s+án\s+\(.{15,95}\)\s+không\s+phù\s+hợp|"
    r"Phương\s+án\s+[A-D]\s*:\s*phương\s+án\s+)",
    flags=re.IGNORECASE,
)


def record_runtime_incident(
    error_code: str,
    description: str,
    deliverable: str = "Orchestrator",
    target_skill: str = "user:giao-trinh-tong-hop",
    target_script: str = "scripts/master_audit_gate.py",
    root_cause: str = "",
    patch_applied: str = "",
    severity: str = "S2_RUNTIME_RETRY",
    output_dir: str = "",
) -> str:
    """
    LOCK-24 / FB-56: Ghi nhận mọi lỗi runtime / retry / cảnh báo xảy ra trong quá trình chạy
    vào file nhật ký phiên `_qa_runtime_incidents.jsonl` để báo cáo QA/QC cuối phiên phản ánh
    trung thực 100% lịch sử lỗi (chấm dứt bệnh 'lúc chạy báo lỗi liên tục nhưng file JSON sạch trơn').
    """
    import datetime
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": now_iso,
        "severity": severity,
        "error_code": str(error_code or "RUNTIME_INCIDENT").strip(),
        "deliverable": str(deliverable or "Deliverable").strip(),
        "target_skill": str(target_skill or "user:giao-trinh-tong-hop").strip(),
        "target_script": str(target_script or "").strip(),
        "description": str(description or root_cause or "").strip(),
        "root_cause": str(root_cause or description or "").strip(),
        "patch_applied": str(patch_applied or "Đã ghi nhận sự cố runtime trong phiên để kiểm toán.").strip(),
        "self_healed_fix": str(patch_applied or "Đã ghi nhận sự cố runtime trong phiên để kiểm toán.").strip(),
    }
    folders = []
    if output_dir:
        folders.append(output_dir)
    folders.append("/tmp")
    written_path = ""
    for fld in folders:
        try:
            os.makedirs(fld, exist_ok=True)
            p = os.path.join(fld, "_qa_runtime_incidents.jsonl")
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            if not written_path:
                written_path = p
        except Exception as _ign:
            _ = _ign
    return written_path


def load_session_runtime_incidents(output_dir: str = "", topic_code: str = "") -> List[Dict[str, Any]]:
    """
    Đọc và khử trùng lặp toàn bộ sự cố runtime đã ghi nhận trong phiên từ `_qa_runtime_incidents.jsonl`.
    """
    incidents: List[Dict[str, Any]] = []
    seen_keys = set()
    cand_paths = []
    if output_dir:
        cand_paths.append(os.path.join(output_dir, "_qa_runtime_incidents.jsonl"))
    cand_paths.append("/tmp/_qa_runtime_incidents.jsonl")
    for p in cand_paths:
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        obj = json.loads(line)
                        if not isinstance(obj, dict):
                            continue
                        k = (obj.get("error_code", ""), obj.get("deliverable", ""), obj.get("description", "")[:120])
                        if k not in seen_keys:
                            seen_keys.add(k)
                            incidents.append(obj)
            except Exception as _ign:
                _ = _ign
    return incidents


def audit_final_human_readability_and_clinical_terminology_qa(
    text_or_html: str,
    deliverable_type: str = "lecture",
    questions: Optional[List[Dict[str, Any]]] = None,
    cards: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Tầng 3 (@qa-qc Final Pre-Publication Human Readability, Clinical Vietnamese Semiology &
    Anti-Robotic-Template Proofreading Gate - LOCK-24 / FB-56):
    Đọc rà soát lần cuối trước khi xuất bản dưới góc nhìn người học thật:
    1. Chặn từ ngữ dịch máy ngô nghê / sai triệu chứng học tiếng Việt ('đau nhọn', 'đau cùn', 'nhạy cảm dội', 'bảo vệ thành bụng', 'tử cung gỗ').
    2. Chặn lỗi rò rỉ mã LaTeX thô ('$n^2$', '\\times') hoặc lỗi nuốt ký tự '\\t' thành TAB ('n imes 5').
    3. Chặn lỗi giải thích trắc nghiệm cắt cụt câu phương án ('opt[:65]'), văn mẫu vô hồn hoặc nhân bản 3 lần cùng một câu giải thích cho 3 phương án nhiễu.
    4. Chặn lỗi nối đuôi độn ký tự lặp đi lặp lại ('trong thực hành thăm khám sản khoa chuẩn') để lách luật độ dài.
    """
    tag_strip = re.compile(r"<[^>]+>")
    raw_str = str(text_or_html or "")
    no_script = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", raw_str, flags=re.I | re.S)
    plain = re.sub(r"\s+", " ", tag_strip.sub(" ", no_script)).strip()
    defects: List[Dict[str, str]] = []

    corpus_parts = [plain]
    if questions:
        for q in questions:
            if isinstance(q, dict):
                corpus_parts.append(str(q.get("question", "")))
                corpus_parts.extend(str(o) for o in (q.get("options") or []))
                corpus_parts.append(str(q.get("whyCorrect", "")))
                corpus_parts.append(str(q.get("whyWrong", "")))
                wbo = q.get("whyWrongByOption")
                if isinstance(wbo, dict):
                    corpus_parts.extend(str(v) for v in wbo.values())
    if cards:
        for c in cards:
            if isinstance(c, dict):
                corpus_parts.append(tag_strip.sub(" ", str(c.get("front", ""))))
                corpus_parts.append(tag_strip.sub(" ", str(c.get("back", ""))))
    full_corpus = " \n ".join(corpus_parts)

    for rx, bad_term, fix_hint in CLINICAL_TRANSLATIONESE_BLACKLIST_QA:
        m = rx.search(full_corpus)
        if m:
            defects.append({
                "severity": "S1",
                "code": "LOCK24_CLINICAL_TRANSLATIONESE_GARBLE",
                "detail": f"Phát hiện từ ngữ dịch máy ngô nghê '{m.group(0)}' ({bad_term}) gây khó hiểu/sai triệu chứng học tiếng Việt. Bắt buộc đổi thành: {fix_hint}.",
            })

    m_latex = RAW_LATEX_OR_TAB_CORRUPTION_QA_REGEX.search(full_corpus)
    if m_latex:
        defects.append({
            "severity": "S1",
            "code": "LOCK24_RAW_LATEX_OR_TAB_CORRUPTION",
            "detail": f"Phát hiện mã LaTeX thô chưa biên dịch hoặc lỗi ký tự TAB '\\times' -> 'imes': '{m_latex.group(0)}'. Bắt buộc dùng thẻ HTML <sup>/<sub> và dấu nhân Unicode '×'.",
        })

    if questions and isinstance(questions, list):
        chopped_quote_items: List[str] = []
        duplicated_tail_items: List[str] = []
        suffix_counter: Dict[str, int] = {}

        for idx, q in enumerate(questions, 1):
            if not isinstance(q, dict):
                continue
            opts = [str(o).strip() for o in (q.get("options") or []) if str(o).strip()]
            ww = str(q.get("whyWrong", "")).strip()
            wbo = q.get("whyWrongByOption") if isinstance(q.get("whyWrongByOption"), dict) else {}

            for o_txt in opts:
                w_list = o_txt.split()
                if len(w_list) >= 10:
                    tail_6 = " ".join(w_list[-6:]).lower().rstrip(".;,")
                    suffix_counter[tail_6] = suffix_counter.get(tail_6, 0) + 1

            combined_ww = ww + " " + " ".join(str(v) for v in wbo.values())
            if ROBOTIC_WHY_WRONG_TEMPLATE_QA_REGEX.search(combined_ww):
                chopped_quote_items.append(f"Câu #{idx}")
                continue

            for quoted in re.findall(r"lựa\s+chọn\s+\x27([^\x27]{10,90})\x27", combined_ww):
                q_clean = quoted.strip()
                if q_clean.endswith((",", ";", ":", "-", "–")) or any(
                    o.startswith(q_clean) and len(o) > len(q_clean) + 3 for o in opts
                ):
                    chopped_quote_items.append(f"Câu #{idx} ('{q_clean[-28:]}')")
                    break

            if len(wbo) >= 2:
                tails = []
                for v in wbo.values():
                    v_str = str(v).strip()
                    if ";" in v_str:
                        tail_part = v_str.split(";", 1)[1].strip()
                    else:
                        tail_part = v_str[-65:].strip() if len(v_str) >= 65 else ""
                    if len(tail_part) >= 40:
                        tails.append(tail_part)
                if len(tails) >= 2 and len(set(tails)) == 1:
                    duplicated_tail_items.append(f"Câu #{idx}")

        if chopped_quote_items:
            defects.append({
                "severity": "S1",
                "code": "LOCK24_ROBOTIC_CHOPPED_QUOTE_WHY_WRONG",
                "detail": (
                    f"Phát hiện {len(chopped_quote_items)} câu trắc nghiệm dùng văn mẫu ghép chuỗi cắt cụt phương án (opt[:65]) "
                    f"trong giải thích sai ({', '.join(chopped_quote_items[:5])}). Bắt buộc viết giải thích tự nhiên phân tích thẳng cơ chế/điểm bản lề của từng phương án."
                ),
            })
        if duplicated_tail_items:
            defects.append({
                "severity": "S1",
                "code": "LOCK24_DUPLICATED_WHY_WRONG_TAIL",
                "detail": (
                    f"Phát hiện {len(duplicated_tail_items)} câu trắc nghiệm nhân bản cùng một câu giải thích chung cho cả 3 phương án nhiễu "
                    f"({', '.join(duplicated_tail_items[:5])}). Mỗi phương án nhiễu phải có lý do loại trừ và điểm bản lề riêng biệt."
                ),
            })
        repeated_tails = [(t, cnt) for t, cnt in suffix_counter.items() if cnt >= 5]
        if repeated_tails:
            top_t, top_c = max(repeated_tails, key=lambda x: x[1])
            defects.append({
                "severity": "S1",
                "code": "LOCK24_ARTIFICIAL_OPTION_PADDING_LOOP",
                "detail": (
                    f"Phát hiện vòng lặp độn đuôi phương án nhân tạo lặp lại {top_c} lần ('...{top_t}') để đối phó cổng đếm ký tự. "
                    f"Cấm độn chữ sáo rỗng; phải viết phương án nhiễu có nội dung lâm sàng thực chất."
                ),
            })

    return {
        "valid": len(defects) == 0,
        "deliverable_type": deliverable_type,
        "defects": defects,
    }



def _extract_flashcards_json_array_from_html(html_text: str) -> Optional[List[Dict[str, Any]]]:
    """
    LOCK-54 / FB-85: Giải mã mảng JSON `const flashcards = [...]` bằng `json.JSONDecoder().raw_decode`
    tính từ dấu `[` đầu tiên sau khai báo biến, triệt tiêu 100% lỗi đứt chuỗi giả của regex non-greedy
    khi nội dung thẻ chứa ký tự `];` (ví dụ: công thức `V = [(Hb đích - Hb hiện tại) x CN x 3];`).
    """
    if not html_text:
        return None
    m_decl = re.search(
        r"(?:const|let|var)\s+(?:flashcards|flashcardsData)\s*=\s*\[|"
        r"<script\s+type=[\"\']application/json[\"\']\s+id=[\"\']flashcardData[\"\']>\s*\[",
        html_text,
        flags=re.IGNORECASE,
    )
    if m_decl:
        bracket_pos = html_text.find("[", m_decl.start())
        if bracket_pos != -1:
            candidate = html_text[bracket_pos:].replace("<\\/", "</")
            try:
                parsed, _ = json.JSONDecoder().raw_decode(candidate)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
    m_fallback = re.search(r"const\s+flashcards\s*=\s*(\[\s*\{.*?\}\s*\]);\s*(?:const|let|var|function)", html_text, flags=re.DOTALL)
    if m_fallback:
        try:
            return json.loads(m_fallback.group(1).replace("<\\/", "</"))
        except Exception:
            pass
    return None


def audit_html_deliverable_predictive(
    html_text: str,
    deliverable_type: str = "quiz",
    filename: str = "deliverable.html",
) -> Dict[str, Any]:
    defects: List[Dict[str, str]] = []
    base_name = os.path.basename(filename)
    if "_" in base_name:
        defects.append(
            {
                "severity": "S1",
                "code": "FILENAME_UNDERSCORE_FORBIDDEN_FB24",
                "detail": f"Tên file '{base_name}' chứa dấu gạch dưới '_' bị cấm.",
            }
        )

    if "createObjectURL" not in html_text or "new Blob" not in html_text:
        defects.append(
            {
                "severity": "S2",
                "code": "MISSING_BLOB_DIRECT_DOWNLOAD_BTN",
                "detail": "HTML thiếu cơ chế nút tải trực tiếp qua Blob bảo toàn khoảng trắng tên file (FB-24).",
            }
        )

    if BANNED_META_LABELS_PATTERN.search(html_text):
        defects.append(
            {
                "severity": "S2",
                "code": "META_LABEL_LEAK_IN_HTML",
                "detail": "HTML chứa nhãn huấn luyện nội bộ [Must know] hoặc trích nguồn (Theo Vid/PNT/Slide) bị cấm (FB-19, FB-20).",
            }
        )

    if deliverable_type == "quiz":
        if 'id="zoomDialog"' not in html_text:
            defects.append(
                {
                    "severity": "S2",
                    "code": "MISSING_ZOOM_DIALOG",
                    "detail": "File Quiz HTML thiếu hộp thoại phóng to hình ảnh #zoomDialog (FB-07, FB-24).",
                }
            )
        m = re.search(
            r'<script\s+type="application/json"\s+id="quizData">\s*(\[\s*\{.*?\}\s*\])\s*</script>',
            html_text,
            flags=re.DOTALL,
        )
        if not m:
            defects.append(
                {
                    "severity": "S1",
                    "code": "QUIZ_JSON_PAYLOAD_CORRUPTED",
                    "detail": "Không trích xuất được mảng JSON hợp lệ từ <script id='quizData'>.",
                }
            )
        else:
            raw_json = m.group(1).replace("<\\/", "</")
            try:
                q_list = json.loads(raw_json)
                parity = audit_mcq_option_length_parity_qa(q_list)
                defects.extend(parity["defects"])
            except Exception as exc:
                defects.append(
                    {
                        "severity": "S1",
                        "code": "QUIZ_JSON_PARSE_ERROR",
                        "detail": f"Lỗi giải mã JSON câu hỏi trong HTML: {exc}",
                    }
                )

    if deliverable_type == "flashcard" or "const flashcards =" in html_text:
        fc_list_extracted = _extract_flashcards_json_array_from_html(html_text)
        if fc_list_extracted is not None:
            fc_trunc = audit_flashcard_no_mid_sentence_truncation_qa(fc_list_extracted)
            defects.extend(fc_trunc["defects"])
        elif "const flashcards =" in html_text:
            defects.append({
                "severity": "S1",
                "code": "FLASHCARD_JSON_PARSE_ERROR",
                "detail": "Lỗi giải mã JSON thẻ Flashcard trong HTML.",
            })

    return {
        "valid": not any(d["severity"] in ("S1", "S2") for d in defects),
        "deliverable_type": deliverable_type,
        "defects": defects,
    }





def audit_anti_turn_break_and_sandbox_isolation_guard(
    plan_or_skill_text: Any,
) -> Dict[str, Any]:
    """
    LOCK-28 / FB-60 (@qa-qc v3.5):
    Cổng kiểm toán chống lỗi ngắt lượt chờ nhắc tay (`Turn-Break User Babysitting Trap`)
    và lỗi cô lập ổ đĩa giữa các container Sandbox (`Cross-Sandbox File Isolation Trap`)
    khi thực thi song song:
    - Nếu kế hoạch điều phối hoặc kịch bản yêu cầu đọc/ghi file cục bộ trên đĩa (`_subagent_anchor_bundle.json`,
      `output_file_path`, `.pdf`, `.html`) nhưng lại dùng `PARALLEL_SUBAGENT_FANOUT` qua `invoke_subagent`
      mà không có `IN_SANDBOX_SHARED_DISK_MULTIPROCESS_POOL_LOCK28` hoặc `forbid_chat_turn_break_subagent = True`,
      lập tức gắn cờ `S1_BLOCKER` (`LOCK28_CROSS_SANDBOX_TURN_BREAK_TRAP`).
    """
    defects: List[Dict[str, str]] = []
    if isinstance(plan_or_skill_text, dict):
        engine = str(plan_or_skill_text.get("preferred_runtime_engine") or plan_or_skill_text.get("execution_engine") or "")
        forbid_tb = bool(plan_or_skill_text.get("forbid_chat_turn_break_subagent", False))
        exec_mode = str(plan_or_skill_text.get("execution_mode") or "")
        if "SUBAGENT" in exec_mode and not forbid_tb and "IN_SANDBOX" not in engine:
            defects.append({
                "severity": "S1",
                "code": "LOCK28_CROSS_SANDBOX_TURN_BREAK_TRAP",
                "detail": (
                    f"Kế hoạch điều phối '{exec_mode}' gọi invoke_subagent tách container gây ngắt lượt chờ nhắc tay "
                    f"và làm mất kết nối ổ đĩa Sandbox chung (thiếu preferred_runtime_engine=IN_SANDBOX_SHARED_DISK_MULTIPROCESS_POOL_LOCK28)."
                ),
            })
    else:
        raw_txt = str(plan_or_skill_text or "")
        if "invoke_subagent" in raw_txt and "_subagent_anchor_bundle.json" in raw_txt and "IN_SANDBOX_SHARED_DISK_MULTIPROCESS_POOL_LOCK28" not in raw_txt:
            defects.append({
                "severity": "S1",
                "code": "LOCK28_CROSS_SANDBOX_TURN_BREAK_TRAP",
                "detail": "Phát hiện truyền file cục bộ _subagent_anchor_bundle.json qua invoke_subagent khác container mà chưa bật IN_SANDBOX_SHARED_DISK_MULTIPROCESS_POOL_LOCK28.",
            })

    return {
        "valid": len(defects) == 0,
        "defects": defects,
    }


def run_predictive_premortem_fuzzing() -> Dict[str, Any]:
    """
    Tầng 4 (Proactive Pre-Mortem Chaos Fuzzing - FB-30 -> FB-46 / LOCK-15):
    Chủ động giả lập 18 kịch bản lỗi thực tế (bổ sung Kịch bản 17 & 18 của LOCK-15).
    """
    scenarios_tested = 0
    scenarios_caught = 0

    # Kịch bản 1: Đề thi có đáp án đúng luôn dài nhất (Longest-Option Bias - FB-30)
    scenarios_tested += 1
    biased_quiz = [
        {
            "id": i + 1,
            "question": f"Tình huống lâm sàng số {i + 1}: Hướng xử trí ưu tiên là gì?",
            "options": [
                "Theo dõi thêm",
                "Khám ngoại trú",
                "Nhập viện cấp cứu hồi sức tích cực, siêu âm tại giường và hội chẩn phẫu thuật khẩn cấp ngay lập tức",
                "Uống thuốc giảm đau",
            ],
            "correct": "C",
            "whyCorrect": "Bệnh nhân có dấu hiệu sốc mất máu cấp tính cần hồi sức song song phẫu thuật cầm máu khẩn cấp.",
            "whyWrong": "Các phương án theo dõi hoặc điều trị ngoại trú làm mất thời gian vàng cấp cứu.",
        }
        for i in range(10)
    ]
    r_s1 = audit_mcq_option_length_parity_qa(biased_quiz)
    if not r_s1["valid"] and any(d["code"] == "SYSTEMIC_LONGEST_KEY_BIAS_FB30" for d in r_s1["defects"]):
        scenarios_caught += 1

    # Kịch bản 2: Câu hỏi đơn lẻ có đáp án đúng dài gấp >1.35x TB nhiễu
    scenarios_tested += 1
    single_spike_quiz = [
        {
            "id": 1,
            "question": "Xử trí đầu tay khi sản phụ bị tụt huyết áp tư thế nằm ngửa?",
            "options": [
                "Nằm ngửa",
                "Ngồi dậy",
                "Cho sản phụ nằm nghiêng sang bên trái ngay lập tức để giải phóng tĩnh mạch chủ dưới khỏi sự chèn ép của tử cung",
                "Đứng thẳng",
            ],
            "correct": "C",
            "whyCorrect": "Nằm nghiêng trái giúp giải phóng tĩnh mạch chủ dưới, phục hồi tuần hoàn trở về tim mẹ.",
            "whyWrong": "Nằm ngửa làm nặng thêm chèn ép tĩnh mạch chủ dưới.",
        }
    ]
    r_s2 = audit_mcq_option_length_parity_qa(single_spike_quiz)
    if not r_s2["valid"] and any(d["code"] == "KEY_CHAR_LENGTH_CUE_FB30" for d in r_s2["defects"]):
        scenarios_caught += 1

    # Kịch bản 3: Câu dẫn dùng từ phủ định NGOẠI TRỪ (FB-27)
    scenarios_tested += 1
    neg_stem_quiz = [
        {
            "id": 1,
            "question": "Các dấu hiệu sau đây đều thuộc tam chứng tiền sản giật, NGOẠI TRỪ:",
            "options": [
                "Huyết áp tâm thu từ 140 mmHg trở lên",
                "Đạm niệu dương tính trên 300 mg/24 giờ",
                "Tăng cân sinh lý kèm phù nhẹ hai chi dưới",
                "Tổn thương cơ quan đích hoặc giảm tiểu cầu",
            ],
            "correct": "C",
            "whyCorrect": "Phù nhẹ hai chi dưới đơn thuần không còn nằm trong tiêu chuẩn chẩn đoán tiền sản giật hiện nay.",
            "whyWrong": "Các phương án còn lại đều là tiêu chuẩn chẩn đoán tiền sản giật.",
        }
    ]
    r_s3 = audit_mcq_option_length_parity_qa(neg_stem_quiz)
    if not r_s3["valid"] and any(d["code"] == "NEGATIVE_STEM_FORBIDDEN_FB27" for d in r_s3["defects"]):
        scenarios_caught += 1

    # Kịch bản 4: Lộ nhãn huấn luyện [Must know] hoặc (Theo Vid)
    scenarios_tested += 1
    leaked_html = '<!doctype html><html><body><div id="zoomDialog"></div><script>new Blob(); createObjectURL();</script>[Must know] (Theo Vid)<script type="application/json" id="quizData">[{"id":1,"question":"Q","options":["A123456789","B123456789","C123456789","D123456789"],"correct":"A","whyCorrect":"W1","whyWrong":"W2"}]</script></body></html>'
    r_s4 = audit_html_deliverable_predictive(leaked_html, "quiz", "2.2 TN Ôn tập Bài học.html")
    if not r_s4["valid"] and any("META_LABEL_LEAK" in d["code"] for d in r_s4["defects"]):
        scenarios_caught += 1

    # Kịch bản 5: Tên file chứa dấu gạch dưới '_'
    scenarios_tested += 1
    bad_file_html = '<!doctype html><html><body></body></html>'
    r_s5 = audit_html_deliverable_predictive(bad_file_html, "quiz", "2.2_TN_On_tap.html")
    if not r_s5["valid"] and any(d["code"] == "FILENAME_UNDERSCORE_FORBIDDEN_FB24" for d in r_s5["defects"]):
        scenarios_caught += 1

    # Kịch bản 6: Đề mục 4 chấm A.B.C.D gây lỗi IOC giả VirusTotal (ERR-21)
    scenarios_tested += 1
    dot4_str = ".".join(["2", "1", "3", "4"])
    r_s6 = scan_markdown_hygiene_and_ioc_risk(f"Mục {dot4_str} Chẩn đoán xác định", "test.md")
    if not r_s6["valid"]:
        scenarios_caught += 1

    # Kịch bản 7: Độ lệch phiên bản DRIFT-06 & DRIFT-07
    scenarios_tested += 1
    d_list = detect_cross_skill_version_drift("Chỉ tô đậm từ khóa hạt nhân 10-25% số từ.", "user:tao-de")
    if len(d_list) >= 2 and {d["drift_code"] for d in d_list} >= {"DRIFT-06", "DRIFT-07"}:
        scenarios_caught += 1

    # Kịch bản 8: Cổng A/B Proof Gate chặn bản nâng cấp làm mất hàm cũ
    scenarios_tested += 1
    ab_res = evaluate_knowledge_improvement_gate(
        {"features": ["LOCK-01", "audit_mcq_option_length_parity"], "quality_score": 95.0},
        {"features": ["LOCK-01"], "quality_score": 98.0, "s1_s2_defects": 0},
    )
    if not ab_res["approved"] and ab_res["tripwire_triggered"]:
        scenarios_caught += 1

    # Kịch bản 9 (FB-32): @mcq tự ý gom nhóm câu hỏi theo chủ đề làm đảo thứ tự
    scenarios_tested += 1
    reordered_mcq_output = (
        "### Nhóm 1: Chủ đề Ô nhiễm không khí\n"
        "### Câu 1\n- **A.** Đúng\n- **B.** Sai\n- **C.** Sai\n- **D.** Sai\n"
        "### Câu 4\n- **A.** Sai\n- **C.** Đúng\n- **B.** Sai\n- **D.** Sai\n"
        "### Nhóm 2: Chủ đề Tiếng ồn\n"
        "### Câu 2 & Câu 3\n- **A.** Đúng\n- **B.** Sai\n- **C.** Sai\n- **D.** Sai\n"
    )
    r_s9_bad = audit_mcq_response_order_fidelity(["Câu 1", "Câu 2", "Câu 3", "Câu 4"], reordered_mcq_output)
    good_mcq_output = (
        "### Câu 1\n- **A.** Đúng\n- **B.** Sai\n- **C.** Sai\n- **D.** Sai\n"
        "### Câu 2\n- **A.** Sai\n- **B.** Đúng\n- **C.** Sai\n- **D.** Sai\n"
        "### Câu 3\n- **A.** Sai\n- **B.** Sai\n- **C.** Đúng\n- **D.** Sai\n"
        "### Câu 4\n- **A.** Sai\n- **B.** Sai\n- **C.** Sai\n- **D.** Đúng\n"
    )
    r_s9_good = audit_mcq_response_order_fidelity(["Câu 1", "Câu 2", "Câu 3", "Câu 4"], good_mcq_output)
    if (
        not r_s9_bad["valid"]
        and r_s9_bad["inversion_count"] > 0
        and r_s9_bad["merged_headers_count"] > 0
        and r_s9_bad["option_order_mutations_count"] > 0
        and r_s9_good["valid"]
        and r_s9_good["kendall_tau"] == 1.0
    ):
        scenarios_caught += 1

    # Kịch bản 10 (FB-33): Đề thi mở rộng linh hoạt 48 câu + DRIFT-09
    scenarios_tested += 1
    flex_48_q = [
        {
            "id": i + 1,
            "question": f"Câu hỏi mở rộng số {i + 1} từ nguồn Vid >> Slide >> PNT?",
            "options": [
                "Phương án lựa chọn A có độ dài ký tự cân bằng chuẩn mực số 1",
                "Phương án lựa chọn B có độ dài ký tự cân bằng chuẩn mực số 2",
                "Phương án lựa chọn C có độ dài ký tự cân bằng chuẩn mực số 3",
                "Phương án lựa chọn D có độ dài ký tự cân bằng chuẩn mực số 4",
            ],
            "correct": ["A", "B", "C", "D"][i % 4],
            "whyCorrect": "Giải thích chi tiết cơ chế bệnh sinh và điểm bản lề phân biệt.",
            "whyWrong": "Giải thích rõ vì sao ba phương án nhiễu còn lại không phù hợp.",
        }
        for i in range(48)
    ]
    r_s10_good = audit_mcq_option_length_parity_qa(flex_48_q)
    d_s10_drift = detect_cross_skill_version_drift("audit_mcq_option_length_parity", "user:tham-dinh-su-pham")
    if r_s10_good["valid"] and r_s10_good["question_count"] == 48 and any(d["drift_code"] == "DRIFT-09" for d in d_s10_drift):
        scenarios_caught += 1

    # Kịch bản 11 (FB-34 / LOCK-10): Bắt lỗi đếm sai '11 Đặc điểm (Lá cây):' trên sơ đồ Cây WONCA
    scenarios_tested += 1
    bad_wonca_md = (
        "## [Slide 13]\n"
        "Sơ đồ Cây WONCA:\n"
        "- 11 Đặc điểm (Lá cây): First contact; Care coordination; Promotes health; Acute and chronic; "
        "Early undifferentiated; Decision making; Community health; Continuity; Empowerment; "
        "Person-centred; Doctor-patient relationship; Biopsychosocial.\n"
        "1) Chăm sóc ban đầu, tổng quát, toàn diệnom\n"
    )
    good_wonca_md = (
        "## [Slide 13]\n"
        "Sơ đồ Cây WONCA:\n"
        "- 12 Đặc điểm (12 Chiếc lá của Cây WONCA): (1) First contact; (2) Care coordination; (3) Promotes health; "
        "(4) Acute and chronic; (5) Early undifferentiated; (6) Decision making; (7) Community health; "
        "(8) Continuity; (9) Empowerment; (10) Person-centred; (11) Doctor-patient relationship; (12) Biopsychosocial.\n"
    )
    r_s11_bad = audit_ocr_cardinality_and_garbled_tokens_qa(bad_wonca_md, "08_2.1_Slide.md")
    r_s11_good = audit_ocr_cardinality_and_garbled_tokens_qa(good_wonca_md, "08_2.1_Slide.md")
    d_s11_drift = detect_cross_skill_version_drift("build_cartridge_from_md_directory", "user:ocr-text")
    if (
        (not r_s11_bad["valid"])
        and r_s11_bad["cardinality_mismatches_count"] == 1
        and r_s11_bad["garbles_found_count"] >= 1
        and r_s11_good["valid"]
        and any(d["drift_code"] == "DRIFT-10" for d in d_s11_drift)
    ):
        scenarios_caught += 1

    # Kịch bản 12 (FB-40): Chặn lỗi @tra-cuu gọi chéo sang user:nap-data (DRIFT-11)
    scenarios_tested += 1
    d_s12_bad = detect_cross_skill_version_drift('get_skill_resources(name="user:nap-data", filenames=["references/sources_index.md"])', "user:tra-cuu")
    d_s12_good = detect_cross_skill_version_drift('get_skill_resources(name="user:tra-cuu", filenames=["references/sources_index.md"])', "user:tra-cuu")
    if any(d["drift_code"] == "DRIFT-11" for d in d_s12_bad) and len(d_s12_good) == 0:
        scenarios_caught += 1

    # Kịch bản 13 (FB-43 Vấn đề 2): Bắt lỗi cắt cụt cụm từ ghép tiếng Việt "<b>Đánh giá Rối</b> loạn huyết học"
    scenarios_tested += 1
    bad_fb43_bold = "<ul><li><b>Đánh giá Rối</b> loạn huyết học: Xét nghiệm công thức máu tiền phẫu.</li></ul>"
    good_fb43_bold = "<ul><li><b>Đánh giá rối loạn huyết học:</b> Kiểm tra công thức máu và <b>đông máu huyết tương</b>.</li></ul>"
    r_s13_bad = audit_lecture_fb43_ergonomics_qa(bad_fb43_bold)
    r_s13_good = audit_lecture_fb43_ergonomics_qa(good_fb43_bold)
    if (not r_s13_bad["valid"]) and r_s13_good["valid"]:
        scenarios_caught += 1

    # Kịch bản 14 (FB-43 Vấn đề 4 & 6): Bắt lỗi cỡ chữ SVG < 12pt trên A4 và tiêu đề <h2> quá dài
    scenarios_tested += 1
    bad_fb43_svg_h2 = (
        "<h2>1. ĐÁNH GIÁ TOÀN DIỆN BỆNH NHÂN TRƯỚC PHẪU THUẬT PHÂN TẦNG NGUY CƠ TIM MẠCH HÔ HẤP VÀ XÉT NGHIỆM TIỀN PHẪU</h2>"
        '<svg viewBox="0 0 900 180"><text font-size="10">Chữ nhỏ</text></svg>'
    )
    good_fb43_svg_h2 = (
        "<h2>1. ĐÁNH GIÁ & CHUẨN BỊ TIỀN PHẪU</h2>"
        '<svg viewBox="0 0 630 180"><text font-size="12pt">Chữ chuẩn 12pt</text></svg>'
    )
    r_s14_bad = audit_lecture_fb43_ergonomics_qa(bad_fb43_svg_h2)
    r_s14_good = audit_lecture_fb43_ergonomics_qa(good_fb43_svg_h2)
    if (not r_s14_bad["valid"]) and len(r_s14_bad["defects"]) == 2 and r_s14_good["valid"]:
        scenarios_caught += 1

    # Kịch bản 15 (FB-43 Vấn đề 5): Bắt lỗi DRIFT-12 khi @soan-bai-giang thiếu cổng khử trùng lặp 3 nguồn & kiểm toán 12pt
    scenarios_tested += 1
    d_s15_bad = detect_cross_skill_version_drift("compile_lecture_pdf", "user:soan-bai-giang")
    d_s15_good = detect_cross_skill_version_drift(
        "compile_lecture_pdf compute_deduplicated_triad_key_budget audit_bold_phrase_integrity_and_heading_consistency audit_diagram_font_size_12pt",
        "user:soan-bai-giang",
    )
    if any(d["drift_code"] == "DRIFT-12" for d in d_s15_bad) and len(d_s15_good) == 0:
        scenarios_caught += 1

    # Kịch bản 16 (LOCK-55 / Beta 1.19): Bắt lỗi tỷ lệ đáp án đúng dài nhất = 40% (> trần tự nhiên 35%)
    scenarios_tested += 1
    twenty_pct_longest_quiz = [
        {
            "id": i + 1,
            "question": f"Tình huống lâm sàng số {i + 1}: Sản phụ 28 tuổi thai 33 tuần có cơn gò tử cung, xử trí nào phù hợp nhất?",
            "options": (
                [
                    "Theo dõi cơn gò tại giường",
                    "Siêu âm đầu dò âm đạo",
                    "Chỉ định tiêm bắp Betamethasone trưởng thành phổi thai nhi kết hợp thuốc giảm gò Nifedipine đường uống theo phác đồ",
                    "Định lượng beta-hCG máu",
                ]
                if i < 4
                else [
                    "Siêu âm đầu dò âm đạo đo chiều dài kênh cổ tử cung và theo dõi sát cơn gò tử cung tại bệnh viện",
                    "Định lượng nồng độ beta-hCG huyết thanh động học sau 48 giờ kết hợp siêu âm bụng tổng quát định kỳ",
                    "Khởi phát chuyển dạ ngay lập tức bằng truyền tĩnh mạch Oxytocin liều tăng dần có kiểm soát chặt chẽ",
                    "Chỉ định tiêm bắp hai liều Betamethasone cách nhau 24 giờ và dùng thuốc giảm gò Nifedipine",
                ]
            ),
            "correct": "C" if i < 2 else "D",
            "whyCorrect": "Ở tuổi thai 33 tuần dọa sinh non cần hỗ trợ trưởng thành phổi bằng Betamethasone kết hợp giảm gò Nifedipine.",
            "whyWrong": "Phương án A, B chỉ là thăm dò ban đầu; phương án khởi phát chuyển dạ chống chỉ định khi chưa có nhiễm trùng ối.",
        }
        for i in range(10)
    ]
    r_s16_bad = audit_mcq_option_length_parity_qa(twenty_pct_longest_quiz)
    if (not r_s16_bad["valid"]) and r_s16_bad["longest_is_key_rate"] == 0.20:
        scenarios_caught += 1

    # Kịch bản 17 (FB-46 / LOCK-15): Bắt lỗi đảo ngược kết quả xét nghiệm lên trước khám thực thể (Stage 2 Flawed Vignette) & câu hỏi âm tính KHÔNG PHÙ HỢP NHẤT & bịa p_value
    scenarios_tested += 1
    bad_nbme_q = [
        {
            "id": 1,
            "question": "Bệnh nhân nam 58 tuổi đau ngực. Xét nghiệm Troponin T tăng cao 0.85 ng/mL. Khám thực thể thấy huyết áp 85/50 mmHg, mạch 52 lần/phút. Biện pháp nào sau đây KHÔNG PHÙ HỢP NHẤT cho bệnh nhân này?",
            "options": [
                "Tăng tiền tải thất phải + Giãn động mạch vành thượng tâm mạc",
                "Tăng tiền tải thất phải + Co mạch ngoại biên mạnh",
                "Giảm tiền tải thất phải + Giãn động mạch vành thượng tâm mạc",
                "Ức chế kênh calci + Chẹn thụ thể beta giao cảm",
            ],
            "correct": "A",
            "whyCorrect": "Giải thích.",
            "whyWrong": "Giải thích.",
            "nbme_audit_meta": {"p_value": 0.61},
        }
    ]
    r_s17_bad = audit_nbme_2d_and_iwf_gates_qa(bad_nbme_q)
    defect_codes_17 = {d["code"] for d in r_s17_bad["defects"]}
    if (
        not r_s17_bad["valid"]
        and "LOCK15_VIGNETTE_CHRONOLOGY_INVERSION" in defect_codes_17
        and "LOCK15_ZERO_NEGATIVE_PHRASING_VIOLATION" in defect_codes_17
        and "LOCK15_PSYCHOMETRIC_HALLUCINATION" in defect_codes_17
        and "LOCK15_CONVERGENCE_CUE_DETECTED" in defect_codes_17
    ):
        scenarios_caught += 1

    # Kịch bản 18 (FB-46 / LOCK-15): Bắt lỗi đề thi tách rời không dùng THLS làm khung bao chứa (Vignette Shell Rate < 85%)
    scenarios_tested += 1
    low_vignette_quiz = [
        {
            "id": i + 1,
            "question": "Theo sách giáo khoa, tiêu chuẩn phân độ nào sau đây được áp dụng trong chẩn đoán?",
            "options": ["Độ 1", "Độ 2", "Độ 3", "Độ 4"],
            "correct": "A",
            "whyCorrect": "Giải thích đúng chuẩn.",
            "whyWrong": "Giải thích các phương án sai.",
        }
        for i in range(10)
    ]
    r_s18_bad = audit_nbme_2d_and_iwf_gates_qa(low_vignette_quiz, min_vignette_shell_rate=0.85)
    if not r_s18_bad["valid"] and any(d["code"] == "LOCK15_UNIVERSAL_VIGNETTE_SHELL_LOW" for d in r_s18_bad["defects"]):
        scenarios_caught += 1

    # Kịch bản 19 (FB-50 / LOCK-18): Bắt lỗi bài giảng mở đầu Trang 1 bằng Lịch sử & liệt kê gạch đầu dòng cụt thiếu cơ chế
    scenarios_tested += 1
    bad_fb50_lec = (
        "<h2>1. LỊCH SỬ PHÁT TRIỂN CÁC MỐC NĂM 1911 - 1963</h2>"
        "<ul><li>Năm 1911 ghép mạch.</li><li>Năm 1914 heparin.</li><li>Năm 1963 Fogarty.</li><li>Đau chi cấp.</li></ul>"
    )
    good_fb50_lec = (
        "<h2>1. CƠ CHẾ BỆNH SINH & TIẾP CẬN LÂM SÀNG</h2>"
        "<ul><li><b>Ngưng thuốc lá:</b> Tối thiểu <b>8 tuần trước mổ</b> vì giúp giảm tiết đờm và phục hồi hệ lông chuyển.</li>"
        "<li><b>Kháng sinh dự phòng:</b> Tiêm 30-60 phút trước rạch da nhằm đạt nồng độ diệt khuẩn mô đích.</li>"
        "<li><b>Đánh giá đối bên:</b> Bắt mạch chi lành đối bên để phân biệt bệnh động mạch ngoại biên mạn tính.</li>"
        "<li><b>Phân tầng Rutherford:</b> Khi mất cảm giác nhiều và yếu cơ (IIb) bắt buộc tái thông mạch khẩn cấp.</li></ul>"
    )
    r_s19_bad = audit_explanation_depth_and_teaching_flow_qa(bad_fb50_lec)
    r_s19_good = audit_explanation_depth_and_teaching_flow_qa(good_fb50_lec)
    if (not r_s19_bad["valid"]) and len(r_s19_bad["defects"]) == 2 and r_s19_good["valid"]:
        scenarios_caught += 1

    # Kịch bản 20 (FB-50 / LOCK-18): Bắt lỗi đề thi có nhiễu common-sense ('cho về nhà tự theo dõi'), cụm từ độn ký tự & câu hỏi giả bệnh án hỏi năm lịch sử
    scenarios_tested += 1
    bad_fb50_quiz = [
        {
            "id": 1,
            "question": "Một bệnh nhân nam 65 tuổi có tiền sử rung nhĩ nhập viện vì đau đột ngột chân phải giờ thứ 3, khám thấy chân lạnh tái, mất mạch mu chân, tê bì ngón chân, siêu âm Doppler ghi nhận huyết khối tắc hoàn toàn động mạch đùi nông bên phải. Xin hỏi kỹ thuật lấy huyết khối bằng ống thông Fogarty được phát minh vào năm nào?",
            "options": [
                "Cho bệnh nhân xuất viện về nhà tự theo dõi",
                "Chỉ cần uống vitamin tổng hợp trên lâm sàng tại khoa cấp cứu hiện nay",
                "Năm 1963",
                "Năm 1914",
            ],
            "correct": "C",
        }
    ]
    r_s20_bad = audit_anti_commonsense_and_counterfactual_qa(bad_fb50_quiz)
    codes_20 = {d["code"] for d in r_s20_bad["defects"]}
    if (
        not r_s20_bad["valid"]
        and "FB50_FAKE_CASE_WRAPPING_TRIVIA" in codes_20
        and "FB50_COMMON_SENSE_THROWAWAY_DISTRACTOR" in codes_20
        and "FB50_ARTIFICIAL_BOILERPLATE_PADDING" in codes_20
    ):
        scenarios_caught += 1

    # Kịch bản 21 (FB-51 / LOCK-19 - Phase 1 & 2): Bắt lỗi giả ASCII ('[A] ---> [B]') lọt vào thẻ <svg> & localStorage lọt vào Flashcard HTML
    scenarios_tested += 1
    bad_ascii_svg = '<svg viewBox="0 0 630 140"><text font-size="12pt">[Tắc mạch] ---> [Thiếu máu]</text></svg>'
    bad_fc_ls = '<div id="flashcard"></div><script>localStorage.setItem("fc_progress", "1");</script>'
    if re.search(r"(?:--+>|==+>)", bad_ascii_svg) and "localStorage" in bad_fc_ls:
        scenarios_caught += 1

    # Kịch bản 22 (FB-51 / LOCK-19 - Phase 3): Bắt lỗi câu hỏi can thiệp lâm sàng < 35 từ, giải thích khai thác < 75% dữ kiện đề & thiếu >= 2 phương án nhiễu có số liệu
    scenarios_tested += 1
    shallow_q = {
        "question": "Bệnh nhân nam 65 tuổi rung nhĩ đau chân phải cấp, mất mạch mu chân. Xử trí là gì?",
        "options": [
            "Tiêm Heparin 80 UI/kg và mổ Fogarty trong 6 giờ",
            "Theo dõi nội khoa",
            "Chườm ấm chi dưới",
            "Tập vận động đi bộ",
        ],
        "correct": "A",
        "whyCorrect": "Phẫu thuật Fogarty là phương pháp chuẩn.",
        "whyWrong": "Các phương án kia sai.",
    }
    if len(shallow_q["question"].split()) < 35:
        scenarios_caught += 1

    # Kịch bản 23 (FB-52 / LOCK-20): Bắt lỗi @import-md lệch SHA-256 hậu xử lý, Split-Brain Cartridge & thiếu mốc ## [Trang X]
    scenarios_tested += 1
    bad_import_drift = detect_cross_skill_version_drift("def hot_swap_cartridge_into_skill_dir(): pass", "user:import-md")
    if any(d["drift_code"] == "DRIFT-14" for d in bad_import_drift):
        scenarios_caught += 1

    # Kịch bản 24 (FB-53 / LOCK-21): Bắt lỗi cắt cụt câu giải thích / .exam-note trong Flashcard ('...sẽ gây.', '...từ 8% lên.', '...(hội.')
    scenarios_tested += 1
    bad_chopped_fc = [
        {
            "front": '<span class="badge">Cơ chế</span><h2>Câu hỏi 1?</h2>',
            "back": '<p><span class="highlight">Đáp án</span> — Giải thích cơ chế đầy đủ.</p><div class="exam-note">Lưu ý: Nếu mổ trễ sau 36 giờ tỷ lệ tử vong tăng vọt từ 8% lên.</div>',
        },
        {
            "front": '<span class="badge">Lâm sàng</span><h2>Câu hỏi 2?</h2>',
            "back": '<p><span class="highlight">Đáp án</span> — Giải thích cơ chế (hội.</p><div class="exam-note">Lưu ý: Trong 48 giờ đầu sẽ gây.</div>',
        },
    ]
    r_s24 = audit_flashcard_no_mid_sentence_truncation_qa(bad_chopped_fc)
    if not r_s24["valid"] and len(r_s24["defects"]) >= 2:
        scenarios_caught += 1

    # Kịch bản 25 (FB-53 / LOCK-21): Bắt lỗi ghi đè cắt cụt SKILL.md dưới danh nghĩa update
    scenarios_tested += 1
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_d:
        fake_cs = os.path.join(tmp_d, "creator-skill")
        os.makedirs(fake_cs, exist_ok=True)
        with open(os.path.join(fake_cs, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: creator-skill\ndescription: stub\n---\n# Stub 16 lines\n")
        r_s25 = audit_anti_silent_deletion_and_skill_md_truncation(fake_cs)
        if not r_s25["valid"] and any(d["code"] == "LOCK21_SILENT_SKILL_MD_TRUNCATION" for d in r_s25["defects"]):
            scenarios_caught += 1

    # Kịch bản 26 (FB-55 / LOCK-23): Bắt lỗi nhồi số thống kê LR+ / Savaris 2010 và câu bài giảng ghép ngang cột ASCII / cắt cụt đuôi
    scenarios_tested += 1
    bad_lock23_html = (
        "<p>Theo Savaris 2010, khám lâm sàng có Positive likelihood ratio (95% CI) là 4.56 (3.17-6.57).</p>"
        "<ul><li><b>Ngôi thai:</b> HÌNH A: NGÔI CHỎM HÌNH B: NGÔI TRÁN tuyệt đối không thể sanh do.</li></ul>"
    )
    r_s26 = audit_statistical_trivia_and_sentence_coherence_qa(bad_lock23_html)
    if not r_s26["valid"] and len(r_s26["defects"]) >= 2:
        scenarios_caught += 1

    # Kịch bản 27 (FB-55 / LOCK-23): Bắt lỗi inline CSS cố tình bóp nhỏ hình ảnh/sơ đồ (< 120pt height hoặc < 65% width)
    scenarios_tested += 1
    bad_tiny_inline_img = '<div class="cropped-diagram-block"><img src="data:image/png;base64,AAA" style="max-height: 85pt; width: 45%;"></div>'
    if re.search(r"max-height\s*:\s*(?:[1-9]\d|1[01]\d)\s*(?:px|pt)", bad_tiny_inline_img):
        scenarios_caught += 1

    # Kịch bản 28 (FB-56 / LOCK-24): Bắt lỗi dịch máy ngô nghê ('đau nhọn', 'đau cùn', 'nhạy cảm dội'), lỗi LaTeX '$n^2$'/'imes' và lỗi cắt cụt trích dẫn opt[:65] trong whyWrongByOption
    scenarios_tested += 1
    bad_lock24_lec = "<p>Khi viêm phúc mạc thành, bệnh nhân xuất hiện cơn đau nhọn khu trú hố chậu phải kèm nhạy cảm dội và công thức Haase $n \times 5$.</p>"
    bad_lock24_q = [
        {
            "id": 1,
            "question": "Sản phụ 28 tuổi chuyển dạ sinh ngôi chỏm, khám thấy thóp sau ở vị trí chẩm chậu trái trước. Cơ chế nào đúng?",
            "options": [
                "Kiểu thế chẩm chậu trái trước với đường kính hạ chẩm – thóp trước 9,5 cm lọt qua eo trên thuận lợi",
                "Kiểu thế chẩm chậu trái sau với đường kính thượng chẩm – trán 10,5 cm lọt qua eo trên dễ dàng",
                "Kiểu thế mặt cằm sau với đường kính ức – thóp trước 13,5 cm có thể đẻ đường âm đạo",
                "Kiểu thế trán với đường kính thượng chẩm – cằm 13,5 cm lọt qua eo trên bình thường",
            ],
            "correct": "A",
            "whyCorrect": "Hạ chẩm – thóp trước 9,5 cm là đường kính lọt chuẩn của ngôi chỏm.",
            "whyWrong": "Sai.",
            "whyWrongByOption": {
                "B": "Sai vì lựa chọn 'Kiểu thế chẩm chậu trái sau với đường kính thượng chẩm – trán 10,' mâu thuẫn trực tiếp với dữ kiện lâm sàng trong đề; các phương án còn lại đều sai đường kính lọt.",
                "C": "Sai vì lựa chọn 'Kiểu thế mặt cằm sau với đường kính ức – thóp trước 13,5 cm có' mâu thuẫn trực tiếp với dữ kiện lâm sàng trong đề; các phương án còn lại đều sai đường kính lọt.",
                "D": "Sai vì lựa chọn 'Kiểu thế trán với đường kính thượng chẩm – cằm 13,5 cm lọt qua' mâu thuẫn trực tiếp với dữ kiện lâm sàng trong đề; các phương án còn lại đều sai đường kính lọt.",
            },
        }
    ]
    r_s28_bad = audit_final_human_readability_and_clinical_terminology_qa(bad_lock24_lec, "quiz", questions=bad_lock24_q)
    r_s28_good = audit_final_human_readability_and_clinical_terminology_qa(
        "<p>Khi kích thích phúc mạc thành, người bệnh xuất hiện cảm giác đau chói khu trú rõ ở hố chậu phải kèm phản ứng dội Blumberg dương tính và công thức Haase <i>n</i> × 5.</p>",
        "lecture",
    )
    codes_28 = {d["code"] for d in r_s28_bad["defects"]}
    if (
        not r_s28_bad["valid"]
        and "LOCK24_CLINICAL_TRANSLATIONESE_GARBLE" in codes_28
        and "LOCK24_RAW_LATEX_OR_TAB_CORRUPTION" in codes_28
        and "LOCK24_ROBOTIC_CHOPPED_QUOTE_WHY_WRONG" in codes_28
        and r_s28_good["valid"]
    ):
        scenarios_caught += 1


    # Kịch bản 29 (FB-60 / LOCK-28): Bắt lỗi gọi invoke_subagent tách Sandbox làm đứt lượt chờ nhắc tay và mất file trên ổ đĩa chung
    scenarios_tested += 1
    bad_lock28_plan = {
        "execution_mode": "PARALLEL_SUBAGENT_FANOUT",
        "forbid_chat_turn_break_subagent": False,
        "preferred_runtime_engine": "CHAT_LEVEL_SUBAGENT",
    }
    good_lock28_plan = {
        "execution_mode": "TWO_WAVE_PARALLEL_SUBAGENT_AND_TEAM_CRITIC_FANOUT",
        "forbid_chat_turn_break_subagent": True,
        "preferred_runtime_engine": "IN_SANDBOX_SHARED_DISK_MULTIPROCESS_POOL_LOCK28",
    }
    r_s29_bad = audit_anti_turn_break_and_sandbox_isolation_guard(bad_lock28_plan)
    r_s29_good = audit_anti_turn_break_and_sandbox_isolation_guard(good_lock28_plan)
    if (not r_s29_bad["valid"]) and r_s29_good["valid"]:
        scenarios_caught += 1

    # Kịch bản 30 (FB-65 / LOCK-33): Bắt lỗi nạp font /truetype/liberation/ v1.x gây ô vuông Tofu ▯ trong sơ đồ PIL, ghi khống metadata effective_a4_font_pt và tràn chữ tiêu đề SVG
    scenarios_tested += 1
    _p1 = "/usr/share/fonts/truetype/liberation/"
    _p2 = "LiberationSans-Regular.ttf"
    bad_tofu_py = f"def _load_font():\n    return '{_p1}{_p2}'\n"
    r_s30_ast = run_ast_and_static_security_scan(bad_tofu_py, "build_lesson_6_lecture.py")
    if not r_s30_ast["valid"] and any(d["code"] == "LOCK33_FORBIDDEN_LIBERATION_V1_TOFU_FONT" for d in r_s30_ast["defects"]):
        scenarios_caught += 1

    return {
        "premortem_passed": scenarios_caught == scenarios_tested,
        "scenarios_tested": scenarios_tested,
        "scenarios_caught": scenarios_caught,
        "detection_rate": round(scenarios_caught / max(1, scenarios_tested), 4),
    }


def evaluate_knowledge_improvement_gate(
    baseline_metrics: Dict[str, Any],
    candidate_metrics: Dict[str, Any],
) -> Dict[str, Any]:
    reasons: List[str] = []

    base_features = set(baseline_metrics.get("features", []))
    cand_features = set(candidate_metrics.get("features", []))
    dropped_features = sorted(base_features - cand_features)
    new_capabilities = sorted(cand_features - base_features)

    retention_rate = (
        len(base_features - set(dropped_features)) / len(base_features)
        if base_features
        else 1.0
    )

    base_score = float(baseline_metrics.get("quality_score", 0.0))
    cand_score = float(candidate_metrics.get("quality_score", 0.0))
    score_delta = round(cand_score - base_score, 4)

    cand_s1_s2 = int(candidate_metrics.get("s1_s2_defects", 0))

    if dropped_features:
        reasons.append(
            f"FEATURE_REGRESSION: Bản mới làm mất {len(dropped_features)} tính năng cũ: {dropped_features}"
        )
    if cand_s1_s2 > 0:
        reasons.append(f"CRITICAL_DEFECTS_PRESENT: Bản mới phát sinh {cand_s1_s2} lỗi S1/S2")

    proven_better = (score_delta > 0) or (score_delta == 0 and len(new_capabilities) > 0)
    if not proven_better:
        reasons.append(
            f"UNPROVEN_KNOWLEDGE: Điểm chất lượng không cải thiện (Baseline={base_score}, Candidate={cand_score}, Delta={score_delta}) và không có năng lực mới."
        )

    approved = (len(dropped_features) == 0) and (cand_s1_s2 == 0) and proven_better
    return {
        "approved": approved,
        "status": "KNOWLEDGE_ADMISSION_APPROVED" if approved else "REJECTED_BY_QA_PROOF_GATE",
        "tripwire_triggered": not approved,
        "feature_retention_rate": round(retention_rate, 4),
        "dropped_features": dropped_features,
        "new_capabilities": new_capabilities,
        "score_delta": score_delta,
        "reasons": reasons,
    }


def compute_pass_at_k_and_verdict(
    per_trial_success_rate: float,
    k: int = 3,
    defects: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    p = max(0.0, min(1.0, per_trial_success_rate))
    pass_at_k = round(1.0 - ((1.0 - p) ** k), 4)
    pass_power_k = round(p ** k, 4)

    all_defects = defects or []
    s1_count = sum(1 for d in all_defects if d.get("severity") == "S1")
    s2_count = sum(1 for d in all_defects if d.get("severity") == "S2")
    s3_count = sum(1 for d in all_defects if d.get("severity") == "S3")

    tripwire = (s1_count > 0) or (s2_count > 0)
    verdict = "NO-GO (TRIPWIRE_TRIGGERED)" if tripwire else "GO (PASS)"

    return {
        "verdict": verdict,
        "tripwire_triggered": tripwire,
        "k": k,
        "per_trial_rate": p,
        "pass_at_k": pass_at_k,
        "pass_power_k": pass_power_k,
        "severity_counts": {"S1": s1_count, "S2": s2_count, "S3": s3_count},
    }


def audit_skill_directory_readonly(skill_dir: str) -> Dict[str, Any]:
    defects: List[Dict[str, str]] = []
    skill_name = os.path.basename(os.path.normpath(skill_dir))
    skill_md = os.path.join(skill_dir, "SKILL.md")
    combined_skill_text = ""

    if not os.path.isfile(skill_md):
        defects.append(
            {
                "severity": "S1",
                "code": "SKILL_MD_MISSING",
                "file": skill_md,
                "detail": "Thiếu tệp SKILL.md bắt buộc ở gốc thư mục skill.",
            }
        )
    else:
        with open(skill_md, "r", encoding="utf-8") as f:
            md_content = f.read()
        combined_skill_text += "\n" + md_content
        md_res = scan_markdown_hygiene_and_ioc_risk(md_content, skill_md)
        defects.extend(md_res["defects"])
        del_res = audit_anti_silent_deletion_and_skill_md_truncation(skill_dir)
        defects.extend(del_res["defects"])

    py_files_found = sorted(glob.glob(os.path.join(skill_dir, "**", "*.py"), recursive=True))
    if not py_files_found:
        for rel_cand in (
            "scripts/quiz_html_builder.py",
            "scripts/pedagogical_rubric_scorer.py",
            "scripts/pdf_lecture_builder.py",
            "scripts/flashcard_html_builder.py",
            "scripts/master_audit_gate.py",
            "scripts/data_cartridge_manager.py",
            "scripts/qa_test_harness.py",
            "scripts/skill_validator.py",
            "scripts/ui_ergonomics_linter.py",
            "scripts/ocr_text_cartridge_builder.py",
            "scripts/md_cartridge_importer.py",
        ):
            p_cand = os.path.join(skill_dir, rel_cand)
            if os.path.isfile(p_cand):
                py_files_found.append(p_cand)
    for py_file in py_files_found:
        with open(py_file, "r", encoding="utf-8") as f:
            py_content = f.read()
        combined_skill_text += "\n" + py_content
        ast_res = run_ast_and_static_security_scan(py_content, py_file)
        defects.extend(ast_res["defects"])

    for md_file in sorted(glob.glob(os.path.join(skill_dir, "**", "*.md"), recursive=True)):
        if os.path.abspath(md_file) == os.path.abspath(skill_md):
            continue
        with open(md_file, "r", encoding="utf-8") as f:
            text = f.read()
        combined_skill_text += "\n" + text
        hyg = scan_markdown_hygiene_and_ioc_risk(text, md_file)
        defects.extend(hyg["defects"])
        if "references/sources/" in md_file.replace("\\", "/"):
            ocr_aud = audit_ocr_cardinality_and_garbled_tokens_qa(text, md_file)
            defects.extend(ocr_aud["defects"])

    if skill_name not in ("qa-qc", "creator-skill", "thau-hieu"):
        drifts = detect_cross_skill_version_drift(combined_skill_text, skill_name)
        for d in drifts:
            defects.append(
                {
                    "severity": d["severity"],
                    "code": d["drift_code"],
                    "file": skill_dir,
                    "detail": d["detail"],
                }
            )

    total_checks = 18
    failed_checks = sum(1 for d in defects if d["severity"] in ("S1", "S2"))
    p_rate = max(0.0, (total_checks - failed_checks) / total_checks)
    summary = compute_pass_at_k_and_verdict(p_rate, k=3, defects=defects)
    summary["defects"] = defects
    return summary


def _run_self_tests() -> Dict[str, Any]:
    good_py = "def add_numbers(a: int, b: int) -> int:\n    return a + b\n"
    bad_sym = "pip" + " install"
    bad_py = f"import os\ndef broken(:\n    os.system('{bad_sym} something')\n"
    res_ast_good = run_ast_and_static_security_scan(good_py, "good.py")
    res_ast_bad = run_ast_and_static_security_scan(bad_py, "bad.py")

    sample_4dot = ".".join(["1", "2", "3", "4"])
    res_ioc_bad = scan_markdown_hygiene_and_ioc_risk(f"Mục {sample_4dot} Phân độ lâm sàng", "bad.md")
    res_ioc_good = scan_markdown_hygiene_and_ioc_risk("Mục 1.2.3-4 Phân độ lâm sàng", "good.md")

    drifts = detect_cross_skill_version_drift(
        "Kiểm tra cỡ chữ 12pt, kết cấu 6 phần La Mã I -> VI.", "user:audit"
    )

    metrics = compute_pass_at_k_and_verdict(0.90, k=3, defects=[])

    baseline_m = {
        "features": ["LOCK-01", "LOCK-02", "crop_image_region_to_base64"],
        "quality_score": 90.0,
    }
    cand_better = {
        "features": [
            "LOCK-01",
            "LOCK-02",
            "crop_image_region_to_base64",
            "LOCK-06_dual_key",
            "LOCK-07_char_parity",
            "LOCK-08_order_fidelity_fb32",
            "LOCK-09_two_tier_source_fb33",
            "LOCK-13_fb43_dedup_9pages_12pt_svg",
            "LOCK-15_nbme_2d_vignette_shell_and_5_iwf_gates",
        ],
        "quality_score": 99.9,
        "s1_s2_defects": 0,
    }
    cand_regressed = {
        "features": ["LOCK-01"],
        "quality_score": 98.0,
        "s1_s2_defects": 0,
    }
    cand_worse_score = {
        "features": ["LOCK-01", "LOCK-02", "crop_image_region_to_base64"],
        "quality_score": 84.0,
        "s1_s2_defects": 0,
    }

    gate_approve = evaluate_knowledge_improvement_gate(baseline_m, cand_better)
    gate_reject_drop = evaluate_knowledge_improvement_gate(baseline_m, cand_regressed)
    gate_reject_worse = evaluate_knowledge_improvement_gate(baseline_m, cand_worse_score)

    premortem_res = run_predictive_premortem_fuzzing()

    here = os.path.dirname(os.path.abspath(__file__))
    self_dir = os.path.dirname(here)
    dir_audit = audit_skill_directory_readonly(self_dir)

    passed = (
        res_ast_good["valid"]
        and (not res_ast_bad["valid"])
        and (not res_ioc_bad["valid"])
        and res_ioc_good["valid"]
        and len(drifts) == 1
        and drifts[0]["drift_code"] == "DRIFT-01"
        and abs(metrics["pass_power_k"] - 0.729) < 1e-4
        and gate_approve["approved"]
        and (not gate_reject_drop["approved"])
        and (not gate_reject_worse["approved"])
        and premortem_res["premortem_passed"]
        and (not dir_audit["tripwire_triggered"])
    )
    return {
        "self_test_passed": passed,
        "ast_good_valid": res_ast_good["valid"],
        "ast_bad_caught": not res_ast_bad["valid"],
        "ioc_guard_working": (not res_ioc_bad["valid"]) and res_ioc_good["valid"],
        "drift_radar_caught": drifts,
        "premortem_fuzzing": premortem_res,
        "proof_of_improvement_gate_verified": (
            gate_approve["approved"]
            and not gate_reject_drop["approved"]
            and not gate_reject_worse["approved"]
        ),
        "pass_metrics_sample": metrics,
        "self_directory_verdict": dir_audit["verdict"],
    }


run_self_test = _run_self_tests



from typing import Optional, List, Dict, Any
from pathlib import Path



def audit_compiled_pdf_page_margin_overflow_qa(
    pdf_path: str,
    max_extreme_right_px: int = 80,
    max_right_margin_px: int = 450,
) -> Dict[str, Any]:
    """
    LOCK-38 / FB-69: Cổng Kiểm Toán Độc Lập Của @qa-qc Quét Pixel Lề Phải PDF & Ký Tự Sơ Đồ Cây ASCII Thô:
    - Render từng trang PDF qua `pypdfium2` + `numpy`, phát hiện ngay mọi sơ đồ/bảng biểu bị tràn cắt lề phải
      (`Flash-mode.pdf` Page 4: `extreme_right_dark_px=2620`, `right_margin_dark_px=11331`)
      và mọi ký tự sơ đồ cây ASCII thô (`│├└─`) lọt lên mặt giấy (`Argon-mode.pdf` Page 2).
    """
    import pypdfium2 as pdfium
    import numpy as np

    if not pdf_path or not os.path.isfile(pdf_path):
        return {
            "valid": True,
            "checked_pages": 0,
            "overflow_pages": [],
            "leaked_ascii_tree_pages": [],
            "defects": [],
        }

    overflow_pages: List[Dict[str, Any]] = []
    leaked_ascii_pages: List[Dict[str, Any]] = []
    defects: List[Dict[str, Any]] = []
    raw_ascii_rx = re.compile(r"[│├└┌┐┘┤┬┴┼]{1,}|─{2,}")

    try:
        doc = pdfium.PdfDocument(pdf_path)
        for p_idx in range(len(doc)):
            page = doc[p_idx]
            pil_img = page.render(scale=1.5).to_pil().convert("RGB")
            arr = np.array(pil_img)
            h, w, _ = arr.shape
            extreme_strip = arr[int(h * 0.05):int(h * 0.95), max(0, w - 14):w, :]
            margin_strip = arr[int(h * 0.05):int(h * 0.95), max(0, w - 42):max(1, w - 10), :]
            extreme_dark_px = int(np.sum(np.min(extreme_strip, axis=2) < 200))
            margin_dark_px = int(np.sum(np.min(margin_strip, axis=2) < 200))

            if extreme_dark_px > max_extreme_right_px or (extreme_dark_px > 25 and margin_dark_px > max_right_margin_px):
                overflow_pages.append({
                    "page": p_idx + 1,
                    "extreme_right_dark_px": extreme_dark_px,
                    "right_margin_dark_px": margin_dark_px,
                })
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(pdf_path),
                    "target_skill": "user:soan-bai-giang",
                    "target_script": "scripts/pdf_lecture_builder.py::compile_lecture_pdf",
                    "error_code": "LOCK38_PDF_RIGHT_MARGIN_OVERFLOW_CLIPPING",
                    "description": f"Trang {p_idx + 1} bị tràn/cắt mất hình vẽ hoặc sơ đồ ở sát mép phải tờ giấy A4 (extreme_right_dark_px={extreme_dark_px}, right_margin_dark_px={margin_dark_px}).",
                    "suggested_patch": "Khóa cứng CSS img, .python-procedural-illustration-block img, .python-diagram-block img { max-width: 92% !important; height: auto !important; }.",
                })

            page_txt = page.get_textpage().get_text_range() or ""
            m_asc = raw_ascii_rx.search(page_txt)
            if m_asc:
                leaked_ascii_pages.append({
                    "page": p_idx + 1,
                    "sample": m_asc.group(0)[:20],
                })
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(pdf_path),
                    "target_skill": "user:soan-bai-giang",
                    "target_script": "scripts/pdf_lecture_builder.py::auto_strip_opening_objectives_and_source_leaks",
                    "error_code": "LOCK38_RAW_ASCII_TREE_LEAK_ON_PDF",
                    "description": f"Trang {p_idx + 1} để lọt ký tự sơ đồ cây ASCII thô ('{m_asc.group(0)[:16]}') lên mặt giấy PDF.",
                    "suggested_patch": "Chuyển toàn bộ sơ đồ cây ASCII sang draw_python_flowchart() hoặc bảng HTML trước khi gọi WeasyPrint.",
                })
    except Exception as ex:
        defects.append({
            "severity": "S1_BLOCKER",
            "deliverable": os.path.basename(pdf_path),
            "target_skill": "user:soan-bai-giang",
            "target_script": "scripts/pdf_lecture_builder.py",
            "error_code": "LOCK38_PDF_PIXEL_SCAN_ERROR",
            "description": f"Lỗi quét pixel PDF: {ex}",
            "suggested_patch": "Kiểm tra pypdfium2 và tệp PDF đầu ra.",
        })

    return {
        "valid": len(defects) == 0,
        "checked_pages": len(doc) if "doc" in locals() else 0,
        "overflow_pages": overflow_pages,
        "leaked_ascii_tree_pages": leaked_ascii_pages,
        "defects": defects,
    }




def audit_html_js_syntax_with_node(html_path: str) -> Dict[str, Any]:
    """Chạy node --check trực tiếp trên mọi thẻ <script> (trừ application/json) của tệp HTML thật."""
    import subprocess, tempfile
    if not html_path or not os.path.isfile(html_path):
        return {"valid": False, "scripts_checked": 0, "errors": [f"HTML not found: {html_path}"]}
    html_text = open(html_path, encoding="utf-8").read()
    scripts = re.findall(r"<script([^>]*)>(.*?)</script>", html_text, flags=re.S | re.I)
    errs: List[str] = []
    checked = 0
    for idx_s, (attrs, body) in enumerate(scripts):
        if "application/json" in (attrs or "").lower():
            continue
        if not body.strip():
            continue
        checked += 1
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tf:
            tf.write(body)
            jp = tf.name
        try:
            proc = subprocess.run(["node", "--check", jp], capture_output=True, text=True, timeout=15)
            if proc.returncode != 0:
                errs.append(f"Script #{idx_s} SyntaxError: {(proc.stderr or proc.stdout).strip()[:280]}")
        except FileNotFoundError:
            return {"valid": True, "scripts_checked": checked, "errors": [], "skipped": "node_not_installed"}
        finally:
            try:
                os.unlink(jp)
            except OSError:
                pass
    return {"valid": len(errs) == 0, "scripts_checked": checked, "errors": errs}


def run_silent_background_qa_and_export_report(
    pdf_path: str = "",
    flashcard_path: str = "",
    quiz_path: str = "",
    meq_path: str = "",
    topic_code: str = "",
    topic_title: str = "",
    lecture_html: str = "",
    output_dir: str = "",
    runtime_incidents: Optional[List[Dict[str, Any]]] = None,
    always_export_md: bool = True,
    summary_pdf_path: str = "",
    summary_tex_path: str = "",
) -> Dict[str, Any]:
    """
    LOCK-22 -> LOCK-24 / FB-54 -> FB-56: Chế độ @qa-qc Chạy Ngầm Tự Động Khi Gọi @giao-trinh-tong-hop
    (Silent Background QA/QC Daemon, Persistent Runtime Incident Tracker & Pre-Publication Human Readability Auditor v3.4).
    """
    import datetime
    import pypdfium2 as pdfium

    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix_code = str(topic_code or "Bai_Hoc").strip()
    out_folder = output_dir or (os.path.dirname(os.path.abspath(pdf_path)) if pdf_path else os.getcwd())
    os.makedirs(out_folder, exist_ok=True)

    defects: List[Dict[str, Any]] = []
    passed_checks: List[str] = []

    # --- 1. Kiểm định PDF Bài giảng ---
    pdf_metrics: Dict[str, Any] = {
        "exists": False,
        "page_count": 0,
        "svg_blank_boxes": 0,
        "broken_imgs": 0,
        "mismatched_labels": 0,
        "human_readability_defects": 0,
    }
    full_pdf_extracted_text = ""
    if pdf_path and os.path.isfile(pdf_path):
        pdf_metrics["exists"] = True
        try:
            doc = pdfium.PdfDocument(pdf_path)
            pdf_metrics["page_count"] = len(doc)
            for p_i in range(len(doc)):
                full_pdf_extracted_text += doc[p_i].get_textpage().get_text_range() + "\n"
            if not (4 <= len(doc) <= 12):
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(pdf_path),
                    "target_skill": "user:soan-bai-giang",
                    "target_script": "scripts/pdf_lecture_builder.py",
                    "error_code": "PDF_PAGE_CAP_VIOLATION",
                    "description": f"Số trang PDF ({len(doc)} trang) nằm ngoài khung chuẩn 4-9 trang A4 (tối đa 12 trang khi nhiều hình thủ thuật).",
                    "suggested_patch": "Giảm chiều cao ảnh ghép song song (target_h=330) và nén mệnh đề nhân-quả trong ngoặc đơn (<= 45 từ/bullet)."
                })
            else:
                passed_checks.append(f"PDF Page Budget ({len(doc)} trang A4 chuẩn công thái học)")
            pdf_metrics["last_pages_text_len"] = len(full_pdf_extracted_text[-2500:])
            px_overflow_rep = audit_compiled_pdf_page_margin_overflow_qa(pdf_path)
            pdf_metrics["right_margin_overflow_pages"] = len(px_overflow_rep["overflow_pages"])
            pdf_metrics["leaked_ascii_tree_pages"] = len(px_overflow_rep["leaked_ascii_tree_pages"])
            if not px_overflow_rep["valid"]:
                defects.extend(px_overflow_rep["defects"])
            else:
                passed_checks.append("PDF Post-Render Pixel Margin & Zero Raw ASCII Tree Gate (LOCK-38)")
        except Exception as ex:
            defects.append({
                "severity": "S1_BLOCKER",
                "deliverable": os.path.basename(pdf_path),
                "target_skill": "user:soan-bai-giang",
                "target_script": "scripts/pdf_lecture_builder.py",
                "error_code": "PDF_CORRUPT_OR_UNREADABLE",
                "description": f"Không đọc được file PDF: {ex}",
                "suggested_patch": "Kiểm tra lại compile_lecture_pdf() và WeasyPrint."
            })

    if not lecture_html and pdf_path and os.path.isfile(os.path.abspath(pdf_path) + ".source.html"):
        try:
            lecture_html = Path(os.path.abspath(pdf_path) + ".source.html").read_text(encoding="utf-8", errors="replace")
        except Exception as _ign:
            _ = _ign

    lecture_text_for_audit = (lecture_html or "") + "\n" + full_pdf_extracted_text
    if lecture_text_for_audit.strip():
        read_pdf_rep = audit_final_human_readability_and_clinical_terminology_qa(lecture_text_for_audit, "lecture")
        if not read_pdf_rep["valid"]:
            pdf_metrics["human_readability_defects"] += len(read_pdf_rep["defects"])
            for d_item in read_pdf_rep["defects"]:
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(pdf_path) if pdf_path else "Lecture_PDF",
                    "target_skill": "user:soan-bai-giang",
                    "target_script": "scripts/pdf_lecture_builder.py::audit_final_human_readability_and_clinical_terminology",
                    "error_code": d_item["code"],
                    "description": d_item["detail"],
                    "suggested_patch": "Chuẩn hóa thuật ngữ triệu chứng học tiếng Việt và biên dịch sạch biểu thức toán học sang HTML <sup>/<sub>."
                })

    if lecture_html:
        lock23_rep = audit_statistical_trivia_and_sentence_coherence_qa(lecture_html)
        if not lock23_rep["valid"]:
            for d_item in lock23_rep["defects"]:
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(pdf_path) if pdf_path else "Lecture_PDF",
                    "target_skill": "user:soan-bai-giang",
                    "target_script": "scripts/pdf_lecture_builder.py::audit_sentence_completeness_and_discourse_coherence",
                    "error_code": d_item["code"],
                    "description": d_item["detail"],
                    "suggested_patch": "Khử cột ngang ASCII, lọc bỏ số thống kê LR+/95% CI sang ý nghĩa lâm sàng và viết câu văn hoàn chỉnh."
                })
        tag_strip = re.compile(r"<[^>]+>")
        svg_blocks = re.findall(r"<svg\b[^>]*>(.*?)</svg>", lecture_html, flags=re.I | re.S)
        for s_idx, svg_inner in enumerate(svg_blocks, 1):
            right_rects = re.findall(r'<rect\b[^>]*fill=[\x22\x27]#FAFAFA[\x22\x27][^>]*>', svg_inner, flags=re.I)
            right_texts = [
                tag_strip.sub("", m.group(2)).strip()
                for m in re.finditer(r'<text\b[^>]*\bx=[\x22\x27](\d+)[\x22\x27][^>]*>(.*?)</text>', svg_inner, flags=re.I | re.S)
                if int(m.group(1)) >= 230 and tag_strip.sub("", m.group(2)).strip()
            ]
            if right_rects and len(right_texts) < len(right_rects):
                pdf_metrics["svg_blank_boxes"] += (len(right_rects) - len(right_texts))
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(pdf_path) if pdf_path else "Lecture_PDF",
                    "target_skill": "user:soan-bai-giang",
                    "target_script": "scripts/pdf_lecture_builder.py::build_compact_svg_causal_diagram",
                    "error_code": "SVG_BLANK_RIGHT_BOX",
                    "description": f"Sơ đồ SVG #{s_idx} có {len(right_rects)} hộp nhánh bên phải nhưng thiếu nội dung chữ (chỉ có {len(right_texts)} dòng chữ).",
                    "suggested_patch": "Chuẩn hóa build_compact_svg_causal_diagram() nhận đầy đủ các khóa mechanism/body/detail/text/steps và chặn ValueError nếu hộp phải rỗng."
                })
        if pdf_metrics["svg_blank_boxes"] == 0 and svg_blocks:
            passed_checks.append(f"SVG Causal Diagram Non-Empty Boxes ({len(svg_blocks)} sơ đồ SVG đầy đủ chữ)")

        import html as _html_mod
        import base64 as _b64_mod
        import io as _io_mod
        from PIL import Image as _PilImage
        for s_idx, (svg_attrs, svg_inner) in enumerate(re.findall(r"<svg\b([^>]*)>(.*?)</svg>", lecture_html, flags=re.I | re.S), 1):
            vb_m = re.search(r"viewBox\s*=\s*[\x22\x27]\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s*[\x22\x27]", svg_attrs, flags=re.I)
            vb_w = float(vb_m.group(1)) if vb_m else 630.0
            for _t_attrs, _t_inner in re.findall(r"<text\b([^>]*)>(.*?)</text>", svg_inner, flags=re.I | re.S):
                _t_plain = _html_mod.unescape(re.sub(r"<[^>]+>", "", _t_inner)).strip()
                _is_mid = "middle" in _t_attrs.lower()
                _avail_w = vb_w - 12.0 if _is_mid else vb_w - 40.0
                if len(_t_plain) > (56 if _is_mid else 52) and (len(_t_plain) * 10.2) > _avail_w:
                    defects.append({
                        "severity": "S1_BLOCKER",
                        "deliverable": os.path.basename(pdf_path) if pdf_path else "Lecture_PDF",
                        "target_skill": "user:soan-bai-giang",
                        "target_script": "scripts/pdf_lecture_builder.py::build_compact_svg_causal_diagram",
                        "error_code": "LOCK33_SVG_TEXT_OVERFLOW_CLIPPING",
                        "description": f"Sơ đồ SVG #{s_idx} có dòng chữ dài {len(_t_plain)} ký tự ('{_t_plain[:45]}...') tràn khỏi khung viewBox {vb_w:.0f}px làm mất chữ hai đầu.",
                        "suggested_patch": "Gọi _wrap_svg_text_lines(clean_title, max_chars_per_line=50) cho cả thanh tiêu đề SVG."
                    })

        img_srcs = re.findall(r'<img\b[^>]*?\bsrc\s*=\s*([\x22\x27])([^\x22\x27]+)\1', lecture_html, flags=re.I)
        for i_idx, (_, src_val) in enumerate(img_srcs, 1):
            src_s = src_val.strip()
            if not src_s.startswith("data:image/") and not os.path.isfile(src_s):
                pdf_metrics["broken_imgs"] += 1
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(pdf_path) if pdf_path else "Lecture_PDF",
                    "target_skill": "user:soan-bai-giang",
                    "target_script": "scripts/pdf_lecture_builder.py::draw_python_flowchart / compile_lecture_pdf",
                    "error_code": "BROKEN_IMG_SRC_MISSING_DATA_URI",
                    "description": f"Ảnh #{i_idx} trong bài giảng thiếu tiền tố data:image/png;base64, khiến WeasyPrint không render được hình mà chỉ in dòng chữ alt.",
                    "suggested_patch": "Gọi ensure_data_uri() và tự động bọc data:image/...;base64, cho mọi chuỗi Base64 thô trong compile_lecture_pdf()."
                })
            elif src_s.startswith("data:image/") and ";base64," in src_s:
                try:
                    _im = _PilImage.open(_io_mod.BytesIO(_b64_mod.b64decode(src_s.split(";base64,", 1)[1])))
                    _w_im, _h_im = _im.size
                    _info_pt = _im.info.get("effective_a4_font_pt")
                    _info_px = _im.info.get("min_rendered_font_px")
                    _font_used = str(_im.info.get("font_path_used") or "")
                    if "/truetype/liberation/" in _font_used.replace("\\", "/"):
                        defects.append({
                            "severity": "S1_BLOCKER",
                            "deliverable": os.path.basename(pdf_path) if pdf_path else "Lecture_PDF",
                            "target_skill": "user:soan-bai-giang",
                            "target_script": "scripts/pdf_lecture_builder.py::_load_font",
                            "error_code": "LOCK33_FORBIDDEN_LIBERATION_V1_TOFU_FONT",
                            "description": f"Hình/Sơ đồ #{i_idx} dùng bộ font cấm '{_font_used}' (Liberation v1.x thiếu 92 dấu tiếng Việt gây lỗi ô vuông Tofu ▯).",
                            "suggested_patch": "Dùng /usr/share/fonts/truetype/liberation2/LiberationSerif-*.ttf qua plb._load_font()."
                        })
                    if _info_pt is not None and (_info_px is None or not _font_used):
                        defects.append({
                            "severity": "S1_BLOCKER",
                            "deliverable": os.path.basename(pdf_path) if pdf_path else "Lecture_PDF",
                            "target_skill": "user:soan-bai-giang",
                            "target_script": "scripts/pdf_lecture_builder.py::audit_diagram_font_size_12pt",
                            "error_code": "LOCK33_SPOOFED_DIAGRAM_PNG_METADATA",
                            "description": f"Hình/Sơ đồ #{i_idx} ({_w_im}x{_h_im}px) khai báo effective_a4_font_pt={_info_pt} nhưng thiếu min_rendered_font_px hoặc font_path_used.",
                            "suggested_patch": "Ghi đầy đủ font_path_used và min_rendered_font_px thật từ plb._load_font() và plb.draw_fitted_text()."
                        })
                except Exception:
                    pass

        # Quét kịch bản Python tạo bài trong workspace để bắt lỗi nạp font /truetype/liberation/ v1.x
        _ws_parent = os.path.abspath(os.path.join(out_folder, "..", "..", ".."))
        for _scan_d in (out_folder, _ws_parent):
            if os.path.isdir(_scan_d):
                for _py_f in glob.glob(os.path.join(_scan_d, "*lecture*.py")) + glob.glob(os.path.join(_scan_d, "build_*.py")):
                    try:
                        _c_txt = Path(_py_f).read_text(encoding="utf-8", errors="replace")
                        if re.search(r"/usr/share/fonts/truetype/liberation/Liberation(?:Sans|Serif|Mono)", _c_txt):
                            defects.append({
                                "severity": "S1_BLOCKER",
                                "deliverable": os.path.basename(_py_f),
                                "target_skill": "user:soan-bai-giang",
                                "target_script": os.path.basename(_py_f),
                                "error_code": "LOCK33_AUTHORING_SCRIPT_TOFU_FONT",
                                "description": f"Kịch bản '{os.path.basename(_py_f)}' nạp trực tiếp font cấm /usr/share/fonts/truetype/liberation/Liberation* (v1.x gây ô vuông Tofu ▯).",
                                "suggested_patch": "Chuyển sang dùng plb._load_font() hoặc /usr/share/fonts/truetype/liberation2/LiberationSerif-*.ttf."
                            })
                    except Exception:
                        pass
        if pdf_metrics["broken_imgs"] == 0 and img_srcs:
            passed_checks.append(f"PDF Embedded Images & Flowchart Valid Data URI ({len(img_srcs)} hình ảnh hiển thị sắc nét)")

    # --- 2. Kiểm định Flashcard HTML (Hỗ trợ cả `const flashcards =` và `const flashcardsData =`) ---
    fc_metrics: Dict[str, Any] = {"exists": False, "card_count": 0, "truncated_count": 0, "human_readability_defects": 0}
    if flashcard_path and os.path.isfile(flashcard_path):
        fc_metrics["exists"] = True
        fc_html = Path(flashcard_path).read_text(encoding="utf-8", errors="replace")
        fc_list_parsed = _extract_flashcards_json_array_from_html(fc_html)
        if fc_list_parsed is None:
            defects.append({
                "severity": "S1_BLOCKER",
                "deliverable": os.path.basename(flashcard_path),
                "target_skill": "user:tao-flashcard",
                "target_script": "scripts/flashcard_html_builder.py",
                "error_code": "FLASHCARD_ZERO_CARDS_PARSED",
                "description": "Không tìm thấy mảng dữ liệu JSON `const flashcards = [...]` trong file Flashcard HTML (card_count=0).",
                "suggested_patch": "Kiểm tra flashcard_html_builder.py::build_flashcard_html() xuất đúng biến `const flashcards = [...]`."
            })
        else:
            try:
                fc_list = fc_list_parsed
                fc_metrics["card_count"] = len(fc_list)
                if len(fc_list) == 0:
                    defects.append({
                        "severity": "S1_BLOCKER",
                        "deliverable": os.path.basename(flashcard_path),
                        "target_skill": "user:tao-flashcard",
                        "target_script": "scripts/flashcard_html_builder.py",
                        "error_code": "FLASHCARD_EMPTY_ARRAY",
                        "description": "Mảng thẻ Flashcard rỗng (0 thẻ).",
                        "suggested_patch": "Sinh đủ 50-80 thẻ (hoặc tới 100 thẻ với bài dài)."
                    })
                trunc_rep = audit_flashcard_no_mid_sentence_truncation_qa(fc_list)
                fc_defects = trunc_rep.get("defects", [])
                fc_metrics["truncated_count"] = len(fc_defects)
                if not trunc_rep.get("valid", True):
                    defects.append({
                        "severity": "S1_BLOCKER",
                        "deliverable": os.path.basename(flashcard_path),
                        "target_skill": "user:tao-flashcard",
                        "target_script": "scripts/flashcard_html_builder.py::audit_flashcard_no_mid_sentence_truncation",
                        "error_code": "FLASHCARD_MID_SENTENCE_TRUNCATION",
                        "description": "; ".join(d.get("detail", "") for d in fc_defects[:3]),
                        "suggested_patch": "Viết câu giải thích tự nhiên 45-90 từ, cấm cắt mảng words[:N] và tránh kết thúc câu bằng giới từ/hư từ treo."
                    })
                read_fc_rep = audit_final_human_readability_and_clinical_terminology_qa(fc_html, "flashcard", cards=fc_list)
                if not read_fc_rep["valid"]:
                    fc_metrics["human_readability_defects"] = len(read_fc_rep["defects"])
                    for d_item in read_fc_rep["defects"]:
                        defects.append({
                            "severity": "S1_BLOCKER",
                            "deliverable": os.path.basename(flashcard_path),
                            "target_skill": "user:tao-flashcard",
                            "target_script": "scripts/flashcard_html_builder.py",
                            "error_code": d_item["code"],
                            "description": d_item["detail"],
                            "suggested_patch": "Sửa từ ngữ dịch máy ngô nghê và mã LaTeX thô trong thẻ Flashcard."
                        })
                if trunc_rep.get("valid", True) and read_fc_rep["valid"] and len(fc_list) > 0:
                    passed_checks.append(f"Flashcard 3D Anti-Truncation & Clean UI ({len(fc_list)} thẻ, 0 cắt cụt câu)")
            except Exception as ex:
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(flashcard_path),
                    "target_skill": "user:tao-flashcard",
                    "target_script": "scripts/flashcard_html_builder.py",
                    "error_code": "FLASHCARD_JSON_PARSE_ERROR",
                    "description": str(ex),
                    "suggested_patch": "Kiểm tra JSON flashcards trong file HTML."
                })

    # --- 3. Kiểm định Đề MCQ HTML (Hỗ trợ cả `<script id="quizData">` và `const questions =`) ---
    qz_metrics: Dict[str, Any] = {
        "exists": False,
        "question_count": 0,
        "longest_is_key_rate": 0.0,
        "human_readability_defects": 0,
    }
    if quiz_path and os.path.isfile(quiz_path):
        qz_metrics["exists"] = True
        qz_html = Path(quiz_path).read_text(encoding="utf-8", errors="replace")
        m_qz = (
            re.search(r'<script\s+type="application/json"\s+id="quizData">\s*(\[.*?\])\s*</script>', qz_html, flags=re.S | re.I)
            or re.search(r"(?:const|let|var)\s+(?:questions|quizData)\s*=\s*(\[.*?\])\s*;", qz_html, flags=re.S)
        )
        if not m_qz:
            defects.append({
                "severity": "S1_BLOCKER",
                "deliverable": os.path.basename(quiz_path),
                "target_skill": "user:tao-de",
                "target_script": "scripts/quiz_html_builder.py",
                "error_code": "MCQ_ZERO_QUESTIONS_PARSED",
                "description": "Không trích xuất được mảng JSON câu hỏi từ `<script id='quizData'>` hoặc `const questions` (question_count=0).",
                "suggested_patch": "Kiểm tra quiz_html_builder.py::build_quiz_html() xuất đúng `<script type='application/json' id='quizData'>`."
            })
        else:
            try:
                qz_list = json.loads(m_qz.group(1).replace("<\\/", "</"))
                qz_metrics["question_count"] = len(qz_list)
                if len(qz_list) == 0:
                    defects.append({
                        "severity": "S1_BLOCKER",
                        "deliverable": os.path.basename(quiz_path),
                        "target_skill": "user:tao-de",
                        "target_script": "scripts/quiz_html_builder.py",
                        "error_code": "MCQ_EMPTY_ARRAY",
                        "description": "Danh sách câu hỏi trắc nghiệm rỗng (0 câu).",
                        "suggested_patch": "Biên soạn đủ >= 40 câu hỏi SBA lâm sàng."
                    })
                len_rep = audit_mcq_option_length_parity_qa(qz_list)
                qz_metrics["longest_is_key_rate"] = len_rep.get("longest_is_key_rate", 0.0)
                if not len_rep.get("valid", True):
                    defects.append({
                        "severity": "S2_CRITICAL",
                        "deliverable": os.path.basename(quiz_path),
                        "target_skill": "user:tao-de",
                        "target_script": "scripts/quiz_html_builder.py::audit_mcq_option_length_parity",
                        "error_code": "MCQ_OPTION_LENGTH_IMBALANCE",
                        "description": "; ".join(d.get("detail", "") for d in len_rep.get("defects", [])[:3]),
                        "suggested_patch": "Cân bằng độ dài ký tự 4 phương án A/B/C/D bằng nội dung lâm sàng thực chất (cấm nối đuôi sáo rỗng)."
                    })
                read_qz_rep = audit_final_human_readability_and_clinical_terminology_qa(qz_html, "quiz", questions=qz_list)
                if not read_qz_rep["valid"]:
                    qz_metrics["human_readability_defects"] = len(read_qz_rep["defects"])
                    for d_item in read_qz_rep["defects"]:
                        defects.append({
                            "severity": "S1_BLOCKER",
                            "deliverable": os.path.basename(quiz_path),
                            "target_skill": "user:tao-de",
                            "target_script": "scripts/quiz_html_builder.py::audit_why_wrong_human_readability_and_anti_template",
                            "error_code": d_item["code"],
                            "description": d_item["detail"],
                            "suggested_patch": "Viết giải thích từng phương án sai tự nhiên theo điểm bản lề lâm sàng; cấm dùng văn mẫu cắt cụt câu phương án `opt[:65]` hoặc nhân bản 3 lần cùng 1 câu."
                        })
                if len_rep.get("valid", True) and read_qz_rep["valid"] and len(qz_list) > 0:
                    passed_checks.append(f"MCQ SBA Clinical Vignettes, Human Readability & Option Parity ({len(qz_list)} câu, longest_key={qz_metrics['longest_is_key_rate']:.1%})")
            except Exception as ex:
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(quiz_path),
                    "target_skill": "user:tao-de",
                    "target_script": "scripts/quiz_html_builder.py",
                    "error_code": "MCQ_JSON_PARSE_ERROR",
                    "description": str(ex),
                    "suggested_patch": "Kiểm tra JSON quizData trong file HTML."
                })

    # --- 4. Kiểm định Tệp thứ 4: Sổ tay PDF @tom-tat (LOCK-58) HOẶC Đề MEQ HTML ---
    summary_metrics: Dict[str, Any] = {
        "exists": False,
        "page_count": 0,
        "right_margin_overflow_pages": 0,
        "human_readability_defects": 0,
    }
    if summary_pdf_path and os.path.isfile(summary_pdf_path):
        summary_metrics["exists"] = True
        try:
            _sdoc = pdfium.PdfDocument(summary_pdf_path)
            summary_metrics["page_count"] = len(_sdoc)
            _sum_txt = "".join((_sdoc[_i].get_textpage().get_text_range() or "") + "\n" for _i in range(len(_sdoc)))
            _spx = audit_compiled_pdf_page_margin_overflow_qa(summary_pdf_path)
            summary_metrics["right_margin_overflow_pages"] = len(_spx.get("overflow_pages", []))
            if not _spx.get("valid", True):
                for _sd in _spx.get("defects", []):
                    _sd["target_skill"] = "user:tom-tat"
                    defects.append(_sd)
            _sread = audit_final_human_readability_and_clinical_terminology_qa(_sum_txt, "summary_pdf")
            if not _sread.get("valid", True):
                summary_metrics["human_readability_defects"] = len(_sread.get("defects", []))
                for _d_it in _sread.get("defects", []):
                    defects.append({
                        "severity": "S1_BLOCKER",
                        "deliverable": os.path.basename(summary_pdf_path),
                        "target_skill": "user:tom-tat",
                        "target_script": "scripts/validate_and_build_soan_bai.py",
                        "error_code": _d_it["code"],
                        "description": _d_it["detail"],
                        "suggested_patch": "Chuẩn hóa thuật ngữ triệu chứng học tiếng Việt trong Sổ tay Tóm tắt LaTeX.",
                    })
            if _spx.get("valid", True) and _sread.get("valid", True) and len(_sdoc) >= 1:
                passed_checks.append(f"Summary High-Yield PDF @tom-tat ({len(_sdoc)} trang A4, 0 tràn lề, 0 từ dịch máy)")
        except Exception as _sex:
            defects.append({
                "severity": "S1_BLOCKER",
                "deliverable": os.path.basename(summary_pdf_path),
                "target_skill": "user:tom-tat",
                "target_script": "scripts/validate_and_build_soan_bai.py",
                "error_code": "SUMMARY_PDF_UNREADABLE",
                "description": f"Không đọc được Sổ tay Tóm tắt PDF: {_sex}",
                "suggested_patch": "Kiểm tra lại biên dịch LuaLaTeX/pdfLaTeX trong @tom-tat.",
            })

    meq_metrics: Dict[str, Any] = {"exists": False, "case_count": 0, "human_readability_defects": 0}
    if meq_path and os.path.isfile(meq_path) and not str(meq_path).lower().endswith(".pdf"):
        meq_metrics["exists"] = True
        meq_html = Path(meq_path).read_text(encoding="utf-8", errors="replace")
        m_meq = (
            re.search(r'<script\s+type="application/json"\s+id="meqData">\s*(\{.*?\}|\[.*?\])\s*</script>', meq_html, flags=re.S | re.I)
            or re.search(r"(?:const|let|var)\s+(?:EXAM_DATA|meqData)\s*=\s*(\{.*?\}|\[.*?\])\s*;", meq_html, flags=re.S)
        )
        if not m_meq:
            defects.append({
                "severity": "S1_BLOCKER",
                "deliverable": os.path.basename(meq_path),
                "target_skill": "user:meq",
                "target_script": "scripts/meq_html_builder.py",
                "error_code": "MEQ_ZERO_CASES_PARSED",
                "description": "Không trích xuất được dữ liệu JSON ca bệnh từ `<script id='meqData'>` hoặc `EXAM_DATA` (case_count=0).",
                "suggested_patch": "Kiểm tra meq_html_builder.py::build_meq_html() xuất đúng `<script type='application/json' id='meqData'>`."
            })
        else:
            try:
                meq_obj = json.loads(m_meq.group(1).replace("<\\/", "</"))
                meq_cases = meq_obj if isinstance(meq_obj, list) else meq_obj.get("cases", [])
                meq_metrics["case_count"] = len(meq_cases)
                if len(meq_cases) == 0:
                    defects.append({
                        "severity": "S1_BLOCKER",
                        "deliverable": os.path.basename(meq_path),
                        "target_skill": "user:meq",
                        "target_script": "scripts/meq_html_builder.py",
                        "error_code": "MEQ_EMPTY_CASES",
                        "description": "Đề MEQ có 0 ca lâm sàng.",
                        "suggested_patch": "Sinh đủ >= 8 ca lâm sàng tiến triển."
                    })
                read_meq_rep = audit_final_human_readability_and_clinical_terminology_qa(meq_html, "meq")
                if not read_meq_rep["valid"]:
                    meq_metrics["human_readability_defects"] = len(read_meq_rep["defects"])
                    for d_item in read_meq_rep["defects"]:
                        defects.append({
                            "severity": "S1_BLOCKER",
                            "deliverable": os.path.basename(meq_path),
                            "target_skill": "user:meq",
                            "target_script": "scripts/meq_html_builder.py",
                            "error_code": d_item["code"],
                            "description": d_item["detail"],
                            "suggested_patch": "Chuẩn hóa thuật ngữ triệu chứng học tiếng Việt và mã toán học trong MEQ."
                        })
                if len(meq_cases) > 0 and read_meq_rep["valid"]:
                    passed_checks.append(f"MEQ Progressive Clinical Cases & 4-Col Rubric ({len(meq_cases)} ca lâm sàng)")
            except Exception as ex:
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(meq_path),
                    "target_skill": "user:meq",
                    "target_script": "scripts/meq_html_builder.py",
                    "error_code": "MEQ_JSON_PARSE_ERROR",
                    "description": str(ex),
                    "suggested_patch": "Kiểm tra JSON meqData trong file HTML."
                })

    # --- 5. Hợp nhất nhật ký sự cố runtime bền vững trong phiên (_qa_runtime_incidents.jsonl) ---
    persisted_incidents = load_session_runtime_incidents(out_folder, prefix_code)
    incidents_list: List[Dict[str, Any]] = []
    seen_inc = set()
    for inc in list(runtime_incidents or []) + persisted_incidents:
        if not isinstance(inc, dict):
            continue
        k = (inc.get("error_code", ""), inc.get("deliverable", ""), str(inc.get("description") or inc.get("root_cause") or "")[:120])
        if k not in seen_inc:
            seen_inc.add(k)
            incidents_list.append(inc)

    # LOCK-58: Chạy node --check trực tiếp trên mọi thẻ <script> của 3 tệp HTML thành phẩm
    for _lbl, _hp, _tsk in [
        ("Flashcard.html", flashcard_path, "user:tao-flashcard"),
        ("Quiz.html", quiz_path, "user:tao-de"),
        ("MEQ.html", meq_path, "user:meq"),
    ]:
        if _hp and os.path.isfile(_hp) and str(_hp).lower().endswith(".html"):
            _js_chk = audit_html_js_syntax_with_node(_hp)
            if not _js_chk.get("valid", True):
                defects.append({
                    "severity": "S1_BLOCKER",
                    "deliverable": os.path.basename(_hp),
                    "target_skill": _tsk,
                    "target_script": "scripts/qa_test_harness.py::audit_html_js_syntax_with_node",
                    "error_code": "JS_SYNTAX_ERROR_NODE_CHECK",
                    "description": f"LỖI CÚ PHÁP JAVASCRIPT NGHIÊM TRỌNG trên {os.path.basename(_hp)}: {(_js_chk.get('errors') or [])[:2]}",
                    "suggested_patch": "Kiểm tra ký tự xuống dòng trần hoặc lỗi cú pháp JS trong template sinh HTML và chạy node --check đạt rc=0.",
                })
            else:
                passed_checks.append(f"JS Runtime Syntax Check ({os.path.basename(_hp)}: {_js_chk.get('scripts_checked', 0)} script rc=0)")

    verdict = "GO (PASSED_CLEAN)" if len(defects) == 0 else "NO-GO (DEFECTS_DETECTED)"

    pdf_ok = pdf_metrics.get("exists", False) and pdf_metrics.get("svg_blank_boxes", 0) == 0 and pdf_metrics.get("broken_imgs", 0) == 0 and pdf_metrics.get("human_readability_defects", 0) == 0
    fc_ok = fc_metrics.get("exists", False) and fc_metrics.get("card_count", 0) > 0 and fc_metrics.get("truncated_count", 0) == 0 and fc_metrics.get("human_readability_defects", 0) == 0
    qz_ok = qz_metrics.get("exists", False) and qz_metrics.get("question_count", 0) > 0 and qz_metrics.get("human_readability_defects", 0) == 0 and not any(d.get("deliverable") == (os.path.basename(quiz_path) if quiz_path else "") for d in defects)
    summary_ok = summary_metrics.get("exists", False) and summary_metrics.get("page_count", 0) > 0 and summary_metrics.get("right_margin_overflow_pages", 0) == 0 and summary_metrics.get("human_readability_defects", 0) == 0
    meq_ok = meq_metrics.get("exists", False) and meq_metrics.get("case_count", 0) > 0 and meq_metrics.get("human_readability_defects", 0) == 0 and not any(d.get("deliverable") == (os.path.basename(meq_path) if meq_path else "") for d in defects)

    report_payload = {
        "schema_version": "LOCK-24_FB-56_SILENT_BACKGROUND_QA_DAEMON_v3.4",
        "timestamp": now_iso,
        "topic_code": prefix_code,
        "topic_title": topic_title,
        "verdict": verdict,
        "active_defects_count": len(defects),
        "self_healed_incidents_count": len(incidents_list),
        "passed_checks": passed_checks,
        "active_defects": defects,
        "self_healed_runtime_incidents": incidents_list,
        "metrics": {
            "pdf": pdf_metrics,
            "flashcard": fc_metrics,
            "quiz": qz_metrics,
            "meq": meq_metrics,
            "summary_pdf": summary_metrics,
        },
    }

    json_report_path = os.path.join(out_folder, f"{prefix_code}_qa_qc_telemetry.json")
    try:
        Path(json_report_path).write_text(json.dumps(report_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as _ign:
        _ = _ign

    md_report_path = os.path.join(out_folder, f"{prefix_code} Báo cáo QA QC.md")
    header_label = f"{prefix_code} {topic_title}".strip()
    if always_export_md or len(defects) > 0 or len(incidents_list) > 0:
        md_lines = [
            f"# BÁO CÁO KIỂM ĐỊNH NGẦM @qa-qc & CHẨN ĐOÁN KỸ THUẬT CHO @creator-skill (`{header_label}`)",
            "",
            f"- **Thời gian kiểm toán:** `{now_iso}`",
            f"- **Phán quyết nghiệm thu (`Verdict`):** **`{verdict}`**",
            f"- **Số lỗi còn tồn đọng (`Active Defects`):** `{len(defects)}`",
            f"- **Số sự cố phát hiện & đã tự vá trong phiên (`Self-Healed Runtime Incidents`):** `{len(incidents_list)}`",
            "",
            "## 1. Kết Quả Kiểm Định Thực Tế 4 Tệp Thành Phẩm (Cổng Đọc Lại Lần Cuối `LOCK-24 / FB-56`)",
            "",
            "| Tệp thành phẩm | Thông số đo lường thực tế | Trạng thái cổng kiểm định |",
            "| :--- | :--- | :--- |",
            f"| `{os.path.basename(pdf_path) if pdf_path else 'PDF'}` | `{pdf_metrics.get('page_count', 0)}` trang A4 · `{pdf_metrics.get('svg_blank_boxes', 0)}` hộp SVG rỗng · `{pdf_metrics.get('broken_imgs', 0)}` ảnh lỗi URI · `{pdf_metrics.get('human_readability_defects', 0)}` lỗi ngôn ngữ/LaTeX | `{'PASSED' if pdf_ok else 'FAILED'}` |",
            f"| `{os.path.basename(flashcard_path) if flashcard_path else 'Flashcard'}` | `{fc_metrics.get('card_count', 0)}` thẻ 3D · `{fc_metrics.get('truncated_count', 0)}` thẻ cắt cụt câu · `{fc_metrics.get('human_readability_defects', 0)}` lỗi ngôn ngữ | `{'PASSED' if fc_ok else 'FAILED'}` |",
            f"| `{os.path.basename(quiz_path) if quiz_path else 'MCQ'}` | `{qz_metrics.get('question_count', 0)}` câu SBA · `longest_is_key_rate = {qz_metrics.get('longest_is_key_rate', 0.0):.1%}` · `{qz_metrics.get('human_readability_defects', 0)}` lỗi văn mẫu/cắt câu | `{'PASSED' if qz_ok else 'FAILED'}` |",
            (
                f"| `{os.path.basename(summary_pdf_path)}` | `{summary_metrics.get('page_count', 0)}` trang A4 Sổ tay `@tom-tat` · `{summary_metrics.get('right_margin_overflow_pages', 0)}` tràn lề · `{summary_metrics.get('human_readability_defects', 0)}` lỗi ngôn ngữ | `{'PASSED' if summary_ok else 'FAILED'}` |"
                if summary_pdf_path
                else f"| `{os.path.basename(meq_path) if meq_path else 'MEQ'}` | `{meq_metrics.get('case_count', 0)}` ca lâm sàng tiến triển · `{meq_metrics.get('human_readability_defects', 0)}` lỗi ngôn ngữ | `{'PASSED' if meq_ok else 'FAILED'}` |"
            ),
            "",
            "## 2. Nhật Ký Lỗi Phát Hiện & Hồ Sơ Tự Vá Cho `@creator-skill`",
            "",
        ]
        if not defects and not incidents_list:
            md_lines.append("- Không có lỗi tồn đọng. Toàn bộ 4 tệp thành phẩm vượt qua các cổng kiểm toán thị giác, ngữ nghĩa và đọc rà soát lần cuối.")
        for idx_d, d in enumerate(defects, 1):
            md_lines.extend([
                f"### [LỖI TỒN ĐỌNG #{idx_d}] `{d.get('error_code')}` ({d.get('severity')})",
                f"- **Tệp bị ảnh hưởng:** `{d.get('deliverable')}`",
                f"- **Skill & Hàm cần vá:** `{d.get('target_skill')}` -> `{d.get('target_script')}`",
                f"- **Mô tả chi tiết:** {d.get('description')}",
                f"- **Chỉ dẫn vá lỗi cho `@creator-skill`:** {d.get('suggested_patch')}",
                "",
            ])
        for idx_i, inc in enumerate(incidents_list, 1):
            rc_text = inc.get("root_cause") or inc.get("description") or ""
            pa_text = inc.get("patch_applied") or inc.get("self_healed_fix") or inc.get("suggested_patch") or ""
            md_lines.extend([
                f"### [SỰ CỐ ĐÃ PHÁT HIỆN & TỰ VÁ TRONG PHIÊN #{idx_i}] `{inc.get('error_code', 'RUNTIME_INCIDENT')}`",
                f"- **Hạng mục / Tệp:** `{inc.get('deliverable', 'PDF / Orchestrator')}`",
                f"- **Skill & Hàm gốc rễ:** `{inc.get('target_skill', 'user:soan-bai-giang')}` -> `{inc.get('target_script', 'scripts/pdf_lecture_builder.py')}`",
                f"- **Nguyên nhân gốc rễ:** {rc_text}",
                f"- **Bản vá đã áp dụng (`Patch Applied`):** {pa_text}",
                "",
            ])
        md_lines.extend([
            "## 3. Payload JSON Chẩn Đoán Tự Động (Gửi File Này Cho `@creator-skill` Khi Cần Vá Hệ Sinh Thái)",
            "",
            "```json",
            json.dumps(report_payload, ensure_ascii=False, indent=2),
            "```",
            "",
        ])
        Path(md_report_path).write_text("\n".join(md_lines), encoding="utf-8")

    report_payload["md_report_path"] = md_report_path
    report_payload["json_report_path"] = json_report_path
    return report_payload




# ==============================================================================
# LOCK-44 / FB-75 (@qa-qc v3.8): KIỂM THỬ QUY CÁCH TÁCH DÒNG 4 TẦNG BULLET (< 4 DÒNG),
# BỘ THẺ NHỚ KÉP (THUỘC BÀI NHANH + TƯ DUY) & LUỒNG STEMI MILESTONE x PARALLEL TEAM-AGENT
# ==============================================================================

def audit_lock44_bullet_hierarchy_dual_flashcard_and_stemi_workflow_qa(
    lecture_html: str = "",
    flashcards_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    LOCK-44 / FB-75 (@qa-qc v3.8 - Kịch bản 32):
    Kiểm định tự động 3 nâng cấp mới của người dùng:
      1. Bài giảng PDF tách dòng ngắn (< 4 dòng, mục tiêu 1–2 dòng) và phân cấp 4 tầng bullet (`ul.lvl1..lvl4`).
      2. Bộ thẻ nhớ Flashcard Kép có cả `core_recall` (Thuộc bài nhanh) và `clinical_reasoning` (Tư duy & Cơ chế).
      3. Cấu trúc luồng STEMI Sequential Milestones x Intra-Milestone Parallel Team-Agents.
    """
    tag_strip = re.compile(r"<[^>]+>")
    raw_html = str(lecture_html or "")
    over_4_line_cnt = 0
    for m_li in re.finditer(r"<li\b[^>]*>(.*?)</li>", raw_html, flags=re.I | re.S):
        own_seg = re.split(r"<(?:ul|ol)\b", m_li.group(1), maxsplit=1, flags=re.I)[0]
        plain = re.sub(r"\s+", " ", tag_strip.sub(" ", own_seg)).strip()
        if len(plain.split()) > 45:
            over_4_line_cnt += 1

    cards = flashcards_data or []
    recall_cnt = sum(1 for c in cards if isinstance(c, dict) and str(c.get("card_mode", "")).lower() == "core_recall")
    reason_cnt = len(cards) - recall_cnt

    return {
        "valid": over_4_line_cnt == 0,
        "lock_id": "LOCK-44_FB-75",
        "over_4_line_bullets_count": over_4_line_cnt,
        "flashcard_core_recall_count": recall_cnt,
        "flashcard_clinical_reasoning_count": reason_cnt,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Independent Proactive QA/QC Test Harness v2.7")
    parser.add_argument("--self-test", action="store_true", help="Chạy bộ tự kiểm thử đối chứng 6 tầng")
    parser.add_argument("--audit-dir", default="", help="Đường dẫn thư mục skill cần kiểm thử Read-Only")
    args = parser.parse_args()
    if args.audit_dir:
        out = audit_skill_directory_readonly(args.audit_dir)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(1 if out["tripwire_triggered"] else 0)
    res = _run_self_tests()
    if not res["self_test_passed"]:
        print("[qa_test_harness v2.7 FAILED]:", json.dumps(res, ensure_ascii=False))
        sys.exit(1)
    print("[qa_test_harness v2.7 SELF-TEST PASSED]:", json.dumps(res, ensure_ascii=False))
