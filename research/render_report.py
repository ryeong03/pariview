"""Render the research companion and check A4 pagination, text, and layout."""
from pathlib import Path
import json
import re
import pymupdf
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    page = browser.new_page(viewport={'width':900,'height':1300}, device_scale_factor=1)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto((ROOT / 'research-and-strategy.html').as_uri(), wait_until='networkidle')
    page.evaluate('document.fonts.ready')
    report = page.evaluate('''() => ({
      fontsLoaded:document.fonts.check('14px Pretendard'),
      brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),
      pages:[...document.querySelectorAll('.page')].map((p,i)=>{
        const box=p.getBoundingClientRect(),body=p.querySelector('.page-content').getBoundingClientRect(),foot=p.querySelector(':scope>footer').getBoundingClientRect();
        return {page:i+1,bodyBottom:body.bottom-box.top,footerTop:foot.top-box.top,gap:foot.top-body.bottom,
          overflow:[...p.querySelectorAll('h1,h2,h3,p,td,th,.reference')].filter(e=>e.scrollWidth>e.clientWidth+2||e.getBoundingClientRect().right>box.right+1).map(e=>e.textContent.slice(0,70))};
      })
    })''')
    report['errors'] = errors
    (ROOT / 'research/report-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    for index in [0,1,3,5,6]:
        page.locator('.page').nth(index).screenshot(path=str(ROOT / f'research/report-preview-{index+1}.png'))
    bad = [p for p in report['pages'] if p['gap'] < 8 or p['overflow']]
    if bad or errors or report['brokenImages'] or not report['fontsLoaded']:
        raise RuntimeError(json.dumps(report, ensure_ascii=False, indent=2))
    page.pdf(path=str(ROOT / 'PariView_Research_and_Strategy.pdf'), prefer_css_page_size=True, print_background=True)
    browser.close()

with pymupdf.open(ROOT / 'PariView_Research_and_Strategy.pdf') as pdf:
    assert len(pdf) == 7, len(pdf)
    texts = []
    for page in pdf:
        mm = [round(page.rect.width/72*25.4,2), round(page.rect.height/72*25.4,2)]
        assert abs(mm[0]-210)<.5 and abs(mm[1]-297)<.5, mm
        text = page.get_text()
        assert len(text)>500
        assert '\ufffd' not in text
        texts.append(text)
    text = re.sub(r'\s+', '', '\n'.join(texts))
    for token in ['11.8','60.5','76명','MacLennan','Unwin','Matsuzaki','Yosef','김경민','Swedo','Dunn','Blackburn','Jüris','Jager','10.1007/s10803-021-05186-3','10.1002/aur.70283']:
        assert re.sub(r'\s+','',token) in text, token
    report.update(pdfPages=len(pdf),pageSizeMM=mm,textCharacters=sum(map(len,texts)),pdfLinks=sum(len(page.get_links()) for page in pdf))
(ROOT / 'research/report-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
