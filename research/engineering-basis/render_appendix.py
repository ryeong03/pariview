"""Render the one-page appendix and retain source/code verification metadata."""
import ast
import asyncio
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import pymupdf
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPECTED = {'SOUND_RISE_LU':6.,'SOUND_LOUD_LUFS':-16.,'LIGHT_JUMP_Y':18.,'MERGE_GAP_S':.4,
            'MIN_LEN_S':.2,'LIGHT_HOLD_S':.8,'SILENCE_LUFS':-70.,'NOTICE_SOUND_RISE_LU':18.,
            'NOTICE_SOUND_ABOVE_MED_LU':4.,'NOTICE_SOUND_LOUD_OVER_MED':12.,'NOTICE_LIGHT_JUMP_Y':45.,
            'NOTICE_LIGHT_RANGE_RATIO':.30,'NOTICE_COOLDOWN_S':5.,'NOTICE_MERGE_S':2.,'NOTICE_SKIP_START_S':1.}

async def main():
    code = ROOT/'analysis/sensory_map.py'
    constants = {}
    for item in ast.parse(code.read_text()).body:
        if isinstance(item, ast.Assign) and isinstance(item.targets[0], ast.Name):
            if item.targets[0].id in EXPECTED:
                constants[item.targets[0].id] = ast.literal_eval(item.value)
    assert constants == EXPECTED, 'Code parameters changed: update appendix before rendering'
    clips = []
    for stem, expected in [('tears-lab',(13,3)),('sintel',(19,5)),('bunny',(20,3))]:
        path = ROOT/f'web/dist/assets/scenes/{stem}-map.json'
        data = json.loads(path.read_text())
        assert (len(data['events']),len(data['noticeEvents'])) == expected
        clips.append({'clip':stem,'duration':data['duration'],'events':len(data['events']),
                      'notices':len(data['noticeEvents']),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    check = subprocess.run([sys.executable,'analysis/notice_report.py'],cwd=ROOT,capture_output=True,text=True,check=True)
    (HERE/'notice-check.txt').write_text(check.stdout)
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
        page = await browser.new_page()
        await page.goto((HERE/'technical-design.html').as_uri(),wait_until='networkidle')
        await page.evaluate('document.fonts.ready')
        await page.emulate_media(media='print')
        layout = await page.evaluate('''() => {
          const a=document.querySelector('article').getBoundingClientRect();
          const m=document.querySelector('main').getBoundingClientRect();
          const f=document.querySelector('footer').getBoundingClientRect();
          return {footerGap:f.top-m.bottom,overflow:[...document.querySelectorAll('main *')].filter(e=>{
            const r=e.getBoundingClientRect();return r.width&&(r.left<a.left||r.right>a.right+.5);
          }).map(e=>e.tagName),fonts:[...document.fonts].map(f=>f.status)};
        }''')
        assert layout['footerGap']>=5 and not layout['overflow'] and all(f=='loaded' for f in layout['fonts']),layout
        await page.pdf(path=str(HERE/'PariView_Technical_Design_Appendix.pdf'),print_background=True,prefer_css_page_size=True)
        await browser.close()
    with pymupdf.open(HERE/'PariView_Technical_Design_Appendix.pdf') as doc:
        assert len(doc)==1
        assert abs(doc[0].rect.width-595.28)<1 and abs(doc[0].rect.height-841.89)<1
        doc[0].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4),alpha=False).save(HERE/'preview.png')
        pdf_links=len(doc[0].get_links())
    files=['analysis/sensory_map.py','analysis/notice_report.py','web/dist/app.js','LICENSE']
    validation={'checked_at':datetime.now().astimezone().isoformat(),
                'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                'files_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
                'constants':constants,'clips':clips,'notice_check_exit':check.returncode,
                'layout':layout,'pdf_pages':1,'pdf_size':'A4','pdf_links':pdf_links,'pass':True}
    (HERE/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(validation,ensure_ascii=False,indent=2))

if __name__=='__main__':asyncio.run(main())
