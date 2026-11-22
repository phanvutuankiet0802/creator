#!/usr/bin/env python3
"""Adaptive Academic Quality Contract v1.0.

Deterministic, subject-aware **structural** validation, NOT a semantic judge.
The engine receives a human/LLM-drafted evidence-anchored learning blueprint.
Its preflight / artifact gates fail closed for missing Critical objectives, invalid
source lineage, generic MEQ, and unreviewed outputs. Domain classification is
provisional; independent domain review is required before declaring READY.
Stdlib only; a byte-identical copy can be bundled with standalone skills.
"""
from __future__ import annotations
import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

VERSION = "1.1.0"
PRIORITIES = {"P0", "P1", "P2", "P3", "P4"}
MODES = {"lecture", "flashcard", "mcq", "meq", "monograph"}
DOMAINS = {
    "surgery": ("ngoai khoa", "phau thuat", "mo cap cuu", "tai thong mach"),
    "internal_medicine": ("noi khoa", "noi tiet", "tim mach", "ho hap", "than hoc", "benh noi khoa"),
    "anatomy": ("giai phau", "dong mach", "than kinh", "vi tri", "lien quan giai phau", "co quan"),
    "physiology": ("sinh ly", "dieu hoa", "hang dinh", "co che phan hoi", "ap suat", "sinh ly hoc"),
    "pharmacology": ("duoc ly", "thuoc", "lieu dung", "tac dung phu", "tuong tac thuoc", "duoc dong"),
    "microbiology": ("vi sinh", "vi khuan", "virus", "nam", "khang sinh do", "nuoi cay"),
    "public_health": ("dich te", "y te cong cong", "nghien cuu", "ty suat", "quan the", "sang loc", "dich hoc"),
    "medical_imaging": ("chan doan hinh anh", "x quang", "ct scan", "mri", "sieu am", "hinh anh hoc"),
    "pathology": ("giai phau benh", "mo benh hoc", "vi the", "te bao hoc", "mo hoc"),
    "clinical_skills": ("ky nang lam sang", "hoi benh", "tham kham", "osce", "kham benh"),
    "environmental_medicine": ("y hoc moi truong", "suc khoe moi truong", "phoi nhiem moi truong"),
    "family_medicine": ("y hoc gia dinh", "cham soc lien tuc", "bac si gia dinh"),
    "occupational_medicine": ("y hoc lao dong", "suc khoe nghe nghiep", "benh nghe nghiep"),
}
COMPETENCIES = {
    "recognition", "mechanism", "spatial", "interpretation", "differential",
    "clinical_decision", "procedure", "quantitative", "population_reasoning",
    "evidence_appraisal", "safety", "communication", "recall", "integration",
}
REASONING_COMPETENCIES = {"differential", "clinical_decision", "interpretation", "procedure", "evidence_appraisal", "population_reasoning", "integration", "mechanism", "spatial", "quantitative"}
QUAD_KINDS = frozenset({"lecture", "flashcard", "mcq", "meq"})
MEQ_ACTIONS = frozenset({"interpret", "analyze", "explain_mechanism", "diagnose", "prioritize", "calculate", "compare", "justify", "choose_management", "evaluate_evidence", "identify_structure", "recall_foundation"})



def _ascii(text: Any) -> str:
    v = unicodedata.normalize("NFD", str(text).lower())
    v = "".join(ch for ch in v if unicodedata.category(ch) != "Mn").replace("đ", "d")
    return re.sub(r"\s+", " ", v).strip()


def _nontrivial(value: Any, minimum: int = 16) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum


def _issue(code: str, detail: str, *, path: str = "") -> Dict[str, str]:
    return {"code": code, "detail": detail, "path": path}


