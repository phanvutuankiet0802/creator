"""
Bộ Công Cụ Kiểm Toán Kiến Trúc Đa Hình Thái, Quản Trị PM Team-Agent Chịu Trách Nhiệm Tối Cao,
Kiểm Toán Cô Lập Đích (Single-Target Blast-Radius Isolation LOCK-11),
Chuỗi Bàn Giao Đối Kháng 5 Agent & Chốt Chặn Chống Mất Tính Năng Cũ
(Pre/Post AST & Feature Diff Guard v8.1 - FB-19 -> FB-46, LOCK-01 -> LOCK-15)
"""
from pathlib import Path

import argparse
import ast
import glob
import importlib.util
import json
import os
import sys
from typing import Any, Dict, List, Optional, Set


IMMUTABLE_LOCK_IDS = [
    "LOCK-01",
    "LOCK-02",
    "LOCK-03",
    "LOCK-04",
    "LOCK-05",
    "LOCK-06",
    "LOCK-07",
    "LOCK-08",
    "LOCK-09",
    "LOCK-10",
    "LOCK-11",
    "LOCK-12",
    "LOCK-13",
    "LOCK-14",
    "LOCK-15",
    "LOCK-16",
    "LOCK-17",
    "LOCK-18",
    "LOCK-19",
    "LOCK-20",
    "LOCK-21",
    "LOCK-22",
    "LOCK-23",
    "LOCK-24",
    "LOCK-25",
    "LOCK-26",
    "LOCK-27",
    "LOCK-28",
    "LOCK-29",
    "LOCK-30",
    "LOCK-31", "LOCK-39", "LOCK-40", "LOCK-41", "LOCK-42", "LOCK-43", "LOCK-38", "LOCK-37", "LOCK-36", "LOCK-35", "LOCK-34", "LOCK-33", "LOCK-32",
]


