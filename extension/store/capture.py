"""Create 1280x800 listing graphics from live, unmodified extension UI captures."""
import base64
import html
import re
import sys
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'tests'))
from helpers import launch,popup,inspect


def data(path):
    return 'data:image/png;base64,'+base64.b64encode(Path(path).read_bytes()).decode()


def render(context,film,pop,title,subtitle,tag,filename):
    page=context.new_page();page.set_viewport_size({'width':1280,'height':800})
    markup='''<!doctype html><html lang="ko"><meta charset="utf-8"><style>
    *{box-sizing:border-box}body{margin:0;background:#f6f7f9;color:#17181d;font-family:-apple-system,'Apple SD Gothic Neo',sans-serif}
    header{height:145px;padding:28px 46px 22px;display:flex;align-items:center;justify-content:space-between;background:#fff;border-bottom:1px solid #e6e8ed}
    .brand{font-size:17px;font-weight:700;color:#003cdc;margin-bottom:8px}.brand img{width:24px;height:24px;vertical-align:middle;margin-right:8px}
    h1{font-size:36px;letter-spacing:-1.4px;line-height:1.25;margin:0}.tag{font-size:13px;color:#626671;padding:10px 16px;background:#f6f7f9;border-radius:8px}
    main{display:grid;grid-template-columns:766px 340px;gap:36px;margin:23px 46px 0}.caption{font-size:12px;color:#626671;margin:0 0 8px}
    .player{padding:12px;background:#fff;border:1px solid #e2e5eb;border-radius:16px}.player img{width:740px;height:310px;object-fit:cover;display:block;border-radius:7px}
    .popup{border:1px solid #e2e5eb;border-radius:14px;overflow:hidden;background:#fff;box-shadow:0 8px 28px #1320380b}.popup img{display:block;width:338px}
    h2{font-size:26px;letter-spacing:-.8px;margin:25px 0 9px}.sub{font-size:17px;line-height:1.65;color:#515764;margin:0;max-width:690px}
    .features{display:flex;gap:10px;margin:19px 0}.features span{background:#fff;border:1px solid #e2e5eb;padding:11px 14px;border-radius:9px;font-size:14px}
    footer{position:absolute;left:46px;bottom:14px;font-size:10px;color:#727681;max-width:760px;line-height:1.5}
    </style><header><div><div class="brand"><img src="{{ICON}}">PariView 시청 설정</div><h1>{{TITLE}}</h1></div><span class="tag">Mac · Windows의 PC 크롬</span></header>
    <main><section><p class="caption">유튜브에서 실제 재생한 화면</p><div class="player"><img src="{{FILM}}"></div><h2>{{TAG}}</h2><p class="sub">{{SUBTITLE}}</p><div class="features"><span>밝기 · 대비 · 색감</span><span>음량 · 지원되는 소리 효과</span><span>현재 탭 상태 확인</span></div></section><aside><p class="caption">실제 PariView 확장 프로그램 팝업</p><div class="popup"><img src="{{POPUP}}"></div></aside></main>
    <footer>실제 Chromium에서 캡처한 영상과 확장 프로그램 화면을 배치한 소개 이미지<br>Big Buck Bunny © Blender Foundation · CC BY 3.0 · YouTube는 Google LLC의 상표이며 PariView는 공식 제휴 제품이 아니에요</footer></html>'''
    values={'ICON':data(HERE.parent/'icons/icon32.png'),'TITLE':html.escape(title),'FILM':data(film),'TAG':html.escape(tag),'SUBTITLE':html.escape(subtitle),'POPUP':data(pop)}
    markup=re.sub(r'\{\{(\w+)\}\}',lambda m:values[m.group(1)],markup)
    page.set_content(markup);page.evaluate('document.fonts.ready');page.wait_for_function("() => [...document.images].every(i=>i.complete && i.naturalWidth)");page.screenshot(path=str(HERE/filename));page.close()


with tempfile.TemporaryDirectory(prefix='pariview-store-') as tmp,sync_playwright() as p:
    tmp=Path(tmp);ctx=launch(p,tmp/'profile')
    try:
        pop=popup(ctx)
        app=ctx.new_page();app.goto('https://pariview-production.up.railway.app/#studio',wait_until='domcontentloaded')
        app.wait_for_selector('#save-settings',state='attached')
        app.evaluate("() => {for(const [id,value] of Object.entries({brightness:75,contrast:90,saturation:80,warmth:12,volume:35,highCut:45})){const e=document.getElementById(id);e.value=value;e.dispatchEvent(new Event('input',{bubbles:true}))}document.getElementById('save-settings').click()}")
        app.wait_for_function("() => document.documentElement.dataset.pariviewExtension==='synced'")
        page=ctx.new_page();page.set_viewport_size({'width':1280,'height':800});page.goto('https://www.youtube.com/watch?v=aqz-KE-bpKQ',wait_until='domcontentloaded',timeout=60000)
        page.wait_for_function("() => document.querySelector('video')?.readyState>=2",timeout=60000)
        page.wait_for_timeout(5000)
        page.mouse.click(15,15);page.evaluate("() => {const v=document.querySelector('video');v.currentTime=20;v.play().catch(()=>{})}")
        page.wait_for_timeout(1500)
        page.evaluate("() => {document.querySelector('video').play().catch(()=>{})}")
        page.wait_for_function("() => document.querySelector('video').currentTime>20.5",timeout=60000)
        status=inspect(pop,page)
        assert status['state']=='applied',status
        page.mouse.move(1200,790);page.wait_for_timeout(2300)
        page.locator('#movie_player').screenshot(path=str(tmp/'on-video.png'))
        inspect(pop,page);pop.locator('body').screenshot(path=str(tmp/'on-popup.png'))
        pop.click('#enabled');page.wait_for_timeout(400)
        status=inspect(pop,page);assert status['state']=='off',status
        page.locator('#movie_player').screenshot(path=str(tmp/'off-video.png'))
        pop.locator('body').screenshot(path=str(tmp/'off-popup.png'))
        cache=Path('/tmp/pariview-webstore-captures');cache.mkdir(exist_ok=True)
        for name in ['on-video.png','on-popup.png','off-video.png','off-popup.png']:(cache/name).write_bytes((tmp/name).read_bytes())
        render(ctx,tmp/'on-video.png',tmp/'on-popup.png','맞춘 화면과 소리를 유튜브에서도','PariView에서 편안한 설정을 고르고 저장하면 웹 영상에서도 이어서 사용할 수 있어요','한 번 저장하고 영상에서도 이어서','screenshot-01.png')
        render(ctx,tmp/'off-video.png',tmp/'off-popup.png','내가 원할 때 켜고 끄는 시청 설정','재생 위치와 플레이어 음량은 유지하면서 한 번의 스위치로 화면과 소리 효과를 해제해요','원래 화면과 소리로 언제든','screenshot-02.png')
        print('Captured 2 listing screenshots at 1280x800 from live YouTube and extension states')
    finally:
        ctx.close()
