"""Independent technical gate for ALI guideline triage and original-PDF figure coverage.

This tool never substitutes an automated decision for clinical peer review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

ALLOWED_SIGNALS = {'DIRECT_CONFLICT','DIRECT_SUPPORT','CONTEXTUAL','NEEDS_SPECIFIC_PROTOCOL', 'NEEDS_SPECIFIC_CONTEXT','DIRECT_SUPPORT_WITH_LIMITS','UNVERIFIED_GENERALIZATION','NOT_CLINICALLY_VERIFIED'}

def assess(claims: dict[str, Any], visuals: dict[str, Any], source_zip: Path) -> dict[str, Any]:
    errors: list[str] = []
    pending: list[str] = []
    registry = claims.get('claims')
    sources = claims.get('sources', {})
    if not isinstance(registry, list) or not registry:
        errors.append('EMPTY_CLAIM_REVIEW_REGISTER')
        registry = []
    seen = set()
    for item in registry:
        if not isinstance(item, dict):
            errors.append('CLAIM_NOT_OBJECT');continue
        oid=item.get('objective')
        if not isinstance(oid,str) or not oid or oid in seen:
            errors.append('CLAIM_ID_DUPLICATE_OR_INVALID');continue
        seen.add(oid)
        if item.get('external_evidence_signal') not in ALLOWED_SIGNALS:
            errors.append(f'UNDEFINED_EVIDENCE_SIGNAL:{oid}')
        for key in item.get('reference_keys',[]):
            if key not in sources:
                errors.append(f'UNKNOWN_REFERENCE:{oid}:{key}')
        if item.get('manual_clinician_review_verified') or item.get('review_status') == 'APPROVED':
            # These fields live in untrusted JSON; there is no independently verified identity.
            errors.append(f'UNTRUSTED_MEDICAL_SELF_CERTIFICATION:{oid}')
        if item.get('source_review_status') != 'AWAITING_REVIEW':
            pending.append(f'UNRECONCILED_REVIEW_STATUS:{oid}')
        if item.get('triage_decision') not in {'NEEDS_CLINICAL_ADJUDICATION','PENDING_PROTOCOL_AND_CLINICAL_REVIEW','PENDING_EXPERT_REVIEW','PENDING_ORIGINAL_STUDY','PENDING_HISTORICAL_SOURCE'}:
            errors.append(f'INVALID_TRIAGE_DECISION:{oid}')
        pending.append(f'UNRESOLVED_CLINICAL_OR_HISTORICAL_CLAIM:{oid}')
    if claims.get('release_allowed') or claims.get('reviewer_identity_verified'):
        errors.append('UNTRUSTED_RELEASE_ASSERTION')
    # Reinspect original PDF bytes, not merely the authored manifest counts.
    pdfium = None
    try:
        import fitz  # PyMuPDF; optional dependency for the actual PDF review operation.
    except ImportError:
        fitz = None
        try:
            import pypdfium2 as pdfium
        except ImportError:
            errors.append('PDF_PAGE_INSPECTION_BACKEND_UNAVAILABLE')
    recorded=visuals.get('files')
    if not isinstance(recorded,list) or not recorded:
        errors.append('NO_PDF_SOURCE_MANIFEST');recorded=[]
    try:
        with zipfile.ZipFile(source_zip) as z:
            raw_archives={i.filename:z.read(i) for i in z.infolist() if not i.is_dir()}
            archive={name:hashlib.sha256(raw).hexdigest() for name,raw in raw_archives.items()}
    except (OSError,zipfile.BadZipFile):
        errors.append('SOURCE_ARCHIVE_UNAVAILABLE');archive={};raw_archives={}
    declared=set()
    visual_count=0
    for rec in recorded:
        if not isinstance(rec,dict):errors.append('INVALID_PDF_SOURCE_ITEM');continue
        name=rec.get('filename')
        if not isinstance(name,str) or name in declared:
            errors.append('DUPLICATE_PDF_SOURCE');continue
        declared.add(name)
        if archive.get(name)!=rec.get('sha256'):
            errors.append(f'SOURCE_PDF_BYTES_MISMATCH:{name}')
        pages=rec.get('pages_manifest')
        if not isinstance(pages,list) or len(pages)!=rec.get('pages'):
            errors.append(f'PAGE_MANIFEST_INCOMPLETE:{name}')
            continue
        # A forged page-by-page manifest must not pass solely by matching archive hash.
        raw=raw_archives.get(name)
        if (fitz is not None or pdfium is not None) and raw is not None:
            try:
                if fitz is not None:
                    pdf=fitz.open(stream=raw,filetype='pdf')
                    if len(pdf)!=rec.get('pages'):
                        errors.append(f'PDF_PAGE_COUNT_MISMATCH:{name}')
                    for n,p in enumerate(pages,1):
                        if n > len(pdf):break
                        pg=pdf[n-1]
                        actual_text=len(pg.get_text())
                        actual_images=len(pg.get_images(full=True))
                        actual_flag=actual_images>0 or len(pg.get_text().strip())<100
                        if (p.get('chars_from_pdf_text') != actual_text or
                            p.get('embedded_images') != actual_images or
                            p.get('needs_visual_review') != actual_flag):
                            errors.append(f'PDF_PAGE_METADATA_MISMATCH:{name}:{n}')
                else:
                    pdf=pdfium.PdfDocument(raw)
                    if len(pdf)!=rec.get('pages'):
                        errors.append(f'PDF_PAGE_COUNT_MISMATCH:{name}')
                    pdf.close()
            except (ValueError, RuntimeError, TypeError) as exc:
                errors.append(f'INVALID_PDF_BYTES:{name}:{type(exc).__name__}')
        for n,p in enumerate(pages,1):
            if not isinstance(p,dict) or p.get('page')!=n or not isinstance(p.get('embedded_images'),int) or not isinstance(p.get('chars_from_pdf_text'),int):
                errors.append(f'INVALID_PAGE_ENTRY:{name}:{n}');continue
            if p.get('needs_visual_review'):
                visual_count+=1
        if rec.get('scope','').startswith('PENDING'):
            pending.append(f'ADDITIONAL_PDF_SCOPE_UNRESOLVED:{name}')
    for filename in archive:
        if filename.lower().endswith('.pdf') and filename not in declared:
            errors.append(f'PDF_MISSING_FROM_MANIFEST:{filename}')
    if not visuals.get('all_sources_exhaustively_reviewed'):
        pending.append('ORIGINAL_PDF_FIGURES_NOT_FULLY_REVIEWED')
    # We cannot trust an editable manifest as an independent reviewer approval.
    if visuals.get('all_sources_exhaustively_reviewed'):
        pending.append('VISUAL_APPROVAL_NOT_INDEPENDENTLY_VERIFIED')
    return {'status':'BLOCKED_INTEGRITY' if errors else 'HOLD_FOR_CLINICAL_AND_VISUAL_REVIEW',
            'technical_valid':not errors,'medical_approved':False,'release_allowed':False,
            'claim_count':len(registry),'original_pdfs':len(recorded),
            'visual_review_page_candidates':visual_count,
            'integrity_errors':sorted(set(errors)),'pending_reviews':sorted(set(pending))}

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('guideline_triage_json');p.add_argument('pdf_visual_manifest_json')
    p.add_argument('--source-archive',required=True);p.add_argument('--output')
    a=p.parse_args()
    result=assess(json.loads(Path(a.guideline_triage_json).read_text(encoding='utf-8')),
                  json.loads(Path(a.pdf_visual_manifest_json).read_text(encoding='utf-8')),
                  Path(a.source_archive))
    payload=json.dumps(result,ensure_ascii=False,indent=2)
    if a.output: Path(a.output).write_text(payload,encoding='utf-8')
    print(payload)
    return 2 if result['integrity_errors'] else 0
if __name__=='__main__':raise SystemExit(main())
