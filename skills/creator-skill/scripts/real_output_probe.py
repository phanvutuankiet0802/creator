#!/usr/bin/env python3
"""Probe actual deliverables, not declared metadata.

Detects *review candidates*, never certifies medical content, semantic difficulty,
or clinical accuracy. Stdlib HTML/JSON; PyMuPDF/pypdfium2 for real PDF pages.
"""
from __future__ import annotations
import argparse
from collections import Counter
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unicodedata

class ScriptCollector(HTMLParser):
    def __init__(self):
        super().__init__(); self.depth = False; self.buf = []; self.scripts = []; self.current_attrs = {}
        self.controls = []; self.ids = set(); self.form_controls = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        if tag in {'button','input','select','textarea'}:
            self.controls.append((tag,a))
            self.form_controls.add(tag)
        if tag == 'script': self.depth = True; self.buf = []; self.current_attrs = a
    def handle_data(self, data):
        if self.depth: self.buf.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self.depth:
            self.scripts.append((self.current_attrs, ''.join(self.buf)))
            self.depth = False


def parse_html_data(path: str, kind: str = ''):
    """Select kind-specific payload, never arbitrary first JSON object/config."""
    h=ScriptCollector();h.feed(Path(path).read_text(encoding='utf-8'))
    known={'mcq':'quizData','meq':'meqData'}
    sought=known.get(kind)
    if sought:
        for attrs, raw in h.scripts:
            if attrs.get('id') == sought and attrs.get('type') == 'application/json':
                return json.loads(raw)
        # Backwards compatibility for older test fixtures with exactly one anonymous
        # application/json script. Never pick the first object in a multi-script page.
        raw_json = [raw for attrs,raw in h.scripts if attrs.get('type')=='application/json']
        if len(raw_json)==1 and len(h.scripts)==1:
            value=json.loads(raw_json[0])
            if (kind=='mcq' and isinstance(value,list)) or (kind=='meq' and isinstance(value,dict) and isinstance(value.get('cases'),list)):
                return value
        raise ValueError('Missing canonical '+kind+' data script id='+sought)
    if kind == 'flashcard':
        decoder=json.JSONDecoder()
        for attrs, raw in h.scripts:
            m=re.search(r'(?:const|let|var)\s+flashcards\s*=\s*',raw)
            if m:
                value,_=decoder.raw_decode(raw[m.end():].lstrip())
                if isinstance(value,list):return value
        raw_json=[raw for attrs,raw in h.scripts if attrs.get('type')=='application/json']
        if len(raw_json)==1 and len(h.scripts)==1:
            value=json.loads(raw_json[0])
            if isinstance(value,list):return value
        raise ValueError('Missing flashcards JSON assignment')
    raise ValueError('Artifact kind must be one of flashcard/mcq/meq')


def probe_html_runtime_shell(path: str, kind: str):
    """Conservative static UI prerequisite, NOT a browser test."""
    h=ScriptCollector();h.feed(Path(path).read_text(encoding='utf-8'))
    scripts=[src for attr,src in h.scripts if attr.get('type') != 'application/json']
    if not h.controls or not scripts:
        return {'valid':False,'error':'UI_CONTROLS_OR_EXECUTABLE_SCRIPT_MISSING'}
    required={
        'flashcard': {'flashcard','flipBtn','nextBtn'},
        'mcq': {'list','answered','grid'},
        'meq': {'caseContainer','caseNav','resetAllBtn'},
    }[kind]
    missing=sorted(required-h.ids)
    if missing:
        return {'valid':False,'error':'REQUIRED_UI_ELEMENTS_MISSING', 'ids':missing}
    return {'valid':True,'note':'Static prerequisite only; browser interactions still unverified'}


def norm(s):
    t=unicodedata.normalize('NFD',str(s).casefold())
    return ''.join(c for c in t if unicodedata.category(c)!='Mn').replace('đ','d')

def clean(s):return re.sub(r'<[^>]*>',' ',unescape(str(s)))

def pdf_pages(path):
    try:
        import fitz
        with fitz.open(path) as d:return len(d), d[0].get_text() if len(d) else ''
    except ImportError:
        import pypdfium2 as pdfium
        doc=pdfium.PdfDocument(path);pages=len(doc)
        first=doc[0].get_textpage().get_text_range() if pages else ''
        doc.close();return pages,first

