#!/usr/bin/env python3
"""Academic Intelligence preflight v0.1 (stdlib only).

This is a deterministic evidence/coverage gate. It CANNOT classify medical
importance, adjudicate contradictions or certify >90% semantic coverage.
Only user-selected *full* source text can support a source anchor.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Mapping

VERSION = '0.1.0'
DOMAINS = {
  'surgery', 'internal_medicine', 'anatomy', 'physiology', 'pharmacology',
  'microbiology', 'public_health', 'medical_imaging', 'pathology',
  'clinical_skills', 'environmental_medicine', 'family_medicine',
  'occupational_medicine', 'epidemiology', 'biostatistics', 'preventive_medicine',
  'oncology', 'nursing', 'other'
}
LESSON_TYPES = {
  'foundations', 'concepts', 'mechanisms', 'clinical_diagnosis',
  'clinical_management', 'procedure', 'prevention', 'population_health',
  'research_methods', 'interpretation', 'mixed'
}
PRIORITIES = {'P0','P1','P2','P3','P4'}
ARTIFACTS = {'lecture','flashcard','mcq','meq'}

def issue(code, path, message):
    return {'code': code, 'path': path, 'detail': message}

def normalize(text):
    return ' '.join(unicodedata.normalize('NFC', str(text)).split())

def ascii_words(text):
    s = unicodedata.normalize('NFD', str(text).casefold())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn').replace('đ','d')
    return re.findall(r'[a-z0-9]+', s)

def check_profile(profile: Mapping[str, Any]):
    errors=[]
    if not isinstance(profile, Mapping): return [issue('PROFILE_MISSING','profile','Thiếu hồ sơ phân loại môn và bài.')]
    domains=profile.get('domains', [])
    if not isinstance(domains, list) or not domains or any(x not in DOMAINS for x in domains):
        errors.append(issue('BAD_SUBJECT_PROFILE','profile.domains','Cần domain hợp lệ; có thể đa nhãn.'))
    if profile.get('lesson_type') not in LESSON_TYPES:
        errors.append(issue('BAD_LESSON_TYPE','profile.lesson_type','Thiếu bản chất bài học hợp lệ.'))
    if not normalize(profile.get('classification_reason','')) or len(normalize(profile.get('classification_reason',''))) < 25:
        errors.append(issue('MISSING_CLASSIFICATION_REASON','profile.classification_reason','Phải giải thích bằng mục tiêu của chính bài học.'))
    return errors

def detect_polarity_conflict(quote, assertion):
    """Only an *advisory* alarm for a conspicuous opposed phrase, NOT NLI."""
    q=' '.join(ascii_words(quote)); a=' '.join(ascii_words(assertion))
    wordsq=set(q.split()); wordsa=set(a.split())
    if len((wordsq & wordsa) - {'la','co','duoc','va','trong','khi','can','cho','cua'}) < 3:
        return False
    pairs=[('chong chi dinh','chi dinh'),('khong nen','nen'),('khong duoc','duoc'),('khong can','can')]
    for negative,positive in pairs:
        if negative in q and negative not in a and positive in a:
            return True
        if negative in a and negative not in q and positive in q:
            return True
    return False

def audit_preflight(payload: Mapping[str, Any]) -> dict:
    errors=[]; warnings=[]
    errors+=check_profile(payload.get('profile'))
    sources=payload.get('sources', [])
    inventory=payload.get('inventory', [])
    objectives=payload.get('objectives', [])
    if not isinstance(sources,list) or not sources:
        errors.append(issue('NO_SOURCES','sources','Cần danh sách nguồn được chọn.')); sources=[]
    if not isinstance(inventory,list) or not inventory:
        errors.append(issue('NO_CONCEPT_INVENTORY','inventory','Chưa lập inventory ý chính từ toàn văn nguồn.')); inventory=[]
    if not isinstance(objectives,list) or not objectives:
        errors.append(issue('NO_OBJECTIVES','objectives','Chưa có mục tiêu học tập.')); objectives=[]
    src={}; seen_src=set()
    for i,s in enumerate(sources):
        if not isinstance(s,dict):errors.append(issue('BAD_SOURCE',f'sources[{i}]','Nguồn không phải object.'));continue
        sid=s.get('id'); text=s.get('full_text')
        if not isinstance(sid,str) or not sid or sid in seen_src: errors.append(issue('BAD_SOURCE_ID',f'sources[{i}]','Source ID rỗng hoặc trùng.'));continue
        seen_src.add(sid)
        if not isinstance(text,str) or not text.strip():
            errors.append(issue('MISSING_FULL_SOURCE_TEXT',f'sources[{i}]','Không có full-text thực; UUID không phải nội dung nguồn.')); continue
        actual=hashlib.sha256(text.encode('utf-8')).hexdigest()
        if s.get('sha256') != actual:
            errors.append(issue('SOURCE_HASH_MISMATCH',f'sources[{i}]','Hash nguồn không khớp full-text.'))
        if s.get('read_complete') is not True:
            errors.append(issue('FULL_READ_UNCONFIRMED',f'sources[{i}]','Chưa xác nhận đã đọc toàn nguồn.'))
        src[sid]=text
    lo={}
    for i,o in enumerate(objectives):
        if not isinstance(o,dict) or not o.get('id') or o['id'] in lo:
            errors.append(issue('BAD_OBJECTIVE_ID',f'objectives[{i}]','LO trùng, thiếu ID hoặc sai kiểu.'));continue
        lo[o['id']]=o
        if not normalize(o.get('statement','')) or len(normalize(o.get('statement',''))) < 14:
            errors.append(issue('OBJECTIVE_STATEMENT_MISSING',f'objectives[{i}]','LO cần phát biểu mục tiêu cụ thể.'))
        if o.get('priority') not in PRIORITIES: errors.append(issue('BAD_PRIORITY',f'objectives[{i}]','Thiếu P0–P4.'))
        if not normalize(o.get('priority_rationale')) or len(normalize(o.get('priority_rationale'))) < 20:
            errors.append(issue('MISSING_PRIORITY_RATIONALE',f'objectives[{i}]','Cần biện minh ưu tiên theo bài.'))
        if o.get('priority') in {'P0','P1'} and not normalize(o.get('risk_if_missed')):
            errors.append(issue('MISSING_IMPACT_IF_OMITTED',f'objectives[{i}]','Chưa giải thích hậu quả bỏ sót ý trọng tâm.'))
        if not o.get('source_ids') or any(s not in src for s in o.get('source_ids',[])):
            errors.append(issue('OBJECTIVE_SOURCE_GAP',f'objectives[{i}]','LO không được neo vào nguồn đã đọc.'))
        plan=o.get('artifact_plan',[])
        if o.get('priority') in {'P0','P1'}:
            if not isinstance(plan,list) or not plan or any(kind not in ARTIFACTS for kind in plan):
                errors.append(issue('MISSING_ARTIFACT_PLAN',f'objectives[{i}]','LO trọng tâm cần kế hoạch xuất sản phẩm hợp lệ.'))
            elif payload.get('delivery_profile')=='quad_pack' and ('lecture' not in plan or 'flashcard' not in plan):
                errors.append(issue('CORE_LECTURE_FLASHCARD_GAP',f'objectives[{i}]','P0/P1 phải được dự kiến trình bày trong lecture và flashcard.'))
    concepts={}; total=0; mapped=0; unmapped=[]
    for i,c in enumerate(inventory):
        p=f'inventory[{i}]'
        if not isinstance(c,dict):errors.append(issue('BAD_CONCEPT',p,'Ý nguồn không phải object.')); continue
        cid=c.get('id'); sid=c.get('source_id'); quote=c.get('quote','')
        if not isinstance(cid,str) or not cid or cid in concepts:
            errors.append(issue('DUPLICATE_CONCEPT',p,'Mỗi ý nguồn cần ID duy nhất.'));continue
        concepts[cid]=c
        if sid not in src: errors.append(issue('UNKNOWN_CONCEPT_SOURCE',p,'Nguồn không tồn tại/không có full-text.'))
        elif not isinstance(quote,str) or len(normalize(quote)) < 12 or normalize(quote) not in normalize(src[sid]):
            errors.append(issue('EVIDENCE_QUOTE_NOT_IN_SOURCE',p,'Trích dẫn không khớp nguyên văn nguồn.'))
        if not normalize(c.get('source_location','')):
            errors.append(issue('NO_SOURCE_LOCATION',p,'Thiếu vị trí nguồn (mục/trang/đoạn).'))
        priority=c.get('priority')
        if priority not in PRIORITIES: errors.append(issue('BAD_CONCEPT_PRIORITY',p,'Thiếu mức ưu tiên.'))
        if priority in {'P0','P1'}:
            total+=1
            links=c.get('objective_ids',[])
            if isinstance(links,list) and links and all(x in lo for x in links):
                mapped+=1
                for lid in links:
                    if sid not in lo[lid].get('source_ids',[]):
                        errors.append(issue('CONCEPT_OBJECTIVE_SOURCE_DRIFT',p,f'{cid} từ {sid} neo tới {lid} nhưng LO không ghi nguồn này.'))
                    if lo[lid].get('priority') not in {'P0','P1'}:
                        errors.append(issue('CORE_PRIORITY_LAUNDERING',p,f'{cid} là P0/P1 nhưng LO {lid} bị xếp P2-P4.'))
                    assertion=lo[lid].get('statement','')
                    if detect_polarity_conflict(quote,assertion):
                        warnings.append(issue('POSSIBLE_POLARITY_CONTRADICTION',p,f'Ý {cid} có thể đảo khẳng định/phủ định so với {lid}; cần chuyên gia đối chiếu.'))
            else:
                unmapped.append(cid)
    missing_source_inventory=sorted(set(src)-{c.get('source_id') for c in concepts.values() if isinstance(c,dict)})
    if missing_source_inventory:
        errors.append(issue('SELECTED_SOURCE_NOT_IN_INVENTORY','inventory',f'Các nguồn được chọn không có ý nào trong inventory: {missing_source_inventory}.'))
    if total == 0:
        errors.append(issue('EMPTY_CORE_INVENTORY','inventory','Không có ý P0/P1 để kiểm định; phải xác nhận độc lập phạm vi.'))
    coverage=round(mapped/total,4) if total else None
    if total and coverage < .90:
        errors.append(issue('CORE_COVERAGE_BELOW_90','inventory',f'Liên kết LO cho ý P0/P1 mới đạt {coverage:.1%}; thiếu {unmapped}.'))
    # Notes: even a 100% match only means all DECLARED concepts have LO links.
    if payload.get('delivery_profile')=='quad_pack':
        plans={kind for o in lo.values() if o.get('priority') in {'P0','P1'} for kind in o.get('artifact_plan',[]) if isinstance(kind,str)}
        if ARTIFACTS-plans:
            errors.append(issue('QUAD_CORE_ASSESSMENT_PLAN_GAP','objectives',f'Chưa gán P0/P1 cho các loại sản phẩm: {sorted(ARTIFACTS-plans)}.'))
    if payload.get('inventory_scope_reviewed') is not True:
        errors.append(issue('INVENTORY_SCOPE_UNREVIEWED','inventory_scope_reviewed','Chưa chứng minh inventory đã lấy đủ ý nguồn.'))
    if not any(o.get('priority') == 'P0' for o in lo.values()):
        warnings.append(issue('NO_P0_CHECK_REQUIRED','objectives','Không phát hiện P0: cần phê duyệt chuyên môn, không tự nâng điểm.'))
    # Context Intelligence: user/discipline/goal constraints must be explicitly
    # traceable. The deterministic gate detects drift, NOT pedagogical truth.
    context_report = None
    if payload.get('context') is not None or payload.get('delivery_profile') == 'quad_pack':
        import importlib.util
        ctx_path = Path(__file__).with_name('context_intelligence.py')
        spec = importlib.util.spec_from_file_location('context_intelligence_local', ctx_path)
        if spec is None or spec.loader is None:
            raise RuntimeError('context_intelligence missing')
        ctx_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ctx_mod)
        context_report = ctx_mod.audit_context(
            payload.get('context'),
            profile=payload.get('profile'),
            source_ids=list(src),
            objectives=objectives,
            inventory=inventory,
            handoff=payload.get('handoff')
        )
        errors.extend(context_report['errors'])
        warnings.extend(context_report['warnings'])
    status='BLOCKED' if errors else 'STRUCTURE_PASS_SEMANTIC_REVIEW_REQUIRED'
    return {'version':VERSION,'status':status,'valid_structure':not errors,
        'semantic_validated':False, 'release_allowed':False,
        'context_intelligence':context_report, 'declared_core_coverage':coverage,'core_total':total,'core_mapped':mapped,
        'unmapped_core_concepts':unmapped,'errors':errors,'warnings':warnings,
        'limitation':'90% chỉ là độ phủ mục tiêu với inventory KHAI BÁO, không chứng minh bao phủ 90% toàn nguồn hoặc điểm thi 9+. Phải thẩm định độc lập tính đầy đủ inventory, tính đúng ngữ nghĩa và chất lượng sản phẩm.'}

def main():
    p=argparse.ArgumentParser(description='Audit academic-source-to-LO preflight; never self-certify release')
    p.add_argument('--input',required=True)
    p.add_argument('--out')
    a=p.parse_args()
    report=audit_preflight(json.loads(Path(a.input).read_text(encoding='utf-8')))
    rendered=json.dumps(report,ensure_ascii=False,indent=2)
    if a.out: Path(a.out).write_text(rendered,encoding='utf-8')
    print(rendered)
    raise SystemExit(2 if report['status']=='BLOCKED' else 0)

if __name__=='__main__':main()
