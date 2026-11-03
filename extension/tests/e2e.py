"""Real Chromium check for the PariView extension (6 items).

Prereq: PariView web running at http://127.0.0.1:4178 (python3 web/serve.py).
Run:    python3 extension/tests/e2e.py
Checks: 1 connect before save  2 save → synced  3 filter on another page
        4 reset → defaults      5 popup off/on   6 video keeps playing
Uses Playwright's bundled Chromium (headless channel 'chromium'); Chrome stable ignores --load-extension.
"""
import hashlib, json, os, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

EXT = Path(os.environ.get('PARIVIEW_EXTENSION', Path(__file__).resolve().parents[1])).resolve()
APP = 'http://127.0.0.1:4178/'
ext_id = ''.join(chr(ord('a') + int(c, 16)) for c in hashlib.sha256(str(EXT).encode()).hexdigest()[:32])

fixture = Path(tempfile.mkdtemp(prefix='pv-ext-fixture-'))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'testsrc=size=320x180:rate=24', '-f', 'lavfi', '-i', 'sine=frequency=440', '-t', '4', '-c:v', 'libvpx-vp9', '-c:a', 'libopus', str(fixture / 'clip.webm')], check=True)
(fixture / 'site.html').write_text('<html><body><video id="v" src="clip.webm" muted playsinline loop style="width:320px"></video></body></html>')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '4193', '--bind', '127.0.0.1', '-d', str(fixture)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
R, errs = {}, []
try:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(tempfile.mkdtemp(), headless=True, channel='chromium', viewport={'width': 1440, 'height': 900}, args=[f'--disable-extensions-except={EXT}', f'--load-extension={EXT}'])
        pop = ctx.new_page(); pop.goto(f'chrome-extension://{ext_id}/popup.html')
        store = lambda: pop.evaluate('new Promise(r=>chrome.storage.local.get(null,r))')
        app = ctx.new_page(); app.on('pageerror', lambda e: errs.append('app:' + str(e)))
        app.goto(APP + '#chrome'); app.wait_for_timeout(2500)
        R['1_connected'] = app.evaluate('document.documentElement.dataset.pariviewExtension') == 'connected' and store().get('profile') is None
        app.goto(APP + '#studio'); app.wait_for_timeout(2000)
        app.evaluate("()=>{const r=document.querySelector('#brightness');r.value=60;r.dispatchEvent(new Event('input',{bubbles:true}))}")
        app.evaluate("document.querySelector('#save-settings').click()"); app.wait_for_timeout(700)
        R['2_synced'] = app.evaluate('document.documentElement.dataset.pariviewExtension') == 'synced' and store()['profile']['settings']['brightness'] == 60
        site = ctx.new_page(); site.on('pageerror', lambda e: errs.append('site:' + str(e)))
        site.goto('http://127.0.0.1:4193/site.html'); site.wait_for_timeout(600); site.mouse.click(5, 5)
        site.evaluate('document.getElementById("v").play()'); site.wait_for_timeout(800)
        F = lambda: site.evaluate('getComputedStyle(document.getElementById("v")).filter')
        R['3_filter_other_page'] = 'brightness(0.6)' in F()
        app.bring_to_front(); app.evaluate("document.querySelector('#reset-settings').click()"); app.wait_for_timeout(700)
        R['4_reset_defaults'] = store()['profile']['settings']['brightness'] == 85 and 'brightness(0.85)' in F()
        pop.reload(); pop.wait_for_timeout(400)
        pop.click('#enabled'); pop.wait_for_timeout(400); off = F()
        pop.click('#enabled'); pop.wait_for_timeout(400); on = F()
        R['5_popup_toggle'] = off == 'none' and 'brightness(0.85)' in on
        R['6_keeps_playing'] = site.evaluate('!document.getElementById("v").paused')
        ctx.close()
finally:
    srv.terminate()
R['errors'] = errs
print(json.dumps(R, ensure_ascii=False, indent=1))
sys.exit(0 if all(v for k, v in R.items() if k != 'errors') and not errs else 1)