def item(kind,code,detail,ids=None):
    return {'kind':kind,'code':code,'detail':detail,'ids':ids or [],'status':'REVIEW_CANDIDATE'}

def audit_bundle(lecture_pdf,flashcard_html,mcq_html,meq_html):
    paths=[lecture_pdf,flashcard_html,mcq_html,meq_html]
    missing=[x for x in paths if not Path(x).is_file()]
    if missing:return {'status':'BLOCKED','errors':[{'code':'MISSING_DELIVERABLE','paths':missing}]}
    n_pages,first=pdf_pages(lecture_pdf)
    try:
        F=parse_html_data(flashcard_html,'flashcard'); Q=parse_html_data(mcq_html,'mcq'); M=parse_html_data(meq_html,'meq')
    except (ValueError, json.JSONDecodeError) as exc:
        return {'status':'BLOCKED','errors':[{'code':'HTML_DATA_UNREADABLE','detail':str(exc)}],'warnings':[]}
    if not isinstance(F,list) or not isinstance(Q,list) or not isinstance(M,dict) or not isinstance(M.get('cases'),list):
        return {'status':'BLOCKED','errors':[{'code':'BAD_HTML_DATA_SHAPE'}]}
    errors=[]; warnings=[]
    for kind, html in [('flashcard',flashcard_html),('mcq',mcq_html),('meq',meq_html)]:
        check=probe_html_runtime_shell(html,kind)
        if not check['valid']:
            errors.append({'code':'HTML_UI_SHELL_UNUSABLE','kind':kind,'detail':check})
    # Structural validation MUST inspect item fields, not just list/dict shells.
    def valid_flashcard(c):
        return isinstance(c,dict) and bool(str(c.get('front','')).strip()) and bool(str(c.get('back','')).strip())
    def valid_mcq(q):
        if not isinstance(q,dict):return False
        if not str(q.get('question') or q.get('stem') or '').strip():return False
        opts=q.get('options')
        if not isinstance(opts,list) or len(opts)<2 or any(not str(x).strip() for x in opts):return False
        correct=q.get('correct',q.get('correct_index'))
        if isinstance(correct,int):return 0 <= correct < len(opts)
        if isinstance(correct,str):
            c=correct.strip().upper()
            return (len(c)==1 and 'A' <= c <= chr(ord('A')+len(opts)-1)) or (c.isdigit() and int(c)<len(opts))
        return False
    bad_flash=[i for i,c in enumerate(F) if not valid_flashcard(c)]
    bad_mcq=[i for i,q in enumerate(Q) if not valid_mcq(q)]
    if bad_flash:errors.append({'code':'FLASHCARD_ITEM_SCHEMA_INVALID','indices':bad_flash[:30],'invalid_count':len(bad_flash)})
    if bad_mcq:errors.append({'code':'MCQ_ITEM_SCHEMA_INVALID','indices':bad_mcq[:30],'invalid_count':len(bad_mcq)})
    if not F: errors.append({'code':'FLASHCARD_EMPTY'})
    if not Q: errors.append({'code':'MCQ_EMPTY'})
    if not M['cases']: errors.append({'code':'MEQ_CASES_EMPTY'})
    if n_pages>9 or n_pages<1: errors.append({'code':'LECTURE_PAGE_CAP','pages':n_pages})
    types=Counter(str(c.get('type','')) for c in F)
    periphery=[c.get('id') for c in F if norm(c.get('type','')) in {'lich su','dich te'}]
    if periphery:
        warnings.append(item('flashcard','POSSIBLE_LOW_VALUE_CARDS','Verify historical/epidemiological cards are important for THIS lesson; never globally discard epidemiology.',periphery[:20]))
    if 'lich su' in norm(first[:300]):
        warnings.append(item('lecture','FIRST_PAGE_HISTORY_PRIORITY','First page foregrounds history; verify objective alignment before treating this as important.'))
    bypass=[]; artificial=[]
    bypass_keywords=['dinh nghia','la bao lau','bao nhieu phan tram','ty le','moc thoi gian','nam nao','nguoi nao','phan loai vao nhom','chiem ty le']
    for q in Q:
        stem=norm(q.get('question','')); tail=stem[-280:]
        if len(stem)>350 and any(x in tail for x in bypass_keywords):bypass.append(q.get('id'))
        opts=q.get('options',[])
        if any('tren lam sang tai khoa cap cuu hien' in norm(opt) for opt in opts):artificial.append(q.get('id'))
    if bypass:warnings.append(item('mcq','CASE_DEPENDENCE_ABLATION_REQUIRED','Long vignette plus a fact-recall lead-in: remove case data and test whether item remains answerable.',bypass))
    if artificial:warnings.append(item('mcq','DISTRACTOR_ARTIFICIAL_FILLER','At least one distractor appears padded with generic clinical boilerplate.',artificial))
    leak=[]; stage_info=[]; subq_count=0
    high_info=['rutherford','chan ep khoang','bac cau mach','tieu soi huyet','thuyen tac']
    for c in M.get('cases',[]):
        title=norm(c.get('case_title','')); code=c.get('case_code') or c.get('case_id')
        stages=c.get('stages',[])
        for st in stages:
            stage_name=norm(st.get('stage_title',''))
            qs=st.get('sub_questions',st.get('questions',[]));subq_count+=len(qs)
            stage_info.append(len(qs))
            if st is stages[0] and any(x in title for x in high_info) and any(x in stage_name for x in ['nhan dien','phan tang','xac dinh']):
                leak.append(code); break
    if leak:warnings.append(item('meq','CASE_TITLE_MAY_LEAK_ANSWER','Case title reveals a diagnosis/severity/procedure that the first stage may require deriving.',leak))
    if any(n==0 for n in stage_info):errors.append({'code':'EMPTY_MEQ_STAGE','stages_with_no_questions':stage_info.count(0)})
    return {'status':'BLOCKED' if errors else 'STRUCTURE_PASS_REVIEW_REQUIRED',
       'measured':{'lecture_pdf_pages':n_pages,'flashcard_count':len(F),'flashcard_categories':dict(types),
        'mcq_count':len(Q),'meq_case_count':len(M['cases']),'meq_stage_count':len(stage_info),'meq_question_count':subq_count},
       'errors':errors,'warnings':warnings,
       'limitations':'Warnings are heuristic red flags for an independent reviewer, not proof of medical error, flawed difficulty, or academic validity. No live NotebookLM/Chrome test.'}

