"""Source-byte anchored visual-claim triage for image-only lesson PDFs.

A valid observation list is not an OCR result, medical approval, or evidence
that a lesson was fully covered. Review still has to happen independently.
"""
from __future__ import annotations
import argparse, hashlib, io, json, zipfile
from pathlib import Path

RISK={'LOW','MEDIUM','HIGH','CRITICAL'}
MODES={'FULL_RESOLUTION','CONTACT_SHEET'}

def assess(register:dict, archive:Path, source_markdown:Path|None=None)->dict:
    errors=[];pending=[];seen=set();high=[]
    member=register.get('source_member')
    if not isinstance(member,str) or not member.lower().endswith('.pdf'):
        errors.append('INVALID_SOURCE_MEMBER')
    try:
        archive_bytes=Path(archive).read_bytes()
        if register.get('source_archive_sha256')!=hashlib.sha256(archive_bytes).hexdigest():
            errors.append('ARCHIVE_HASH_MISMATCH')
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
            if any(i.filename==member for i in z.infolist()):raw=z.read(member)
            else:raw=None;errors.append('SOURCE_PDF_MISSING')
    except (OSError,ValueError,zipfile.BadZipFile):
        raw=None;errors.append('ARCHIVE_UNREADABLE')
    if raw is not None and register.get('source_member_sha256')!=hashlib.sha256(raw).hexdigest():
        errors.append('SOURCE_MEMBER_HASH_MISMATCH')
    pdfium=None
    try:import fitz
    except ImportError:
        fitz=None
        try:import pypdfium2 as pdfium
        except ImportError:errors.append('PDF_RENDER_BACKEND_MISSING')
    pdf=None
    if (fitz is not None or pdfium is not None) and raw is not None:
        try:pdf=fitz.open(stream=raw,filetype='pdf') if fitz is not None else pdfium.PdfDocument(raw)
        except Exception:errors.append('SOURCE_PDF_INVALID')
    pages=register.get('pages')
    if not isinstance(pages,list):pages=[];errors.append('INVALID_PAGE_REGISTER')
    if pdf is not None and register.get('pages_expected')!=len(pdf):errors.append('PDF_PAGE_COUNT_MISMATCH')
    for p in pages:
        if not isinstance(p,dict):errors.append('PAGE_NOT_OBJECT');continue
        n=p.get('page')
        if type(n) is not int or n in seen or n<1 or (pdf is not None and n>len(pdf)):
            errors.append(f'PAGE_ID_INVALID_OR_DUPLICATE:{n}');continue
        seen.add(n)
        if p.get('inspected_via') not in MODES:errors.append(f'INVALID_INSPECTION_MODE:{n}')
        if p.get('risk_level') not in RISK:errors.append(f'INVALID_RISK:{n}')
        if p.get('risk_level') in {'HIGH','CRITICAL'}:high.append(n)
        for field in ('topic','visible_claim_excerpt_transcribed','review_question'):
            if not isinstance(p.get(field),str) or len(p[field].strip())<8:
                errors.append(f'INSUFFICIENT_VISUAL_OBSERVATION:{n}:{field}')
        if p.get('claim_clinically_verified') or not p.get('requires_independent_review',True):
            errors.append(f'UNTRUSTED_VISUAL_APPROVAL:{n}')
        if pdf is not None and fitz is not None:
            pg=pdf[n-1];pix=pg.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
            if p.get('render_pixel_sha256')!=hashlib.sha256(pix.samples).hexdigest() or p.get('render_dimensions')!=[pix.width,pix.height]:
                errors.append(f'RENDER_PIXEL_MISMATCH:{n}')
        elif pdf is not None and pdfium is not None:
            pg=pdf[n-1];pil_im=pg.render(scale=1.0).to_pil().convert('RGB')
            if p.get('render_dimensions') and p.get('render_dimensions')!=[pil_im.width,pil_im.height]:
                errors.append(f'RENDER_PIXEL_MISMATCH:{n}')
    if pdf is not None and set(range(1,len(pdf)+1))!=seen:errors.append('IMAGE_ONLY_PAGES_NOT_EXHAUSTIVELY_REGISTERED')
    # Cross-source contradiction audit: two incompatible absolutes cannot be
    # adjudicated by the PDF's generic EBM badge or by manuscript order.
    for conflict in register.get('observed_cross_source_conflicts', []):
        if not isinstance(conflict,dict):errors.append('INVALID_CONFLICT_RECORD');continue
        n=conflict.get('image_pdf_page')
        if n not in seen:errors.append('CONFLICT_IMAGE_PAGE_NOT_REGISTERED')
        if conflict.get('clinical_review')!='AWAITING_REVIEW':
            errors.append('UNTRUSTED_CONFLICT_ADJUDICATION')
        if not isinstance(conflict.get('line_quote'),str) or len(conflict['line_quote'])<12:
            errors.append('UNANCHORED_CONFLICT_QUOTE')
        if source_markdown is None:
            pending.append('CONFLICT_TEXT_SOURCE_NOT_RECHECKED')
        else:
            try:
                mb=Path(source_markdown).read_bytes()
                if hashlib.sha256(mb).hexdigest()!=conflict.get('source_markdown_sha256'):
                    errors.append('CONFLICT_SOURCE_MARKDOWN_HASH_MISMATCH')
                source_lines=mb.decode('utf-8').splitlines()
                i=conflict.get('line_number')
                if type(i) is not int or i<1 or i>len(source_lines) or source_lines[i-1]!=conflict.get('line_quote'):
                    errors.append('CONFLICT_MARKDOWN_QUOTE_NOT_AT_ANCHORED_LINE')
            except (OSError,UnicodeError):errors.append('CONFLICT_MARKDOWN_SOURCE_UNREADABLE')
        pending.append('CONFLICT_NOT_CLINICALLY_ADJUDICATED:'+str(conflict.get('case_id','unknown')))
    if register.get('all_pages_medically_approved') or register.get('authoritative_for_clinical_decisions'):
        errors.append('UNTRUSTED_DOCUMENT_WIDE_APPROVAL')
    if register.get('scope')!='ADDITIONAL_SOURCE_SCOPE_UNCONFIRMED_NOT_PROMOTED_TO_PRIMARY':
        pending.append('SOURCE_SCOPE_REQUIRES_USER_CONTEXT_OR_INDEPENDENT_RECORD')
    else:pending.append('ADDITIONAL_PDF_SCOPE_UNCONFIRMED')
    pending.extend(f'VISUAL_CLAIM_UNVERIFIED_PAGE:{n}' for n in high)
    pending.append('INDEPENDENT_CLINICAL_REVIEW_REQUIRED')
    pending.append('OTHER_ORIGINAL_PDF_PAGES_NOT_CERTIFIED_BY_THIS_REGISTER')
    return {'status':'BLOCKED_INTEGRITY' if errors else 'HOLD_FOR_VISUAL_CLAIM_REVIEW',
      'technical_valid':not errors,'release_allowed':False,'medical_approved':False,
      'pages_registered':len(seen),'pages_full_resolution':sum(p.get('inspected_via')=='FULL_RESOLUTION' for p in pages if isinstance(p,dict)),
      'high_risk_pages':high,'integrity_errors':sorted(set(errors)),'pending_reviews':pending}

def main():
 p=argparse.ArgumentParser();p.add_argument('register_json');p.add_argument('--source-archive',required=True)
 p.add_argument('--output');p.add_argument('--source-markdown');a=p.parse_args()
 res=assess(json.loads(Path(a.register_json).read_text(encoding='utf-8')),Path(a.source_archive),Path(a.source_markdown) if a.source_markdown else None)
 output=json.dumps(res,ensure_ascii=False,indent=2)
 if a.output:Path(a.output).write_text(output,encoding='utf-8')
 print(output)
 return 2 if res['integrity_errors'] else 0
if __name__=='__main__':raise SystemExit(main())