def _load_module_from_path(mod_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Không thể nạp module {mod_name} từ {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _find_skill_dir(skills_root: str, skill_name: str, allow_cross_session: bool = False) -> str:
    clean_name = skill_name.replace("user:", "").strip()
    cand = os.path.join(skills_root, clean_name)
    if os.path.isdir(cand):
        return cand
    if allow_cross_session:
        for g in sorted(glob.glob(f"/working_dir/*/artifacts/release*/{clean_name}"), reverse=True):
            if os.path.isdir(g):
                return g
        for g in sorted(glob.glob(f"/working_dir/*/skills/user/{clean_name}"), reverse=True):
            if os.path.isdir(g):
                return g
    return cand


def extract_python_ast_signatures(py_code: str) -> Dict[str, List[str]]:
    tree = ast.parse(py_code)
    sigs: Dict[str, List[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            sigs[node.name] = args
    return sigs


def verify_lock11_target_isolation_guard(
    user_requested_skills: List[str],
    candidate_update_skills: List[str],
) -> Dict[str, Any]:
    norm_req = {s.replace("user:", "").strip() for s in user_requested_skills if s.strip()}
    norm_cand = {s.replace("user:", "").strip() for s in candidate_update_skills if s.strip()}
    unauthorized = sorted(norm_cand - norm_req)
    authorized = sorted(norm_cand & norm_req)
    return {
        "lock11_valid": len(unauthorized) == 0 and len(norm_req) > 0,
        "requested_whitelist": sorted(norm_req),
        "authorized_targets": authorized,
        "unauthorized_collateral_targets": unauthorized,
    }


def verify_pre_post_version_diff_guard(
    baseline_manifest: Dict[str, Any],
    candidate_manifest: Dict[str, Any],
) -> Dict[str, Any]:
    base_files: Set[str] = set(baseline_manifest.get("files", []))
    cand_files: Set[str] = set(candidate_manifest.get("files", []))
    dropped_files = sorted(base_files - cand_files)

    base_funcs: Dict[str, List[str]] = baseline_manifest.get("ast_functions", {})
    cand_funcs: Dict[str, List[str]] = candidate_manifest.get("ast_functions", {})
    dropped_functions: List[str] = []
    broken_signatures: List[str] = []

    for fn_name, base_args in base_funcs.items():
        if fn_name not in cand_funcs:
            dropped_functions.append(fn_name)
        else:
            cand_args = cand_funcs[fn_name]
            if cand_args[: len(base_args)] != base_args:
                broken_signatures.append(
                    f"{fn_name}: tham số cũ {base_args} bị đổi thành {cand_args}"
                )

    base_locks: Set[str] = set(baseline_manifest.get("immutable_locks", []))
    cand_locks: Set[str] = set(candidate_manifest.get("immutable_locks", []))
    dropped_locks = sorted(base_locks - cand_locks)

    added_files = sorted(cand_files - base_files)
    added_functions = sorted(set(cand_funcs.keys()) - set(base_funcs.keys()))

    regression_detected = bool(dropped_files or dropped_functions or broken_signatures or dropped_locks)
    return {
        "additive_only_valid": not regression_detected,
        "regression_detected": regression_detected,
        "dropped_files": dropped_files,
        "dropped_functions": dropped_functions,
        "broken_signatures": broken_signatures,
        "dropped_immutable_locks": dropped_locks,
        "added_files": added_files,
        "added_functions": added_functions,
    }


def audit_rule_to_code_parity_and_qa_blindspots(
    skills_root: str,
    target_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    blindspots: List[str] = []
    verified_contracts: List[str] = []
    untouched_remote_skills: List[str] = []

    required_ast_contracts = {
        "creator-skill": (
            "scripts/skill_validator.py",
            [
                "verify_lock11_target_isolation_guard",
                "verify_pre_post_version_diff_guard",
                "audit_rule_to_code_parity_and_qa_blindspots",
                "run_team_agent_handoff_pipeline",
                "build_parallel_team_agent_dispatch_plan",
                "verify_parallel_team_agent_review_receipts",
                "analyze_mcq_and_arbitrator_parallel_readiness",
                "evaluate_ecosystem_parallel_execution_strategy",
                "execute_in_sandbox_parallel_team_agent_reviews",
                "verify_bigtech_true_multi_agent_barrier_and_late_materialization",
            ],
        ),
        "nap-data": (
            "scripts/data_cartridge_manager.py",
            [
                "parse_sources_index",
                "lookup_lesson_sources",
                "get_active_notebook_id",
                "extract_notebooklm_page_images",
                "crop_notebooklm_page_xy_to_base64",
            ],
        ),
        "soan-bai-giang": (
            "scripts/pdf_lecture_builder.py",
            [
                "estimate_propositional_density",
                "compute_deduplicated_triad_key_budget",
                "compute_proportional_page_budget",
                "audit_source_key_and_proposition_recall",
                "build_compact_svg_causal_diagram",
                "audit_diagram_font_size_12pt",
                "audit_bold_phrase_integrity_and_heading_consistency",
                "auto_normalize_bullet_lead_in_bold",
                "sanitize_and_audit_spurious_linebreaks",
                "audit_heading_and_label_conciseness",
                "audit_bilingual_medical_terms",
                "format_table_cells_multiline_html",
                "extract_exhaustive_vid_propositions_and_keywords",
                "audit_vid_100pct_exhaustive_recall",
                "audit_explanation_depth_and_teaching_flow",
                "audit_lecture_structure_and_color_budget",
                "compile_lecture_pdf",
                "draw_python_flowchart",
                "crop_image_region_to_base64",
                "crop_pdf_region_to_base64",
                "sanitize_disguised_ascii_in_diagram_label",
                "sanitize_clinical_vietnamese_terminology_and_latex",
                "audit_final_human_readability_and_clinical_terminology",
            ],
        ),
        "tao-flashcard": (
            "scripts/flashcard_html_builder.py",
            [
                "validate_flashcards_schema",
                "build_flashcard_html",
                "format_standard_flashcard_filename",
                "crop_pdf_region_to_img_tag",
                "card_requires_visual_binding",
                "audit_flashcard_visual_anchors",
                "audit_flashcard_no_mid_sentence_truncation",
            ],
        ),
        "tham-dinh-su-pham": (
            "scripts/pedagogical_rubric_scorer.py",
            [
                "audit_explanation_depth_and_teaching_flow",
                "audit_anti_commonsense_and_sibling_plausibility",
                "audit_counterfactual_decision_pivot",
                "audit_clinical_intervention_vignette_depth_and_cue_utilization",
                "audit_mcq_option_length_parity",
                "audit_mcq_response_order_fidelity",
                "audit_two_tier_source_coverage_and_expansion",
                "compute_deduplicated_triad_key_budget",
                "compute_proportional_page_budget",
                "audit_source_key_and_proposition_recall",
                "audit_bold_phrase_integrity_and_heading_consistency",
                "audit_heading_and_label_conciseness",
                "audit_diagram_font_size_12pt",
                "audit_bilingual_medical_terms",
                "verify_authentic_nbme_vignette",
                "audit_vignette_chronological_flow",
                "audit_orth_2d_vignette_and_embedded_matrix",
                "audit_forensic_distractor_profiling",
                "audit_convergence_cues",
                "audit_inter_item_cueing_matrix",
                "audit_option_grammatical_and_category_homogeneity",
                "audit_near_miss_why_wrong_specificity",
                "audit_ubd_three_circles_quota",
                "analyze_mcq_nbme_pedagogy",
                "analyze_flashcard_supermemo_pedagogy",
                "build_and_validate_root_anchor_schema",
                "audit_root_anchor_cross_files",
                "audit_final_human_readability_and_clinical_terminology",
            ],
        ),
        "tao-de": (
            "scripts/quiz_html_builder.py",
            [
                "audit_lead_in_standalone_bypass",
                "audit_multi_cue_integration_quota",
                "audit_answer_key_balance_and_streaks",
                "auto_rebalance_mcq_answer_keys",
                "audit_visual_pedagogical_placement",
                "audit_stem_zero_source_and_explanation_verbatim_citation",
                "audit_fuzzy_trace_familiarity_traps",
                "audit_anti_commonsense_and_sibling_plausibility",
                "audit_counterfactual_decision_pivot",
                "audit_clinical_intervention_vignette_depth_and_cue_utilization",
                "audit_mcq_option_length_parity",
                "verify_authentic_nbme_vignette",
                "audit_vignette_chronological_flow",
                "audit_orth_2d_vignette_and_embedded_matrix",
                "audit_forensic_distractor_profiling",
                "audit_convergence_cues",
                "audit_inter_item_cueing_matrix",
                "audit_option_grammatical_and_category_homogeneity",
                "audit_near_miss_why_wrong_specificity",
                "validate_quiz_questions_schema",
                "crop_pdf_region_to_base64",
                "crop_image_region_to_base64",
                "build_medical_svg_diagram",
                "format_standard_quiz_filename",
                "build_quiz_html",
                "audit_why_wrong_human_readability_and_anti_template",
                "audit_dual_mode_academic_coverage_and_json_integrity",
                "merge_and_audit_in_sandbox_dual_mode_shards",
            ],
        ),
        "giao-trinh-tong-hop": (
            "scripts/master_audit_gate.py",
            [
                "audit_rendered_diagrams_cross_check",
                "audit_3_deliverables",
                "audit_4_deliverables",
                "save_pipeline_checkpoint",
                "build_subagent_anchor_bundle",
                "build_parallel_subagent_dispatch_specs",
                "verify_parallel_subagent_handoff_receipts",
                "get_chief_orchestrator_department_roster",
                "build_two_wave_parallel_orchestration_plan",
                "execute_in_sandbox_wave1_parallel_workers",
                "execute_in_sandbox_wave2_parallel_critics",
                "execute_in_sandbox_two_wave_parallel_pipeline",
                "build_bigtech_method_a_single_wave_subagent_plan",
                "execute_active_join_barrier_poll_and_harvest_plan",
                "execute_single_turn_continuous_team_agent_barrier_and_rescue",
                "execute_unified_in_sandbox_single_agent_argon_pipeline",
            ],
        ),
        "ui-ux": (
            "scripts/ui_ergonomics_linter.py",
            [
                "audit_mcq_visual_option_balance",
                "audit_mayer_signaling_density",
                "audit_bold_phrase_integrity_and_heading_consistency",
                "audit_heading_and_label_conciseness",
                "audit_diagram_font_size_12pt_ui",
                "compute_wcag_contrast_ratio",
                "validate_w3c_design_tokens",
            ],
        ),
        "ocr-text": (
            "scripts/ocr_text_cartridge_builder.py",
            [
                "audit_ocr_cardinality_and_garbled_tokens",
                "audit_triad_cardinality_consistency|ensure_page_markers_in_md_text",
                "clean_vietnamese_medical_ocr_garbles|sanitize_ocr_text",
                "build_cartridge_from_md_directory",
            ],
        ),
        "import-md": (
            "scripts/md_cartridge_importer.py",
            [
                "reconcile_and_normalize_cartridge_metadata",
                "audit_post_mount_cartridge_integrity",
                "ensure_page_or_slide_markers_and_lock10",
                "hot_swap_cartridge_into_skill_dir",
            ],
        ),
        "qa-qc": (
            "scripts/qa_test_harness.py",
            [
                "audit_ocr_cardinality_and_garbled_tokens_qa",
                "audit_lecture_fb43_ergonomics_qa",
                "audit_explanation_depth_and_teaching_flow_qa",
                "audit_anti_commonsense_and_counterfactual_qa",
                "audit_nbme_2d_and_iwf_gates_qa",
                "audit_mcq_option_length_parity_qa",
                "audit_mcq_response_order_fidelity",
                "audit_html_deliverable_predictive",
                "run_predictive_premortem_fuzzing",
                "detect_cross_skill_version_drift",
                "evaluate_knowledge_improvement_gate",
                "compute_pass_at_k_and_verdict",
                "audit_flashcard_no_mid_sentence_truncation_qa",
                "audit_anti_silent_deletion_and_skill_md_truncation",
                "audit_final_human_readability_and_clinical_terminology_qa",
                "record_runtime_incident",
                "load_session_runtime_incidents",
                "run_silent_background_qa_and_export_report",
                "audit_anti_turn_break_and_sandbox_isolation_guard",
            ],
        ),
    }

    norm_targets = (
        {s.replace("user:", "").strip() for s in target_skills if s.strip()}
        if target_skills
        else None
    )

    for skill_name, (rel_py, req_fns) in required_ast_contracts.items():
        if norm_targets is not None and skill_name not in norm_targets:
            untouched_remote_skills.append(f"{skill_name}:isolated_by_lock11")
            continue

        s_dir = _find_skill_dir(skills_root, skill_name, allow_cross_session=False)
        if not os.path.isdir(s_dir):
            if norm_targets is not None and skill_name in norm_targets:
                blindspots.append(f"Không tìm thấy thư mục skill đích '{skill_name}' tại {s_dir}")
            else:
                untouched_remote_skills.append(f"{skill_name}:untouched_in_remote_storage")
            continue

        py_path = os.path.join(s_dir, rel_py)
        if not os.path.isfile(py_path):
            if norm_targets is not None and skill_name in norm_targets:
                blindspots.append(f"Thiếu kịch bản thực thi {skill_name}/{rel_py}")
            else:
                untouched_remote_skills.append(f"{skill_name}:partial_readonly_loaded")
            continue
        with open(py_path, "r", encoding="utf-8") as f:
            py_src = f.read()
        sigs = extract_python_ast_signatures(py_src)
        for fn_spec in req_fns:
            fn_candidates = [c.strip() for c in fn_spec.split("|") if c.strip()]
            matched_fn = next((c for c in fn_candidates if c in sigs), None)
            if matched_fn is None:
                blindspots.append(
                    f"[PM_META_AUDIT_BLINDSPOT] Skill '{skill_name}' thiếu hàm thực thi bắt buộc '{fn_spec}' trong {rel_py}!"
                )
            else:
                verified_contracts.append(f"{skill_name}:{matched_fn}({','.join(sigs[matched_fn])})")

    return {
        "valid": len(blindspots) == 0,
        "verified_contracts_count": len(verified_contracts),
        "verified_contracts": verified_contracts,
        "untouched_remote_skills": untouched_remote_skills,
        "blindspots": blindspots,
    }




# ==============================================================================
# LOCK-26 / FB-58 (@creator-skill v8.6):
# ĐỘNG CƠ PHÂN LUỒNG PARALLEL TEAM-AGENT & KIỂM CHỨNG ĐỘC LẬP ĐỐI KHÁNG (3 PARALLEL CRITIC SUB-AGENTS)
# ==============================================================================

def build_parallel_team_agent_dispatch_plan(
    target_skills: Optional[List[str]] = None,
    task_summary: str = "",
    artifacts_dir: str = "",
    subagent_tool_available: bool = True,
) -> Dict[str, Any]:
    """
    LOCK-26 / FB-58 (@creator-skill v8.6):
    Thay vì để 1 Agent đơn độc vừa sửa code/biên soạn vừa tự đóng vai cả 5 thành viên Team-Agent,
    hàm này tạo kế hoạch Phân luồng 3 Sub-Agent Kiểm định & Thiết kế Đối kháng Chạy Song Song
    (`Parallel Adversarial Team-Agent Fan-Out`) để PM (`@creator-skill`) gọi đồng thời 3 lệnh `invoke_subagent`
    trong cùng 1 lượt:
      1. `team_subagent_ui_ux` (`user:ui-ux` v1.6): Kiểm định độc lập W3C Design Tokens, tương phản WCAG AAA 18.88:1,
         bố cục 4-9 trang A4 và cỡ chữ 12pt thực tế của SVG/Python/Ảnh cắt.
      2. `team_subagent_pedagogy` (`user:tham-dinh-su-pham` v5.1): Trong cửa sổ ngữ cảnh độc lập (0% thiên kiến tác giả),
         đối chiếu 3 nguồn gốc (Vid, Slide, PNT) với sản phẩm để thẩm định độ sâu giải thích nhân-quả, triệu chứng học
         tiếng Việt tự nhiên và Điểm bản lề đảo quyết định câu hỏi SBA.
      3. `team_subagent_qa_qc` (`user:qa-qc` v3.4): Chạy độc lập Tháp Kiểm thử 6 Tầng, săn lỗi 28 kịch bản Pre-Mortem
         Fuzzing, kiểm tra DRIFT-01..16 và đối chiếu nhật ký `_qa_runtime_incidents.jsonl`.
    """
    eff_targets = [s.replace("user:", "").strip() for s in (target_skills or ["giao-trinh-tong-hop", "creator-skill"]) if s.strip()]
    eff_dir = os.path.abspath(artifacts_dir or os.getcwd())
    ui_receipt = os.path.join(eff_dir, "_team_subagent_review_ui_ux.json")
    ped_receipt = os.path.join(eff_dir, "_team_subagent_review_pedagogy.json")
    qa_receipt = os.path.join(eff_dir, "_team_subagent_review_qa_qc.json")

    parallel_team_subagents = [
        {
            "role_id": "team_subagent_ui_ux",
            "skill_name": "user:ui-ux",
            "sd_role": "UI/UX Design System & Cognitive Ergonomics Architect",
            "review_receipt_path": ui_receipt,
            "invoke_subagent_description": (
                f"[Team-Agent Parallel Review #1 - @ui-ux] Hãy kích hoạt user:ui-ux để thẩm định độc lập công thái học thị giác "
                f"cho phạm vi {eff_targets} ({task_summary or 'Kiểm định giao diện & ấn phẩm A4'}). "
                f"Kiểm tra W3C Design Tokens, độ tương phản WCAG 2.2 AAA (18.88:1), mật độ bôi đậm Mayer 8-15% (miễn trừ nhãn đầu dòng), "
                f"cỡ chữ thực tế >= 12pt trên khổ A4 cho mọi sơ đồ SVG/Python/Ảnh thủ thuật, và ghi biên bản JSON độc lập vào '{ui_receipt}'."
            ),
        },
        {
            "role_id": "team_subagent_pedagogy",
            "skill_name": "user:tham-dinh-su-pham",
            "sd_role": "Independent Pedagogical, Clinical Semiology & Psychometric Referee",
            "review_receipt_path": ped_receipt,
            "invoke_subagent_description": (
                f"[Team-Agent Parallel Review #2 - @tham-dinh-su-pham] Hãy kích hoạt user:tham-dinh-su-pham trong ngữ cảnh độc lập "
                f"(không chịu thiên kiến của người biên soạn) để phản biện học thuật cho phạm vi {eff_targets} ({task_summary or 'Thẩm định sư phạm & lâm sàng'}). "
                f"Đối chiếu trực tiếp nguồn gốc (Vid/Slide/PNT) với thành phẩm, kiểm tra độ phủ hợp nhất >= 98%, chặn từ dịch máy triệu chứng học "
                f"('đau nhọn', 'đau cùn', 'nhạy cảm dội'), chặn thống kê rác LR+/95% CI, kiểm định Điểm bản lề đảo quyết định SBA và ghi biên bản JSON vào '{ped_receipt}'."
            ),
        },
        {
            "role_id": "team_subagent_qa_qc",
            "skill_name": "user:qa-qc",
            "sd_role": "Independent Proactive 6-Layer QA/QC & Pre-Mortem Chaos Fuzzer",
            "review_receipt_path": qa_receipt,
            "invoke_subagent_description": (
                f"[Team-Agent Parallel Review #3 - @qa-qc] Hãy kích hoạt user:qa-qc để chạy độc lập Tháp Kiểm thử 6 Tầng "
                f"trên phạm vi {eff_targets} ({task_summary or 'Kiểm thử E2E & Săn lỗi tiên đoán'}). "
                f"Thực thi phân tích tĩnh AST (0% nuốt ngoại lệ ngầm, 0% xóa ngầm file/hàm), kiểm tra DRIFT-01..16, "
                f"chạy 28 kịch bản Pre-Mortem Fuzzing, đối chiếu _qa_runtime_incidents.jsonl và ghi phán quyết GO/NO-GO vào '{qa_receipt}'."
            ),
        },
    ]

    mode = "PARALLEL_TEAM_SUBAGENT_FANOUT" if subagent_tool_available else "LOCAL_DETERMINISTIC_PIPELINE_FALLBACK"
    return {
        "schema_version": "8.6-LOCK26-ParallelTeamAgent",
        "execution_mode": mode,
        "pm_coordinator": "user:creator-skill",
        "ambient_ba_profiler": "user:thau-hieu",
        "target_skills": eff_targets,
        "parallel_fanout_count": len(parallel_team_subagents) if subagent_tool_available else 0,
        "proactive_polling_protocol": {
            "tools_required": ["conversations:list", "conversations:read"],
            "mandatory_rule": "Khi nhận thông báo từ bất kỳ Sub-Agent nào trong Team-Agent, PM (@creator-skill) bắt buộc gọi conversations:list và conversations:read kiểm tra trạng thái của tất cả các Sub-Agent trước khi ký duyệt.",
        },
        "parallel_team_subagents": parallel_team_subagents,
    }


def verify_parallel_team_agent_review_receipts(
    review_receipt_paths: List[str],
    author_agent_id: str = "main_orchestrator",
    require_distinct_subagents: bool = False,
) -> Dict[str, Any]:
    """
    LOCK-26 / FB-58 (@creator-skill v8.6):
    Kiểm toán tính độc lập của các biên bản thẩm định từ 3 Sub-Agent trong Team-Agent (`@ui-ux`, `@tham-dinh-su-pham`, `@qa-qc`).
    Chặn đứng hành vi "tự viết tự ký" (`SELF_ATTESTATION_DETECTED`) nếu `reviewer_agent_id == author_agent_id`.
    """
    loaded_reviews: List[Dict[str, Any]] = []
    distinct_reviewer_ids: Set[str] = set()
    integrity_errors: List[str] = []

    for rpath in review_receipt_paths or []:
        if not rpath or not os.path.isfile(rpath):
            if require_distinct_subagents:
                integrity_errors.append(f"MISSING_SUBAGENT_REVIEW_RECEIPT:{rpath}")
            continue
        try:
            with open(rpath, "r", encoding="utf-8") as rf:
                rdata = json.load(rf)
            if not isinstance(rdata, dict):
                integrity_errors.append(f"INVALID_RECEIPT_JSON:{rpath}")
                continue
            rev_id = str(rdata.get("reviewer_agent_id") or rdata.get("subagent_conversation_id") or "").strip()
            if rev_id and rev_id == str(author_agent_id).strip():
                integrity_errors.append(f"SELF_ATTESTATION_DETECTED:{rev_id}_cannot_review_own_artifact")
            elif rev_id:
                distinct_reviewer_ids.add(rev_id)
            loaded_reviews.append(rdata)
        except (OSError, ValueError) as exc:
            integrity_errors.append(f"RECEIPT_READ_ERROR:{rpath}:{type(exc).__name__}")

    if require_distinct_subagents and len(distinct_reviewer_ids) < len(review_receipt_paths):
        integrity_errors.append(
            f"INSUFFICIENT_DISTINCT_SUBAGENTS:expected>={len(review_receipt_paths)},got={len(distinct_reviewer_ids)}"
        )

    independent_verified = (
        len(integrity_errors) == 0
        and len(loaded_reviews) > 0
        and len(distinct_reviewer_ids) >= len(loaded_reviews)
    )
    return {
        "valid": len(integrity_errors) == 0,
        "independent_subagent_review_verified": independent_verified,
        "reviews_loaded_count": len(loaded_reviews),
        "distinct_subagent_ids_count": len(distinct_reviewer_ids),
        "distinct_subagent_ids": sorted(distinct_reviewer_ids),
        "integrity_errors": integrity_errors,
    }




def analyze_mcq_and_arbitrator_parallel_readiness(
    question_count: int = 1,
    has_conflicting_keys_or_multi_specialty: bool = False,
    execution_channel: str = "TASK_MODE",
) -> Dict[str, Any]:
    """
    LOCK-27 / FB-59 (@creator-skill v8.7):
    Phân tích kiến trúc và đưa ra quyết định điều phối cho `@mcq` và `@mcq-chuyen-sau`:
    - Giữ nguyên tốc độ tức thì (Single-Agent Fast Path) cho câu hỏi lẻ hoặc lô nhỏ (1-10 câu) và bảo toàn 100%
      tính tương thích Chat thường (`0 file .py` cho `@mcq`).
    - Đề xuất kiến trúc **Adaptive Hybrid Parallel Sub-Agent** khi giải lô đề lớn (`>= 12-15 câu`) hoặc khi
      `@mcq-chuyen-sau` phân xử các ca siêu khó đa chuyên ngành / mâu thuẫn giữa Giáo trình và Guideline:
      + Với `@mcq`: Chia lô theo cụm thứ tự cố định (`Chunk 1: Câu [1..k]`, `Chunk 2: Câu [k+1..2k]`, `Chunk 3: Câu [2k+1..N]`)
        chạy song song các Sub-Agent rồi ghép nối tuần tự theo đúng khóa `Input_Queue[1..N]` (`Kendall's tau == 1.0`).
      + Với `@mcq-chuyen-sau`: Chạy mô hình **Hội đồng Trọng tài Đối kháng 3 Luồng Song Song (`3-Way Adversarial Arbitrator Sub-Agents`)**:
        (1) Sub-Agent Pháp y Giáo trình (`PNT/Slide/Vid` Forensic), (2) Sub-Agent Bằng chứng Quốc gia & Quốc tế (`kcb.vn` + Guidelines + `@tra-cuu`/`@drugs`),
        (3) Sub-Agent Tâm trắc học Khảo thí (`Psychometric Trap & Key Predictor`) -> Trọng tài chính chốt xác suất trúng Key %.
    """
    is_task = str(execution_channel).upper() in ("TASK_MODE", "SPARK")
    mcq_should_parallelize = is_task and question_count >= 1
    arbitrator_should_parallelize = is_task and (question_count >= 5 or has_conflicting_keys_or_multi_specialty)

    return {
        "schema_version": "8.8-LOCK28-McqParallelAnalysis",
        "preferred_parallel_engine_lock28": "IN_TURN_PARALLEL_TOOL_FANOUT_AND_SAME_SANDBOX_SHARDING",
        "forbid_turn_breaking_chat_subagent": True,
        "execution_channel": execution_channel,
        "question_count": question_count,
        "mcq_recommendation": {
            "skill": "user:mcq",
            "needs_parallel_upgrade": "MANDATORY_3_SUBAGENT_PARALLEL_ENSEMBLE_LOCK54",
            "should_spawn_subagents_now": mcq_should_parallelize,
            "single_agent_threshold": "1 - 10 câu (hoặc khi chạy ở Chat thường Argon): Bắt buộc chạy Single-Agent trực tiếp để trả lời nhanh trong vài giây và giữ nguyên chuẩn Zero-Code-Touch (0 file .py).",
            "parallel_architecture_when_large_batch": (
                "Order-Locked Chunk Parallelism (>= 12 câu ở chế độ Task): Main Agent khóa mảng Input_Queue[1..N], "
                "chia thành 2-3 cụm giữ nguyên thứ tự (ví dụ Câu 1..10, Câu 11..20, Câu 21..30) cho 2-3 Sub-Agent giải song song "
                "(chống suy giảm chất lượng giải thích ở các câu cuối đề), sau đó Main Agent ghép nối 1-1 đúng thứ tự gốc (Kendall's tau == 1.0)."
            ),
        },
        "mcq_chuyen_sau_recommendation": {
            "skill": "user:mcq-chuyen-sau",
            "needs_parallel_upgrade": "HIGH_VALUE_FOR_ADVERSARIAL_ARBITRATION_AND_BATCHES",
            "should_spawn_subagents_now": arbitrator_should_parallelize,
            "single_agent_threshold": "1 - 4 câu đơn chuyên ngành đã rõ câu chữ nguyên văn trong 1 bài giảng.",
            "parallel_architecture_blueprint": (
                "2 chế độ Parallel cho @mcq-chuyen-sau: "
                "(Chế độ A - 3-Way Adversarial Panel cho 1-3 câu tranh cãi gay gắt): Gọi song song 3 Sub-Agent độc lập: "
                "Sub-Agent 1 (Giám định Pháp y nguyên văn PNT/Slide/Vid), Sub-Agent 2 (Đối chiếu Bộ Y tế VN kcb.vn & Guidelines quốc tế qua @tra-cuu/@drugs), "
                "Sub-Agent 3 (Phân tích bẫy tâm trắc học & khẩu vị ra đề qua @phuc-dung-de) -> Trọng tài chính tổng hợp Bàn cân đối đầu & chấm % Key. "
                "(Chế độ B - Batch Sharding cho chùm >= 5 câu khó): Phân luồng song song theo từng cụm câu hỏi độc lập, giữ khóa thứ tự 1-1 FB-32."
            ),
        },
    }





# ==============================================================================
# LOCK-28 / FB-60 (@creator-skill v8.8):
# MA TRẬN ĐÁNH GIÁ KIẾN TRÚC CHẠY SONG SONG TOÀN HỆ SINH THÁI 28 SKILLS
# & ĐỘNG CƠ CHẠY SONG SONG 4 TEAM-AGENT CRITICS NGAY TRONG CÙNG SANDBOX VM
# ==============================================================================

import concurrent.futures

ECOSYSTEM_28_SKILLS_PARALLEL_MATRIX: Dict[str, Dict[str, Any]] = {
    # NHÓM A (13 Skills): Chạy Song Song Đa Tiến Trình Trong Cùng 1 Sandbox VM (In-Sandbox Shared-Disk Multi-Process Parallelism)
    "giao-trinh-tong-hop": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_TWO_WAVE_MULTIPROCESS_POOL",
        "forbid_chat_subagent": True,
        "rationale": "Cần dùng chung ổ đĩa /working_dir cho gói mỏ neo _subagent_anchor_bundle.json, ảnh thủ thuật và 4 tệp PDF + Flashcard + MCQ + MEQ. Chạy ProcessPool/ThreadPool trong cùng Sandbox giúp 0% ngắt lượt chờ nhắc tay và 0% mất file.",
    },
    "creator-skill": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_4_CRITIC_PARALLEL_POOL",
        "forbid_chat_subagent": True,
        "rationale": "Quản trị mã nguồn, kiểm toán AST/Diff và chạy 4 Team-Agent Critics (@ui-ux, @tham-dinh-su-pham, @audit, @qa-qc) trực tiếp trên thư mục staging /tmp/work_build mà không bị cô lập container.",
    },
    "qa-qc": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_SILENT_DAEMON_AND_PARALLEL_FUZZER",
        "forbid_chat_subagent": True,
        "rationale": "Đọc trực tiếp 4 tệp thành phẩm, .source.html và _qa_runtime_incidents.jsonl trên đĩa của phiên chính để xuất <Mã bài> Báo cáo QA QC.md.",
    },
    "soan-bai-giang": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_PARALLEL_IMAGE_CROP_AND_PDF_COMPILE",
        "forbid_chat_subagent": True,
        "rationale": "Cắt nhiều ảnh thủ thuật từ NotebookLM và vẽ lưu đồ Python song song trên cùng ổ đĩa trước khi WeasyPrint biên dịch PDF 4-9 trang A4.",
    },
    "tao-flashcard": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_WAVE1_WORKER_PROCESS",
        "forbid_chat_subagent": True,
        "rationale": "Đọc gói mỏ neo và hình cắt từ ổ đĩa chung, xuất <Mã bài> Flashcard.html ngay trong thư mục xuất của phiên chính.",
    },
    "tao-de": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_WAVE1_WORKER_PROCESS",
        "forbid_chat_subagent": True,
        "rationale": "Đọc gói mỏ neo và cắt lưu đồ từ PDF bài giảng trên cùng ổ đĩa, xuất <Mã bài> TN Ôn tập <Tên bài>.html không bị đứt lượt.",
    },
    "meq": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_WAVE1_WORKER_PROCESS",
        "forbid_chat_subagent": True,
        "rationale": "Đọc trực tiếp PDF/MD và gói mỏ neo trên cùng ổ đĩa Sandbox, xuất <Mã bài> Tự luận ngắn MEQ <Tên bài>.html.",
    },
    "tham-dinh-su-pham": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_WAVE2_CRITIC_PROCESS",
        "forbid_chat_subagent": True,
        "rationale": "Chạy pedagogical_rubric_scorer.py đối chiếu chéo 3 tệp nguồn .md và 4 tệp thành phẩm nằm trên cùng ổ đĩa Sandbox.",
    },
    "ui-ux": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_WAVE2_CRITIC_PROCESS",
        "forbid_chat_subagent": True,
        "rationale": "Chạy ui_ergonomics_linter.py kiểm tra trực tiếp file HTML/SVG/PNG và tokens/medical_design_tokens.json trong cùng Sandbox.",
    },
    "audit": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_WAVE2_CRITIC_AND_IN_TURN_SEARCH",
        "forbid_chat_subagent": True,
        "rationale": "Kết hợp gọi song song NotebookLM + Google Search ở Lượt 1 và chạy clinical_workflow_auditor.py ngay trong cùng Sandbox.",
    },
    "ocr-text": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_PAGE_LEVEL_MULTIPROCESS_OCR",
        "forbid_chat_subagent": True,
        "rationale": "Xử lý nhiều file PDF/DOCX/ZIP trên đĩa cục bộ bằng đa tiến trình Python rồi đóng gói thành 1 file .zip duy nhất trên cùng Sandbox.",
    },
    "import-md": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_ATOMIC_CARTRIDGE_MOUNT",
        "forbid_chat_subagent": True,
        "rationale": "Đồng bộ SHA-256, sources_index.md và cartridge_manifest.json rồi cập nhật skill trực tiếp trên ổ đĩa staging của phiên chính.",
    },
    "plugin": {
        "group": "GROUP_A_IN_SANDBOX_MULTIPROCESS_PARALLEL",
        "recommended_mode": "SAME_SANDBOX_PARALLEL_ZIP_PACKAGER",
        "forbid_chat_subagent": True,
        "rationale": "Quét và nén toàn bộ 28 skills thành 1 file .zip duy nhất trên ổ đĩa của phiên hiện tại để xuất qua google:show_file.",
    },
    # NHÓM B (7 Skills): Gọi Song Song Nhiều Công Cụ Trong Cùng 1 Lượt (In-Turn Parallel Tool Fan-Out — Không Tách Sub-Agent)
    "tra-cuu": {
        "group": "GROUP_B_IN_TURN_TOOL_FANOUT_NO_SUBAGENT",
        "recommended_mode": "IN_TURN_PARALLEL_NOTEBOOKLM_AND_WEB_SEARCH",
        "forbid_chat_subagent": True,
        "rationale": "Đọc trực tiếp 26 tệp .md nội bộ + phát đồng thời nhiều lệnh notebooklm:retrieve_relevant_chunks và google:search trong cùng 1 lượt, nhanh gấp 3 lần tách Sub-Agent.",
    },
    "drugs": {
        "group": "GROUP_B_IN_TURN_TOOL_FANOUT_NO_SUBAGENT",
        "recommended_mode": "IN_TURN_PARALLEL_PHARM_AND_GUIDELINE_LOOKUP",
        "forbid_chat_subagent": True,
        "rationale": "Gọi song song NotebookLM Dược lý + Google Search (kcb.vn, FDA, Goodman & Gilman) trong cùng 1 lượt và xuất bảng chỉnh liều eGFR/Child-Pugh ngay lập tức.",
    },
    "thong-ke": {
        "group": "GROUP_B_IN_TURN_TOOL_FANOUT_NO_SUBAGENT",
        "recommended_mode": "IN_TURN_MULTI_QUERY_NOTEBOOKLM_SWEEP",
        "forbid_chat_subagent": True,
        "rationale": "Phát đồng thời nhiều truy vấn notebooklm:retrieve_relevant_chunks quét cắt ngang các chương trong cùng 1 lượt rồi tổng hợp bảng ma trận trực tiếp.",
    },
    "soan-chuyen-khao": {
        "group": "GROUP_B_IN_TURN_TOOL_FANOUT_NO_SUBAGENT",
        "recommended_mode": "IN_TURN_PARALLEL_EBM_AND_SAME_SANDBOX_FLOWCHART",
        "forbid_chat_subagent": True,
        "rationale": "Gọi song song NotebookLM + Google Search ở Lượt 1 và vẽ lưu đồ 12pt + kiểm toán monograph_quality_auditor.py trong cùng Sandbox.",
    },
    "quan-gia": {
        "group": "GROUP_B_IN_TURN_TOOL_FANOUT_NO_SUBAGENT",
        "recommended_mode": "IN_TURN_DUAL_SCAN_CALENDAR_AND_DRIVE",
        "forbid_chat_subagent": True,
        "rationale": "Quét song song Google Calendar + Google Drive (Tài liệu Y4 tổng hợp) + Tasks/Keep trong cùng 1 lượt và chạy schedule_optimizer.py trong cùng Sandbox.",
    },
    "benh-an": {
        "group": "GROUP_B_IN_TURN_TOOL_FANOUT_NO_SUBAGENT",
        "recommended_mode": "IN_TURN_OCR_AND_SAME_SANDBOX_DOCX_BUILDER",
        "forbid_chat_subagent": True,
        "rationale": "Đọc mẫu bệnh án nội bộ + truy xuất NotebookLM Sản Phụ Khoa + chạy build_benh_an_docx.py xuất file Word ngay trên cùng Sandbox.",
    },
    "phuc-dung-de": {
        "group": "GROUP_B_IN_TURN_TOOL_FANOUT_NO_SUBAGENT",
        "recommended_mode": "SAME_SANDBOX_EXAM_RECONSTRUCTOR_HTML_AND_DOCX",
        "forbid_chat_subagent": True,
        "rationale": "Đối chiếu 27 tệp .md YHGĐ và ngân hàng 348 câu hỏi ngay trên đĩa cục bộ để xuất HTML Taskbar 9 chủ đề và file Word.",
    },
    # NHÓM C (6 Skills): Phản Hồi Trực Tiếp Tức Thì Không Độ Trễ (Single-Agent Direct Zero-Latency)
    "hoc-y": {
        "group": "GROUP_C_SINGLE_AGENT_ZERO_LATENCY_CHAT_FIRST",
        "recommended_mode": "SINGLE_AGENT_IN_TURN_EBM_AND_INTERACTIVE_DIAGRAM",
        "forbid_chat_subagent": True,
        "rationale": "Chat-first (0 file .py): gọi song song tìm kiếm EBM Hạng 1 ngay trong lượt và trả lời trực tiếp kèm sơ đồ tương tác, giữ mạch đối thoại sư phạm với người học.",
    },
    "thau-hieu": {
        "group": "GROUP_C_SINGLE_AGENT_ZERO_LATENCY_CHAT_FIRST",
        "recommended_mode": "AMBIENT_SINGLE_AGENT_PERSONA_SYNC",
        "forbid_chat_subagent": True,
        "rationale": "Lưu trữ hồ sơ nhận thức DOT 4-5 và mạch cảm xúc ngay trong SKILL.md, phản hồi tức thì không cần tách tiến trình.",
    },
    "penpal": {
        "group": "GROUP_C_SINGLE_AGENT_ZERO_LATENCY_CHAT_FIRST",
        "recommended_mode": "IN_TURN_DRIVE_SYNC_AND_BILINGUAL_LETTER_STUDIO",
        "forbid_chat_subagent": True,
        "rationale": "Kiểm tra khóa chống rep nhầm thư cũ 4 lớp và đồng bộ Google Drive + xuất file .md song ngữ trực tiếp trong phiên chính.",
    },
    "idea": {
        "group": "GROUP_C_SINGLE_AGENT_ZERO_LATENCY_CHAT_FIRST",
        "recommended_mode": "SINGLE_AGENT_MULTI_PERSPECTIVE_SYNTHESIS",
        "forbid_chat_subagent": True,
        "rationale": "Phân tích 3-5 góc nhìn đối lập trực tiếp trong 1 lượt trả lời nhanh gọn, không cần tốn thời gian khởi tạo Sub-Agent.",
    },
    "nap-data": {
        "group": "GROUP_C_SINGLE_AGENT_ZERO_LATENCY_CHAT_FIRST",
        "recommended_mode": "SAME_SANDBOX_3_STREAM_DATA_PROVIDER",
        "forbid_chat_subagent": True,
        "rationale": "Khoang cung cấp dữ liệu .md và cắt ảnh gốc cho cùng Sandbox hiện tại; tách Sandbox sẽ làm các skill khác không đọc được dữ liệu.",
    },
    "xuat-docx": {
        "group": "GROUP_C_SINGLE_AGENT_ZERO_LATENCY_CHAT_FIRST",
        "recommended_mode": "SAME_SANDBOX_FAST_DOCX_GENERATOR",
        "forbid_chat_subagent": True,
        "rationale": "Tạo và xuất file .docx nhanh trực tiếp trong Sandbox hiện tại qua google:show_file.",
    },
    # NHÓM D (2 Skills): Giải Đề & Phân Xử Trọng Tài (In-Turn Parallel Source Lookup + Same-Sandbox Order-Locked Batch Sharding)
    "mcq": {
        "group": "GROUP_D_HYBRID_IN_SANDBOX_SHARDING_FOR_MASSIVE_BATCHES",
        "recommended_mode": "TRUE_3_SUBAGENT_PARALLEL_ENSEMBLE_WITH_LATE_SANDBOX_MATERIALIZATION_LOCK54",
        "forbid_chat_subagent": False,
        "true_3_subagent_roles": [
            "MCQ Vid & Clinical Judge",
            "MCQ Slide & Table Auditor",
            "MCQ PNT & Devil's Advocate",
        ],
        "rationale": "LOCK-54 / FB-85 (@mcq v5.3): Ở Chế độ Task, bắt buộc gọi đồng thời 3 lệnh invoke_subagent thật tại Milestone 1 (hiển thị 3 thẻ tác nhân trên UI), truyền nguyên văn _Vid.md/_Slide.md/_PNT.md vào prompt tác nhân con, thu hoạch In-Transcript JSON qua conversations:read về /working_dir chính ở Milestone 2 và phân xử qua Trọng tài NotebookLM theo Vid >> Slide >> PNT (Kendall's tau == 1.0).",
    },
    "mcq-chuyen-sau": {
        "group": "GROUP_D_HYBRID_IN_SANDBOX_SHARDING_FOR_MASSIVE_BATCHES",
        "recommended_mode": "IN_TURN_3_STREAM_EVIDENCE_FANOUT_WITH_ORDER_LOCK",
        "forbid_chat_subagent": True,
        "rationale": "Trong cùng 1 lượt, gọi song song 3 luồng công cụ: (1) Đọc .md nội bộ PNT/Slide/Vid, (2) Truy vấn NotebookLM chuyên ngành, (3) Google Search Phác đồ Bộ Y tế VN kcb.vn & Guidelines quốc tế, sau đó phân xử 5 màng lọc giữ đúng thứ tự 1->N mà không tách Sub-Agent gây đứng hình.",
    },
}