def to_markdown(r):
    m=r.get('measured',{});t=['# Kiểm toán sơ bộ trên bộ sản phẩm THẬT (không dựa metadata)',
      '',f"- Trạng thái: **{r['status']}** (KHÔNG phải chứng nhận chất lượng học thuật).",
      f"- Tệp đo được: PDF **{m.get('lecture_pdf_pages','?')} trang**; flashcard **{m.get('flashcard_count','?')} thẻ**; MCQ **{m.get('mcq_count','?')} câu**; MEQ **{m.get('meq_case_count','?')} ca, {m.get('meq_stage_count','?')} giai đoạn, {m.get('meq_question_count','?')} câu thành phần**.",'', '## Những chỗ cần người thẩm định kiểm chứng']
    for i,w in enumerate(r.get('warnings',[]),1):t.append(f"{i}. **{w['kind']} – {w['code']}**: {w['detail']} Mẫu ID: {', '.join(map(str,w['ids'][:10])) if w['ids'] else 'Không áp dụng'}.")
    if not r.get('warnings'):t.append('Không phát hiện cảnh báo heuristic, vẫn phải thẩm định học thuật.')
    t+=['','## Yêu cầu kiểm thử tiếp theo','- Đọc lại nguồn để lập LO P0/P1 và xem điểm nào bị thiếu, không dùng tỷ lệ keyword làm bằng chứng đủ.','- Thẩm định MCQ: xóa vignette, tự trả lời; sửa câu có thể trả lời chỉ từ lead-in.','- Thẩm định MEQ: ẩn tiêu đề/phân độ, công bố từng giai đoạn, chấm chuỗi bằng barem từng ý.','- Thẩm định giải thích bài giảng: đọc thử tuyến tính và đánh dấu chỗ mất liên kết nhân-quả.','',r.get('limitations','')]
    return '\n'.join(t)+'\n'

def main():
    p=argparse.ArgumentParser();p.add_argument('lecture');p.add_argument('flashcard');p.add_argument('mcq');p.add_argument('meq');p.add_argument('--json');p.add_argument('--markdown');a=p.parse_args()
    result=audit_bundle(a.lecture,a.flashcard,a.mcq,a.meq)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if a.json:Path(a.json).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    if a.markdown:Path(a.markdown).write_text(to_markdown(result),encoding='utf8')
    raise SystemExit(2 if result['status']=='BLOCKED' else 0)
if __name__=='__main__':main()
