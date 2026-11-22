#!/usr/bin/env python3
"""Context Intelligence contract: deterministic consistency checks, never semantic certification.

This module does not decide what matters in medicine. It verifies that authoring
choices explicitly depend on user intent, lesson context, available sources and
objectives, so cross-skill handoffs cannot silently drop declared constraints.
"""
from __future__ import annotations
import hashlib
import json
from typing import Any, Mapping

VERSION = '0.1.0'
FIELDS = ('goal', 'audience', 'use_case', 'topic', 'domains', 'lesson_type', 'source_ids', 'constraints', 'decisions')
ALLOWED_ACTIONS = {'explain_in_depth', 'explain_briefly', 'visualize', 'assess', 'omit_with_reason', 'defer_for_review'}
CORE = {'P0', 'P1'}

def issue(code: str, path: str, detail: str) -> dict:
    return {'code': code, 'path': path, 'detail': detail}

def canonical_context(context: Mapping[str, Any]) -> dict:
    """Context fingerprint includes objective decisions; excludes only comments and run timestamps."""
    return {k: context.get(k) for k in ('goal', 'audience', 'use_case', 'topic', 'domains', 'lesson_type', 'source_ids', 'constraints', 'decisions')}

def context_fingerprint(context: Mapping[str, Any]) -> str:
    payload = json.dumps(canonical_context(context), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def audit_context(context: Any, *, profile: Mapping[str, Any] | None = None,
                  source_ids: list[str] | None = None,
                  objectives: list[dict] | None = None,
                  inventory: list[dict] | None = None,
                  handoff: Mapping[str, Any] | None = None) -> dict:
    errors=[]; warnings=[]
    if not isinstance(context, dict):
        return {'status':'BLOCKED', 'errors':[issue('CONTEXT_MISSING','context','Không có hồ sơ ngữ cảnh.')],
                'warnings':[], 'semantic_validated':False, 'context_fingerprint':None}
    for field in FIELDS:
        val=context.get(field)
        if val is None or val == '' or val == [] or val == {}:
            errors.append(issue('CONTEXT_FIELD_MISSING',f'context.{field}',f'Thiếu ngữ cảnh {field}.'))
    for field in ('goal','audience','use_case','topic'):
        if field in context and not isinstance(context[field], str):
            errors.append(issue('CONTEXT_WRONG_TYPE',f'context.{field}','Phải là chuỗi văn bản.'))
    for field in ('domains','source_ids'):
        if field in context and (not isinstance(context[field],list) or any(not isinstance(x,str) or not x for x in context[field])):
            errors.append(issue('CONTEXT_WRONG_TYPE',f'context.{field}','Phải là danh sách định danh.'))
    if isinstance(profile,Mapping):
        if set(context.get('domains',[]) if isinstance(context.get('domains'),list) else []) != set(profile.get('domains',[])):
            errors.append(issue('CONTEXT_SUBJECT_DRIFT','context.domains','Môn trong context khác hồ sơ phân loại.'))
        if context.get('lesson_type') != profile.get('lesson_type'):
            errors.append(issue('CONTEXT_LESSON_DRIFT','context.lesson_type','Bản chất bài khác hồ sơ phân loại.'))
    if source_ids is not None and set(context.get('source_ids',[]) if isinstance(context.get('source_ids'),list) else []) != set(source_ids):
        errors.append(issue('CONTEXT_SOURCE_DRIFT','context.source_ids','Nguồn context khác nguồn được chọn.'))
    constraints=context.get('constraints', {})
    if not isinstance(constraints,dict):
        errors.append(issue('CONTEXT_WRONG_TYPE','context.constraints','Constraints phải là object.'));constraints={}
    else:
        include=constraints.get('must_include',[]); exclude=constraints.get('must_avoid',[])
        if not isinstance(include,list) or not isinstance(exclude,list):
            errors.append(issue('CONTEXT_WRONG_TYPE','context.constraints','must_include/must_avoid phải là danh sách.'))
        elif set(map(str.lower,map(str,include))) & set(map(str.lower,map(str,exclude))):
            errors.append(issue('CONTEXT_INSTRUCTION_COLLISION','context.constraints','Cùng một yêu cầu vừa bắt buộc vừa cấm.'))
        # Exact output constraints agreed for the 4-product lecture workflow.
        if context.get('use_case') == 'quad_pack':
            if constraints.get('lecture_max_a4_pages') != 9:
                errors.append(issue('LECTURE_PAGE_CONTRACT_DRIFT','context.constraints','Bài giảng tối đa 9 trang A4.'))
            if constraints.get('output_count') != 4:
                errors.append(issue('QUAD_FILE_CONTRACT_DRIFT','context.constraints','Quad pack bắt buộc đúng 4 tệp.'))
    decisions=context.get('decisions',[])
    if not isinstance(decisions,list):
        errors.append(issue('CONTEXT_WRONG_TYPE','context.decisions','Decisions phải là danh sách.'));decisions=[]
    objective_map={o.get('id'):o for o in (objectives or []) if isinstance(o,dict) and isinstance(o.get('id'),str)}
    covered=set()
    concept_map={c.get('id'):c for c in (inventory or []) if isinstance(c,dict) and isinstance(c.get('id'),str)}
    for i,d in enumerate(decisions):
        prefix=f'context.decisions[{i}]'
        if not isinstance(d,dict):
            errors.append(issue('BAD_CONTEXT_DECISION',prefix,'Quyết định phải là object.'));continue
        lid=d.get('objective_id')
        if objectives is not None and lid not in objective_map:
            errors.append(issue('UNKNOWN_CONTEXT_OBJECTIVE',prefix,'Không có LO tương ứng.'))
        if lid in covered:
            errors.append(issue('DUPLICATE_CONTEXT_DECISION',prefix,'Một LO bị khai báo quyết định lặp.'))
        covered.add(lid)
        if d.get('action') not in ALLOWED_ACTIONS:
            errors.append(issue('INVALID_CONTEXT_ACTION',prefix,'Thiếu hành động có thể giải thích.'))
        for field in ('why_for_this_lesson','source_grounding','tradeoff'):
            if not isinstance(d.get(field),str) or not d[field].strip():
                errors.append(issue('CONTEXT_JUSTIFICATION_MISSING',f'{prefix}.{field}','Thiếu lý do riêng cho bài, neo nguồn hoặc đánh đổi.'))
        refs=d.get('source_ids')
        if not isinstance(refs,list) or not refs:
            errors.append(issue('CONTEXT_DECISION_NO_SOURCE',prefix,'Quyết định chưa chỉ ra nguồn.'))
        elif source_ids is not None and any(r not in source_ids for r in refs):
            errors.append(issue('CONTEXT_DECISION_UNKNOWN_SOURCE',prefix,'Quyết định trỏ tới nguồn ngoài phạm vi.'))
        if inventory is not None and lid in objective_map and objective_map[lid].get('priority') in CORE:
            linked = d.get('concept_ids')
            if not isinstance(linked,list) or not linked:
                errors.append(issue('CORE_CONTEXT_CONCEPT_LINK_MISSING',prefix,'P0/P1 chưa gắn ý nguồn cụ thể; lý do tự khai không đủ.'))
            else:
                for cid in linked:
                    concept=concept_map.get(cid)
                    if concept is None:
                        errors.append(issue('CONTEXT_UNKNOWN_CONCEPT',prefix,'ID ý nguồn không tồn tại.'))
                    elif lid not in concept.get('objective_ids',[]):
                        errors.append(issue('CONTEXT_CONCEPT_OBJECTIVE_DRIFT',prefix,'Ý nguồn không thuộc LO đang quyết định.'))
                    elif isinstance(refs,list) and concept.get('source_id') not in refs:
                        errors.append(issue('CONTEXT_CONCEPT_SOURCE_DRIFT',prefix,'Ý nguồn và trích dẫn trong quyết định khác nhau.'))
        if lid in objective_map:
            objective=objective_map[lid]
            if isinstance(refs,list) and not set(refs).intersection(objective.get('source_ids',[])):
                errors.append(issue('CONTEXT_DECISION_SOURCE_MISMATCH',prefix,'Nguồn quyết định không thuộc LO.'))
            if objective.get('priority') in CORE and d.get('action') == 'omit_with_reason':
                errors.append(issue('CORE_CONTEXT_OMISSION',prefix,'Không bỏ P0/P1 chỉ vì muốn văn bản ngắn; phải chuyển sang review/scope conflict.'))
    for lid,o in objective_map.items():
        if o.get('priority') in CORE and lid not in covered:
            errors.append(issue('CORE_CONTEXT_DECISION_MISSING','context.decisions',f'LO trọng tâm {lid} không có quyết định dạy và đánh giá theo ngữ cảnh.'))
    if isinstance(handoff,Mapping):
        fp=handoff.get('context_fingerprint')
        if fp != context_fingerprint(context):
            errors.append(issue('HANDOFF_CONTEXT_DRIFT','handoff.context_fingerprint','Bản giao việc khác bối cảnh đã chốt.'))
        if handoff.get('purpose') != context.get('goal'):
            errors.append(issue('HANDOFF_PURPOSE_DRIFT','handoff.purpose','Mục đích bị đổi khi bàn giao.'))
    # A valid structure is NOT proof the decisions are pedagogically justified.
    if not errors:
        warnings.append(issue('CONTEXT_SEMANTICS_REVIEW_REQUIRED','context','Cần so sánh cặp tình huống và đánh giá sản phẩm thực; metadata không chứng minh hiểu bối cảnh.'))
    return {'version':VERSION, 'status':'BLOCKED' if errors else 'STRUCTURE_PASS_CONTEXT_REVIEW_REQUIRED',
            'context_fingerprint':context_fingerprint(context), 'semantic_validated':False,
            'release_allowed':False, 'errors':errors, 'warnings':warnings}


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description='Check context contract consistency, NOT medical meaning.')
    parser.add_argument('--input',required=True,help='A JSON file containing context/profile/sources/objectives/inventory.')
    parser.add_argument('--out')
    args=parser.parse_args()
    data=json.loads(Path(args.input).read_text(encoding='utf-8'))
    report=audit_context(data.get('context'),profile=data.get('profile'),
                         source_ids=[x.get('id') for x in data.get('sources',[]) if isinstance(x,dict)],
                         objectives=data.get('objectives',[]),inventory=data.get('inventory',[]),
                         handoff=data.get('handoff'))
    output=json.dumps(report,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).write_text(output,encoding='utf-8')
    print(output)
    raise SystemExit(2 if report['status']=='BLOCKED' else 0)
