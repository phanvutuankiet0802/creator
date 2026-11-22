#!/usr/bin/env python3
"""Source-anchored triage of teaching order and case-dependence for real artifacts.

Conservative by design: returns review candidates, never proof of a medical or
pedagogical fault. Historical/definition content is NEVER globally forbidden.
No framework, network access or separate agent is required.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Any


def _norm(t: str) -> str:
    x = unicodedata.normalize('NFD', str(t).casefold()).replace('đ','d')
    x = ''.join(c for c in x if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', x).strip()


def _clean_html(text: str) -> str:
    from html import unescape
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]*>', ' ', str(text)))).strip()


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_priority_plan(plan: dict[str, Any], source_dir: str | Path) -> dict[str, Any]:
    """Reject unsourced LO labels; passing does not validate LO priority semantics."""
    base=Path(source_dir).resolve()
    issues=[]
    evidence=[]
    objs=plan.get('objectives',[])
    if not isinstance(objs,list) or not objs:
        issues.append('EMPTY_OBJECTIVE_PLAN')
        objs=[]
    # Verify every selected source, not only sources cited by the draft objectives.
    selected=plan.get('selected_sources',[])
    if not isinstance(selected,list) or not selected:
        issues.append('SELECTED_SOURCE_REGISTER_MISSING')
    else:
        listed=set()
        for i,record in enumerate(selected):
            if not isinstance(record,dict):
                issues.append(f'SELECTED_SOURCE_INVALID:{i}');continue
            fname=record.get('file')
            if not isinstance(fname,str) or Path(fname).is_absolute() or '..' in Path(fname).parts:
                issues.append(f'SELECTED_SOURCE_PATH_INVALID:{i}');continue
            path=(base/fname).resolve()
            if not path.is_relative_to(base) or not path.is_file():
                issues.append(f'SELECTED_SOURCE_MISSING:{i}');continue
            if fname in listed:issues.append(f'SELECTED_SOURCE_DUPLICATE:{fname}')
            listed.add(fname)
            if _sha(path)!=record.get('sha256'):issues.append(f'SELECTED_SOURCE_HASH_MISMATCH:{fname}')
    seen=set()
    for i,o in enumerate(objs):
        if not isinstance(o,dict):
            issues.append(f'OBJECTIVE_NOT_OBJECT:{i}');continue
        oid=o.get('id')
        if not oid or oid in seen:issues.append(f'OBJECTIVE_ID_INVALID:{i}')
        seen.add(oid)
        if o.get('priority') not in {'P0','P1','P2','P3','P4'}:
            issues.append(f'PRIORITY_INVALID:{oid}')
        if not str(o.get('rationale','')).strip():issues.append(f'REASON_MISSING:{oid}')
        fname=o.get('source_file')
        if not isinstance(fname,str) or not fname or Path(fname).is_absolute() or '..' in Path(fname).parts:
            issues.append(f'SOURCE_PATH_INVALID:{oid}');continue
        src=(base/fname).resolve()
        if not src.is_relative_to(base) or not src.is_file():
            issues.append(f'SOURCE_MISSING:{oid}');continue
        raw=src.read_text(encoding='utf-8')
        digest=_sha(src)
        if digest != o.get('source_sha256'):
            issues.append(f'SOURCE_HASH_MISMATCH:{oid}');continue
        quote=_norm(str(o.get('source_quote','')))
        if len(quote)<15 or quote not in _norm(raw):
            issues.append(f'QUOTE_NOT_IN_SOURCE:{oid}');continue
        evidence.append({'objective':oid,'source_file':fname,'source_sha256':digest,
                         'quote_verified':True,'declared_priority':o.get('priority')})
    return {'status':'BLOCKED' if issues else 'STRUCTURE_PASS_SEMANTIC_REVIEW_REQUIRED',
            'issues':issues,'evidence':evidence,'objective_count':len(objs),
            'priority_correctness_verified':False}


RECALL_LEAD_IN = re.compile(
    r'(?:\bmoc thoi gian\b|\bbao nhieu\b|\bchiem ty le\b|\bty le bao\b|\bnam nao\b|'
    r'\bduoc dinh nghia\b|\bkhai niem\b|\bnguoi dau tien\b|\bnam \d{4}\b)')


def case_lead_in(question: str) -> str:
    """Extract last interrogative sentence as an ablation prompt, not a semantic verdict."""
    question=re.sub(r'\s+',' ',str(question)).strip()
    # Typical vignette has multiple declarative sentences then the lead-in.
    parts=re.split(r'(?<=[.!?])\s+',question)
    tail=parts[-1].strip() if len(parts)>1 else question
    return tail


def audit_case_dependence_candidates(questions: list[dict[str,Any]], *, min_case_chars: int=350) -> dict[str, Any]:
    candidates=[]
    for i,q in enumerate(questions):
        if not isinstance(q,dict):continue
        full=str(q.get('question') or q.get('stem') or '')
        lead=case_lead_in(full)
        n=_norm(lead)
        if len(full)>=min_case_chars and RECALL_LEAD_IN.search(n):
            candidates.append({
                'id':q.get('id',i+1),'reason':'LONG_CASE_WITH_RECALL_STYLE_LEAD_IN',
                'full_stem':full,'lead_in_without_case':lead,
                'options':q.get('options',[]),
                'review_instructions':'First answer the isolated lead-in using only options. Then compare with full case; note whether patient data changed the reasoning. Independent subject review required.',
                'finding':'ABLATION_REVIEW_REQUIRED',
            })
    return {'count':len(candidates),'candidate_ids':[x['id'] for x in candidates],
            'candidates':candidates,
            'semantic_case_dependency_verified':False,
            'note':'Keyword candidate detector; not an automatic difficulty/quality verdict.'}


def audit_teaching_sequence(lecture_pdf: str|Path, cards: list[dict[str,Any]], plan: dict[str,Any],
                            *, sample_first_cards: int=8) -> dict[str,Any]:
    """Measure early placement of *plan-declared* peripheral categories only.

    The user may explicitly prioritize history in some subjects; the plan controls
    the category set. No fixed cross-specialty quota is enforced.
    """
    try:
        import fitz
        with fitz.open(str(lecture_pdf)) as pdf:
            page_count=len(pdf)
            page1=pdf[0].get_text() if page_count else ''
    except ImportError:
        import pypdfium2 as pdfium
        doc=pdfium.PdfDocument(str(lecture_pdf))
        page_count=len(doc)
        page1=doc[0].get_textpage().get_text_range() if page_count else ''
        doc.close()
    peripheral={_norm(x) for x in plan.get('peripheral_categories_for_this_lesson',[])}
    first=cards[:sample_first_cards]
    candidate=[{'id':c.get('id',i+1),'category':c.get('type','')}
               for i,c in enumerate(first) if _norm(c.get('type','')) in peripheral]
    first_heading=''
    for line in page1.splitlines():
        if re.match(r'^\s*(?:\d+[.)]|I[.)])\s+',line):first_heading=line.strip();break
    heading= _norm(first_heading)
    heads_history=bool(peripheral.intersection({'lich su','history'}) and 'lich su' in heading)
    return {'pdf_pages':page_count,'pdf_first_heading':first_heading,
            'first_page_peripheral_heading':heads_history,
            'first_cards_checked':len(first),'first_cards_peripheral':candidate,
            'issues':([{'code':'FIRST_PAGE_PERIPHERAL_TOPIC','review':'Review ordering; source objective may still require concise coverage.'}] if heads_history else []) +
                     ([{'code':'EARLY_PERIPHERAL_FLASHCARDS','card_ids':[x['id'] for x in candidate],
                        'review':'Compare with P0/P1 priorities and user intent; do not auto-delete.'}] if candidate else []),
            'academic_priority_verified':False}


def run_review(source_dir: str|Path, priority_plan: dict[str,Any], lecture_pdf: str|Path,
               flashcards: list[dict[str,Any]], mcqs: list[dict[str,Any]]) -> dict[str,Any]:
    v=verify_priority_plan(priority_plan,source_dir)
    if v['issues']:
        return {'status':'BLOCKED','source_plan':v,'case_ablation':None,'teaching_sequence':None}
    cases=audit_case_dependence_candidates(mcqs)
    sequence=audit_teaching_sequence(lecture_pdf,flashcards,priority_plan)
    return {'status':'REVIEW_REQUIRED','source_plan':v,'case_ablation':cases,
            'teaching_sequence':sequence,'semantic_academic_approval':False}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-dir',required=True)
    ap.add_argument('--priority-plan',required=True)
    ap.add_argument('--lecture-pdf',required=True)
    ap.add_argument('--flashcards-json',required=True)
    ap.add_argument('--mcq-json',required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    data=run_review(args.source_dir,json.loads(Path(args.priority_plan).read_text()),
                    args.lecture_pdf,json.loads(Path(args.flashcards_json).read_text()),
                    json.loads(Path(args.mcq_json).read_text()))
    Path(args.out).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(data['status'],data['source_plan']['objective_count'],
          data['case_ablation']['count'] if data['case_ablation'] else 'BLOCKED')
    raise SystemExit(2 if data['status']=='BLOCKED' else 0)


if __name__=='__main__':main()
