"""Live YouTube smoke test in an unsigned-in temporary Chromium profile.

Uses real PariView save/reset buttons, actual YouTube media, and native SPA links
Signal taps measure digital output; this is not a human listening evaluation
"""
import argparse
import json
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from helpers import launch, popup, inspect, instrument, evaluate, check

parser=argparse.ArgumentParser()
parser.add_argument('--app',default='https://pariview-production.up.railway.app/')
parser.add_argument('--artifacts',default='/tmp/pariview-extension-qa')
args=parser.parse_args()
artifacts=Path(args.artifacts);artifacts.mkdir(parents=True,exist_ok=True)
results={}
with tempfile.TemporaryDirectory(prefix='pariview-youtube-') as profile, sync_playwright() as p:
    ctx=launch(p,profile)
    try:
        pop=popup(ctx)
        app=ctx.new_page();app.goto(args.app+'#studio',wait_until='domcontentloaded');app.wait_for_selector('#brightness',state='attached')
        app.wait_for_function("document.documentElement.dataset.pariviewExtension==='connected'")
        check(results,'public_app_connected',True)
        desired={'brightness':60,'contrast':95,'saturation':75,'warmth':20,'volume':35,'highCut':45}
        app.evaluate("values => {for(const [id,value] of Object.entries(values)){const el=document.getElementById(id);el.value=value;el.dispatchEvent(new Event('input',{bubbles:true}));}if(document.getElementById('dialogueBoost').getAttribute('aria-checked')!=='true')document.getElementById('dialogueBoost').click()}",desired)
        app.wait_for_timeout(300)
        check(results,'preview_does_not_sync',pop.evaluate('chrome.storage.local.get("profile")').get('profile') is None)
        app.evaluate("document.getElementById('save-settings').click()")
        app.wait_for_function("document.documentElement.dataset.pariviewExtension==='synced'")
        stored=pop.evaluate('chrome.storage.local.get("profile")')['profile']['settings']
        check(results,'saved_settings_sync',all(stored[k]==v for k,v in desired.items()) and stored['dialogueBoost'])
        page=ctx.new_page();page.goto('https://www.youtube.com/watch?v=R6MlUcmOul8',wait_until='domcontentloaded',timeout=60000)
        page.wait_for_function("() => document.querySelector('video')?.readyState>=2",timeout=60000)
        w=instrument(ctx,page)
        check(results,'youtube_visual_filter',page.locator('video').first.evaluate('(v)=>getComputedStyle(v).filter')=='brightness(0.6) contrast(0.95) saturate(0.75) sepia(0.07)')
        page.mouse.click(15,15)
        page.evaluate("() => {const v=document.querySelector('video');v.currentTime=55;return v.play()}")
        page.wait_for_function("() => !document.querySelector('video').paused && document.querySelector('video').currentTime>55.5",timeout=30000)
        page.wait_for_timeout(500)
        status=inspect(pop,page);params=evaluate(w,'__pvQA.parameters()');signal=evaluate(w,'__pvQA.measure()')
        check(results,'youtube_audio_effects_and_nonzero_signal',status['state']=='applied' and signal['inputRMS']>1e-4 and signal['outputRMS']>1e-5 and abs(params['gain'][0]-.35)<.001 and abs(params['filters'][0]['frequency']-20000*(.16**.45))<2 and abs(params['filters'][1]['gain']-4)<.001,{'parameters':params,'signal':signal,'status':status['state']})
        page.screenshot(path=str(artifacts/'youtube-applied.png'))
        pop.locator('body').screenshot(path=str(artifacts/'popup-applied.png'))
        page.evaluate('window.__pariviewNavigationSentinel=crypto.randomUUID()')
        sentinel=page.evaluate('window.__pariviewNavigationSentinel')
        # Follow a real YouTube recommendation link, preserving the SPA document
        candidate=page.locator('a[href^="/watch?v="]').evaluate_all("els=>els.filter(e=>e.getClientRects().length && !e.href.includes('v=R6MlUcmOul8')).map(e=>e.getAttribute('href'))[0]")
        if not candidate:
            raise AssertionError('No visible YouTube recommendation available for native SPA test')
        next_link=page.locator(f'a[href={json.dumps(candidate)}]').filter(visible=True).first
        next_link.click(timeout=15000)
        page.wait_for_function("() => !location.search.includes('v=R6MlUcmOul8')",timeout=30000)
        page.wait_for_function("() => document.querySelector('video')?.readyState>=2",timeout=60000)
        page.mouse.click(15,15)
        page.evaluate("document.querySelector('video').play()")
        page.wait_for_timeout(1500)
        status=inspect(pop,page)
        check(results,'youtube_native_spa_next_video',page.evaluate('window.__pariviewNavigationSentinel')==sentinel and status['state']=='applied' and 'brightness(0.6)' in page.locator('video').first.evaluate('(v)=>getComputedStyle(v).filter'),{'video':page.url.split('&')[0],'status':status['state']})
        video_before=page.locator('video').first.evaluate('(v)=>({time:v.currentTime,rate:v.playbackRate,volume:v.volume,muted:v.muted})')
        pop.click('#enabled');page.wait_for_timeout(300)
        status=inspect(pop,page);params=evaluate(w,'__pvQA.parameters()');signal=evaluate(w,'__pvQA.measure()')
        after=page.locator('video').first.evaluate('(v)=>({time:v.currentTime,rate:v.playbackRate,volume:v.volume,muted:v.muted,paused:v.paused,filter:getComputedStyle(v).filter})')
        check(results,'youtube_off_restores_signal_and_keeps_playing',status['state']=='off' and params['bypass'] and after['filter']=='none' and not after['paused'] and after['time']>video_before['time'] and all(after[k]==video_before[k] for k in ['rate','volume','muted']) and signal['inputRMS']>1e-4 and abs(signal['ratio']-1)<.06,{'signal':signal,'playback':after})
        pop.click('#enabled');page.wait_for_timeout(400)
        check(results,'youtube_on_again',inspect(pop,page)['state']=='applied' and not page.locator('video').first.evaluate('(v)=>v.paused'))
        app.evaluate("document.getElementById('reset-settings').click()")
        page.wait_for_timeout(600)
        store=pop.evaluate('chrome.storage.local.get("profile")')['profile']['settings']
        params=evaluate(w,'__pvQA.parameters()')
        check(results,'public_reset_reaches_live_youtube',store['brightness']==85 and store['contrast']==90 and store['volume']==35 and not store['dialogueBoost'] and 'brightness(0.85) contrast(0.9)' in page.locator('video').first.evaluate('(v)=>getComputedStyle(v).filter') and abs(params['filters'][1]['gain'])<.01 and not page.locator('video').first.evaluate('(v)=>v.paused'),params)
        app.evaluate("() => {const r=document.getElementById('brightness');r.value=50;r.dispatchEvent(new Event('input',{bubbles:true}))}")
        page.wait_for_timeout(300)
        check(results,'unsaved_preview_does_not_change_youtube',pop.evaluate('chrome.storage.local.get("profile")')['profile']['settings']['brightness']==85 and 'brightness(0.85)' in page.locator('video').first.evaluate('(v)=>getComputedStyle(v).filter'))
        page.screenshot(path=str(artifacts/'youtube-reset.png'))
        report={'app':args.app,'browser':ctx.browser.version,'human_listening':False,'results':results}
        (artifacts/'youtube-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        print(json.dumps({'passed':len(results),'artifacts':str(artifacts)},ensure_ascii=False))
    finally:
        ctx.close()
