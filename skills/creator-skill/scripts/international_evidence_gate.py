#!/usr/bin/env python3
"""Conservative evidence reconciliation: source and external snapshots, no autonomous medical approval.

Offline verifier checks integrity and red flags; a verified excerpt is NOT proof of clinical correctness.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _safe_file(root: Path, name: Any) -> Path | None:
    if not isinstance(name, str) or not name or Path(name).is_absolute() or '..' in Path(name).parts:
        return None
    p=(root/name).resolve()
    return p if p.is_relative_to(root) and p.is_file() else None


def _verified_quote(data: str, quote: Any) -> bool:
    # Literal quotes, NOT loose keyword matching. Exact record protects provenance, not truth.
    return isinstance(quote, str) and len(quote.strip())>=12 and quote in data


def assess(profile: dict[str, Any], root: str | Path) -> dict[str, Any]:
    root=Path(root).resolve()
    problems=[]; review=[]; evidence=[]
    src_list=profile.get('sources')
    if not isinstance(src_list,list) or not src_list: problems.append('SOURCE_REGISTER_EMPTY');src_list=[]
    srcmap={}
    for row in src_list:
        sid=row.get('id') if isinstance(row,dict) else None
        p=_safe_file(root,row.get('path') if isinstance(row,dict) else None)
        if not sid or sid in srcmap or p is None:
            problems.append(f'INVALID_SOURCE:{sid}');continue
        if sha256(p)!=row.get('sha256'):
            problems.append(f'SOURCE_HASH_MISMATCH:{sid}');continue
        srcmap[sid]=(row,p)
        if row.get('kind')=='vid' and row.get('presenter_role')=='student' and not row.get('faculty_approval_evidence'):
            review.append(f'STUDENT_VID_NO_VERIFIED_APPROVAL:{sid}')
    claims=profile.get('claims')
    if not isinstance(claims,list) or not claims: problems.append('CLAIMS_EMPTY');claims=[]
    claimids=set()
    for c in claims:
        if not isinstance(c,dict):problems.append('CLAIM_INVALID');continue
        cid=c.get('id')
        if not isinstance(cid,str) or not cid or cid in claimids:
            problems.append(f'CLAIM_ID_INVALID:{cid}');continue
        claimids.add(cid)
        sid=c.get('source_id')
        if sid not in srcmap:problems.append(f'CLAIM_SOURCE_MISSING:{cid}');continue
        src,srcpath=srcmap[sid]
        text=srcpath.read_text(encoding='utf-8')
        if not _verified_quote(text,c.get('source_quote')):
            problems.append(f'CLAIM_QUOTE_NOT_IN_SOURCE:{cid}');continue
        if c.get('risk') not in ('critical','high','routine'):
            problems.append(f'CLAIM_RISK_INVALID:{cid}');continue
        if c.get('risk') in ('critical','high') and not str(c.get('context','')).strip():
            review.append(f'CLINICAL_CONTEXT_MISSING:{cid}')
        ex=c.get('external_evidence',[])
        if not isinstance(ex,list):problems.append(f'EXTERNAL_REGISTER_INVALID:{cid}');continue
        if c.get('risk') in ('critical','high') and not ex:
            review.append(f'HIGH_RISK_WITHOUT_EXTERNAL_EVIDENCE:{cid}')
        valid_evidence_count=0
        for i,e in enumerate(ex):
            if not isinstance(e,dict):problems.append(f'EXTERNAL_ENTRY_INVALID:{cid}:{i}');continue
            p=_safe_file(root,e.get('snapshot_path'))
            if p is None:problems.append(f'EXTERNAL_SNAPSHOT_MISSING:{cid}:{i}');continue
            if sha256(p)!=e.get('sha256'):
                problems.append(f'EXTERNAL_SNAPSHOT_HASH_MISMATCH:{cid}:{i}');continue
            if not _verified_quote(p.read_text(encoding='utf-8'),e.get('quote')):
                problems.append(f'EXTERNAL_QUOTE_NOT_IN_SNAPSHOT:{cid}:{i}');continue
            if not str(e.get('url','')).startswith('https://') or not e.get('title') or not e.get('year'):
                problems.append(f'EXTERNAL_METADATA_INCOMPLETE:{cid}:{i}');continue
            valid_evidence_count+=1
        if valid_evidence_count:
            review.append(f'EXTERNAL_SEMANTIC_ARBITRATION_REQUIRED:{cid}')
        if c.get('conflict_status') in ('contradiction','context_dependent','outdated'):
            review.append(f'CONFLICT_NEEDS_MEDICAL_REVIEW:{cid}')
        if c.get('risk') in ('critical','high') and c.get('release_claim')=='verified':
            problems.append(f'UNTRUSTED_MEDICAL_VERIFICATION:{cid}')
        evidence.append({'claim_id':cid,'source_sha256':sha256(srcpath),'snapshot_count':valid_evidence_count,'clinical_correctness_verified':False})
    if profile.get('pdf_show_citations') is True:problems.append('PDF_PROVENANCE_VISIBLE_CONTRACT_VIOLATION')
    if problems:status='BLOCKED_INTEGRITY'
    else:status='HOLD_FOR_MEDICAL_REVIEW'
    return {'status':status,'integrity_issues':problems,'review_flags':review,
            'evidence':evidence,'medical_certified':False,'source_role_is_global_rank':False,
            'note':'Offline existence, hash and quote checks only. No trust-root clinical adjudication. External snapshot must be acquired legally and independently reviewed.'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('profile');ap.add_argument('--root',required=True);ap.add_argument('--out',required=True)
    a=ap.parse_args();result=assess(json.loads(Path(a.profile).read_text(encoding='utf-8')),a.root)
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(result['status'],len(result['integrity_issues']),len(result['review_flags']))
    return 2 if result['status']=='BLOCKED_INTEGRITY' else 0
if __name__=='__main__':raise SystemExit(main())
