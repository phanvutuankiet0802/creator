"""Conservative red-flag screening of prior ALI artifacts (not academic grading)."""
import argparse, json, re
from pathlib import Path
from bs4 import BeautifulSoup

def visible(html):
    return BeautifulSoup(html, 'html.parser').get_text(' ', strip=True)

def assess(lecture_path: Path, mcq_path: Path, flash_path: Path, meq_path: Path):
    from bs4 import BeautifulSoup
    try:
        import fitz
        lecture=fitz.open(lecture_path)
        pdf_pages_cnt=len(lecture)
        first=' '.join(p.get_text() for p in list(lecture)[:1])
    except ImportError:
        import pypdfium2 as pdfium
        lecture=pdfium.PdfDocument(str(lecture_path))
        pdf_pages_cnt=len(lecture)
        first=lecture[0].get_textpage().get_text_range() if pdf_pages_cnt else ''
    mcq_soup=BeautifulSoup(mcq_path.read_text(encoding='utf-8'),'html.parser')
    mcq=json.loads(mcq_soup.find('script',id='quizData').text)
    fs=flash_path.read_text(encoding='utf-8')
    match=re.search(r'const flashcards = (\[.*?\]);\s*let currentIndex',fs,re.S)
    if not match: raise ValueError('NO_FLASHCARDS_ARRAY')
    cards=json.loads(match.group(1))
    meq=json.loads(BeautifulSoup(meq_path.read_text(encoding='utf-8'),'html.parser').find('script',id='meqData').text)
    # Only a candidate signal: NOT proof that the clinical vignette is redundant.
    needles=('moc thoi gian','ty le','bao nhieu phan tram','nam 1911','nam 1914','nam 1963','dich te')
    import unicodedata
    def fold(s):
      x=unicodedata.normalize('NFKD',s.casefold());return ''.join(c for c in x if not unicodedata.combining(c)).replace('đ','d')
    candidates=[]
    for q in mcq:
        question=str(q.get('question',''))
        last=fold(question)[-330:]
        if len(question)>320 and ('benh nhan' in fold(question)[:140] or 'nguoi benh' in fold(question)[:140]) and any(w in last for w in needles):
            candidates.append({'id':q.get('id'),'question_tail':question[-210:],'reason':'long_vignette_then_potential_standalone_fact','status':'REVIEW_ABLATION_MANUALLY'})
    history=[]
    for i,c in enumerate(cards,1):
        front=visible(c.get('front',''))
        if any(w in fold(front) for w in ('1911','1914','1963','lich su')):
            history.append({'index':i,'id':c.get('id'),'front_excerpt':front[:180]})
    first_hist = any(w in fold(first[:2500]) for w in ('lich su','1911','1963'))
    titles=[str(c.get('title','')) for c in meq.get('cases',[])]
    return {'artifact_filenames':{'lecture':lecture_path.name,'mcq':mcq_path.name,'flashcard':flash_path.name,'meq':meq_path.name},
            'counts':{'pdf_pages':pdf_pages_cnt,'mcq':len(mcq),'flashcards':len(cards),'meq_cases':len(titles)},
            'lecture_first_page_mentions_history':first_hist,
            'flashcard_history_date_count':len(history),'flashcard_history_examples':history[:8],
            'mcq_context_ablation_candidates':candidates,
            'meq_title_examples':titles[:3],
            'caution':'All flags are contextual REVIEW candidates, not findings of medical error or proof that vignette can be removed.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('pdf');p.add_argument('mcq');p.add_argument('flashcard');p.add_argument('meq');p.add_argument('--output')
    a=p.parse_args();out=assess(*map(Path,(a.pdf,a.mcq,a.flashcard,a.meq)))
    result=json.dumps(out,ensure_ascii=False,indent=2)
    if a.output:Path(a.output).write_text(result,encoding='utf-8')
    print(result)
if __name__=='__main__': main()
