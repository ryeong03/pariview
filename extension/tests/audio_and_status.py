"""Deterministic real-browser regressions for audio, status, lifecycle and bypass."""
import functools
import http.server
import json
import subprocess
import tempfile
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright
from helpers import launch, popup, save, inspect, instrument, evaluate, check

results = {}
with tempfile.TemporaryDirectory(prefix='pariview-audio-') as tmp, sync_playwright() as p:
    root = Path(tmp)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','testsrc=size=320x180:rate=24','-f','lavfi','-i','sine=frequency=440','-t','6','-c:v','libvpx-vp9','-c:a','libopus',str(root/'clip.webm')],check=True)
    (root/'video.html').write_text('<!doctype html><title>Video fixture</title><button id="play" onclick="v.play()">Play</button><video id="v" src="clip.webm" loop preload="auto" style="width:320px;filter:grayscale(0.2)"></video>')
    (root/'empty.html').write_text('<!doctype html><h1>No video</h1>')
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=tmp))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    port = server.server_port
    base = f'http://127.0.0.1:{port}'
    ctx = launch(p,root/'profile')
    try:
        pop = popup(ctx)
        check(results,'empty_profile_has_public_app_link',pop.locator('#open-empty').is_visible())
        page = ctx.new_page();page.goto(base+'/video.html');page.wait_for_function('v.readyState >= 2')
        w = instrument(ctx,page)
        save(pop,brightness=60,contrast=95,saturation=75,warmth=20,volume=35,highCut=0,compression=False)
        s = inspect(pop,page)
        check(results,'waits_for_gesture_without_audio_takeover',s['state']=='gesture' and evaluate(w,'__pvQA.parameters().sources')==0,s)
        page.click('#play');page.wait_for_timeout(700)
        s = inspect(pop,page);params=evaluate(w,'__pvQA.parameters()');signal=evaluate(w,'__pvQA.measure()')
        check(results,'actual_gain_035_and_audio_signal',s['state']=='applied' and params['context']=='running' and abs(signal['ratio']-.35)<.02,{'parameters':params,'signal':signal})
        page.evaluate('v.playbackRate=0.75;v.volume=0.6')
        before=page.evaluate('v.currentTime')
        pop.click('#enabled');page.wait_for_timeout(250)
        signal=evaluate(w,'__pvQA.measure()');s=inspect(pop,page)
        check(results,'off_restores_original_filter_and_exact_audio_bypass',page.evaluate('getComputedStyle(v).filter')=='grayscale(0.2)' and evaluate(w,'__pvQA.parameters().bypass') and abs(signal['ratio']-1)<.02 and s['state']=='off',signal)
        check(results,'off_keeps_playback_volume_rate',page.evaluate('!v.paused && v.volume===0.6 && v.playbackRate===0.75 && !v.muted') and page.evaluate('v.currentTime')!=before)
        pop.click('#enabled');page.wait_for_timeout(300)
        check(results,'on_reuses_audio_graph',evaluate(w,'__pvQA.parameters().sources')==1 and inspect(pop,page)['state']=='applied')
        save(pop,brightness=85,contrast=90,volume=0,highCut=55,dialogueBoost=True,compression=True)
        page.wait_for_timeout(900);params=evaluate(w,'__pvQA.parameters()');signal=evaluate(w,'__pvQA.measure()')
        check(results,'zero_volume_and_supported_effect_parameters',signal['outputRMS']<1e-5 and abs(params['filters'][0]['frequency']-20000*(.16**.55))<2 and abs(params['filters'][1]['gain']-4)<.001 and params['compression'][0]['ratio']==5,{'parameters':params,'signal':signal})
        page.evaluate('v.muted=true');s=inspect(pop,page)
        check(results,'muted_state_is_explicit', '음소거' in s['detail'],s)
        save(pop,brightness=85,contrast=90,volume=35,compression=True)
        page.evaluate("v.muted=false;v.src='clip.webm?next=1';v.load();v.play()")
        page.wait_for_timeout(600)
        check(results,'same_element_new_source',inspect(pop,page)['state']=='applied' and evaluate(w,'__pvQA.parameters().sources')==1)
        page.evaluate("v.remove();const n=document.createElement('video');n.id='v';n.src='clip.webm';n.loop=true;n.style.width='320px';document.body.append(n);n.play()")
        page.wait_for_timeout(700)
        check(results,'replacement_video_attaches',inspect(pop,page)['state']=='applied' and evaluate(w,'__pvQA.parameters().sources')==2)
        page.goto(base+'/empty.html')
        check(results,'no_video_is_explicit',inspect(pop,page)['state']=='no-video')
        page.evaluate("const v=document.createElement('video');v.id='v';v.src='http://localhost:"+str(port)+"/clip.webm';v.style.width='320px';document.body.append(v)")
        page.wait_for_function('v.readyState >= 2')
        w=instrument(ctx,page)
        page.mouse.click(5,5);page.evaluate('v.play()');page.wait_for_timeout(300)
        s=inspect(pop,page)
        check(results,'cross_origin_keeps_native_audio',s['state']=='visual-only' and evaluate(w,'__pvQA.parameters().sources')==0 and page.evaluate('!v.paused'),s)
        page.goto(base+'/video.html');page.wait_for_function('v.readyState>=2');w=instrument(ctx,page)
        page.evaluate("v.dispatchEvent(new Event('encrypted'))")
        page.click('#play');page.wait_for_timeout(300)
        check(results,'encrypted_event_prevents_takeover',inspect(pop,page)['state']=='visual-only' and evaluate(w,'__pvQA.parameters().sources')==0)
        page.goto(base+'/video.html');page.wait_for_function('v.readyState>=2');w=instrument(ctx,page);page.click('#play');page.wait_for_timeout(300)
        page.evaluate("v.dispatchEvent(new Event('encrypted'))")
        check(results,'protected_transition_requires_reload',inspect(pop,page)['state']=='reload-required')
        page.goto(base+'/empty.html')
        page.evaluate("const f=document.createElement('iframe');f.src='video.html';document.body.append(f)")
        page.wait_for_timeout(600)
        s=inspect(pop,page)
        check(results,'iframe_video_is_detected',s['state']!='no-video' and sum(len(f['videos']) for f in s['frames'])==1,s)
        # Browser-internal pages have no content script
        page.goto('chrome://version')
        check(results,'unsupported_tab_is_explicit',inspect(pop,page)['state']=='unavailable')
        print(json.dumps({'passed':len(results),'results':results},ensure_ascii=False,indent=2))
    finally:
        ctx.close();server.shutdown();server.server_close()
