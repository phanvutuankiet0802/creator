#!/usr/bin/env python3
"""Verify source PDF page anchoring for MCQ pilots. Structural evidence only.

Require a real PDF file, its SHA-256, page index (1-based), and verbatim quote
on THAT page, not an arbitrary quote elsewhere in the document. PDF scanned
pages require human visual review; this module deliberately does NOT OCR them.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path
from typing import Mapping, Sequence


def _norm(s):
    return re.sub(r'\s+', ' ', str(s)).strip().casefold()


def audit_pdf_page_grounding(questions: Sequence[dict], pdf_sources: Mapping[str, str], *, require_all=True) -> dict:
    pymupdf = None
    pdfium = None
    try:
        import pymupdf
    except ImportError:
        try:
            import pypdfium2 as pdfium
        except ImportError as e:
            return {'status':'BLOCKED','errors':[{'code':'PDF_READER_MISSING','detail':str(e)}],
                    'release_allowed':False,'semantic_validated':False}
    errors=[]; docs={}; source_digests={}; page_counts={}
    try:
        for source_id,path in pdf_sources.items():
            p=Path(path)
            if not p.is_file():
                errors.append({'code':'PDF_SOURCE_MISSING','source_id':source_id});continue
            data=p.read_bytes(); source_digests[source_id]=hashlib.sha256(data).hexdigest()
            try:
                if pymupdf is not None:
                    d=pymupdf.open(stream=data,filetype='pdf')
                    docs[source_id]=[_norm(page.get_text('text')) for page in d]
                    page_counts[source_id]=len(d)
                    d.close()
                else:
                    d=pdfium.PdfDocument(data)
                    docs[source_id]=[_norm(d[i].get_textpage().get_text_range()) for i in range(len(d))]
                    page_counts[source_id]=len(d)
                    d.close()
            except Exception as exc:
                errors.append({'code':'PDF_SOURCE_UNREADABLE','source_id':source_id,'detail':str(exc)})
        for index,item in enumerate(questions,1):
            ident=item.get('id',index) if isinstance(item,dict) else index
            anchor=item.get('source_anchor') if isinstance(item,dict) else None
            if not isinstance(anchor,dict):
                errors.append({'code':'PDF_PAGE_ANCHOR_MISSING','item_id':ident}); continue
            sid=anchor.get('source_id'); page=anchor.get('pdf_page'); expected=anchor.get('pdf_sha256');quote=anchor.get('exact_quote')
            if sid not in pdf_sources:
                errors.append({'code':'PDF_SOURCE_ID_UNREGISTERED','item_id':ident});continue
            if not isinstance(page,int) or isinstance(page,bool) or not 1<=page<=len(docs.get(sid,[])):
                errors.append({'code':'PDF_PAGE_INVALID','item_id':ident});continue
            if not isinstance(expected,str) or expected!=source_digests.get(sid):
                errors.append({'code':'PDF_SHA256_MISMATCH','item_id':ident});continue
            if not isinstance(quote,str) or len(_norm(quote))<12:
                errors.append({'code':'PDF_QUOTE_TOO_SHORT','item_id':ident});continue
            if _norm(quote) not in docs[sid][page-1]:
                errors.append({'code':'PDF_QUOTE_NOT_ON_PAGE','item_id':ident,'page':page})
            if not docs[sid][page-1]:
                errors.append({'code':'PDF_IMAGE_PAGE_REQUIRES_VISUAL_REVIEW','item_id':ident,'page':page})
        if not pdf_sources:
            errors.append({'code':'PDF_SOURCE_REGISTRY_EMPTY'})
        if not questions and require_all:
            errors.append({'code':'NO_QUESTIONS'})
    finally:
        docs.clear()
    return {'status':'BLOCKED' if errors else 'PAGE_EVIDENCE_PASS_REVIEW_REQUIRED',
            'errors':errors,'source_digests':source_digests,'page_counts':page_counts,
            'question_count':len(questions),'release_allowed':False,'semantic_validated':False}
