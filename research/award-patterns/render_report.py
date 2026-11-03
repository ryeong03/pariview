"""Render and check the A4 award-case report with the locally installed Chrome."""
import asyncio
import json
from collections import Counter
from pathlib import Path
import fitz
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent

async def main():
    data = json.loads((HERE/'sources.json').read_text())
    assert len(data['cases']) == 10
    assert sum(r['points'] for r in data['rubric']) == 100
    assert Counter(c['source_type'] for c in data['cases']) == Counter(data['method']['award_sources'])
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
        tab = await browser.new_page(viewport={'width':1180,'height':1280},device_scale_factor=1)
        errors=[]
        tab.on('pageerror',lambda error:errors.append(str(error)))
        await tab.goto((HERE/'strategy.html').as_uri(), wait_until='networkidle')
        await tab.evaluate('document.fonts.ready')
        await tab.emulate_media(media='print')
        checks=await tab.evaluate('''() => {
          const pages=[...document.querySelectorAll('.page')];
          return {
            pages:pages.map((page,i)=>{
              const main=page.querySelector('main').getBoundingClientRect();
              const foot=page.querySelector('footer').getBoundingClientRect();
              const r=page.getBoundingClientRect();
              const overflow=[...page.querySelectorAll('main *')].filter(el=>{
                const b=el.getBoundingClientRect();
                return b.width && (b.right>r.right+1 || b.left<r.left-1);
              }).map(el=>el.tagName+':'+el.textContent.slice(0,40));
              return {page:i+1,content_bottom:main.bottom-r.top,footer_top:foot.top-r.top,gap:foot.top-main.bottom,horizontal_overflow:overflow};
            }),
            fonts:[...document.fonts].map(f=>({family:f.family,status:f.status})),
            broken_images:[...document.images].filter(i=>!i.complete || !i.naturalWidth).map(i=>i.src),
            broken_anchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash),
            external_links:[...document.querySelectorAll('a[href^="https://"]')].length
          };
        }''')
        checks['page_errors']=errors
        checks['source_cases']=len(data['cases'])
        checks['rubric_total']=sum(r['points'] for r in data['rubric'])
        checks['pass']=not errors and not checks['broken_images'] and not checks['broken_anchors'] and all(p['gap']>=6 and not p['horizontal_overflow'] for p in checks['pages']) and all(f['status']=='loaded' for f in checks['fonts'])
        (HERE/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(checks,ensure_ascii=False,indent=2))
        if not checks['pass']:
            await browser.close()
            raise SystemExit('Report layout failed; no final PDF emitted')
        await tab.pdf(path=str(HERE/'PariView_Award_Strategy.pdf'),print_background=True,prefer_css_page_size=True,display_header_footer=False)
        await browser.close()
    with fitz.open(HERE/'PariView_Award_Strategy.pdf') as doc:
        assert len(doc)==len(checks['pages'])
        assert all(abs(p.rect.width-595.28)<1 and abs(p.rect.height-841.89)<1 for p in doc)
        checks['pdf_pages']=len(doc)
        checks['pdf_links']=sum(len(p.get_links()) for p in doc)
        checks['pdf_page_size']='A4'
        for pno,name in [(0,'preview-cover.png'),(3,'preview-reference.png'),(5,'preview-rubric.png'),(9,'preview-business.png')]:
            doc[pno].get_pixmap(matrix=fitz.Matrix(1.3,1.3),alpha=False).save(HERE/name)
    (HERE/'validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pdf_pages':checks['pdf_pages'],'pdf_links':checks['pdf_links'],'pass':checks['pass']}))

asyncio.run(main())
