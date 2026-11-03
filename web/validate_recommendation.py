"""Independent recommendation UI checks; provider routes are mocked explicitly.

Run against ai/server.py: uv run --with playwright python web/validate_recommendation.py
No user keys, external model calls, repository mutations, or deployment actions.
"""
import argparse
import json
from playwright.sync_api import sync_playwright

HTML = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/styles.css"><button data-action="ai-recommend">연구 기반 PariView-AI 추천받기</button>
<video id="film" src="/assets/scenes/tears-lab.mp4" muted></video><script type="module">
import {initRecommendation} from '/recommendation.js'; import {defaults} from '/settings.js';
window.recState={settings:{...defaults,captionYellow:true},saved:0,preview:null,compared:null};
window.rec=initRecommendation({getSettings:()=>({...recState.settings}),
onPreview:next=>{recState.preview=next},onCancelPreview:()=>{recState.preview=null},
onApply:(next,meta)=>{recState.settings=next;recState.saved++;recState.meta=meta},
onCompare:(axis,next,meta)=>{recState.compared={axis,next,meta}},getComparisons:()=>[]});
window.ready=true;</script></html>'''


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base-url',default='http://127.0.0.1:4189');args=parser.parse_args()
    checks=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/recommendation-harness',lambda route:route.fulfill(status=200,content_type='text/html',body=HTML))
        page.goto(args.base_url+'/recommendation-harness');page.wait_for_function('window.ready')
        def open_form():
            page.locator('[data-action="ai-recommend"]').click()
            page.locator('.pv-rec-form').wait_for()
        def submit():
            page.locator('.pv-rec-form [type="submit"]').click()
            page.locator('[data-apply]').wait_for()
        open_form();page.locator('input[value="light"]').check();submit()
        assert page.locator('.pv-rec-method').inner_text()=='연구 기반 기본 제안'
        assert page.evaluate('recState.saved')==0
        assert page.locator('[data-setting="brightness"]').input_value()=='77'
        assert page.locator('.pv-rec-caption').evaluate('(el)=>getComputedStyle(el).color')=='rgb(255, 224, 61)'
        assert '미연결' not in page.locator('.pv-rec').inner_text()
        assert '오류' not in page.locator('.pv-rec').inner_text()
        checks.append('unconfigured gracefully offers honest default with no save')
        page.locator('[data-setting="brightness"]').fill('72')
        page.locator('[data-preview]').click();page.wait_for_function('recState.preview?.brightness===72')
        assert page.evaluate('recState.settings.brightness')==85
        page.locator('[data-cancel]').click()
        assert page.evaluate('recState.preview===null && recState.saved===0 && recState.settings.brightness===85 && recState.settings.captionYellow===true')
        checks.append('edit and preview are reversible on cancel')
        open_form();submit();page.locator('[data-setting="brightness"]').fill('71')
        page.locator('[data-apply]').click()
        assert page.evaluate('recState.saved===1 && recState.settings.brightness===71 && recState.meta.edited && recState.settings.captionYellow===true')
        checks.append('only explicit apply saves edited settings')
        open_form();submit();page.locator('[data-compare]').click()
        assert page.evaluate('recState.saved===1 && recState.compared.axis==="brightness" && recState.compared.next.captionYellow===true')
        checks.append('next comparison transfers draft without saving')
        page.route('**/api/recommendation/status',lambda route:route.fulfill(json={'configured':True}))
        page.route('**/api/recommendation',lambda route:route.fulfill(json={'source':'ai','evidenceVersion':'2026-11-04-v1','selection':{'actionIds':['softer_light'],'nextComparisonId':'brightness'}}))
        open_form();submit()
        assert page.locator('.pv-rec-method').inner_text()=='AI 추천'
        assert page.locator('.pv-rec-caption').evaluate('(el)=>getComputedStyle(el).color')=='rgb(255, 224, 61)'
        page.locator('[data-cancel]').click();checks.append('valid mocked AI response has distinct provenance')
        page.unroute('**/api/recommendation')
        page.route('**/api/recommendation',lambda route:route.fulfill(json={'source':'ai','evidenceVersion':'2026-11-04-v1','selection':{'actionIds':['invented'],'nextComparisonId':'diagnosis'}}))
        open_form();submit()
        assert page.locator('.pv-rec-method').inner_text()=='연구 기반 기본 제안'
        page.locator('[data-cancel]').click();checks.append('invalid mocked model IDs cannot enter the result')
        page.unroute('**/api/recommendation')
        page.route('**/api/recommendation',lambda route:route.fulfill(status=503,body='unavailable'))
        open_form();submit();assert page.locator('.pv-rec-method').inner_text()=='연구 기반 기본 제안'
        page.locator('[data-cancel]').click();checks.append('provider HTTP failure quietly returns default')
        for value in [True,False,None]:
            page.evaluate('(value)=>{if(value===null)delete recState.settings.captionYellow;else recState.settings.captionYellow=value}',value)
            open_form();submit()
            color=page.locator('.pv-rec-caption').evaluate('(el)=>getComputedStyle(el).color')
            assert color==('rgb(255, 224, 61)' if value else 'rgb(255, 255, 255)')
            page.locator('[data-apply]').click()
            assert page.evaluate('recState.settings.captionYellow') is (value is True)
        checks.append('yellow, white and legacy preferences survive preview and apply without colour recommendations')
        for width in [390,768,1440]:
            page.set_viewport_size({'width':width,'height':900});open_form();submit()
            overflow=page.locator('.pv-rec').evaluate('(el)=>el.scrollWidth>el.clientWidth+1')
            assert not overflow, width
            page.locator('.pv-rec-evidence summary').click()
            assert page.locator('.pv-rec-evidence a').count()>=2
            page.screenshot(path=f'/tmp/pariview-recommendation-{width}.png',full_page=False)
            page.keyboard.press('Escape');assert not page.locator('.pv-rec').is_visible()
        checks.append('390/768/1440 responsive layout, research links and Escape close')
        page.unroute('**/api/recommendation');page.unroute('**/api/recommendation/status')
        page.set_viewport_size({'width':1440,'height':1000})
        page.evaluate('localStorage.setItem("pariview-fit-v1",JSON.stringify({settings:{brightness:85,captionYellow:true}}))')
        page.goto(args.base_url+'/');page.wait_for_function('window.__pariview?.recommendationUI')
        page.locator('.hero-actions [data-action="fit"]').click()
        assert page.locator('.mode-option').count()==5
        page.locator('#close-fit').click()
        before=page.evaluate('({settings:window.__pariview.settings,stored:localStorage.getItem("pariview-fit-v1"),original:window.__pariview.original})')
        def open_integrated():
            page.locator('.hero-actions [data-action="ai-recommend"]').click();page.locator('.pv-rec-form').wait_for()
        open_integrated();page.locator('.pv-rec input[value="light"]').check();submit()
        page.locator('[data-setting="brightness"]').fill('73');page.locator('[data-preview]').click()
        page.wait_for_function('window.__pariview.settings.brightness===73')
        assert page.evaluate('localStorage.getItem("pariview-fit-v1")')==before['stored']
        page.locator('[data-listen]').click();page.wait_for_function('!document.querySelector(".pv-rec video").muted')
        page.locator('[data-cancel]').click()
        after=page.evaluate('({settings:window.__pariview.settings,stored:localStorage.getItem("pariview-fit-v1"),original:window.__pariview.original})')
        assert before==after
        assert after['settings']['captionYellow'] is True
        open_integrated();submit();page.locator('[data-setting="brightness"]').fill('74');page.locator('[data-apply]').click()
        assert page.evaluate('JSON.parse(localStorage.getItem("pariview-fit-v1")).settings.brightness')==74
        assert page.evaluate('JSON.parse(localStorage.getItem("pariview-fit-v1")).settings.captionYellow') is True
        open_integrated();submit();page.locator('[data-compare]').click()
        assert page.locator('#fit-dialog').is_visible()
        assert '밝기' in page.locator('.fit-heading').inner_text()
        assert page.evaluate('JSON.parse(localStorage.getItem("pariview-fit-v1")).settings.brightness')==74
        page.locator('#close-fit').click()
        checks.append('integrated entries preserve 5 profiles, preview audio/cancel, save and next A/B hooks')
        assert not errors, errors
        browser.close()
    print(json.dumps({'passed':checks,'pageErrors':errors,'provider':'mocked only'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