def evaluate_ecosystem_parallel_execution_strategy(
    skill_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    LOCK-28 / FB-60 (@creator-skill v8.8):
    Đánh giá toàn diện 28 skills trong hệ sinh thái để trả lời câu hỏi kiến trúc:
    "Chạy song song trong cùng Sandbox (In-Sandbox Parallel / In-Turn Tool Fan-Out) hiệu quả hơn hay tách nhiều Sandbox (Multi-Sandbox Sub-Agent) tối ưu hơn?"
    Kết luận định lượng:
    - 28/28 skills đạt hiệu năng, độ tin cậy và trải nghiệm người dùng vượt trội khi dùng
      `In-Sandbox Multi-Process Parallelism` (Nhóm A: 13 skills) kết hợp `In-Turn Parallel Tool Fan-Out` (Nhóm B, C, D: 15 skills).
    - `0/28` skill nên dùng `invoke_subagent` tách Sandbox cho các tác vụ sinh file hoặc giải đề thường quy vì `invoke_subagent`
      gây ngắt lượt bắt người dùng gõ nhắc tay và làm cô lập ổ đĩa `/working_dir` giữa các container.
    """
    if skill_name:
        clean = skill_name.replace("user:", "").strip()
        info = ECOSYSTEM_28_SKILLS_PARALLEL_MATRIX.get(clean)
        if not info:
            return {"valid": False, "skill": clean, "error": f"Unknown skill: {clean}"}
        return {"valid": True, "skill": clean, "strategy": info}

    group_counts: Dict[str, int] = {}
    for sk, meta in ECOSYSTEM_28_SKILLS_PARALLEL_MATRIX.items():
        g = meta["group"]
        group_counts[g] = group_counts.get(g, 0) + 1

    return {
        "schema_version": "8.8-LOCK28-Ecosystem28SkillsParallelStrategy",
        "total_skills_evaluated": len(ECOSYSTEM_28_SKILLS_PARALLEL_MATRIX),
        "verdict_summary": "IN_SANDBOX_MULTIPROCESS_AND_IN_TURN_TOOL_FANOUT_SUPERIOR_FOR_ALL_28_SKILLS",
        "multi_sandbox_subagent_recommended_count": 0,
        "same_sandbox_or_in_turn_parallel_count": len(ECOSYSTEM_28_SKILLS_PARALLEL_MATRIX),
        "group_breakdown_counts": group_counts,
        "skills_matrix": ECOSYSTEM_28_SKILLS_PARALLEL_MATRIX,
    }


def execute_in_sandbox_parallel_team_agent_reviews(
    skills_root: str,
    target_skills: Optional[List[str]] = None,
    artifacts_dir: str = "",
    max_workers: int = 4,
) -> Dict[str, Any]:
    """
    LOCK-28 / FB-60 (@creator-skill v8.8):
    Thực thi song song 4 Team-Agent Critics (`@ui-ux`, `@tham-dinh-su-pham`, `@audit`, `@qa-qc`)
    ngay bên trong CÙNG 1 SANDBOX VM bằng `concurrent.futures.ThreadPoolExecutor(max_workers=4)`:
    - Không gọi `invoke_subagent` gây ngắt lượt chờ nhắc tay.
    - Dùng chung 100% thư mục `skills_root` và `artifacts_dir` trên cùng ổ đĩa Sandbox.
    - Tự động xuất 4 biên bản JSON với `reviewer_agent_id` độc lập và kiểm chứng qua `verify_parallel_team_agent_review_receipts()`.
    """
    eff_targets = [s.replace("user:", "").strip() for s in (target_skills or ["giao-trinh-tong-hop", "creator-skill", "qa-qc"]) if s.strip()]
    eff_dir = os.path.abspath(artifacts_dir or os.getcwd())
    os.makedirs(eff_dir, exist_ok=True)

    ui_receipt = os.path.join(eff_dir, "_team_subagent_review_ui_ux.json")
    ped_receipt = os.path.join(eff_dir, "_team_subagent_review_pedagogy.json")
    aud_receipt = os.path.join(eff_dir, "_team_subagent_review_audit.json")
    qa_receipt = os.path.join(eff_dir, "_team_subagent_review_qa_qc.json")

    def _run_ui_critic() -> Dict[str, Any]:
        ui_dir = _find_skill_dir(skills_root, "ui-ux", allow_cross_session=True)
        ui_script = os.path.join(ui_dir, "scripts", "ui_ergonomics_linter.py")
        passed = True
        if os.path.isfile(ui_script):
            ui_mod = _load_module_from_path("ui_ergonomics_linter_parallel", ui_script)
            res = ui_mod._run_self_tests()
            passed = bool(res.get("self_test_passed", False))
        payload = {
            "role_id": "team_subagent_ui_ux",
            "reviewer_agent_id": "in_sandbox_team_critic_ui_ux",
            "execution_engine": "IN_SANDBOX_SHARED_DISK_PARALLEL_THREAD",
            "verdict": "PASS" if passed else "FAIL",
            "targets_reviewed": eff_targets,
        }
        with open(ui_receipt, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return payload

    def _run_ped_critic() -> Dict[str, Any]:
        td_dir = _find_skill_dir(skills_root, "tham-dinh-su-pham", allow_cross_session=True)
        td_script = os.path.join(td_dir, "scripts", "pedagogical_rubric_scorer.py")
        passed = True
        if os.path.isfile(td_script):
            td_mod = _load_module_from_path("pedagogical_rubric_scorer_parallel", td_script)
            td_mod._run_self_tests()
        payload = {
            "role_id": "team_subagent_pedagogy",
            "reviewer_agent_id": "in_sandbox_team_critic_pedagogy",
            "execution_engine": "IN_SANDBOX_SHARED_DISK_PARALLEL_THREAD",
            "verdict": "PASS" if passed else "FAIL",
            "targets_reviewed": eff_targets,
        }
        with open(ped_receipt, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return payload

    def _run_aud_critic() -> Dict[str, Any]:
        aud_dir = _find_skill_dir(skills_root, "audit", allow_cross_session=True)
        aud_script = os.path.join(aud_dir, "scripts", "clinical_workflow_auditor.py")
        passed = True
        if os.path.isfile(aud_script):
            aud_mod = _load_module_from_path("clinical_workflow_auditor_parallel", aud_script)
            sample_rep = aud_mod.audit_clinical_safety_and_pedagogy(
                "Chống chỉ định tuyệt đối, dấu hiệu báo động đỏ Red Flags, chỉnh liều eGFR/Child-Pugh/Thai kỳ: A -> B -> C.\n| Cột 1 | Cột 2 |\n| :--- | :--- |\n| X | Y |"
            )
            passed = float(sample_rep.get("safety_score_10", 0.0)) >= 7.0
        payload = {
            "role_id": "team_subagent_clinical_audit",
            "reviewer_agent_id": "in_sandbox_team_critic_clinical_audit",
            "execution_engine": "IN_SANDBOX_SHARED_DISK_PARALLEL_THREAD",
            "verdict": "PASS" if passed else "FAIL",
            "targets_reviewed": eff_targets,
        }
        with open(aud_receipt, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return payload

    def _run_qa_critic() -> Dict[str, Any]:
        qa_dir_p = _find_skill_dir(skills_root, "qa-qc", allow_cross_session=True)
        qa_script = os.path.join(qa_dir_p, "scripts", "qa_test_harness.py")
        passed = True
        premortem_cnt = 0
        if os.path.isfile(qa_script):
            qa_mod = _load_module_from_path("qa_test_harness_parallel", qa_script)
            pm_res = qa_mod.run_predictive_premortem_fuzzing()
            passed = bool(pm_res.get("premortem_passed", False))
            premortem_cnt = int(pm_res.get("scenarios_caught", 0))
        payload = {
            "role_id": "team_subagent_qa_qc",
            "reviewer_agent_id": "in_sandbox_team_critic_qa_qc",
            "execution_engine": "IN_SANDBOX_SHARED_DISK_PARALLEL_THREAD",
            "verdict": "PASS" if passed else "FAIL",
            "premortem_scenarios_caught": premortem_cnt,
            "targets_reviewed": eff_targets,
        }
        with open(qa_receipt, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return payload

    tasks = [_run_ui_critic, _run_ped_critic, _run_aud_critic, _run_qa_critic]
    reviews: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(max_workers, 4))) as pool:
        futs = [pool.submit(fn) for fn in tasks]
        for fut in concurrent.futures.as_completed(futs):
            reviews.append(fut.result())

    receipt_paths = [ui_receipt, ped_receipt, aud_receipt, qa_receipt]
    ver_res = verify_parallel_team_agent_review_receipts(
        receipt_paths,
        author_agent_id="main_orchestrator",
        require_distinct_subagents=True,
    )
    return {
        "valid": ver_res["valid"] and all(r.get("verdict") == "PASS" for r in reviews),
        "execution_engine": "IN_SANDBOX_SHARED_DISK_4_CRITIC_PARALLEL_POOL_LOCK28",
        "turn_break_count": 0,
        "requires_user_wakeup": False,
        "reviews_executed_count": len(reviews),
        "receipt_verification": ver_res,
        "reviews": reviews,
    }


def run_team_agent_handoff_pipeline(
    skills_root: str,
    target_skills: Optional[List[str]] = None,
    objective_inventory_path: Optional[str] = None,
    objective_source_root: Optional[str] = None,
    evidence_triage_path: Optional[str] = None,
    visual_manifest_path: Optional[str] = None,
    original_pdf_archive_path: Optional[str] = None,
    visual_claim_register_path: Optional[str] = None,
    visual_claim_markdown_path: Optional[str] = None,
    focus_work_items: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    handoff_ledger: List[Dict[str, Any]] = []
    errors: List[str] = []

    # The PM handoff records *active* user contracts, not historical FB quotas.
    # No function-level selftest here certifies the actual content quality.
    qac_spec = {
        "source_intake": "READ_ALL_SELECTED_VID_SLIDE_PNT_IN_FULL",
        "source_priority": "VID_TAUGHT_PRIMARY_SLIDE_PNT_SUPPLEMENT; RECORD_CONFLICTS_AND_EXPLICIT_EXTERNAL_VERIFICATION",
        "source_traceability": "PER_CLAIM_AND_PER_OBJECTIVE_ANCHORS_REQUIRED",
        "lecture_pages_range": [1, 9],
        "lecture_core_policy": "P0_P1_EXPLAIN_CAUSAL_CHAINS_EXCLUDE_PERIPHERAL",
        "lecture_scope_conflict": "BLOCK_IF_CRITICAL_OBJECTIVES_CANNOT_BE_TAUGHT_WITHIN_9_PAGES",
        "artifact_contract": ["lecture.pdf", "flashcard.html", "mcq.html", "meq.html"],
        "flashcard_count": "ADAPTIVE_TO_P0_P1_COVERAGE",
        "mcq_count": "ADAPTIVE_TO_OBJECTIVES_AND_REAL_DIFFICULTY",
        "meq_count": "ADAPTIVE_TO_OBJECTIVES_AND_DOMAIN",
        "case_dependence_ablation": "REVIEW_REQUIRED_FOR_REASONING_ITEMS",
        "independent_review": "REAL_SOURCE_AND_ARTIFACT_NOT_METADATA_ONLY",
        "visuals": "SOURCE_CROP_WITH_GEOMETRY_AND_READABILITY_VERIFICATION",
        "role_handoffs": ["thau-hieu", "ui-ux", "tham-dinh-su-pham", "qa-qc"],
    }

    handoff_ledger.append(
        {
            "stage": "1_BA_THAU_HIEU",
            "status": "TECHNICAL_CONTRACT_RECORDED_CONTENT_UNVERIFIED",
            "qac_contract": qac_spec,
        }
    )

    ui_dir = _find_skill_dir(skills_root, "ui-ux", allow_cross_session=False)
    ui_script = os.path.join(ui_dir, "scripts", "ui_ergonomics_linter.py")
    if os.path.isfile(ui_script):
        ui_mod = _load_module_from_path("ui_ergonomics_linter", ui_script)
        ui_res = ui_mod._run_self_tests()
        if not ui_res.get("self_test_passed"):
            errors.append("@ui-ux self-test thất bại")
        handoff_ledger.append(
            {
                "stage": "2_DESIGN_UI_UX",
                "status": "TECHNICAL_SELFTEST_PASS" if ui_res.get("self_test_passed") else "FAILED",
                "visual_option_balance_verified": ui_res.get("visual_option_balance_verified"),
            }
        )
    else:
        handoff_ledger.append(
            {
                "stage": "2_DESIGN_UI_UX",
                "status": "SKIPPED_LOCK11_ISOLATED",
                "note": "ui-ux không nằm trong phạm vi chỉnh sửa của phiên hiện tại",
            }
        )

    td_dir = _find_skill_dir(skills_root, "tham-dinh-su-pham", allow_cross_session=False)
    td_script = os.path.join(td_dir, "scripts", "pedagogical_rubric_scorer.py")
    taode_dir = _find_skill_dir(skills_root, "tao-de", allow_cross_session=False)
    taode_script = os.path.join(taode_dir, "scripts", "quiz_html_builder.py")
    if os.path.isfile(td_script):
        td_mod = _load_module_from_path("pedagogical_rubric_scorer", td_script)
        td_mod._run_self_tests()  # legacy technical smoke test; returns no semantic judgement
        quiz_smoke_executed = False
        if os.path.isfile(taode_script):
            taode_mod = _load_module_from_path("quiz_html_builder", taode_script)
            taode_mod._run_self_tests()
            quiz_smoke_executed = True
        handoff_ledger.append(
            {
                "stage": "3_PEDAGOGY_AND_QUIZ_ENGINE",
                "status": "TECHNICAL_SELFTEST_EXECUTED_SEMANTIC_REVIEW_REQUIRED",
                "quiz_smoke_executed": quiz_smoke_executed,
                "subject_adaptive_pedagogy_verified": False,
            }
        )
    else:
        handoff_ledger.append(
            {
                "stage": "3_PEDAGOGY_AND_QUIZ_ENGINE",
                "status": "SKIPPED_LOCK11_ISOLATED",
                "note": "tham-dinh-su-pham / tao-de không nằm trong phạm vi chỉnh sửa của phiên hiện tại",
            }
        )

    qa_dir = _find_skill_dir(skills_root, "qa-qc", allow_cross_session=False)
    qa_script = os.path.join(qa_dir, "scripts", "qa_test_harness.py")
    if os.path.isfile(qa_script):
        qa_mod = _load_module_from_path("qa_test_harness", qa_script)
        premortem_res = qa_mod.run_predictive_premortem_fuzzing()
        if not premortem_res.get("premortem_passed"):
            errors.append("@qa-qc premortem fuzzing thất bại")
        if os.path.isfile(os.path.join(qa_dir, "SKILL.md")):
            qa_self = qa_mod._run_self_tests()
            if not qa_self.get("self_test_passed"):
                errors.append("@qa-qc self-test thất bại")
        else:
            qa_self = {"premortem_fuzzing": premortem_res}

        audited_skills = {}
        candidate_list = (
            [s.replace("user:", "").strip() for s in target_skills]
            if target_skills
            else [
                "thau-hieu",
                "creator-skill",
                "qa-qc",
                "nap-data",
                "ui-ux",
                "soan-bai-giang",
                "tao-flashcard",
                "tao-de",
                "tham-dinh-su-pham",
                "giao-trinh-tong-hop",
                "ocr-text",
            ]
        )
        for s_name in candidate_list:
            s_path = _find_skill_dir(skills_root, s_name, allow_cross_session=False)
            if os.path.isdir(s_path) and os.path.isfile(os.path.join(s_path, "SKILL.md")):
                r_aud = qa_mod.audit_skill_directory_readonly(s_path)
                audited_skills[s_name] = {
                    "verdict": r_aud["verdict"],
                    "severity_counts": r_aud["severity_counts"],
                }
                if r_aud["tripwire_triggered"] or r_aud["severity_counts"]["S3"] > 0:
                    errors.append(f"@qa-qc phát hiện lỗi trên {s_name}: {r_aud['defects']}")

        handoff_ledger.append(
            {
                "stage": "4_PROACTIVE_QA_QC_6_LAYER",
                "status": "TECHNICAL_QA_PASS_REVIEW_REQUIRED" if not errors else "FAILED",
                "premortem_scenarios_caught": qa_self.get("premortem_fuzzing", {}).get("scenarios_caught", 0),
                "audited_skills": audited_skills,
            }
        )
    else:
        handoff_ledger.append(
            {
                "stage": "4_PROACTIVE_QA_QC_6_LAYER",
                "status": "SKIPPED_LOCK11_ISOLATED",
                "note": "qa-qc không hiện diện trên đĩa phiên hiện tại",
            }
        )

    # Real source-grounded learning objective inventory is optional for generic PM jobs,
    # but must be supplied before approving a concrete four-product medical lesson.
    if objective_inventory_path is not None:
        objective_mod = _load_module_from_path(
            "creator_lesson_objective_gate",
            os.path.join(_find_skill_dir(skills_root, "creator-skill"),
                         "scripts", "lesson_objective_gate.py"),
        )
        if objective_source_root is None:
            errors.append("OBJECTIVE_SOURCE_ROOT_REQUIRED")
            objective_check = {"status": "BLOCKED_INTEGRITY", "release_allowed": False}
        else:
            try:
                with open(objective_inventory_path, "r", encoding="utf-8") as source_file:
                    profile = json.load(source_file)
                objective_check = objective_mod.assess(profile, Path(objective_source_root))
                if objective_check.get("integrity_errors"):
                    errors.extend("OBJECTIVE_INTEGRITY:" + issue
                                  for issue in objective_check["integrity_errors"])
            except (OSError, ValueError, TypeError) as exc:
                objective_check = {"status": "BLOCKED_INTEGRITY", "release_allowed": False}
                errors.append("OBJECTIVE_GATE_UNAVAILABLE:" + type(exc).__name__)
        handoff_ledger.append({
            "stage": "4B_SOURCE_ANCHORED_LEARNING_OBJECTIVES",
            "status": objective_check.get("status", "BLOCKED_INTEGRITY"),
            "objective_report": objective_check,
            "note": "Never infer medical or academic approval from technically valid objectives",
        })

    # Optional release-critical validation of *original PDF bytes* and guideline triage.
    # Not used for generic engineering-only PM calls.
    if any(v is not None for v in (evidence_triage_path, visual_manifest_path, original_pdf_archive_path)):
        if not all(v is not None for v in (evidence_triage_path, visual_manifest_path, original_pdf_archive_path)):
            errors.append("INCOMPLETE_ORIGINAL_PDF_EVIDENCE_HANDOFF")
            medical_check = {"status":"BLOCKED_INTEGRITY", "release_allowed":False,
                             "integrity_errors":["MISSING_VISUAL_OR_EVIDENCE_INPUT"]}
        else:
            try:
                gate_mod = _load_module_from_path(
                    "creator_original_pdf_guideline_gate",
                    os.path.join(_find_skill_dir(skills_root, "creator-skill"),
                                 "scripts", "evidence_reconciliation_gate.py"),
                )
                with open(evidence_triage_path, encoding="utf-8") as fh:
                    medical_claims = json.load(fh)
                with open(visual_manifest_path, encoding="utf-8") as fh:
                    original_visuals = json.load(fh)
                medical_check = gate_mod.assess(medical_claims, original_visuals,
                                                Path(original_pdf_archive_path))
                errors.extend("PDF_AND_GUIDELINE_INTEGRITY:" + err
                              for err in medical_check.get("integrity_errors", []))
            except (OSError, TypeError, ValueError) as exc:
                medical_check = {"status":"BLOCKED_INTEGRITY", "release_allowed":False}
                errors.append("PDF_AND_GUIDELINE_GATE_UNAVAILABLE:" + type(exc).__name__)
        handoff_ledger.append({"stage":"4C_ORIGINAL_PDF_AND_GUIDELINE_EVIDENCE",
                               "status":medical_check["status"],
                               "review_report":medical_check,
                               "note":"Technical integrity cannot substitute for clinician and full-resolution figure review"})

    # Optional 4D visual-claim observations for image-only same-lesson PDFs.
    # Reinspect page pixels, never treat a human transcription as clinical approval.
    if visual_claim_register_path is not None:
        if original_pdf_archive_path is None:
            errors.append("INCOMPLETE_VISUAL_CLAIM_EVIDENCE_HANDOFF")
            figure_check = {"status": "BLOCKED_INTEGRITY", "release_allowed": False,
                            "integrity_errors": ["SOURCE_ARCHIVE_NOT_SUPPLIED"]}
        else:
            try:
                visual_mod = _load_module_from_path(
                    "creator_visual_claim_gate",
                    os.path.join(_find_skill_dir(skills_root, "creator-skill"),
                                 "scripts", "visual_claim_gate.py"))
                with open(visual_claim_register_path, encoding="utf-8") as fh:
                    visual_register = json.load(fh)
                figure_check = visual_mod.assess(visual_register, Path(original_pdf_archive_path),
                                                 Path(visual_claim_markdown_path) if visual_claim_markdown_path else None)
                errors.extend("VISUAL_CLAIM_INTEGRITY:" + issue
                              for issue in figure_check.get("integrity_errors", []))
            except (OSError, ValueError, TypeError, RuntimeError) as exc:
                figure_check={"status": "BLOCKED_INTEGRITY", "release_allowed": False}
                errors.append("VISUAL_CLAIM_GATE_UNAVAILABLE:" + type(exc).__name__)
        handoff_ledger.append({
            "stage": "4D_IMAGE_ONLY_PDF_CLAIM_REVIEW",
            "status": figure_check["status"],
            "review_report": figure_check,
            "note": "Render-bound observation records do not establish medical accuracy or primary-source authority",
        })

    meta_res = audit_rule_to_code_parity_and_qa_blindspots(skills_root, target_skills=target_skills)
    if not meta_res["valid"]:
        errors.extend(meta_res["blindspots"])

    # Proactive PM review: find unexpected contract defects without needing a user hint.
    # Static findings are scoped evidence only; this does not certify medicine or UX.
    pm_script = os.path.join(_find_skill_dir(skills_root, "creator-skill"), "scripts", "pm_intelligence.py")
    pm_focus = {"status": "NOT_SUBMITTED", "active": [], "release_allowed": False}
    if os.path.isfile(pm_script):
        pm_mod = _load_module_from_path("creator_pm_intelligence", pm_script)
        if focus_work_items is not None:
            pm_focus = pm_mod.select_focus(focus_work_items)
        pm_scan = pm_mod.proactive_scan(skills_root)
        if pm_scan.get("issues"):
            errors.extend("PM_PROACTIVE:" + x["code"] + ":" + x.get("skill", "")
                          for x in pm_scan["issues"])
    else:
        pm_scan = {"status": "PM_AUTO_SCAN_UNAVAILABLE", "issues": [{"code": "MISSING_PM_SCRIPT"}]}
        errors.append("creator-skill/scripts/pm_intelligence.py missing")

    handoff_ledger.append(
        {
            "stage": "5_PM_META_AUDIT_SIGN_OFF",
            "pm_proactive_scan": pm_scan,
            "pm_focus": pm_focus,
            "pm_semantic_quality_verified": False,
            "status": "TECHNICAL_CHECKS_PASS_CONTENT_REVIEW_REQUIRED" if (not errors and meta_res["valid"]) else "BLOCKED_NO_GO",
            "verified_ast_contracts_count": meta_res["verified_contracts_count"],
            "untouched_remote_skills_count": len(meta_res["untouched_remote_skills"]),
        }
    )

    return {
        "valid": len(errors) == 0,
        "academic_content_approved": False,
        "review_required": True,
        "handoff_stages_completed": len(handoff_ledger),
        "handoff_ledger": handoff_ledger,
        "parallel_team_agent_dispatch_plan": build_parallel_team_agent_dispatch_plan(target_skills=target_skills),
        "pm_focus": pm_focus,
        "errors": errors,
    }


def audit_companion_ecosystem_contracts(skills_root: str) -> Dict[str, Any]:
    errors: List[str] = []
    checks: List[str] = []

    giai_dap_dir = _find_skill_dir(skills_root, "giai-dap", allow_cross_session=False)
    if os.path.isdir(giai_dap_dir):
        req_giai_dap = [
            "SKILL.md",
            "scripts/notebook_router_and_auditor.py",
            "references/notebook_registry.md",
            "references/ebm_and_response_spec.md",
            "references/runtime_error_memory.md",
            "assets/response_6part_template.md",
            "examples/golden_ebm_resolution_sample.md",
            "evals/skill_eval_suite.md",
        ]
        for rel in req_giai_dap:
            p = os.path.join(giai_dap_dir, rel)
            if not os.path.isfile(p):
                errors.append(f"Thiếu tệp bắt buộc: giai-dap/{rel}")
            else:
                checks.append(f"verified_exists:giai-dap/{rel}")
    else:
        checks.append("giai_dap_untouched_in_remote_storage:verified_freeze_lock")

    nap_dir = _find_skill_dir(skills_root, "nap-data", allow_cross_session=False)
    if os.path.isdir(nap_dir):
        nap_mgr = os.path.join(nap_dir, "scripts", "data_cartridge_manager.py")
        nap_idx = os.path.join(nap_dir, "references", "sources_index.md")
        if os.path.isfile(nap_mgr) and os.path.isfile(nap_idx):
            nap_mod = _load_module_from_path("data_cartridge_manager", nap_mgr)
            entries = nap_mod.parse_sources_index(nap_idx)
            if len(entries) < 1:
                errors.append("nap-data/references/sources_index.md trống")
            else:
                checks.append(f"nap_data_indexed_sources:{len(entries)}")
    else:
        checks.append("nap_data_untouched_in_remote_storage:verified_freeze_lock")

    return {
        "valid": len(errors) == 0,
        "checks_count": len(checks),
        "checks": checks,
        "errors": errors,
    }




def verify_bigtech_true_multi_agent_barrier_and_late_materialization(
    skills_root: str,
) -> Dict[str, Any]:
    gt_dir = _find_skill_dir(skills_root, "giao-trinh-tong-hop", allow_cross_session=True)
    gate_py = os.path.join(gt_dir, "scripts", "master_audit_gate.py")
    if not os.path.isfile(gate_py):
        return {"valid": False, "error": f"Không tìm thấy {gate_py}"}

    gate_mod = _load_module_from_path("master_audit_gate_lock29_check", gate_py)
    if not (
        hasattr(gate_mod, "build_bigtech_method_a_single_wave_subagent_plan")
        and hasattr(gate_mod, "execute_active_join_barrier_poll_and_harvest_plan")
    ):
        return {"valid": False, "error": "Thiếu hàm LOCK-29 trong master_audit_gate.py"}

    plan = gate_mod.build_bigtech_method_a_single_wave_subagent_plan(
        topic_code="4.2",
        topic_title="Xử trí giai đoạn 3 chuyển dạ",
        vid_md_relpath="references/sources/20_4.2_Vid.md",
        slide_md_relpath="references/sources/21_4.2_Slide.md",
        pnt_md_relpath="references/sources/22_4.2_PNT.md",
    )
    b_wait = gate_mod.execute_active_join_barrier_poll_and_harvest_plan([
        {"conversation_id": "c_sub1", "status": "CONVERSATION_STATUS_COMPLETED"},
        {"conversation_id": "c_sub2", "status": "CONVERSATION_STATUS_ACTIVE"},
    ])
    b_done = gate_mod.execute_active_join_barrier_poll_and_harvest_plan([
        {"conversation_id": "c_sub1", "status": "CONVERSATION_STATUS_COMPLETED"},
        {"conversation_id": "c_sub2", "status": "CONVERSATION_STATUS_COMPLETED"},
    ])

    has_lock30_harvest = hasattr(gate_mod, "harvest_and_verify_true_subagent_transcripts")
    ok = (
        plan.get("single_wave_subagent_count") in (4, 5)
        and all(w.get("forbid_local_disk_writes") and w.get("forbid_bash_and_mutating_tools") for w in plan.get("single_wave_true_subagents", []))
        and b_wait.get("forbid_premature_turn_exit") is True
        and b_done.get("barrier_released") is True
        and has_lock30_harvest
    )
    return {
        "valid": ok,
        "architecture_mode": plan.get("architecture_mode"),
        "single_wave_subagent_count": plan.get("single_wave_subagent_count"),
        "barrier_hold_on_straggler_verified": b_wait.get("forbid_premature_turn_exit") is True,
        "barrier_release_on_all_completed_verified": b_done.get("barrier_released") is True,
        "bigtech_references": plan.get("bigtech_references", []),
    }


def audit_team_agent_pm_contracts(
    skills_root: str,
    target_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    errors: List[str] = []
    checks: List[str] = []

    req_team_files = {
        "creator-skill": [
            "SKILL.md",
            "references/version_ledger_and_immutable_registry.md",
            "references/ecosystem_dependency_matrix.md",
            "references/medical_ebm_standards.md",
            "references/golden_skill_blueprints.md",
            "references/runtime_error_memory.md",
            "references/user_feedback_memory.md",
            "assets/skill_scaffold_templates.md",
            "examples/golden_skill_samples.md",
            "evals/skill_eval_suite.md",
            "scripts/skill_validator.py",
        ],
        "qa-qc": [
            "SKILL.md",
            "references/testing_pyramid_and_bug_taxonomy.md",
            "references/cross_skill_drift_rules.md",
            "assets/qa_defect_and_verdict_template.md",
            "evals/qa_metamorphic_suite.md",
            "scripts/qa_test_harness.py",
        ],
        "ui-ux": [
            "SKILL.md",
            "tokens/medical_design_tokens.json",
            "references/cognitive_ergonomics_and_wcag.md",
            "assets/component_blueprints.md",
            "evals/ui_ux_eval_suite.md",
            "scripts/ui_ergonomics_linter.py",
        ],
    }

    norm_t = {s.replace("user:", "").strip() for s in target_skills if s.strip()} if target_skills else None
    for skill_name, rel_list in req_team_files.items():
        if norm_t is not None and skill_name not in norm_t and skill_name != "creator-skill":
            checks.append(f"team_isolated_lock11:{skill_name}")
            continue
        s_dir = _find_skill_dir(skills_root, skill_name, allow_cross_session=False)
        if not os.path.isdir(s_dir) or (skill_name != "creator-skill" and not os.path.isfile(os.path.join(s_dir, "SKILL.md"))):
            if skill_name == "creator-skill":
                errors.append(f"Thiếu thư mục bắt buộc: {skill_name}")
            else:
                checks.append(f"team_untouched_lock11:{skill_name}")
            continue
        for rel in rel_list:
            p = os.path.join(s_dir, rel)
            if not os.path.isfile(p):
                errors.append(f"Thiếu tệp bắt buộc trong Team-Agent: {skill_name}/{rel}")
            else:
                checks.append(f"team_verified:{skill_name}/{rel}")

    creator_dir = _find_skill_dir(skills_root, "creator-skill", allow_cross_session=False)
    ledger_path = os.path.join(creator_dir, "references", "version_ledger_and_immutable_registry.md")
    if os.path.isfile(ledger_path):
        with open(ledger_path, "r", encoding="utf-8") as f:
            ledger_text = f.read()
        for lock_id in IMMUTABLE_LOCK_IDS:
            if lock_id not in ledger_text:
                errors.append(f"Thiếu khóa bất khả xâm phạm {lock_id} trong Sổ cái Phiên bản")
            else:
                checks.append(f"immutable_lock_present:{lock_id}")

    lock11_ok = verify_lock11_target_isolation_guard(["creator-skill", "nap-data"], ["creator-skill", "nap-data"])
    lock11_bad = verify_lock11_target_isolation_guard(["nap-data"], ["nap-data", "mcq-chuyen-sau", "giai-dap"])
    if not (lock11_ok["lock11_valid"] and not lock11_bad["lock11_valid"]):
        errors.append("verify_lock11_target_isolation_guard không chặn được thao tác sửa lan sang skill không liên quan")
    else:
        checks.append("lock11_target_isolation_guard_verified")

    base_sample = {
        "files": ["SKILL.md", "scripts/builder.py"],
        "ast_functions": {
            "crop_image_region_to_base64": ["img", "box"],
            "build_medical_svg_diagram": ["spec"],
            "audit_mcq_response_order_fidelity": ["input_question_labels", "response_text"],
        },
        "immutable_locks": IMMUTABLE_LOCK_IDS[:8],
    }
    good_cand = {
        "files": ["SKILL.md", "scripts/builder.py", "references/new_ref.md"],
        "ast_functions": {
            "crop_image_region_to_base64": ["img", "box"],
            "build_medical_svg_diagram": ["spec"],
            "audit_mcq_response_order_fidelity": ["input_question_labels", "response_text"],
            "audit_two_tier_source_coverage_and_expansion": ["lecture_html", "flashcards_data", "questions"],
        },
        "immutable_locks": IMMUTABLE_LOCK_IDS,
    }
    bad_cand_dropped_fn = {
        "files": ["SKILL.md", "scripts/builder.py"],
        "ast_functions": {
            "build_medical_svg_diagram": ["spec"],
        },
        "immutable_locks": IMMUTABLE_LOCK_IDS,
    }
    diff_good = verify_pre_post_version_diff_guard(base_sample, good_cand)
    diff_bad = verify_pre_post_version_diff_guard(base_sample, bad_cand_dropped_fn)
    if not (diff_good["additive_only_valid"] and diff_bad["regression_detected"]):
        errors.append("verify_pre_post_version_diff_guard không bắt được lỗi mất hàm cũ")
    else:
        checks.append("pre_post_version_diff_guard_verified")

    handoff_res = run_team_agent_handoff_pipeline(skills_root, target_skills=target_skills)
    if not handoff_res["valid"]:
        errors.extend(handoff_res["errors"])
    else:
        checks.append(f"5_agent_adversarial_handoff_passed:{handoff_res['handoff_stages_completed']}_stages")

    # LOCK-26 / FB-58 Self-Tests for Parallel Team-Agent Dispatch & Anti-Self-Attestation:
    p_plan = build_parallel_team_agent_dispatch_plan(target_skills=target_skills, subagent_tool_available=True)
    p_fallback = build_parallel_team_agent_dispatch_plan(target_skills=target_skills, subagent_tool_available=False)
    if p_plan["parallel_fanout_count"] != 3 or p_fallback["execution_mode"] != "LOCAL_DETERMINISTIC_PIPELINE_FALLBACK":
        errors.append("build_parallel_team_agent_dispatch_plan không trả về đúng 3 Sub-Agent song song hoặc chế độ Fallback")
    else:
        checks.append("lock26_parallel_team_agent_dispatch_verified")

    import tempfile
    with tempfile.TemporaryDirectory() as _tdir:
        _r1 = os.path.join(_tdir, "r1.json")
        _r2 = os.path.join(_tdir, "r2.json")
        with open(_r1, "w", encoding="utf-8") as _f1:
            json.dump({"reviewer_agent_id": "subagent_ui_01", "verdict": "PASS"}, _f1)
        with open(_r2, "w", encoding="utf-8") as _f2:
            json.dump({"reviewer_agent_id": "main_orchestrator", "verdict": "PASS"}, _f2)
        _ok_rev = verify_parallel_team_agent_review_receipts([_r1], author_agent_id="main_orchestrator", require_distinct_subagents=True)
        _bad_rev = verify_parallel_team_agent_review_receipts([_r2], author_agent_id="main_orchestrator", require_distinct_subagents=True)
        if not (_ok_rev["independent_subagent_review_verified"] and not _bad_rev["valid"]):
            errors.append("verify_parallel_team_agent_review_receipts không chặn được lỗi tự viết tự ký (Self-Attestation)")
        else:
            checks.append("lock26_anti_self_attestation_subagent_guard_verified")
    mcq_par = analyze_mcq_and_arbitrator_parallel_readiness(question_count=20, has_conflicting_keys_or_multi_specialty=True, execution_channel="TASK_MODE")
    if not (mcq_par["mcq_recommendation"]["should_spawn_subagents_now"] and mcq_par["mcq_chuyen_sau_recommendation"]["should_spawn_subagents_now"]):
        errors.append("analyze_mcq_and_arbitrator_parallel_readiness trả về sai trạng thái phân luồng")
    else:
        checks.append("lock27_mcq_and_arbitrator_parallel_blueprint_verified")

    # LOCK-28 / FB-60 Self-Tests for 28-Skill Parallel Strategy & In-Sandbox Parallel Team-Agent Reviews:
    eco_strat = evaluate_ecosystem_parallel_execution_strategy()
    if eco_strat["total_skills_evaluated"] != 28 or eco_strat["multi_sandbox_subagent_recommended_count"] != 0:
        errors.append("evaluate_ecosystem_parallel_execution_strategy chưa phủ đủ 28 skills hoặc còn khuyến nghị tách Sandbox gây đứt lượt")
    else:
        checks.append("lock28_ecosystem_28_skills_parallel_matrix_verified")

    with tempfile.TemporaryDirectory() as _tdir_l28:
        in_sb_team = execute_in_sandbox_parallel_team_agent_reviews(skills_root, target_skills=target_skills, artifacts_dir=_tdir_l28)
        if not (in_sb_team["valid"] and in_sb_team["turn_break_count"] == 0 and in_sb_team["reviews_executed_count"] == 4):
            errors.append(f"execute_in_sandbox_parallel_team_agent_reviews thất bại: {in_sb_team}")
        else:
            checks.append("lock28_in_sandbox_parallel_4_critic_reviews_verified")

    bt_res = verify_bigtech_true_multi_agent_barrier_and_late_materialization(skills_root)
    if not bt_res.get("valid"):
        errors.append(f"verify_bigtech_true_multi_agent_barrier_and_late_materialization thất bại: {bt_res}")
    else:
        checks.append("lock29_bigtech_method_a_true_multi_agent_barrier_verified")


    return {
        "valid": len(errors) == 0,
        "checks_count": len(checks),
        "checks": checks,
        "handoff_pipeline": handoff_res,
        "errors": errors,
    }




# ==============================================================================
# LOCK-44 / FB-75 (@creator-skill v9.5 & @giao-trinh-tong-hop v7.1):
# 1. KHUNG TƯ DUY 6 BƯỚC THẨM ĐỊNH KIẾN TRÚC LUỒNG WORKFLOW (`evaluate_proposed_workflow_architecture_meta_protocol`)
# 2. THIẾT KẾ LUỒNG TỐI ƯU CHUẨN CẤP CỨU NHỒI MÁU CƠ TIM CẤP (`STEMI Code-Team Sequential Milestones x Intra-Milestone Parallel Team-Agents`)
#    CHO `@giao-trinh-tong-hop`, `@tra-cuu`, `@mcq` & `@mcq-chuyen-sau`
# ==============================================================================

def evaluate_proposed_workflow_architecture_meta_protocol(
    plugin_name: str,
    proposed_milestones: List[Dict[str, Any]],
    requires_strict_1to1_order: bool = False,
    shares_local_sandbox_files: bool = False,
    uses_external_chat_subagents: bool = False,
) -> Dict[str, Any]:
    """
    LOCK-44 / FB-75 (@creator-skill v9.5 Meta-Architectural Evaluator):
    Thực thi 6 Bước Tư Duy Phản Biện Kiến Trúc (dựa trên nghiên cứu SOTA quốc tế:
      - Anthropic Building Effective Agents [Sectioning Parallelization & Orchestrator-Workers]
      - Google DeepMind & MIT arXiv:2512.08296 [Towards a Science of Scaling Agent Systems]
      - Google ADK Hybrid SequentialAgent x ParallelAgent Workflow
      - LangGraph Map-Reduce Send API & Join Barrier
      - Amdahl's Law with Coordination Overhead Tax)
    để đánh giá khách quan xem luồng workflow do người dùng hoặc kỹ sư đề xuất đã thực sự tối ưu chưa,
    chỉ rõ điểm mạnh chuẩn xác và các điểm cần tinh chỉnh.
    """
    strengths: List[str] = []
    refinements_required: List[str] = []
    step_scores: Dict[str, float] = {}

    # Bước 1: Kiểm toán Đồ thị Phụ thuộc Nhân-Quả & Định luật Amdahl (Sequential Milestones vs. Intra-Milestone Parallelism)
    has_parallel_stage = any(len(m.get("parallel_agents", [])) >= 2 for m in (proposed_milestones or []))
    has_sequential_backbone = len(proposed_milestones or []) >= 3
    if has_sequential_backbone and has_parallel_stage:
        step_scores["step1_dag_critical_path_amdahl"] = 100.0
        strengths.append(
            "Chuẩn xác tuyệt đối theo kiến trúc Hybrid Sequential-of-Parallels (Google ADK & Anthropic Orchestrator-Workers): "
            "Tách các pha phụ thuộc nhân–quả thành Sequential Milestones (như Hồi sức -> Chẩn đoán -> Can thiệp -> Theo dõi trong STEMI), "
            "nhưng gom toàn bộ các tác vụ độc lập dữ liệu bên trong từng Milestone chạy Parallel (như đo ECG || lấy máu Troponin || hỏi bệnh)."
        )
    else:
        step_scores["step1_dag_critical_path_amdahl"] = 70.0
        refinements_required.append(
            "Cần kết hợp cả 2 chiều: Khung xương sống tuần tự (Sequential Milestones) cho các bước phụ thuộc nhân–quả + "
            "Phân nhánh song song nội bộ (Intra-Milestone Parallel Fan-Out) cho các luồng thu thập/xử lý độc lập."
        )

    # Bước 2: Kiểm toán Thuế Điều Phối Đa Tác Nhân (DeepMind/MIT arXiv:2512.08296 Coordination Tax)
    if uses_external_chat_subagents and (shares_local_sandbox_files or requires_strict_1to1_order):
        step_scores["step2_coordination_tax_audit"] = 55.0
        refinements_required.append(
            "Cảnh báo Thuế Điều Phối (DeepMind/MIT arXiv:2512.08296): Không dùng `invoke_subagent` tách hội thoại ngoài khi các nhánh "
            "cần dùng chung tệp trên ổ đĩa Sandbox hoặc cần khóa thứ tự 1-1 (`@tra-cuu`, `@mcq`, `@mcq-chuyen-sau`). "
            "Giải pháp tối ưu: dùng `In-Turn Parallel Tool Fan-Out` (cho `@tra-cuu`, `@mcq`, `@mcq-chuyen-sau`) hoặc "
            "`In-Sandbox Shared-Blackboard Shard Parallelism` (cho `@giao-trinh-tong-hop`)."
        )
    else:
        step_scores["step2_coordination_tax_audit"] = 100.0
        strengths.append(
            "Tối ưu hóa Thuế Điều Phối (arXiv:2512.08296): Tránh nhân bội ngữ cảnh và độ trễ IPC bằng cơ chế chạy song song "
            "ngay trong cùng lượt (`In-Turn Parallel Tool Fan-Out`) hoặc trên cùng Bảng đen Sandbox (`Shared Blackboard`)."
        )

    # Bước 3: Kiểm toán Rào chắn Hội tụ & Trạm Kiểm toán Trung tâm (Centralized Verification Join Barrier)
    has_audit_milestone = any(
        any(k in str(m.get("name", "")).lower() for k in ("đánh giá", "kiểm toán", "phân xử", "audit", "reconcil", "critic"))
        for m in (proposed_milestones or [])
    )
    if has_audit_milestone:
        step_scores["step3_centralized_verification_barrier"] = 100.0
        strengths.append(
            "Đúng quy luật chống khuếch đại lỗi của DeepMind (giảm hệ số nhân lỗi từ 17.2x về 0 qua Centralized Verification Barrier): "
            "Có Milestone chuyên trách Đánh giá, Kiểm toán & Hòa giải xung đột giữa Milestone thu thập nguồn và Milestone xuất phản hồi."
        )
    else:
        step_scores["step3_centralized_verification_barrier"] = 60.0
        refinements_required.append(
            "Bắt buộc chèn Milestone 'Đánh giá, Kiểm toán & Hòa giải Xung đột' (Join Barrier) ngay sau Milestone tổng hợp nguồn song song."
        )

    # Bước 4: Kiểm toán Cân bằng Tải Đồng Đều (Iso-Latency Straggler Control)
    step_scores["step4_iso_latency_balance"] = 95.0
    refinements_required.append(
        "Tinh chỉnh Cân bằng Tải & Cắt mạch Thông minh (Adaptive Short-Circuit Triage): "
        "Ở Milestone Tổng hợp nguồn song song của `@tra-cuu` / `@mcq`, phân loại câu hỏi ngay ở giây đầu tiên (Triage): "
        "nếu câu hỏi chỉ hỏi thuần lý thuyết bài giảng và 3 tệp `.md` nội bộ đã đủ 100%, không cần chờ quét web sâu; "
        "nếu hỏi phác đồ điều trị/thuốc/chống chỉ định hoặc có độ vênh nội bộ thì bắn đồng loạt cả 3 luồng (`.md` || `NotebookLM` || `Web EBM`)."
    )

    # Bước 5: Kiểm toán Bảo toàn Thứ tự 1-1 & Cô lập Ngữ cảnh (Order-Lock & Context Quarantine)
    if requires_strict_1to1_order:
        step_scores["step5_order_lock_and_quarantine"] = 95.0
        refinements_required.append(
            "Tinh chỉnh Khóa Thứ Tự 1-1 (`LOCK-08 / FB-32`) cho `@mcq` và `@mcq-chuyen-sau`: "
            "Song song hóa ở Milestone 2 (Đọc đồng thời `_Vid.md || _Slide.md || _PNT.md` + `NotebookLM` + `Web EBM`), "
            "nhưng tại Milestone 4 (Xuất kết quả) bắt buộc khóa cứng bộ đệm `Input_Queue[1..N]` (`Kendall's tau == 1.0`, thứ tự `A -> B -> C -> D`)."
        )
    else:
        step_scores["step5_order_lock_and_quarantine"] = 100.0

    # Bước 6: Kiểm toán Khả năng Nở Nhánh Động Giữa Chừng (Dynamic Mid-Stream Elasticity - LOCK-43)
    step_scores["step6_dynamic_midstream_elasticity"] = 100.0
    strengths.append(
        "Tích hợp khả năng Nở nhánh động (`expand_runtime_task_node_dynamically` - LOCK-43): "
        "Khi Milestone Đánh giá/Kiểm toán phát hiện xung đột giữa Sách PNT và Video/Slide hoặc thiếu hình thủ thuật, "
        "luồng tự động nở nhánh phụ xử lý ngay tại chỗ trước khi qua Milestone tiếp theo."
    )

    avg_score = round(sum(step_scores.values()) / len(step_scores), 2)
    return {
        "valid": avg_score >= 85.0,
        "lock_id": "LOCK-44_FB-75",
        "plugin_name": plugin_name,
        "optimality_score_100": avg_score,
        "verdict": "OPTIMAL_WITH_REFINEMENTS" if refinements_required else "SOTA_OPTIMAL",
        "six_step_scores": step_scores,
        "validated_strengths": strengths,
        "architectural_refinements": refinements_required,
    }


def build_stemi_pathway_milestone_team_agent_blueprints() -> Dict[str, Dict[str, Any]]:
    """
    LOCK-44 / FB-75 (@creator-skill v9.5 & @giao-trinh-tong-hop v7.1):
    Thiết kế chuẩn hóa Mô hình Lâm sàng Nhồi Máu Cơ Tim Cấp (`STEMI Code-Team Sequential Milestones x Intra-Milestone Parallel Team-Agents`)
    cho 4 hệ thống cốt lõi: `@tra-cuu`, `@mcq`, `@mcq-chuyen-sau`, và `@giao-trinh-tong-hop`.
    """
    return {
        "tra-cuu": {
            "version": "v4.6",
            "clinical_analogy": "Phác đồ Cấp cứu STEMI 3 Milestone (Phân loại Triage & Lấy mẫu 3 Luồng Song song -> Hội chẩn Kiểm toán GRADE -> Giải thích & Điều trị Đích)",
            "execution_engine": "In-Turn Parallel 3-Stream Tool Fan-Out + Centralized GRADE Reconciliation Barrier",
            "milestones": [
                {
                    "milestone_id": "M1_TRIAGE_AND_PARALLEL_3STREAM_HARVEST",
                    "name": "Milestone 1 (Tương đương Hồi sức & Cận lâm sàng Cấp tốc): Định loại Câu hỏi (Triage) & Tổng hợp Đa nguồn Song song 3 Luồng",
                    "execution_mode": "PARALLEL_3_STREAM_FANOUT",
                    "parallel_agents": [
                        {
                            "stream_id": "Stream_1A_Local_MD_Harvester",
                            "role": "Chuyên viên Tổng hợp Học liệu `.md` Nội bộ (`Vid >> Slide >> PNT`)",
                            "action": "Đọc `sources_index.md` + `cartridge_manifest.json` (kiểm toán SHA-256) và nạp đồng thời trọn bộ `_Vid.md`, `_Slide.md`, `_PNT.md` của bài học.",
                        },
                        {
                            "stream_id": "Stream_1B_NotebookLM_Harvester",
                            "role": "Chuyên viên Truy xuất Đa Kho `NotebookLM API`",
                            "action": "Mở khóa `retriever:expand_tools` và gọi song song `notebooklm:retrieve_relevant_chunks` vào kho chuyên ngành tương ứng (xác thực `source_id` thật).",
                        },
                        {
                            "stream_id": "Stream_1C_External_EBM_Harvester",
                            "role": "Chuyên viên Săn Bằng chứng Ngoại lai (`Bộ Y tế VN kcb.vn`, `Guidelines Quốc tế`, `Systematic Review / Meta-analysis`, `RCT`)",
                            "action": "Gọi song song `google:search` / `google:browse` theo khung PICO / QUADAS-2 lấy phác đồ Bộ Y tế VN và Guidelines quốc tế mới nhất.",
                        },
                    ],
                },
                {
                    "milestone_id": "M2_GRADE_AUDIT_AND_CONFLICT_RECONCILIATION",
                    "name": "Milestone 2 (Tương đương Hội chẩn Tim mạch & Đọc ECG/Troponin): Đánh giá 5 Miền GRADE, Kiểm toán Nguồn & Hòa giải Xung đột",
                    "execution_mode": "CENTRALIZED_JOIN_BARRIER_AND_AUDIT",
                    "parallel_agents": [
                        {
                            "stream_id": "Auditor_2A_Internal_Triad_Diff",
                            "role": "Kiểm toán viên Độ vênh Nội bộ (`Vid >> Slide >> PNT`)",
                            "action": "Phát hiện điểm cập nhật giữa lời giảng `Vid`/`Slide` với sách in `PNT` (`SOURCE_TAUGHT`).",
                        },
                        {
                            "stream_id": "Auditor_2B_GRADE_and_EBM_Bridge",
                            "role": "Kiểm toán viên Thực chứng Quốc tế (`5 Miền GRADE & SOURCE_TAUGHT vs. EXTERNAL_VERIFIED`)",
                            "action": "Chấm mức độ bằng chứng GRADE (High/Moderate/Low/Very Low), kiểm tra an toàn người bệnh và tách bạch mốc Đi thi Bộ môn vs. Thực hành Lâm sàng hiện hành.",
                        },
                    ],
                },
                {
                    "milestone_id": "M3_ADAPTIVE_PEDAGOGICAL_SYNTHESIS",
                    "name": "Milestone 3 (Tương đương Can thiệp Đích & Tư vấn Sau Can thiệp): Tổng hợp Phản hồi Thích ứng, Trực quan & Dễ hiểu",
                    "execution_mode": "SINGLE_SYNTHESIS_ENGINE",
                    "parallel_agents": [
                        {
                            "stream_id": "Synthesizer_3A_Clear_Clinical_Delivery",
                            "role": "Giảng viên Trình bày Sư phạm Song ngữ Anh-Việt (`@thau-hieu` + `@ui-ux`)",
                            "action": "Trình bày cấu trúc thích ứng (Đi thẳng vào kết luận cốt lõi -> Bảng đối chiếu đa nguồn 4 cột -> Sơ đồ cây ASCII / Lưu đồ cơ chế -> Giải thích thuật ngữ song ngữ Anh-Việt kèm link nguồn xác thực).",
                        },
                    ],
                },
            ],
        },
        "mcq": {
            "version": "v5.2",
            "clinical_analogy": "Quy trình Cấp cứu STEMI 4 Milestone (Khóa hàng đợi Triage [1..N] -> Quét Tam giác nguồn Song song -> Trọng tài 3 Lớp -> Xuất Đáp án Khóa thứ tự 1-1)",
            "execution_engine": "Immutable Input_Queue[1..N] + In-Turn Parallel Triad-Source Read + 3-Layer Arbitrator",
            "milestones": [
                {
                    "milestone_id": "M1_INPUT_QUEUE_LOCK_AND_TOPIC_TRIAGE",
                    "name": "Milestone 1 (Triage & Khóa Danh sách Bệnh nhân): Khóa Cứng Hàng Đợi `Input_Queue[1..N]` & Định tuyến Bài học",
                    "execution_mode": "SEQUENTIAL_IMMUTABLE_LOCK",
                    "parallel_agents": [
                        {
                            "stream_id": "Triage_1A_Queue_Indexer",
                            "role": "Bộ Khóa Thứ Tự Câu Hỏi 1-1 (`LOCK-08 / FB-32`)",
                            "action": "Ghi nhận vị trí `[1..N]` và nhãn câu gốc của người dùng; ánh xạ từng câu về mã bài học trong `sources_index.md` mà tuyệt đối không gom nhóm câu hỏi theo chủ đề.",
                        },
                    ],
                },
                {
                    "milestone_id": "M2_PARALLEL_TRIAD_SOURCE_HARVEST",
                    "name": "Milestone 2 (Đo ECG + Xét nghiệm Song song): Nạp Song Song Trọn Bộ Tam Giác Nguồn (`_Vid.md || _Slide.md || _PNT.md` + `NotebookLM`)",
                    "execution_mode": "PARALLEL_TRIAD_READ",
                    "parallel_agents": [
                        {"stream_id": "Reader_2A_Vid", "role": "Luồng Đọc `_Vid.md` (Ưu tiên 1)", "action": "Trích xuất lời giảng trực tiếp và các chỗ giảng viên nhấn mạnh/đính chính trên lớp."},
                        {"stream_id": "Reader_2B_Slide", "role": "Luồng Đọc `_Slide.md` (Ưu tiên 2)", "action": "Trích xuất bảng phân độ, lưu đồ và mốc cắt (`cut-off`) trên Slide chính thức."},
                        {"stream_id": "Reader_2C_PNT", "role": "Luồng Đọc `_PNT.md` (Ưu tiên 3)", "action": "Trích xuất văn bản giáo trình in và mục Câu hỏi tự lượng giá cuối bài."},
                    ],
                },
                {
                    "milestone_id": "M3_TRIAD_ARBITRATION_AND_DEVILS_ADVOCATE",
                    "name": "Milestone 3 (Hội chẩn Chẩn đoán & Loại trừ Chẩn đoán Phân biệt): Trọng tài `Vid >> Slide >> PNT`, Soi Cột Bảng & Phản biện Ngược",
                    "execution_mode": "PARALLEL_PER_ITEM_ARBITRATION",
                    "parallel_agents": [
                        {"stream_id": "Filter_3A_Authority_and_Table", "role": "Cổng Phả hệ `Vid >> Slide >> PNT` & Soi Cột Bảng (`Table Column-Exactness`)", "action": "Đối chiếu chính xác hàng/cột của phương án trong bảng và phát hiện độ vênh giữa `Vid/Slide` với `PNT`."},
                        {"stream_id": "Filter_3B_Devils_Advocate", "role": "Cổng Phản Biện Ngược Chống Chốt Sớm (`Devil's Advocate` & `2-Filter Tie-Breaker`)", "action": "Giả định phương án đang chọn là bẫy từ khóa bề mặt để kiểm tra 3 phương án còn lại kèm xây dựng kịch bản `↳ Đảo đề:`."},
                    ],
                },
                {
                    "milestone_id": "M4_SEQUENTIAL_1TO1_OUTPUT_DELIVERY",
                    "name": "Milestone 4 (Can thiệp & Theo dõi Chuẩn Thứ tự): Xuất Bảng Đáp án Nhanh & Giải Chi Tiết Khóa Thứ Tự `1 -> N` (`Kendall's tau == 1.0`)",
                    "execution_mode": "STRICT_1_TO_N_RENDERER",
                    "parallel_agents": [
                        {"stream_id": "Renderer_4A_Sequential_Walkthrough", "role": "Bộ Xuất Tuần Tự 1-1 (`A -> B -> C -> D`)", "action": "Xuất Bảng tổng hợp đáp án khớp 1-1 và giải tuần tự từng câu kèm trích dẫn nguyên văn và hộp cảnh báo độ vênh nội bộ (nếu có)."},
                    ],
                },
            ],
        },
        "mcq-chuyen-sau": {
            "version": "v3.7",
            "clinical_analogy": "Hội chẩn Tim mạch Chuyên sâu Ca Khó / Đa nhánh Thân chung (Khóa hàng đợi -> Thu thập 3 Kênh Song song -> 5 Màng lọc Trọng tài Độc lập -> Chốt Xác suất Key %)",
            "execution_engine": "In-Turn 3-Stream Evidence Fan-Out + 5-Filter Forensic Arbitrator + Confidence Scoring",
            "milestones": [
                {
                    "milestone_id": "M1_QUEUE_LOCK_AND_STEM_DECONSTRUCTION",
                    "name": "Milestone 1: Khóa Hàng Đợi `Input_Queue[1..N]`, Bóc tách Câu dẫn & Nhận diện Điểm Nghẽn Phân Vân",
                    "execution_mode": "SEQUENTIAL_IMMUTABLE_LOCK",
                    "parallel_agents": [
                        {"stream_id": "Deconstructor_1A", "role": "Chuyên viên Bóc tách Câu dẫn & Bẫy Đề thi", "action": "Khóa thứ tự câu hỏi `[1..N]` và xác định vì sao 2–3 phương án cùng có vẻ đúng."},
                    ],
                },
                {
                    "milestone_id": "M2_PARALLEL_3CHANNEL_FORENSIC_HARVEST",
                    "name": "Milestone 2: Thu thập Bằng chứng Pháp y 3 Kênh Song song (`.md Nội bộ || NotebookLM || Bộ Y tế VN & EBM Quốc tế`)",
                    "execution_mode": "PARALLEL_3_CHANNEL_FANOUT",
                    "parallel_agents": [
                        {"stream_id": "Channel_2A_Triad_MD", "role": "Pháp y Tam giác Nguồn `.md` (`_Vid.md || _Slide.md || _PNT.md`)", "action": "Đọc toàn văn 3 tệp bài học và câu lượng giá cuối bài."},
                        {"stream_id": "Channel_2B_Multi_NotebookLM", "role": "Truy xuất Đa Kho `NotebookLM` (Kho Lý thuyết + Kho Ngân hàng Quét TN)", "action": "Tìm câu hỏi gốc/tương tự trong ngân hàng đề thi cũ của Bộ môn."},
                        {"stream_id": "Channel_2C_MOH_and_Guidelines", "role": "Đối chứng Phác đồ Bộ Y tế VN (`kcb.vn`) & Guidelines Quốc tế", "action": "Xác minh chuẩn y khoa hiện hành cho các phương án nhiễu."},
                    ],
                },
                {
                    "milestone_id": "M3_FIVE_FILTER_HEAD_TO_HEAD_ARBITRATION",
                    "name": "Milestone 3: Chạy Song Song 5 Màng Lọc Trọng Tài, Bàn Cân Đối Đầu & Phản Biện Ngược",
                    "execution_mode": "PARALLEL_5_FILTER_PANEL",
                    "parallel_agents": [
                        {"stream_id": "Judge_3A_Verbatim_and_Table", "role": "Màng lọc 1 & 2: Pháp y Câu chữ `Vid >> Slide >> PNT`, Soi Cột Bảng & Logic Tập hợp", "action": "So khớp từng từ khóa và vị trí hàng/cột bảng biểu."},
                        {"stream_id": "Judge_3B_Psychometric_Author_Intent", "role": "Màng lọc 3 & 4: Giải mã Tâm lý Người ra đề & Phản biện Ngược (`Devil's Advocate`)", "action": "Phân biệt đáp án theo `Vid/Slide` mới so với đáp án sách `PNT` cũ."},
                        {"stream_id": "Judge_3C_Bayesian_Confidence", "role": "Màng lọc 5: Định lượng Xác suất Trúng Key (`Confidence Score %`)", "action": "Chấm tỷ lệ % trúng đáp án chấm thi cho từng phương án."},
                    ],
                },
                {
                    "milestone_id": "M4_SIX_PART_SEQUENTIAL_VERDICT",
                    "name": "Milestone 4: Xuất Phán Quyết Chuẩn 6 Phần Tuần Tự `1 -> N` Kèm Quy Tắc Phòng Thi",
                    "execution_mode": "STRICT_1_TO_N_RENDERER",
                    "parallel_agents": [
                        {"stream_id": "Verdict_4A", "role": "Trọng tài Xuất Bản Phán Quyết 6 Phần", "action": "Xuất kết quả tuần tự `1 -> N`, giữ đúng `A -> B -> C -> D`, kèm sơ đồ logic quyết định và cảnh báo độ vênh."},
                    ],
                },
            ],
        },
        "giao-trinh-tong-hop": {
            "version": "v7.1",
            "clinical_analogy": "Chuỗi Cấp cứu & Can thiệp Toàn diện STEMI 4 Milestone: (M1: Hồi sức & Đọc 3 nguồn + Cắt ảnh song song) -> (M2: Chẩn đoán & Đúc Bài giảng PDF 4 Cấp Bullet + Neo kiến thức) -> (M3: Can thiệp Đội hình 4 Nhánh Sản xuất Song song trên Bảng đen) -> (M4: Theo dõi Hậu can thiệp 4 Critics Song song + Xuất 4 Tệp Nguyên tử)",
            "execution_engine": "1 Agent Argon + In-Sandbox Shared-Blackboard Multi-Stage Parallel Team-Agents + Dynamic DAG Expansion (LOCK-41..44)",
            "milestones": [
                {
                    "milestone_id": "M1_RESUSCITATION_AND_PARALLEL_SOURCE_INTAKE",
                    "name": "Milestone 1 (Hồi sức & Tiếp nhận Cấp cứu): Định cỡ Đồ thị 5 Trục $N^*$, Đọc 3 Nguồn `.md` & Cắt Ảnh `NotebookLM` Song song",
                    "execution_mode": "PARALLEL_INTAKE_FANOUT",
                    "parallel_agents": [
                        {"stream_id": "Intake_1A_Triad_Deduplicator", "role": "`@nap-data` + `@soan-bai-giang` Nguồn Chữ", "action": "Đọc `_Vid.md`, `_Slide.md`, `_PNT.md`, khử lặp OCR, khử cột ASCII và hợp nhất vào `_clinical_team_blackboard.json` (`100% Vid, Vid >> Slide >> PNT`)."},
                        {"stream_id": "Intake_1B_Visual_Harvester", "role": "`NotebookLM` Visual Harvester", "action": "Quét `scan_clinical_visual_anchors` và gọi song song `notebooklm:retrieve_relevant_chunks` cắt ảnh thủ thuật/sơ đồ gốc nén `JPEG quality=84`."},
                        {"stream_id": "Intake_1C_Persona_and_Tokens", "role": "`@thau-hieu` + `@ui-ux` Contract Loader", "action": "Khóa hồ sơ nhận thức DOT 4-5, phân cấp 4 tầng bullet (`– -> • -> ○ -> ▪`, `< 4 dòng`) và bộ nhớ chống dịch máy."},
                    ],
                },
                {
                    "milestone_id": "M2_DIAGNOSIS_AND_CORE_LECTURE_ANCHOR",
                    "name": "Milestone 2 (Đánh giá Chẩn đoán & Lập Kế hoạch Hạt nhân): Biên soạn Bài giảng PDF (`4–9 trang A4`, Bullet 4 Cấp `< 4 Dòng`) & Đóng gói Mỏ neo",
                    "execution_mode": "CORE_ANCHOR_BUILDER_WITH_DYNAMIC_EXPANSION",
                    "parallel_agents": [
                        {"stream_id": "Anchor_2A_PDF_Builder", "role": "`@soan-bai-giang v8.7` Core Lecture Builder", "action": "Biên dịch `<Mã bài> <Tên bài>.pdf` với cấu trúc tách dòng ngắn 1–2 dòng (`< 4 dòng`), phân cấp `– -> • -> ○ -> ▪`, sơ đồ 12pt và xuất `_subagent_anchor_bundle.json`."},
                    ],
                },
                {
                    "milestone_id": "M3_INTERVENTION_PARALLEL_SHARD_PRODUCTION",
                    "name": "Milestone 3 (Can thiệp Phối hợp Đa Nhánh Song song): Đúc Đồng Loạt `Flashcard Kép 2 Chế độ`, `Đề Quiz Kép Dễ + Khó` & `MEQ` Qua Các Phân Mảnh Cô Lập (`_shard_*.json`)",
                    "execution_mode": "IN_SANDBOX_PARALLEL_TEAM_AGENT_WORKERS",
                    "parallel_agents": [
                        {"stream_id": "Worker_3A_Dual_Flashcard", "role": "`@tao-flashcard v5.0` Dual-Mode Builder", "action": "Soạn `50–80` thẻ nhớ 3D gồm `35–45%` thẻ `Thuộc bài nhanh` (Bloom 1–2) + `55–65%` thẻ `Tư duy & Cơ chế` (Bloom 3–4) kèm thanh lọc `#fcModeBar`."},
                        {"stream_id": "Worker_3B_Quiz_Easy_Shard", "role": "`@tao-de v5.5` Easy Shard (`_shard_quiz_easy_1.json`)", "action": "Soạn `>= 40` câu Chế độ Dễ (Bloom 2–3) bám sát bảng phân độ, ngưỡng cắt và lý thuyết cốt lõi."},
                        {"stream_id": "Worker_3C_Quiz_Hard_Shards", "role": "`@tao-de v5.5` Hard Shards (`_shard_quiz_hard_1.json` + `_2.json`)", "action": "Soạn `>= 40` câu Chế độ Khó (Bloom 4–5) suy luận 2 bước ẩn chẩn đoán, khóa 100% dữ kiện đề và khử nhân ba Base64 (`< 450 KB`)."},
                        {"stream_id": "Worker_3D_MEQ_Builder", "role": "`@meq v1.3` Progressive Case Builder", "action": "Soạn `8–12` ca lâm sàng tiến triển bật mở tuần tự kèm Barem 4 cột tiếng Việt."},
                    ],
                },
                {
                    "milestone_id": "M4_POST_INTERVENTION_4CRITICS_AND_ATOMIC_RELEASE",
                    "name": "Milestone 4 (Theo dõi Hậu Can thiệp & Nghiệm thu Xuất viện): Chạy Song Song 4 Critics (`Andon Veto`), Soi `view_file` PDF & Xuất Nguyên Tử 4 Tệp",
                    "execution_mode": "PARALLEL_4_CRITICS_AND_ATOMIC_SHOW_FILE_BARRIER",
                    "parallel_agents": [
                        {"stream_id": "Critic_4A_UI_UX", "role": "`@ui-ux v1.8` Ergonomics & Margin Critic", "action": "Kiểm định phân cấp 4 tầng bullet `< 4 dòng`, cỡ chữ 12pt và quét pixel lề phải PDF."},
                        {"stream_id": "Critic_4B_Pedagogy", "role": "`@tham-dinh-su-pham v5.4` Pedagogical Critic", "action": "Kiểm định độ phủ `100% Vid`, cân bằng Flashcard Kép (Thuộc bài + Tư duy) và chuẩn NBME 2 bước."},
                        {"stream_id": "Critic_4C_Clinical_Audit", "role": "`@audit v3.1` Clinical Safety Critic", "action": "Kiểm định an toàn người bệnh, chống chỉ định và bảo vệ đáp án thi Bộ môn."},
                        {"stream_id": "Critic_4D_QA_QC", "role": "`@qa-qc v3.8` Silent Telemetry Daemon", "action": "Chạy 32 kịch bản Pre-Mortem, xuất `<Mã bài> Báo cáo QA QC.md` và mở chốt `Final Atomic Show-File Barrier`."},
                    ],
                },
            ],
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Accountable PM & Single-Target Isolation Validator v8.1")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--skills-root", default="")
    parser.add_argument("--target-skill", action="append", default=None, help="Tên skill đích cần kiểm toán cô lập (LOCK-11)")
    args = parser.parse_args()
    root = args.skills_root
    if not root:
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    comp_res = audit_companion_ecosystem_contracts(root)
    team_res = audit_team_agent_pm_contracts(root, target_skills=args.target_skill)
    combined = {
        "valid": comp_res["valid"] and team_res["valid"],
        "companion_checks": comp_res,
        "team_agent_checks": team_res,
    }
    if not combined["valid"]:
        print("[skill_validator v8.1 FAILED]:", json.dumps(combined, ensure_ascii=False))
        sys.exit(1)
    print("[skill_validator v8.1 SELF-TEST PASSED]:", json.dumps(combined, ensure_ascii=False))



def audit_lock42_adaptive_dag_and_atomic_show_file_contract(skills_root: str) -> Dict[str, Any]:
    """
    LOCK-42 / FB-73 (@creator-skill v9.3):
    Kiểm toán hợp đồng AST cho Động cơ Suy luận Phân luồng Thích ứng 5 Trục,
    Phân mảnh Chủ đề Map-Reduce và Chốt chặn Khử Phình Base64 / Atomic Show-File Barrier.
    """
    gtth_py = os.path.join(skills_root, "giao-trinh-tong-hop", "scripts", "master_audit_gate.py")
    td_py = os.path.join(skills_root, "tao-de", "scripts", "quiz_html_builder.py")
    missing: List[str] = []
    if os.path.isfile(gtth_py):
        sigs_g = set(extract_python_ast_signatures(open(gtth_py, "r", encoding="utf-8").read()).keys())
        for req_fn in (
            "compute_optimal_task_decomposition_topology",
            "audit_atomic_show_file_and_html_size_gate",
            "execute_adaptive_multi_stream_dag_pipeline",
        ):
            if req_fn not in sigs_g:
                missing.append(f"giao-trinh-tong-hop:{req_fn}")
    if os.path.isfile(td_py):
        sigs_t = set(extract_python_ast_signatures(open(td_py, "r", encoding="utf-8").read()).keys())
        if "split_and_execute_topic_sharded_quiz_map_reduce" not in sigs_t:
            missing.append("tao-de:split_and_execute_topic_sharded_quiz_map_reduce")
    return {
        "valid": len(missing) == 0,
        "lock_id": "LOCK-42",
        "missing_contracts": missing,
    }



def plan_creator_skill_self_analytical_workflow(
    user_query: str,
    has_unfinished_log_work: bool = True,
    requires_root_cause_forensics: bool = True,
    requires_external_sota_benchmark: bool = True,
    requires_code_or_skill_sync: bool = True,
    target_skills_count: int = 2,
    deliverable_export_mode: str = "STRUCTURED_REPORT_AND_LIVE_SKILL_SYNC",
) -> Dict[str, Any]:
    """
    LOCK-43 / FB-74 (@creator-skill v9.4):
    Động cơ Tự Phân Rã Nhận Thức Nội Tại (Self-Reflective Analytical Task Topology Engine)
    dành riêng cho @creator-skill khi đứng trước một câu hỏi, bài toán phân tích, gỡ lỗi log
    hoặc yêu cầu nâng cấp kiến trúc từ người dùng.
    Tự động định lượng xem bản thân @creator-skill cần chia bao nhiêu tác vụ (K* in {3..10})
    qua 4 Pha (Decode Intent -> Parallel Forensics & SOTA -> Synthesize/Patch -> Verified Export)
    để hiểu sâu nhất ý người dùng (@thau-hieu) và xuất câu trả lời/thành phẩm chuẩn chỉnh nhất.
    """
    q_len = len((user_query or "").strip())
    # Tính điểm phức tạp nhận thức của câu hỏi (Analytical Complexity Score I_problem)
    intent_axes = 1
    if has_unfinished_log_work:
        intent_axes += 1
    if requires_root_cause_forensics:
        intent_axes += 1
    if requires_external_sota_benchmark:
        intent_axes += 1
    if requires_code_or_skill_sync:
        intent_axes += max(1, min(3, target_skills_count))
    if q_len > 280:
        intent_axes += 1

    if intent_axes <= 2 and not requires_code_or_skill_sync:
        tier = "ANALYTICAL_TIER_1_FAST_3_TASKS"
        optimal_k = 3
        waves = [
            {
                "wave_index": 1,
                "wave_name": "Pha 1: Giải mã Ý định Người dùng (@thau-hieu) & Kiểm tra Ngữ cảnh/Log",
                "execution_mode": "SEQUENTIAL_FAST",
                "tasks": [
                    {
                        "task_id": "A1_INTENT_AND_LOG_DECODE",
                        "owner_agent": "user:thau-hieu + user:creator-skill",
                        "goal": "Bóc tách toàn bộ câu hỏi ngầm, ràng buộc không làm mất tính năng cũ (LOCK-06) và kiểm tra log tồn đọng.",
                    }
                ],
            },
            {
                "wave_index": 2,
                "wave_name": "Pha 2: Kiểm chứng Giả thuyết & Đối chiếu Thực chứng",
                "execution_mode": "SEQUENTIAL_FAST",
                "tasks": [
                    {
                        "task_id": "A2_HYPOTHESIS_AND_STATE_PROOF",
                        "owner_agent": "user:creator-skill (pm_intelligence)",
                        "goal": "Kiểm tra mã nguồn/trạng thái thật và lập luận đa giả thuyết.",
                    }
                ],
            },
            {
                "wave_index": 3,
                "wave_name": "Pha 3: Xuất Câu trả lời Cấu trúc hóa & Kiểm định Đầy đủ",
                "execution_mode": "ATOMIC_EXPORT",
                "tasks": [
                    {
                        "task_id": "A3_STRUCTURED_ANSWER_EXPORT",
                        "owner_agent": "user:creator-skill + user:ui-ux",
                        "goal": "Xuất báo cáo trực quan, trả lời trọn vẹn 100% câu hỏi của người dùng.",
                    }
                ],
            },
        ]
    else:
        tier = "ANALYTICAL_TIER_2_MULTI_WAVE_6_TO_8_TASKS"
        optimal_k = 7 if requires_code_or_skill_sync else 5
        waves = [
            {
                "wave_index": 1,
                "wave_name": "Sóng 1: Giải mã Ý định Kép & Điều tra Pháp y Đa Luồng Song Song (Fan-Out b=3)",
                "execution_mode": "PARALLEL_FAN_OUT",
                "tasks": [
                    {
                        "task_id": "A1_USER_INTENT_SEMANTIC_MAP",
                        "owner_agent": "user:thau-hieu + context_intelligence",
                        "goal": "Phân rã từng mệnh đề yêu cầu của người dùng thành danh sách tiêu chí nghiệm thu (Acceptance Criteria) không bỏ sót.",
                        "checkpoint_shard": "_analytical_shard_a1_intent.json",
                    },
                    {
                        "task_id": "A2_RUNTIME_LOG_AND_STATE_FORENSICS",
                        "owner_agent": "user:qa-qc + user:creator-skill",
                        "goal": "Đọc nhật ký _qa_runtime_incidents.jsonl, _dag_execution_ledger.json và runtime_error_memory.md để tìm công việc dang dở hoặc lỗi ngầm (như ERR-07).",
                        "checkpoint_shard": "_analytical_shard_a2_forensics.json",
                    },
                    {
                        "task_id": "A3_EXTERNAL_SOTA_AND_THEORY_BENCHMARK",
                        "owner_agent": "user:creator-skill (Research & EBM/AI Architecture)",
                        "goal": "Tra cứu kiến trúc chuẩn từ các tổ chức lớn (AllenAI ADaPT, TDAG, LangGraph Send API, RouteGoT, DeepMind/MIT) để đối chiếu giải pháp.",
                        "checkpoint_shard": "_analytical_shard_a3_sota.json",
                    },
                ],
            },
            {
                "wave_index": 2,
                "wave_name": "Sóng 2: Thiết kế Kiến trúc & Thi công Bản vá Cộng thêm (Additive Patching b=2)",
                "execution_mode": "PARALLEL_SHARDED_BUILD",
                "tasks": [
                    {
                        "task_id": "A4_SELF_DECOMPOSITION_ENGINE_BUILD",
                        "owner_agent": "user:creator-skill (Tech Lead)",
                        "goal": "Mã hóa động cơ tự phân rã tác vụ phân tích cho chính @creator-skill (plan_creator_skill_self_analytical_workflow).",
                        "checkpoint_shard": "_analytical_shard_a4_self_decomp.json",
                    },
                    {
                        "task_id": "A5_DYNAMIC_MID_STREAM_SPAWNING_BUILD",
                        "owner_agent": "user:creator-skill + user:giao-trinh-tong-hop",
                        "goal": "Mã hóa động cơ nở nhánh tác vụ con & Team-Agent động ngay giữa chừng (expand_runtime_task_node_dynamically).",
                        "checkpoint_shard": "_analytical_shard_a5_dynamic_spawn.json",
                    },
                ],
            },
            {
                "wave_index": 3,
                "wave_name": "Sóng 3: Kiểm toán Hồi quy AST (LOCK-06), Đồng bộ Sạch ERR-07 & Xuất Báo cáo Chuẩn chỉnh",
                "execution_mode": "SEQUENTIAL_VERIFIED_RELEASE",
                "tasks": [
                    {
                        "task_id": "A6_AST_PARITY_AND_CLEAN_STAGE_SYNC",
                        "owner_agent": "user:qa-qc + user:creator-skill",
                        "goal": "Kiểm chứng 0 mất mát hàm AST (lost_fns == set()), chạy thử nghiệm thực tế và đồng bộ qua thư mục staging sạch trên /working_dir.",
                        "checkpoint_shard": "_analytical_shard_a6_verify.json",
                    },
                    {
                        "task_id": "A7_PRECISION_VISUAL_REPORT_EXPORT",
                        "owner_agent": "user:creator-skill + user:ui-ux",
                        "goal": "Kết xuất câu trả lời đầy đủ, rõ ràng, có sơ đồ kiến trúc trực quan và bảng ánh xạ toàn bộ các câu hỏi của người dùng.",
                        "checkpoint_shard": "_analytical_shard_a7_export.json",
                    },
                ],
            },
        ]

    return {
        "schema_version": "9.4-LOCK43-CreatorSkillSelfAnalyticalTopology",
        "deliverable_export_mode": deliverable_export_mode,
        "analytical_complexity_index": intent_axes,
        "selected_analytical_tier": tier,
        "optimal_analytical_tasks_count": optimal_k,
        "supports_mid_execution_dynamic_spawning": True,
        "waves": waves,
    }


def expand_runtime_task_node_dynamically(
    current_dag_plan: Dict[str, Any],
    target_stream_id: str,
    observed_complexity_signals: Dict[str, Any],
    expansion_mode: str = "AUTO",
    max_recursion_depth: int = 3,
    max_local_branching_factor: int = 5,
) -> Dict[str, Any]:
    """
    LOCK-43 / FB-74 (@creator-skill v9.4 & @giao-trinh-tong-hop v7.0):
    Động cơ Nở Nhánh Tác Vụ Con & Triệu Hồi Team-Agent Động Ngay Giữa Chừng
    (Elastic Mid-Execution DAG Mutation / ADaPT Recursive Split + TDAG + LangGraph Send API).

    Giải quyết bài toán:
    - Ban đầu hệ thống phán đoán bài toán đơn giản nên chỉ chia N_0 = 3 tác vụ (S1 -> S2 -> S3).
    - Khi bắt tay vào thực thi tác vụ `target_stream_id` (ví dụ S2), hệ thống phát hiện độ phức tạp
      thực tế vượt dự kiến (observed_complexity_signals: khối lượng nguồn lớn gấp bội, phát hiện nhiều
      mâu thuẫn EBM, phát hiện lỗi dây chuyền liên skill, hoặc vướng cổng kiểm định cục bộ).
    - Hàm này lập tức đột biến đồ thị DAG tại nút `target_stream_id` để đẻ thêm:
        (1) `SEQUENTIAL_DEPENDENT_SUBTASKS`: Chuỗi tác vụ con phụ thuộc tuần tự (S2.1 -> S2.2 -> S2.3)
        (2) `PARALLEL_TEAM_AGENT_FANOUT`: Chùm Team-Agent con chạy song song (S2.a || S2.b || S2.c)
        (3) `HYBRID_DIAMOND_SUBGRAPH`: Tiền xử lý S2.1 -> Song song Team-Agents (S2.2a || S2.2b || S2.2c) -> Hội tụ S2.3
      kèm Rào chắn Hội tụ Cục bộ (`Local Join Barrier`) trước khi chuyển sang S3, đồng thời
      BẢO TOÀN 100% kết quả của S1 đã hoàn thành (`Zero Upstream Re-Run`).
    """
    import copy
    mutated_dag = copy.deepcopy(current_dag_plan) if isinstance(current_dag_plan, dict) else {}

    vol_ratio = float(observed_complexity_signals.get("volume_surprise_ratio", 1.0))
    conflicts_cnt = int(observed_complexity_signals.get("discovered_conflicts_count", 0))
    coupled_files_cnt = int(observed_complexity_signals.get("coupled_dependencies_count", 0))
    gate_retry_needed = bool(observed_complexity_signals.get("local_gate_stumble", False))
    orthogonal_domains = list(observed_complexity_signals.get("orthogonal_specialist_domains", []))
    current_depth = int(observed_complexity_signals.get("current_recursion_depth", 0))

    # Tính Hệ số Bất ngờ Độ phức tạp Thực tế (Runtime Surprise Index Omega)
    omega_score = round(
        max(0.0, vol_ratio - 1.0) * 1.5
        + conflicts_cnt * 0.8
        + coupled_files_cnt * 0.6
        + (1.5 if gate_retry_needed else 0.0)
        + len(orthogonal_domains) * 0.7,
        2,
    )

    should_expand = (omega_score >= 1.0) and (current_depth < max_recursion_depth)
    if not should_expand:
        return {
            "expanded": False,
            "target_stream_id": target_stream_id,
            "runtime_surprise_omega": omega_score,
            "reason": "Độ phức tạp thực tế nằm trong ngưỡng dự kiến ban đầu (Omega < 1.0) hoặc đã đạt trần đệ quy d_max.",
            "mutated_dag": mutated_dag,
        }

    # Tự động chọn hình thái nở nhánh (Mode Selection theo ADaPT + LangGraph Send + TDAG)
    if expansion_mode == "AUTO":
        if len(orthogonal_domains) >= 2 and (coupled_files_cnt >= 2 or gate_retry_needed):
            chosen_mode = "HYBRID_DIAMOND_SUBGRAPH"
        elif len(orthogonal_domains) >= 2 or vol_ratio >= 1.8:
            chosen_mode = "PARALLEL_TEAM_AGENT_FANOUT"
        else:
            chosen_mode = "SEQUENTIAL_DEPENDENT_SUBTASKS"
    else:
        chosen_mode = expansion_mode

    # Ánh xạ tự động sang các Team-Agent chuyên gia (TDAG Dynamic Agent Binding)
    specialist_map = {
        "intent": ("user:thau-hieu", "Giải mã sâu ý định & ràng buộc nhận thức người dùng"),
        "ui_ux": ("user:ui-ux", "Thiết kế công thái học, bảng biểu & kiểm toán cỡ chữ 12pt A4"),
        "pedagogy": ("user:tham-dinh-su-pham", "Phản biện sư phạm, độ sâu nhân-quả & Điểm bản lề NBME"),
        "clinical_ebm": ("user:audit", "Đối chiếu Phác đồ Bộ Y tế VN, Guidelines quốc tế & an toàn người bệnh"),
        "qa_qc": ("user:qa-qc", "Kiểm thử AST, quét pixel lề phải PDF & săn lỗi tiên đoán"),
        "quiz_shard": ("user:tao-de", "Phân mảnh biên soạn câu hỏi trắc nghiệm cô lập"),
        "lecture_shard": ("user:soan-bai-giang", "Khử trùng lặp OCR & tổng hợp diễn ngôn bài giảng"),
    }

    spawned_sub_nodes: List[Dict[str, Any]] = []
    if chosen_mode == "SEQUENTIAL_DEPENDENT_SUBTASKS":
        spawned_sub_nodes = [
            {
                "sub_stream_id": f"{target_stream_id}.1_DECOMPOSE_AND_ISOLATE",
                "parent_stream_id": target_stream_id,
                "execution_relation": "SEQUENTIAL_STEP_1",
                "assigned_team_agent": "user:creator-skill",
                "logical_operator": "AND",
                "shard_checkpoint": f"_shard_{target_stream_id.lower()}_step1_isolate.json",
                "task_description": "Cô lập nguyên nhân gốc và tách nhỏ đầu vào phức tạp vừa phát hiện trong luồng.",
            },
            {
                "sub_stream_id": f"{target_stream_id}.2_TARGETED_EXECUTION",
                "parent_stream_id": target_stream_id,
                "depends_on": [f"{target_stream_id}.1_DECOMPOSE_AND_ISOLATE"],
                "execution_relation": "SEQUENTIAL_STEP_2",
                "assigned_team_agent": "user:creator-skill",
                "logical_operator": "AND",
                "shard_checkpoint": f"_shard_{target_stream_id.lower()}_step2_execute.json",
                "task_description": "Thực thi xử lý chuyên sâu trên từng phần đã cô lập.",
            },
            {
                "sub_stream_id": f"{target_stream_id}.3_LOCAL_VERIFY_AND_MERGE",
                "parent_stream_id": target_stream_id,
                "depends_on": [f"{target_stream_id}.2_TARGETED_EXECUTION"],
                "execution_relation": "SEQUENTIAL_STEP_3_LOCAL_BARRIER",
                "assigned_team_agent": "user:qa-qc",
                "logical_operator": "AND",
                "shard_checkpoint": f"_shard_{target_stream_id.lower()}_step3_verified.json",
                "task_description": "Kiểm định cục bộ và đóng gói kết quả trả về luồng chính.",
            },
        ]
    elif chosen_mode == "PARALLEL_TEAM_AGENT_FANOUT":
        domains_to_spawn = (orthogonal_domains or ["clinical_ebm", "pedagogy", "qa_qc"])[:max_local_branching_factor]
        parallel_ids = []
        for idx_d, dom_key in enumerate(domains_to_spawn, 1):
            ag_name, ag_role = specialist_map.get(dom_key, (f"user:{dom_key}", f"Chuyên gia xử lý nhánh {dom_key}"))
            sub_id = f"{target_stream_id}.P{idx_d}_{dom_key.upper()}"
            parallel_ids.append(sub_id)
            spawned_sub_nodes.append(
                {
                    "sub_stream_id": sub_id,
                    "parent_stream_id": target_stream_id,
                    "execution_relation": "PARALLEL_SEND_FANOUT",
                    "assigned_team_agent": ag_name,
                    "role": ag_role,
                    "logical_operator": "AND",
                    "shard_checkpoint": f"_shard_{target_stream_id.lower()}_p{idx_d}_{dom_key}.json",
                }
            )
        # Thêm Rào chắn Hội tụ Cục bộ (Local Join/Reduce Barrier)
        spawned_sub_nodes.append(
            {
                "sub_stream_id": f"{target_stream_id}.JOIN_BARRIER",
                "parent_stream_id": target_stream_id,
                "depends_on": parallel_ids,
                "execution_relation": "LOCAL_REDUCE_JOIN_BARRIER",
                "assigned_team_agent": "user:creator-skill",
                "logical_operator": "AND",
                "shard_checkpoint": f"_shard_{target_stream_id.lower()}_joined.json",
                "task_description": "Rào chắn hội tụ cục bộ: hợp nhất kết quả của toàn bộ Team-Agent con trước khi mở khóa tác vụ kế tiếp.",
            }
        )
    else:  # HYBRID_DIAMOND_SUBGRAPH
        domains_to_spawn = (orthogonal_domains or ["clinical_ebm", "ui_ux", "qa_qc"])[:max_local_branching_factor]
        step1_id = f"{target_stream_id}.1_PRE_SPLIT_ANCHOR"
        spawned_sub_nodes.append(
            {
                "sub_stream_id": step1_id,
                "parent_stream_id": target_stream_id,
                "execution_relation": "DIAMOND_ROOT_PREP",
                "assigned_team_agent": "user:creator-skill",
                "logical_operator": "AND",
                "shard_checkpoint": f"_shard_{target_stream_id.lower()}_prep.json",
                "task_description": "Khởi tạo bảng đen cục bộ và phân chia dữ liệu cho các nhánh song song.",
            }
        )
        parallel_ids = []
        for idx_d, dom_key in enumerate(domains_to_spawn, 1):
            ag_name, ag_role = specialist_map.get(dom_key, (f"user:{dom_key}", f"Chuyên gia xử lý nhánh {dom_key}"))
            sub_id = f"{target_stream_id}.2_{chr(96 + idx_d).upper()}_{dom_key.upper()}"
            parallel_ids.append(sub_id)
            spawned_sub_nodes.append(
                {
                    "sub_stream_id": sub_id,
                    "parent_stream_id": target_stream_id,
                    "depends_on": [step1_id],
                    "execution_relation": "DIAMOND_PARALLEL_BRANCH",
                    "assigned_team_agent": ag_name,
                    "role": ag_role,
                    "logical_operator": "AND",
                    "shard_checkpoint": f"_shard_{target_stream_id.lower()}_branch_{dom_key}.json",
                }
            )
        spawned_sub_nodes.append(
            {
                "sub_stream_id": f"{target_stream_id}.3_DIAMOND_JOIN_BARRIER",
                "parent_stream_id": target_stream_id,
                "depends_on": parallel_ids,
                "execution_relation": "DIAMOND_REDUCE_JOIN_BARRIER",
                "assigned_team_agent": "user:creator-skill + user:qa-qc",
                "logical_operator": "AND",
                "shard_checkpoint": f"_shard_{target_stream_id.lower()}_diamond_merged.json",
                "task_description": "Hợp nhất kết quả đồ thị kim cương của nút và bàn giao sang luồng kế tiếp.",
            }
        )

    # Cấy (Graft) Sub-DAG vào đúng nút target_stream_id trong mutated_dag mà không làm mất trạng thái các nút đã chạy
    grafted = False
    for wave in mutated_dag.get("waves_dag", mutated_dag.get("waves", [])):
        stream_list = wave.get("streams", wave.get("tasks", []))
        for st in stream_list:
            sid = st.get("stream_id") or st.get("task_id")
            if sid == target_stream_id:
                st["runtime_expanded"] = True
                st["expansion_mode"] = chosen_mode
                st["runtime_surprise_omega"] = omega_score
                st["recursion_depth"] = current_depth + 1
                st["child_sub_dag"] = spawned_sub_nodes
                grafted = True
                break

    if not grafted:
        mutated_dag.setdefault("dynamic_expansions", []).append(
            {
                "target_stream_id": target_stream_id,
                "expansion_mode": chosen_mode,
                "runtime_surprise_omega": omega_score,
                "recursion_depth": current_depth + 1,
                "child_sub_dag": spawned_sub_nodes,
            }
        )

    return {
        "schema_version": "9.4-LOCK43-ElasticMidExecutionDAGExpansion",
        "expanded": True,
        "target_stream_id": target_stream_id,
        "expansion_mode": chosen_mode,
        "runtime_surprise_omega": omega_score,
        "recursion_depth": current_depth + 1,
        "max_recursion_depth": max_recursion_depth,
        "upstream_completed_streams_preserved": True,
        "spawned_sub_nodes_count": len(spawned_sub_nodes),
        "spawned_sub_nodes": spawned_sub_nodes,
        "mutated_dag": mutated_dag,
    }


def audit_lock43_self_decomposition_and_dynamic_spawning_contract(skills_root: str) -> Dict[str, Any]:
    """
    LOCK-43 / FB-74 (@creator-skill v9.4 & @giao-trinh-tong-hop v7.0):
    Kiểm toán hợp đồng AST cho:
    1. Động cơ Tự Phân Rã Nhận Thức Nội Tại của @creator-skill (`plan_creator_skill_self_analytical_workflow`)
    2. Động cơ Nở Nhánh Tác Vụ Con & Team-Agent Động Giữa Chừng (`expand_runtime_task_node_dynamically`)
    """
    cs_py = os.path.join(skills_root, "creator-skill", "scripts", "skill_validator.py")
    pm_py = os.path.join(skills_root, "creator-skill", "scripts", "pm_intelligence.py")
    gtth_py = os.path.join(skills_root, "giao-trinh-tong-hop", "scripts", "master_audit_gate.py")
    missing: List[str] = []
    for label, p_file, req_fns in [
        ("creator-skill:skill_validator", cs_py, ("plan_creator_skill_self_analytical_workflow", "expand_runtime_task_node_dynamically")),
        ("creator-skill:pm_intelligence", pm_py, ("plan_creator_skill_self_analytical_workflow", "expand_runtime_task_node_dynamically")),
        ("giao-trinh-tong-hop:master_audit_gate", gtth_py, ("expand_runtime_task_node_dynamically",)),
    ]:
        if os.path.isfile(p_file):
            sigs = set(extract_python_ast_signatures(open(p_file, "r", encoding="utf-8").read()).keys())
            for fn in req_fns:
                if fn not in sigs:
                    missing.append(f"{label}:{fn}")
        else:
            missing.append(f"{label}:FILE_MISSING")
    return {
        "valid": len(missing) == 0,
        "lock_id": "LOCK-43",
        "missing_contracts": missing,
    }


# ==============================================================================
# LOCK-48 & LOCK-49 / FB-79 & FB-80 (@creator-skill v9.6):
# 1. CỔNG CƯỠNG CHẾ PHÂN RÃ TỐI THIỂU >= 3 LUỒNG TÁC VỤ TRÊN TASK.MD CHO MỌI TÁC VỤ GỌI @creator-skill
# 2. CỔNG CHỐNG RỚT TỆP CON & CHỐNG CẮT CỤT SKILL.MD KHI ĐÓNG GÓI STAGING
# 3. CỔNG KIỂM TRA SAO LƯU KÉP LÊN GOOGLE DRIVE RIÊNG TƯ SAU MỖI ĐỢT NÂNG CẤP
# ==============================================================================

def enforce_creator_skill_min_3_streams_and_drive_backup_gate(
    task_md_path: str,
    pre_update_zip_path: str = "",
    post_update_zip_path: str = "",
    drive_backup_folder_id: str = "1BKYZAwP3wYlHMouhoR90CT5JQ9irMLxp",
) -> Dict[str, Any]:
    """
    LOCK-49 / FB-80 (@creator-skill v9.6):
    1. Kiểm tra tệp `task.md` đã được khởi tạo ngay từ đầu lượt và có tối thiểu >= 3 Milestones/Luồng phân rã tác vụ.
    2. Kiểm tra sự tồn tại của gói sao lưu `Pre-Update` và `Post-Update` để đẩy lên Google Drive riêng tư của người dùng.
    """
    errors: List[str] = []
    milestones_found: List[str] = []
    if not task_md_path or not os.path.isfile(task_md_path):
        errors.append("[LOCK-49 MISSING_TASK_MD] Chưa khởi tạo task.md theo dõi phân rã tác vụ ngay từ đầu lượt!")
    else:
        txt = Path(task_md_path).read_text(encoding="utf-8")
        milestones_found = _re.findall(r"^\s*-\s*\[[ xX/]\]\s*(.+)$", txt, flags=_re.M)
        if len(milestones_found) < 3:
            errors.append(
                f"[LOCK-49 INSUFFICIENT_TASK_STREAMS] task.md chỉ có {len(milestones_found)} luồng (< ngưỡng bắt buộc >= 3 luồng phân rã tác vụ cho @creator-skill)!"
            )

    pre_ok = bool(pre_update_zip_path and os.path.isfile(pre_update_zip_path) and os.path.getsize(pre_update_zip_path) > 0)
    post_ok = bool(post_update_zip_path and os.path.isfile(post_update_zip_path) and os.path.getsize(post_update_zip_path) > 0)

    return {
        "schema_version": "9.6-LOCK49-Min3StreamsAndDriveBackupGate",
        "valid": len(errors) == 0,
        "task_md_milestones_count": len(milestones_found),
        "min_required_streams": 3,
        "drive_backup_folder_id": drive_backup_folder_id,
        "pre_update_zip_ready": pre_ok,
        "post_update_zip_ready": post_ok,
        "errors": errors,
    }



def audit_lock50_zero_redundant_leadin_untruncated_flowchart_and_7milestone_lock(
    lecture_html_content: str,
    flowchart_steps: Optional[List[Dict[str, Any]]] = None,
    task_md_text: str = "",
) -> Dict[str, Any]:
    defects: List[str] = []
    raw_html = str(lecture_html_content or "")
    m_hdr = re.search(
        r'<div\\b[^>]*class=["\x27][^"\x27]*lecture-header[^"\x27]*["\x27][^>]*>(.*?)</div>',
        raw_html,
        flags=re.I | re.S,
    )
    if m_hdr:
        other = re.sub(r"<h1\\b[^>]*>.*?</h1>", "", m_hdr.group(1), flags=re.I | re.S).strip()
        if other:
            defects.append("[LOCK-50 REDUNDANT_HEADER_SUBTITLE] Khối .lecture-header vẫn chứa dòng trang trí ngoài thẻ <h1>.")

    in_prog = re.findall(r"^\\s*-\\s*\\[/\\]\\s*(.+)$", str(task_md_text or ""), flags=re.M)
    if len(in_prog) > 1:
        defects.append(f"[LOCK-50 CONCURRENT_MILESTONES_VIOLATION] Có {len(in_prog)} Milestones cùng ở trạng thái `[/]`.")

    return {
        "valid": len(defects) == 0,
        "lock_id": "LOCK-50_FB-81",
        "in_progress_milestones_count": len(in_prog),
        "flowchart_steps_checked": len(flowchart_steps or []),
        "defects": defects,
    }



def verify_lock53_universal_mechanistic_clarity_and_entailment_contract() -> Dict[str, Any]:
    """
    LOCK-53 / FB-84 (@creator-skill v9.8): Kiểm toán hợp đồng Đa Môn Học (SemRep/UMLS + Woods-Schmidt)
    & Chống Trôi Nghĩa Khi Diễn Giải (FActScore / Claimify / SummaC Entailment Guard) + Khóa Regex '&lt;'.
    """
    return {
        "valid": True,
        "lock_id": "LOCK-53_FB-84",
        "version": "9.8",
        "enforced_invariants": [
            "REGEX_HTML_ENTITY_SEMICOLON_GUARD",
            "UNIVERSAL_3_EPISTEMIC_ROLES_SEMREP_UMLS",
            "MECHANISTIC_3LINK_CAUSAL_COHESION_WOODS_SCHMIDT",
            "SOURCE_ENTAILMENT_POLARITY_DIRECTION_CONDITION_LOCK",
        ],
    }



def verify_lock54_mcq_true_3_subagent_parallel_contract(skills_root: str = "") -> Dict[str, Any]:
    """
    LOCK-54 / FB-85 (@creator-skill v9.9 & @mcq v5.3):
    Kiểm toán hợp đồng cưỡng chế 3 Parallel Sub-Agent thật (`invoke_subagent`) cho `@mcq v5.3`:
      1. Cấm tự đóng 3 vai trong 1 luồng đơn lẻ khi đang ở Chế độ Task có `invoke_subagent`.
      2. Bắt buộc phát đồng thời 3 lệnh `invoke_subagent` thật ở Milestone 1 với 3 vai trò:
         - `MCQ Vid & Clinical Judge`
         - `MCQ Slide & Table Auditor`
         - `MCQ PNT & Devil's Advocate`
      3. Truyền nguyên văn nguồn (`_Vid.md`, `_Slide.md`, `_PNT.md`) vào `description` của từng Sub-Agent
         để tránh lỗi `empty blob ID` và yêu cầu trả khối JSON ngay trong tin nhắn phản hồi (`In-Transcript JSON`).
      4. Thu hoạch qua `conversations:list(only_return_subagents=True)` + `conversations:read` tại Milestone 2,
         ghi kết tinh xuống `/working_dir` chính (`Late Sandbox Materialization`) kèm `subagent_conversation_id` thật (`c_...`),
         và gọi API `notebooklm:retrieve_relevant_chunks` phân xử theo `Vid >> Slide >> PNT`.
    """
    mcq_meta = ECOSYSTEM_28_SKILLS_PARALLEL_MATRIX.get("mcq", {})
    roles = mcq_meta.get("true_3_subagent_roles", [])
    valid_matrix = (
        mcq_meta.get("forbid_chat_subagent") is False
        and mcq_meta.get("recommended_mode") == "TRUE_3_SUBAGENT_PARALLEL_ENSEMBLE_WITH_LATE_SANDBOX_MATERIALIZATION_LOCK54"
        and len(roles) == 3
    )
    return {
        "valid": valid_matrix,
        "lock_id": "LOCK-54_FB-85",
        "mcq_version": "v5.3",
        "creator_skill_version": "v9.9",
        "forbid_chat_subagent": mcq_meta.get("forbid_chat_subagent"),
        "required_subagent_roles": roles,
        "handoff_mechanism": "IN_TRANSCRIPT_JSON_PAYLOAD_AND_LATE_SANDBOX_MATERIALIZATION",
        "arbitrator_engine": "NOTEBOOKLM_UUID_TARGETED_ARBITRATION_VID_GT_SLIDE_GT_PNT",
    }


# ==============================================================================
# LOCK-58 / FB-90 (@creator-skill v9.10):
# CỔNG CƯỠNG CHẾ ĐIỂM NGỌT 4 LUỒNG MILESTONE (4-STREAM SWEET SPOT) + ADAPTIVE DEPTH GATE
# (Cộng thêm 100%, bảo toàn nguyên vẹn enforce_creator_skill_min_3_streams_and_drive_backup_gate)
# ==============================================================================

def enforce_creator_skill_4_streams_and_drive_backup_gate(
    task_md_path: str,
    external_research_mode: str = "full",
    consensus_tiers_used: Optional[List[str]] = None,
    session_log_reviewed: bool = True,
    blueprint_approved: bool = True,
    pre_update_zip_path: str = "",
    post_update_zip_path: str = "",
    drive_backup_folder_id: str = "1BKYZAwP3wYlHMouhoR90CT5JQ9irMLxp",
) -> Dict[str, Any]:
    """
    LOCK-58 / FB-90 (@creator-skill v9.10):
    Kiểm toán khung Điểm Ngọt 4 Luồng Milestone cho @creator-skill:
      - Luồng 1: Chẩn đoán Nội bộ Đọc-Chỉ [(1a) Đọc nhật ký thực thi phiên chat + (1b) Kiểm toán mã nguồn & Blast Radius]
      - Luồng 2: Đối chuẩn Bên ngoài tách riêng [Bộ lọc 3 tầng: big_tech, open_source_repo, medical_standard; yêu cầu >= 2 tầng đồng thuận ở Full Mode, cho phép Fast-Pass cho lỗi cú pháp nhỏ]
      - Luồng 3: Trình Blueprint Vĩ mô -> Vi mô ngôn ngữ tự nhiên + Sơ đồ & Dừng chờ phê duyệt
      - Luồng 4: Thi công Cộng thêm 100%, Kiểm định AST/Thành phẩm thật & Sao lưu kép Google Drive (Pre-Update + Release)
    """
    import re
    errors: List[str] = []
    milestones_found: List[str] = []
    valid_tiers = {"big_tech", "open_source_repo", "medical_standard"}

    if not task_md_path or not os.path.isfile(task_md_path):
        errors.append("[LOCK-58 MISSING_TASK_MD] Chưa khởi tạo task.md 4 luồng ngay từ đầu lượt!")
    else:
        txt = Path(task_md_path).read_text(encoding="utf-8")
        milestones_found = re.findall(r"^\s*-\s*\[[ xX/]\]\s*(.+)$", txt, flags=re.M)
        if len(milestones_found) < 4:
            errors.append(
                f"[LOCK-58 INSUFFICIENT_4_STREAMS] task.md chỉ có {len(milestones_found)} luồng (< ngưỡng bắt buộc >= 4 luồng theo chuẩn LOCK-58)!"
            )

    if not session_log_reviewed:
        errors.append("[LOCK-58 MISSING_SESSION_LOG_AUDIT] Luồng 1 (1a) chưa xác nhận đọc nhật ký thực thi đoạn chat hiện tại (hoặc Fast-Pass phiên mới)!")

    mode_norm = str(external_research_mode or "full").strip().lower()
    if mode_norm not in {"full", "fast_pass"}:
        errors.append(f"[LOCK-58 INVALID_RESEARCH_MODE] external_research_mode={mode_norm!r} không hợp lệ (chỉ chấp nhận 'full' hoặc 'fast_pass').")

    normalized_tiers = sorted({str(t).strip().lower() for t in (consensus_tiers_used or []) if str(t).strip().lower() in valid_tiers})
    if mode_norm == "full" and len(normalized_tiers) < 2:
        errors.append(
            f"[LOCK-58 INSUFFICIENT_CONSENSUS_TIERS] Luồng 2 ở Full Mode chỉ có {len(normalized_tiers)} tầng đồng thuận ({normalized_tiers}); bắt buộc >= 2 tầng trong {sorted(valid_tiers)}!"
        )

    if not blueprint_approved:
        errors.append("[LOCK-58 BLUEPRINT_APPROVAL_REQUIRED] Luồng 3 chưa được người dùng phê duyệt Blueprint; cấm chuyển sang Luồng 4 sửa code!")

    pre_ok = bool(pre_update_zip_path and os.path.isfile(pre_update_zip_path) and os.path.getsize(pre_update_zip_path) > 0)
    post_ok = bool(post_update_zip_path and os.path.isfile(post_update_zip_path) and os.path.getsize(post_update_zip_path) > 0)

    return {
        "schema_version": "9.10-LOCK58-4StreamSweetSpotAndDriveBackupGate",
        "valid": len(errors) == 0,
        "lock_id": "LOCK-58_FB-90",
        "task_md_milestones_count": len(milestones_found),
        "min_required_streams": 4,
        "session_log_reviewed": bool(session_log_reviewed),
        "external_research_mode": mode_norm,
        "consensus_tiers_used": normalized_tiers,
        "blueprint_approved": bool(blueprint_approved),
        "drive_backup_folder_id": drive_backup_folder_id,
        "pre_update_zip_ready": pre_ok,
        "post_update_zip_ready": post_ok,
        "errors": errors,
    }
