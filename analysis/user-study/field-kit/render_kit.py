"""Render and validate the two printable A4 booklets."""
from pathlib import Path
import json
import pymupdf
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent
reports={}
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    page=browser.new_page(viewport={'width':900,'height':1250})
    for name,expected in [('protocol',6),('participant-form',5)]:
        page.goto((HERE/f'{name}.html').as_uri(),wait_until='networkidle')
        page.evaluate('document.fonts.ready')
        checks=page.evaluate('''() => [...document.querySelectorAll('.page')].map((p,i)=>{
          const b=p.getBoundingClientRect(),c=p.querySelector('.content').getBoundingClientRect(),f=p.querySelector('.footer').getBoundingClientRect();
          return {page:i+1,gap:f.top-c.bottom,horizontalOverflow:[...p.querySelectorAll('p,td,th,code')].filter(e=>e.scrollWidth>e.clientWidth+2).map(e=>e.textContent.slice(0,45))};
        })''')
        reports[name]={'layout':checks}
        bad=[c for c in checks if c['gap']<5 or c['horizontalOverflow']]
        if bad: raise RuntimeError(json.dumps({name:bad},ensure_ascii=False))
        page.pdf(path=str(HERE/f'{name}.pdf'),prefer_css_page_size=True,print_background=True)
        page.locator('.page').first.screenshot(path=str(HERE/f'{name}-preview.png'))
        with pymupdf.open(HERE/f'{name}.pdf') as pdf:
            assert len(pdf)==expected,(name,len(pdf))
            for pg in pdf:
                assert abs(pg.rect.width-595.28)<2 and abs(pg.rect.height-841.89)<2
                assert len(pg.get_text())>100 and '\ufffd' not in pg.get_text()
            reports[name]['pages']=len(pdf)
            reports[name]['text_chars']=sum(len(pg.get_text()) for pg in pdf)
    browser.close()
(HERE/'validation.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(reports,ensure_ascii=False,indent=2))
