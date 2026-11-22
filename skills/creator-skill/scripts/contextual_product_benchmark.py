#!/usr/bin/env python3
"""Audit actual A/B learning artifacts, not model self-ratings.

Deterministic checks: source equality, file identity, verifiable excerpt anchors,
context contrast, page cap, and review-record completeness.  Does not certify
medical correctness or authenticate reviewer identity.
"""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import unicodedata
from pathlib import Path
from html.parser import HTMLParser

VERSION = '0.3.0'
RUBRIC = ('source_fidelity', 'reasoning_coherence', 'context_selectivity',
          'readability', 'objective_coverage', 'visual_relevance')

def _issue(code, detail, severity='error'):
    return {'code': code, 'detail': detail, 'severity': severity}

def _normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip().casefold()

class _VisibleHTML(HTMLParser):
    """Conservative static text extraction; executable data is NOT learner-visible."""
    SKIP_TAGS = {'script', 'style', 'template', 'head', 'noscript', 'svg'}
    BLOCK_TAGS = {'div', 'section', 'article', 'p', 'li', 'h1', 'h2', 'h3',
                  'h4', 'h5', 'h6', 'br', 'tr', 'td', 'th', 'button', 'label'}
    VOID_TAGS = {'br','hr','img','input','meta','link','source','area','embed','wbr','col','base'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden_depth = 0
        self.stack = []
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        style = re.sub(r'\s+', '', attrs.get('style', '').lower())
        invisible = (tag in self.SKIP_TAGS or 'hidden' in attrs or
                     attrs.get('aria-hidden', '').lower() == 'true' or
                     'display:none' in style or 'visibility:hidden' in style or
                     attrs.get('type', '').lower() == 'hidden')
        if tag not in self.VOID_TAGS:
            self.stack.append((tag, invisible))
            self.hidden_depth += int(invisible)
        if not self.hidden_depth and tag in self.BLOCK_TAGS:
            self.chunks.append('\n')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        # HTML tag nesting is not always clean; never let an unmatched end tag
        # dismiss a still-open hidden <script> or <template>.
        for j in range(len(self.stack)-1,-1,-1):
            if self.stack[j][0] == tag:
                removed = self.stack[j:]
                self.stack = self.stack[:j]
                self.hidden_depth -= sum(int(flag) for _,flag in removed)
                break
        if not self.hidden_depth and tag in self.BLOCK_TAGS:
            self.chunks.append('\n')

    def handle_data(self, data):
        if self.hidden_depth == 0:
            self.chunks.append(data)

    def text(self):
        return re.sub(r'\n\s*\n+', '\n', ''.join(self.chunks)).strip()


def _browser_html_text(raw, interactions=None):
    """Render a local HTML artifact in a fresh isolated browser with networking blocked.

    This captures *rendered initial DOM*, not answers behind an unclicked card or
    unperformed interaction. Those must have separately tested interaction evidence.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError('Browser HTML mode requires Playwright.') from exc
    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except Exception:
                system_chrome = (shutil.which('chromium') or shutil.which('chromium-browser')
                                 or shutil.which('google-chrome'))
                if not system_chrome:
                    raise
                browser = playwright.chromium.launch(headless=True,
                    executable_path=system_chrome, args=['--no-sandbox'])
            try:
                context = browser.new_context(service_workers='block')
                context.route('**/*', lambda route: route.abort())
                page = context.new_page()
                page.set_content(raw, wait_until='load', timeout=12000)
                page.wait_for_timeout(180)
                captures = [page.locator('body').inner_text(timeout=5000)]
                for step in interactions or []:
                    if (not isinstance(step, dict) or step.get('action') != 'click' or
                        not isinstance(step.get('selector'), str) or
                        not 1 <= len(step['selector']) <= 256):
                        raise ValueError('Each browser interaction must be a bounded click(selector).')
                    page.locator(step['selector']).first.click(timeout=5000)
                    page.wait_for_timeout(90)
                    captures.append(page.locator('body').inner_text(timeout=5000))
                return '\n'.join(captures)
            finally:
                browser.close()
    except Exception as exc:
        raise RuntimeError(f'Cannot establish actual rendered learner text: {exc}') from exc


def _read_artifact(path, *, html_mode='static', interactions=None):
    f = Path(path)
    if not f.is_file():
        raise ValueError(f'Artifact does not exist: {f}')
    if f.suffix.lower() == '.pdf':
        try:
            import fitz
            doc = fitz.open(f)
            try:
                content = '\n'.join(page.get_text(sort=True) for page in doc)
                return {'text': content, 'page_count': len(doc),
                        'is_pdf': True, 'sha256': hashlib.sha256(f.read_bytes()).hexdigest(),
                        'text_scope': 'pdf_extracted_text'}
            finally:
                doc.close()
        except ImportError:
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(str(f))
            try:
                content = '\n'.join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
                return {'text': content, 'page_count': len(doc),
                        'is_pdf': True, 'sha256': hashlib.sha256(f.read_bytes()).hexdigest(),
                        'text_scope': 'pdf_extracted_text'}
            finally:
                doc.close()
    if f.suffix.lower() not in {'.txt', '.md', '.html'}:
        raise ValueError(f'Unsupported artifact type: {f.suffix}')
    raw = f.read_bytes()
    decoded = raw.decode('utf-8')
    if f.suffix.lower() == '.html':
        if html_mode == 'static':
            parser = _VisibleHTML()
            parser.feed(decoded)
            content = parser.text()
            scope = 'static_visible_html_only'
        elif html_mode == 'browser':
            content = _browser_html_text(decoded, interactions=interactions)
            scope = ('rendered_dom_plus_declared_clicks' if interactions else
                     'rendered_initial_dom_no_interactions')
        else:
            raise ValueError(f'Unsupported HTML evidence mode: {html_mode}')
    else:
        content = decoded
        scope = 'plain_text'
    return {'text': content, 'page_count': None,
            'is_pdf': False, 'sha256': hashlib.sha256(raw).hexdigest(),
            'text_scope': scope}

def source_snapshot(spec_sources, *, root):
    """Compute canonical evidence digest from actual source bytes, never metadata alone."""
    if not isinstance(spec_sources, list) or not spec_sources:
        raise ValueError('Nonempty sources manifest with id, file, sha256 is mandatory.')
    seen=set(); rows=[]
    for row in spec_sources:
        if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not row['id'].strip():
            raise ValueError('Every source must have a nonempty id.')
        if row['id'] in seen: raise ValueError('Duplicate source ID.')
        seen.add(row['id'])
        if not isinstance(row.get('file'),str): raise ValueError('Source file is missing.')
        p=(root/row['file']).resolve()
        if root not in p.parents: raise ValueError('Source outside audit root.')
        actual=hashlib.sha256(p.read_bytes()).hexdigest()
        if row.get('sha256') != actual: raise ValueError(f'Source hash mismatch: {row["id"]}')
        rows.append({'id':row['id'],'sha256':actual})
    return hashlib.sha256(json.dumps(sorted(rows,key=lambda x:x['id']),
        ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def audit_pair(spec, *, base_dir='.'):
    errors, warnings, findings = [], [], []
    if not isinstance(spec, dict):
        return {'status': 'BLOCKED', 'errors': [_issue('BAD_SPEC','Expected object')],
                'warnings': [], 'findings': [], 'release_allowed': False}
    mode = spec.get('comparison_type')
    if mode not in ('layout_revision', 'context_adaptation'):
        errors.append(_issue('INVALID_COMPARISON_TYPE','Specify layout_revision or context_adaptation.'))
    root = Path(base_dir).resolve()
    try:
        actual_source_snapshot=source_snapshot(spec.get('sources'),root=root)
    except (OSError,ValueError,TypeError) as exc:
        errors.append(_issue('SOURCE_SNAPSHOT_UNVERIFIED',str(exc)))
        actual_source_snapshot=None
    products = {}
    for key in ('A','B'):
        row = spec.get(key)
        if not isinstance(row,dict) or not isinstance(row.get('file'),str):
            errors.append(_issue('MISSING_ARTIFACT',f'{key} must have file.'))
            continue
        try:
            p = (root/row['file']).resolve()
            # This is an offline artifact tool, never allow traversal out of audit root.
            if p != root and root not in p.parents:
                errors.append(_issue('ARTIFACT_OUTSIDE_ROOT',f'{key}: {row["file"]}'))
                continue
            steps=row.get('html_interactions', [])
            if not isinstance(steps,list) or len(steps)>15:
                raise ValueError('html_interactions must be a list of at most 15 steps.')
            if steps and row.get('html_evidence_mode') != 'browser':
                raise ValueError('HTML interactions require browser evidence mode.')
            products[key] = _read_artifact(p, html_mode=row.get('html_evidence_mode','static'),
                                           interactions=steps)
        except (ValueError, RuntimeError, UnicodeError, OSError) as exc:
            errors.append(_issue('ARTIFACT_UNREADABLE',f'{key}: {exc}'))
            continue
        expected = row.get('artifact_sha256')
        if not isinstance(expected,str) or len(expected)!=64 or expected.lower() != products[key]['sha256']:
            errors.append(_issue('ARTIFACT_HASH_MISMATCH',f'{key} hash missing or does not match bytes.'))
        if not actual_source_snapshot or row.get('source_snapshot_sha256') != actual_source_snapshot:
            errors.append(_issue('SOURCE_SNAPSHOT_MISMATCH',f'{key} source snapshot does not match verified sources.'))
        if not isinstance(row.get('source_ids'),list) or not row['source_ids']:
            errors.append(_issue('SOURCE_IDS_MISSING',f'{key} source IDs missing.'))
        elif isinstance(spec.get('sources'),list) and sorted(row['source_ids']) != sorted(x.get('id') for x in spec['sources'] if isinstance(x,dict)):
            errors.append(_issue('SOURCE_IDS_UNVERIFIED',f'{key} source IDs differ from verified source files.'))
        if not isinstance(row.get('context'),dict) or not row['context']:
            errors.append(_issue('CONTEXT_MISSING',f'{key} context missing.'))
        if products[key]['is_pdf']:
            pages_cap = row.get('page_cap')
            if isinstance(pages_cap,int) and products[key]['page_count']>pages_cap:
                errors.append(_issue('PAGE_CAP_BREACH',f'{key}: {products[key]["page_count"]}>{pages_cap}.'))
        # In the strict academic gates, raw HTML parser output is not enough
        # when CSS or JavaScript determines what the learner actually sees.
        file_suffix = p.suffix.lower()
        if file_suffix == '.html':
            html_head = p.read_text(encoding='utf-8')
            has_dynamic_presentation = bool(re.search(r'<(?:script|style|link)\b', html_head, re.I))
            strict = bool(spec.get('require_full_gold_witnesses') or
                          spec.get('require_pedagogical_contrasts'))
            if strict and has_dynamic_presentation and row.get('html_evidence_mode') != 'browser':
                errors.append(_issue('DYNAMIC_HTML_REQUIRES_BROWSER_EVIDENCE',
                    f'{key}: static extraction cannot verify interactive or styled learning content.'))
            if spec.get('require_interaction_evidence'):
                if row.get('html_evidence_mode') != 'browser' or not row.get('html_interactions'):
                    errors.append(_issue('HTML_INTERACTION_EVIDENCE_MISSING',
                        f'{key}: interaction evidence is mandatory for this benchmark.'))
        if not products[key]['text'].strip():
            errors.append(_issue('EMPTY_ARTIFACT',f'{key} has no extractable text.'))
    if len(products)==2:
        a,b=spec['A'],spec['B']
        if products['A']['sha256']==products['B']['sha256']:
            errors.append(_issue('IDENTICAL_PRODUCTS','A and B are byte-identical, cannot compare adaptation.'))
        if a.get('source_snapshot_sha256')!=b.get('source_snapshot_sha256') or sorted(a.get('source_ids',[])) != sorted(b.get('source_ids',[])):
            errors.append(_issue('SOURCE_DRIFT_IN_AB','A/B must use identical selected source snapshot and IDs.'))
        if mode=='context_adaptation':
            if a.get('context')==b.get('context'):
                errors.append(_issue('NO_CONTEXT_CONTRAST','Context-adaptation A/B must change context.'))
            else:
                changes = [k for k in set(a.get('context',{})) | set(b.get('context',{}))
                           if a.get('context',{}).get(k)!=b.get('context',{}).get(k)]
                findings.append({'changed_context_fields': sorted(changes)})
                if len(changes)!=1:
                    warnings.append(_issue('CONFOUNDED_CONTEXT_CONTRAST',
                        'A/B changes several context fields, so effects cannot be attributed to one factor.', 'warning'))
        if mode=='layout_revision' and a.get('context')!=b.get('context'):
            errors.append(_issue('LAYOUT_CONTEXT_DRIFT','Layout comparison requires same context.'))
        # Exactly-present content witnesses are not a semantic correctness judgment.
        for item in spec.get('witnesses',[]):
            if not isinstance(item,dict) or item.get('variant') not in ('A','B') or not isinstance(item.get('quote'),str) or not item['quote'].strip():
                errors.append(_issue('INVALID_WITNESS','Each witness needs variant and nonempty quote.'))
                continue
            key=item['variant']
            present=_normalize(item['quote']) in _normalize(products[key]['text'])
            findings.append({'witness_id':item.get('id',''), 'variant':key,'found':present})
            if not present:
                errors.append(_issue('WITNESS_NOT_IN_ARTIFACT', f'{key}: {item.get("id", "unlabeled")} quote not found.'))
        if mode=='context_adaptation' and _normalize(products['A']['text'])==_normalize(products['B']['text']):
            errors.append(_issue('NO_OBSERVABLE_TEXT_ADAPTATION','Text is identical after normalization.'))
    # Evidence triangle: objective -> selected REAL source span -> ACTUAL output span.
    # Excerpt matching proves only presence, never clinical/semantic correctness.
    gold=spec.get('gold_checks',[])
    if not isinstance(gold,list):
        errors.append(_issue('BAD_GOLD_FORMAT','gold_checks must be a list.'))
        gold=[]
    source_texts={}
    for source in (spec.get('sources') or []):
        if not isinstance(source,dict) or not isinstance(source.get('file'),str):
            continue
        try:
            p=(root/source['file']).resolve()
            if root in p.parents and p.is_file():
                source_texts[source.get('id')]=p.read_text(encoding='utf8')
        except (OSError,UnicodeError):
            pass
    observed_gold=set()
    for i, gold_item in enumerate(gold):
        if not isinstance(gold_item,dict):
            errors.append(_issue('BAD_GOLD_ITEM',f'gold_checks[{i}] must be an object.'))
            continue
        objective=gold_item.get('objective_id')
        sid=gold_item.get('source_id')
        quoted=gold_item.get('source_quote')
        out=gold_item.get('artifact_quotes')
        if not isinstance(quoted,str) or not quoted.strip() or sid not in source_texts or _normalize(quoted) not in _normalize(source_texts[sid]):
            errors.append(_issue('GOLD_SOURCE_QUOTE_UNVERIFIED',f'Gold check {objective} not anchored in source {sid}.'))
            continue
        if not isinstance(out,dict) or any(not isinstance(out.get(k),str) or
             not out[k].strip() or k not in products or
             _normalize(out[k]) not in _normalize(products[k]['text']) for k in ('A','B')):
            errors.append(_issue('GOLD_OUTPUT_QUOTE_UNVERIFIED',f'Gold check {objective} not anchored in both products.'))
            continue
        observed_gold.add(objective)
    # A/B contextual decisions must be witnessed by ACTUAL distinct output text,
    # under the same verified source snapshot. This is an evidence gate, NOT
    # autonomous approval of whether the pedagogical choice was appropriate.
    contrasts = spec.get('pedagogical_contrasts', [])
    if not isinstance(contrasts, list):
        errors.append(_issue('BAD_PEDAGOGICAL_CONTRASTS', 'pedagogical_contrasts must be an array.'))
        contrasts = []
    valid_contrast_objectives = set()
    changed_context = set()
    if mode == 'context_adaptation' and all(isinstance(spec.get(x), dict) for x in ('A','B')):
        a_ctx = spec['A'].get('context') if isinstance(spec['A'].get('context'),dict) else {}
        b_ctx = spec['B'].get('context') if isinstance(spec['B'].get('context'),dict) else {}
        changed_context = {x for x in set(a_ctx) | set(b_ctx) if a_ctx.get(x) != b_ctx.get(x)}
    for i, contrast in enumerate(contrasts):
        if not isinstance(contrast, dict):
            errors.append(_issue('INVALID_PEDAGOGICAL_CONTRAST',f'Contrast {i} is not an object.'))
            continue
        obj = contrast.get('objective_id')
        sid = contrast.get('source_id')
        quote = contrast.get('source_quote')
        if not isinstance(quote,str) or len(quote.strip()) < 12 or sid not in source_texts or _normalize(quote) not in _normalize(source_texts[sid]):
            errors.append(_issue('PEDAGOGICAL_SOURCE_UNVERIFIED',f'Contrast {i} lacks a verified source excerpt.'))
            continue
        if contrast.get('context_field') not in changed_context:
            errors.append(_issue('PEDAGOGICAL_CONTEXT_UNCHANGED',f'Contrast {i} is not related to the changed context field.'))
            continue
        why = contrast.get('why_this_change')
        if not isinstance(why,str) or len(why.strip()) < 35:
            errors.append(_issue('PEDAGOGICAL_RATIONALE_MISSING',f'Contrast {i} must justify pedagogical choice.'))
            continue
        aq, bq = contrast.get('A_quote'), contrast.get('B_quote')
        if any(not isinstance(x,str) or len(x.strip()) < 22 for x in (aq,bq)) or not all(x in products for x in ('A','B')):
            errors.append(_issue('PEDAGOGICAL_ARTIFACT_EXCERPT_MISSING',f'Contrast {i} requires two substantive real excerpts.'))
            continue
        if any(_normalize(q) not in _normalize(products[k]['text']) for k,q in (('A',aq),('B',bq))):
            errors.append(_issue('PEDAGOGICAL_ARTIFACT_QUOTE_UNVERIFIED',f'Contrast {i} quote is not learner-visible evidence.'))
            continue
        if _normalize(aq) == _normalize(bq):
            errors.append(_issue('PEDAGOGICAL_NO_MEANINGFUL_CONTRAST',f'Contrast {i} repeats the same content.'))
            continue
        if not isinstance(obj,str) or not obj.strip():
            errors.append(_issue('PEDAGOGICAL_OBJECTIVE_MISSING',f'Contrast {i} lacks an objective ID.'))
            continue
        valid_contrast_objectives.add(obj)
        findings.append({'pedagogical_contrast': i, 'objective_id': obj,
                         'context_field': contrast['context_field'],
                         'note': 'Verified literal text, not pedagogical correctness.'})
    if mode == 'context_adaptation':
        if not contrasts:
            warnings.append(_issue('CONTRAST_DECISIONS_NOT_EVIDENCED',
                         'Only a text difference is known; no source-grounded teaching decision was verified.', 'warning'))
        if spec.get('require_pedagogical_contrasts'):
            critical_ids = {x for x in spec.get('critical_objectives',[]) if isinstance(x,str)}
            if not contrasts or not critical_ids or not critical_ids.issubset(valid_contrast_objectives):
                errors.append(_issue('CORE_PEDAGOGICAL_CONTRAST_UNWITNESSED',
                    'Every declared critical objective needs a source-grounded A/B teaching decision.'))
    critical=set(str(x) for x in spec.get('critical_objectives',[]) if isinstance(x,str))
    missing_gold=critical-observed_gold
    if missing_gold:
        warnings.append(_issue('GOLD_OBJECTIVES_UNWITNESSED',
            f'{len(missing_gold)} critical objectives have no source->both-artifacts witness.', 'warning'))
    if spec.get('require_full_gold_witnesses') and missing_gold:
        errors.append(_issue('CRITICAL_OBJECTIVE_UNWITNESSED',
            ', '.join(sorted(missing_gold))))
    if not spec.get('critical_objectives'):
        warnings.append(_issue('GOLD_OBJECTIVES_MISSING','No independently verified critical objective list.', 'warning'))
    reviews = spec.get('reviews',[])
    if reviews and not isinstance(reviews,list):
        errors.append(_issue('BAD_REVIEW_FORMAT','reviews must be an array.'))
        reviews=[]
    complete=[]
    for i,review in enumerate(reviews):
        if not isinstance(review,dict):
            errors.append(_issue('BAD_REVIEW_FORMAT',f'Review {i} is not an object.'))
            continue
        rid=review.get('reviewer_id')
        scores=review.get('scores')
        examples=review.get('evidence_quotes')
        if not isinstance(rid,str) or not rid.strip() or not isinstance(scores,dict) or not isinstance(examples,list):
            errors.append(_issue('INCOMPLETE_REVIEW',f'Review {i} is incomplete.'))
            continue
        if any(k not in scores or not isinstance(scores[k],int) or not (1<=scores[k]<=5) for k in RUBRIC):
            errors.append(_issue('INCOMPLETE_RUBRIC',f'Review {i} requires 1-5 for all six criteria.'))
            continue
        if len(examples)<2 or any(not isinstance(x,dict) or x.get('variant') not in ('A','B') or
            not isinstance(x.get('quote'),str) or not x['quote'].strip() or
            x.get('quote') and (x['variant'] not in products or _normalize(x['quote']) not in _normalize(products[x['variant']]['text']))
            for x in examples):
            errors.append(_issue('REVIEW_EVIDENCE_NOT_VERIFIED', f'Review {i} needs two actual artifact quotes.'))
            continue
        complete.append(rid)
    if len(set(complete))<2:
        warnings.append(_issue('INDEPENDENT_REVIEWS_MISSING','Need at least two distinct complete review records.', 'warning'))
    if reviews and len(complete)!=len(reviews):
        warnings.append(_issue('PARTIAL_REVIEW_RECORDS','Some review records are invalid.','warning'))
    if errors:
        status='BLOCKED'
    elif len(set(complete))<2:
        status='AWAITING_BLIND_REVIEW'
    else:
        status='REVIEW_RECORDS_COMPLETE_VERIFICATION_REQUIRED'
    return {'version':VERSION,'comparison_type':mode,'status':status,
            'release_allowed':False,'semantic_validated':False,
            'products':{k:{'sha256':v['sha256'],'pages':v['page_count'],'text_characters':len(v['text']),'evidence_scope':v['text_scope']} for k,v in products.items()},
            'errors':errors,'warnings':warnings,'findings':findings,
            'note':'HTML script/JSON text is not academic evidence unless rendered and visible. Reviewer IDs are unverified; even supported A/B decisions require semantic review.'}

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('spec', help='A/B JSON manifest')
    ap.add_argument('--out', help='Save JSON report')
    args=ap.parse_args()
    specpath=Path(args.spec).resolve()
    report=audit_pair(json.loads(specpath.read_text(encoding='utf-8')),base_dir=specpath.parent)
    output=json.dumps(report,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).write_text(output,encoding='utf-8')
    print(output)
    raise SystemExit(2 if report['status']=='BLOCKED' else 0)