def suggest_domains(text: str, *, explicit_subjects: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Candidate subject profiles only; keyword inference is NOT verification."""
    if explicit_subjects:
        invalid = sorted(set(explicit_subjects) - set(DOMAINS))
        if invalid:
            return {"status": "NEEDS_CLASSIFICATION", "candidates": [], "unknown": invalid}
        return {"status": "USER_DECLARED_REVIEW_REQUIRED", "candidates": list(dict.fromkeys(explicit_subjects)), "unknown": []}
    n = _ascii(text)
    hits = {key: sum(1 for phrase in patterns if re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", n)) for key, patterns in DOMAINS.items()}
    ranked = sorted([(k, v) for k, v in hits.items() if v > 0], key=lambda kv: (-kv[1], kv[0]))
    if not ranked:
        return {"status": "NEEDS_CLASSIFICATION", "candidates": [], "unknown": []}
    return {"status": "HEURISTIC_CANDIDATES_ONLY", "candidates": [k for k, _ in ranked[:4]], "evidence_counts": dict(ranked)}


def audit_blueprint(blueprint: Mapping[str, Any]) -> Dict[str, Any]:
    errors: List[Dict[str, str]] = []
    sources = blueprint.get("sources", [])
    objectives = blueprint.get("objectives", [])
    src_ids = [s.get("id") for s in sources if isinstance(s, dict)]
    if not sources:
        errors.append(_issue("NO_SOURCES", "Thiếu danh mục nguồn đầu vào.", path="sources"))
    if blueprint.get("delivery_profile", "standalone") not in {"standalone", "quad_pack"}:
        errors.append(_issue("BAD_DELIVERY_PROFILE", "Chỉ hỗ trợ standalone / quad_pack", path="delivery_profile"))
    for i, source in enumerate(sources):
        if not isinstance(source, dict) or source.get("tier") not in {"primary", "external"}:
            errors.append(_issue("BAD_SOURCE_TIER", "Nguồn phải có tầng primary hoặc external", path=f"sources[{i}]"))
        if isinstance(source, dict) and source.get("origin") == "notebooklm" and not (source.get("notebook_id") or source.get("notebook_uuid")):
            errors.append(_issue("MISSING_NOTEBOOK_REF", "NotebookLM cần notebook_id hoặc UUID thật", path=f"sources[{i}]"))
    if len(set(src_ids)) != len(src_ids) or any(not s for s in src_ids):
        errors.append(_issue("BAD_SOURCE_IDS", "Source ID thiếu hoặc trùng.", path="sources"))
    source_map = {s.get("id"): s for s in sources if isinstance(s, dict)}
    if not objectives:
        errors.append(_issue("NO_LEARNING_OBJECTIVES", "Chưa xác định mục tiêu học tập.", path="objectives"))
    ids = [o.get("id") for o in objectives if isinstance(o, dict)]
    if len(set(ids)) != len(ids) or any(not s for s in ids):
        errors.append(_issue("BAD_OBJECTIVE_IDS", "LO ID thiếu hoặc trùng.", path="objectives"))
    critical = []
    for i, o in enumerate(objectives):
        p = f"objectives[{i}]"
        if not isinstance(o, dict):
            errors.append(_issue("BAD_OBJECTIVE", "Mục tiêu phải là object.", path=p)); continue
        oid = str(o.get("id", "?"))
        priority = o.get("priority")
        if priority not in PRIORITIES:
            errors.append(_issue("BAD_PRIORITY", f"{oid}: mức ưu tiên không hợp lệ.", path=p))
        if priority == "P0": critical.append(oid)
        if not _nontrivial(o.get("statement"), 14):
            errors.append(_issue("EMPTY_LO_STATEMENT", f"{oid}: phát biểu mục tiêu quá mơ hồ.", path=p))
        if not _nontrivial(o.get("priority_rationale"), 20):
            errors.append(_issue("MISSING_PRIORITY_RATIONALE", f"{oid}: thiếu biện minh theo môn học.", path=p))
        domains = o.get("domains", [])
        if not domains or (set(domains) - DOMAINS.keys()):
            errors.append(_issue("BAD_DOMAIN", f"{oid}: cần domain hợp lệ, cho phép đa nhãn.", path=p))
        if o.get("competency") not in COMPETENCIES:
            errors.append(_issue("BAD_COMPETENCY", f"{oid}: competency không hợp lệ.", path=p))
        anchored_sources = o.get("source_ids", [])
        if not anchored_sources or set(anchored_sources) - set(source_map):
            errors.append(_issue("MISSING_SOURCE_TRACE", f"{oid}: source_ids thiếu/không tồn tại.", path=p))
        elif priority in {"P0", "P1"} and not any(source_map[sid].get("tier") == "primary" for sid in anchored_sources):
            errors.append(_issue("CORE_NOT_GROUNDED_PRIMARY", f"{oid}: P0/P1 phải neo nguồn học liệu chính.", path=p))
        modes = set(o.get("assessment_modes", []))
        if not modes or modes - MODES:
            errors.append(_issue("BAD_ASSESSMENT_MODES", f"{oid}: assessment_modes thiếu/không hợp lệ.", path=p))
        if priority == "P0" and not _nontrivial(o.get("risk_if_missed"), 12):
            errors.append(_issue("CRITICAL_RISK_UNDEFINED", f"{oid}: thiếu hậu quả khi bỏ sót.", path=p))
        if "meq" in modes and o.get("competency") == "recall" and priority == "P0":
            errors.append(_issue("MEQ_NOT_ALIGNED", f"{oid}: MEQ P0 không thể chỉ yêu cầu nhớ một định nghĩa.", path=p))
    if objectives and not critical:
        review = blueprint.get('criticality_review', {})
        if (not isinstance(review, dict) or review.get('decision') != 'no_p0_justified'
            or not _nontrivial(review.get('evidence'), 40)
            or not review.get('reviewer_id')):
            errors.append(_issue('ZERO_P0_REQUIRES_INDEPENDENT_REVIEW',
                                 'Không có P0 phải được giải trình và thẩm định riêng.', path='criticality_review'))
    return {"valid": not errors, "status": "STRUCTURE_PASS_REVIEW_REQUIRED" if not errors else "BLOCKED", "errors": errors,
            "critical_ids": critical, "objective_count": len(objectives), "source_count": len(sources),
            "note": "Kiểm tra cấu trúc và liên kết khai báo, không chứng minh độ đúng y khoa hay sư phạm."}


def _objective_ids_from_artifact(artifact: Mapping[str, Any]) -> Set[str]:
    seen = set()
    for item in artifact.get("items", []):
        seen.update(item.get("objective_ids", []))
    for case in artifact.get("cases", []):
        for stage in case.get("stages", []):
            for question in stage.get("questions", []):
                seen.update(question.get("objective_ids", []))
    return seen


def audit_artifact(blueprint: Mapping[str, Any], artifact: Mapping[str, Any]) -> Dict[str, Any]:
    errors: List[Dict[str, str]] = []
    kind = artifact.get("kind")
    if kind not in MODES:
        return {"valid": False, "status": "BLOCKED", "errors": [_issue("BAD_ARTIFACT_KIND", str(kind))]}
    objs = {o["id"]: o for o in blueprint.get("objectives", []) if isinstance(o, dict) and o.get("id")}
    req = {oid for oid, obj in objs.items() if obj.get("priority") == "P0" and kind in obj.get("assessment_modes", [])}
    supplied = _objective_ids_from_artifact(artifact)
    missing = sorted(req - supplied)
    unknown = sorted(supplied - objs.keys())
    if missing: errors.append(_issue("CRITICAL_COVERAGE_GAP", f"{kind} thiếu P0: {missing}"))
    if unknown: errors.append(_issue("UNKNOWN_OBJECTIVE_LINK", f"{kind} trỏ LO không tồn tại: {unknown}"))
    if not artifact.get("items") and not artifact.get("cases"):
        errors.append(_issue("EMPTY_ARTIFACT", f"{kind}: không có nội dung."))
    src_ids = {s.get("id") for s in blueprint.get("sources", []) if isinstance(s, dict)}
    for i, item in enumerate(artifact.get("items", [])):
        path = f"items[{i}]"
        if not item.get("objective_ids"):
            errors.append(_issue("UNMAPPED_CONTENT", "Mỗi phần cần neo mục tiêu.", path=path))
        if not item.get("source_ids") or set(item.get("source_ids", [])) - src_ids:
            errors.append(_issue("UNTRACED_CONTENT", "Thiếu nguồn hoặc nguồn không hợp lệ.", path=path))
        if kind in {"lecture", "monograph"}:
            if not _nontrivial(item.get("explanation"), 40):
                errors.append(_issue("SHALLOW_EXPLANATION", "Thiếu giải thích đầy đủ (kiểm tra độ dài tối thiểu, chưa đo tính logic).", path=path))
            is_high = any(objs.get(oid, {}).get("priority") in {"P0", "P1"} for oid in item.get("objective_ids", []))
            if is_high and not _nontrivial(item.get("why_or_how"), 20):
                errors.append(_issue("NO_CAUSAL_BRIDGE", "P0/P1 thiếu cơ chế, lập luận hay quan hệ nhân quả.", path=path))
        if kind == "flashcard":
            if not _nontrivial(item.get("front"), 8) or not _nontrivial(item.get("back"), 8):
                errors.append(_issue("CARD_NOT_ATOMIC", "Thẻ thiếu mặt trước/sau có nghĩa.", path=path))
        if kind == "mcq":
            if len(item.get("options", [])) < 3 or not _nontrivial(item.get("stem"), 12):
                errors.append(_issue("MCQ_FORM", "Thiếu câu dẫn/phương án.", path=path))
            if item.get("correct_index") not in range(len(item.get("options", []))):
                errors.append(_issue("MCQ_NO_KEY", "Khóa đáp án không hợp lệ.", path=path))
            if len(item.get("why_wrong", [])) != max(len(item.get("options", [])) - 1, 0):
                errors.append(_issue("DISTRACTOR_REASONING_MISSING", "Thiếu giải thích riêng cho các phương án sai.", path=path))
            high_reasoning = any(objs.get(oid, {}).get("priority") == "P0" and objs.get(oid, {}).get("competency") in REASONING_COMPETENCIES for oid in item.get("objective_ids", []))
            if high_reasoning and (len(item.get("reasoning_steps", [])) < 2 or not _nontrivial(item.get("decision_justification"), 18)):
                errors.append(_issue("PSEUDO_HIGH_DIFFICULTY", "P0 suy luận cần >=2 bước và giải thích quyết định, không chỉ nhãn Bloom.", path=path))
            key = item.get("options", [])[item["correct_index"]] if isinstance(item.get("correct_index"), int) and 0 <= item["correct_index"] < len(item.get("options", [])) else ""
            if _nontrivial(key, 8) and _ascii(str(key)) in _ascii(str(item.get("title", ""))):
                errors.append(_issue("ANSWER_LEAK_TITLE", "Tiêu đề tiết lộ đáp án.", path=path))
    if kind == "meq":
        for i, case in enumerate(artifact.get("cases", [])):
            path = f"cases[{i}]"
            stages = case.get("stages", [])
            if len(stages) < 2:
                errors.append(_issue("MEQ_NOT_PROGRESSIVE", "MEQ cần ít nhất hai giai đoạn với dữ kiện tiến triển.", path=path))
            previous = None
            detailed_reasoning = 0
            for j, st in enumerate(stages):
                sp = f"{path}.stages[{j}]"
                narr = _ascii(st.get("new_information", ""))
                if not _nontrivial(st.get("new_information"), 16) or (previous is not None and narr == previous):
                    errors.append(_issue("NO_NEW_DECISION_DATA", "Giai đoạn thiếu dữ kiện mới.", path=sp))
                previous = narr
                if not st.get("questions"):
                    errors.append(_issue("EMPTY_MEQ_STAGE", "Giai đoạn không có câu hỏi.", path=sp))
                for q in st.get("questions", []):
                    qid = str(q.get("id", "?"))
                    if not q.get("objective_ids") or set(q.get("objective_ids", [])) - objs.keys():
                        errors.append(_issue("MEQ_UNMAPPED", f"{qid}: không neo LO hợp lệ.", path=sp))
                    if not q.get("source_ids") or set(q.get("source_ids", [])) - src_ids:
                        errors.append(_issue("UNTRACED_MEQ_QUESTION", f"{qid}: câu hỏi không có source_ids hợp lệ.", path=sp))
                    action = q.get("assessment_action")
                    if action is None and q.get("decision_or_conclusion"):
                        action = "justify"  # compatibility with v1.0 manifest
                    if action not in MEQ_ACTIONS:
                        errors.append(_issue("MEQ_UNCLASSIFIED_ACTION", f"{qid}: cần assessment_action phù hợp môn học.", path=sp))
                    if action != "recall_foundation" and len(q.get("reasoning_steps", [])) >= 2:
                        detailed_reasoning += 1
                    # Excluding alternatives is required ONLY when question explicitly asks to compare / choose,
                    # not for e.g. physiological explanation, interpreting graphs, or calculating a rate.
                    if action in {"compare", "choose_management"} and not _nontrivial(q.get("alternative_rejected_why"), 12):
                        errors.append(_issue("MEQ_MISSING_COMPARISON_RATIONALE", f"{qid}: phải giải thích phương án không chọn.", path=sp))
                    for term in q.get("protected_answer_terms", []):
                        if len(_ascii(term)) >= 5 and _ascii(term) in _ascii(case.get("title", "")):
                            errors.append(_issue("MEQ_ANSWER_LEAK", f"{qid}: tiêu đề tiết lộ đáp án.", path=sp))
            if detailed_reasoning < 1:
                errors.append(_issue("MEQ_SHALLOW_REASONING", "Cả ca không có bước suy luận hai tầng; không thể chỉ là chuỗi câu nhớ.", path=path))
    return {"valid": not errors, "status": "STRUCTURE_PASS_REVIEW_REQUIRED" if not errors else "BLOCKED",
            "kind": kind, "missing_critical_objectives": missing, "mapped_objectives": sorted(supplied), "errors": errors}


def release_gate(blueprint: Mapping[str, Any], artifacts: Sequence[Mapping[str, Any]], reviews: Optional[Sequence[Mapping[str, Any]]] = None) -> Dict[str, Any]:
    b = audit_blueprint(blueprint)
    reports = [audit_artifact(blueprint, a) for a in artifacts]
    errors = list(b["errors"])
    for report in reports:
        errors.extend(report["errors"])
    expected = {m for o in blueprint.get("objectives", []) for m in o.get("assessment_modes", []) if o.get("priority") == "P0"}
    produced = {a.get("kind") for a in artifacts}
    if blueprint.get("delivery_profile") == "quad_pack":
        # Fixed output contract applies even when individual items/cases are adaptive.
        expected |= QUAD_KINDS
        if len(artifacts) != 4 or produced != QUAD_KINDS or len(produced) != len(artifacts):
            errors.append(_issue("QUAD_PACK_CONTRACT_BROKEN", "Giáo trình tổng hợp bắt buộc có đúng 4 artifact: lecture, flashcard, mcq, meq."))
    for missing in sorted(expected - produced):
        errors.append(_issue("MISSING_REQUIRED_DELIVERABLE", f"Thiếu đầu ra bắt buộc {missing}."))
    if errors:
        status = "BLOCKED"
    else:
        r = list(reviews or [])
        required_scopes = {"source_fidelity", "pedagogical_coherence", "domain_correctness"} | {f"artifact:{k}" for k in produced}
        approved_scopes = {v.get("scope") for v in r if v.get("independent") is True and v.get("verdict") == "PASS" and _nontrivial(v.get("evidence_note"), 25) and v.get("reviewer_id")}
        # Names in self-declared review JSON are NOT verified identities. At a minimum,
        # avoid counting one reviewer as several independent discipline experts.
        reviewed = {v.get('scope'): v.get('reviewer_id') for v in r if v.get('scope') in required_scopes and v.get('scope') in approved_scopes}
        core = ['source_fidelity', 'pedagogical_coherence', 'domain_correctness']
        distinct_core = len({reviewed.get(k) for k in core if reviewed.get(k)}) == 3
        status = "READY_WITH_INDEPENDENT_ATTESTATIONS" if required_scopes <= approved_scopes and distinct_core else "REVIEW_REQUIRED"
    return {"status": status, "release_allowed": status == "READY_WITH_INDEPENDENT_ATTESTATIONS",
            "structure_valid": not errors, "errors": errors, "blueprint_audit": b, "artifact_audits": reports,
            "required_review_scopes": sorted({"source_fidelity", "pedagogical_coherence", "domain_correctness"} | {f"artifact:{k}" for k in produced}),
            "limitations": "Danh tính reviewer chưa được xác thực bằng hệ thống độc lập; yêu cầu cổng output bổ sung liên kết hash, run ID, source snapshot và kiểm thử trình duyệt."}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--blueprint", required=True)
    p.add_argument("--artifacts", nargs="*", default=[])
    p.add_argument("--reviews")
    args = p.parse_args()
    read = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
    report = release_gate(read(args.blueprint), [read(x) for x in args.artifacts], read(args.reviews) if args.reviews else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["release_allowed"] else 2)

if __name__ == "__main__":
    main()
