from pathlib import Path
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parent
results={}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args=['--enable-webgl','--ignore-gpu-blocklist'])
 page=b.new_page(viewport={'width':1440,'height':900})
 errors=[];bad=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:bad.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
 page.goto('http://127.0.0.1:4178',wait_until='networkidle');page.wait_for_function('window.__pariview && window.__wordmark3D && window.__pariviewMascots.length === 2')
 assert page.locator('#film').get_attribute('src')=='assets/movie-hologram.mp4'
 assert page.locator('.approved-hero').count()==1 and page.locator('#journey').count()==0
 results['logo']=page.evaluate('window.__wordmark3D.engine')
 results['mascots']=page.evaluate('window.__pariviewMascots.map(m=>({wizard:m.wizard,engine:m.engine}))')
 center=page.locator('.hero-copy h1').bounding_box();assert abs(center['x']+center['width']/2-720)<1
 page.locator('#brightness').fill('63');assert '63%' in page.locator('#film').get_attribute('style')
 page.locator('#original-mode').click();assert page.evaluate('window.__pariview.original')
 assert page.locator('#film').evaluate('e=>e.style.filter')=='none'
 page.locator('#custom-mode').click();page.locator('#mute-button').click();page.locator('#play-button').click();page.wait_for_timeout(300)
 assert page.evaluate('!window.__pariview.video.paused')
 assert page.evaluate('window.__pariview.audioRoute')=='compressed'
 page.locator('#expand-settings').click();page.locator('#tab-audio').click();page.locator('#compression').click();assert page.evaluate('window.__pariview.audioRoute')=='original'
 page.locator('#play-button').click();page.locator('#mute-button').click()
 page.locator('#seek').fill('4');page.wait_for_timeout(200);assert page.locator('#film-caption').is_visible()
 page.locator('#tab-cognitive').click();page.locator('#easyCaptions').click();assert '맞추고' in page.locator('#film-caption').inner_text()
 page.locator('#open-recap').click();assert page.locator('#recap-dialog').is_visible();assert '맞추고' in page.locator('#recap-body').inner_text();assert page.locator('#caption-seek').count()==1;page.locator('#close-recap').click()
 page.locator('#seek').fill('8');page.wait_for_timeout(200);results['seek_time']=page.evaluate('window.__pariview.video.currentTime');assert abs(results['seek_time']-8)<.2
 page.locator('#tab-visual').click();page.locator('#notices').click();assert page.locator('#view-event-notice').is_hidden()
 # Five distinct profiles survive applying all skipped comparisons.
 profile_results={}
 for i,profile in enumerate(['gentle','focus','clarity','soft','everyday']):
  page.evaluate('window.__pariview.openFit()');assert page.locator('.mode-option').count()==5
  page.locator(f'[data-mode="{i}"]').click();page.locator('#start-comparison').click()
  for n in range(5):page.locator('#skip-step').click()
  page.locator('#apply-fit').click();state=page.evaluate('window.__pariview.settings');assert state['profileId']==profile;profile_results[profile]=state
 assert profile_results['gentle']['backgroundReduction']==40
 assert profile_results['focus']['dialogueBoost']
 assert profile_results['clarity']['autoBrightness'] and profile_results['clarity']['boldCaptions']
 assert profile_results['soft']['easyCaptions']
 assert profile_results['everyday']['warmth']==25 and profile_results['everyday']['breakReminder']
 results['five_profiles']=profile_results
 # Explicit preferences, uncertainty, back navigation, live audio, then cognitive choice.
 page.evaluate('window.__pariview.openFit()');page.locator('[data-mode="0"]').click();page.locator('#start-comparison').click()
 page.locator('[data-choose="a"]').click();page.locator('#fit-next').click();page.locator('#choose-equal').click();page.locator('#fit-next').click()
 page.locator('[data-listen="a"]').click();page.wait_for_function('!window.__pariview.video.paused',timeout=3500)
 page.locator('[data-choose="a"]').click();page.locator('#fit-next').click();page.locator('[data-choose="b"]').click();page.locator('#fit-next').click();page.locator('[data-choose="b"]').click();page.locator('#fit-next').click();page.locator('#result-back').click();page.locator('#fit-next').click();page.locator('#apply-fit').click()
 fit=page.evaluate('window.__pariview.settings');assert fit['brightness']==65 and fit['contrast']==80 and fit['volume']==22 and not fit['compression'] and fit['easyCaptions']
 assert page.evaluate('window.__pariview.video.paused && window.__pariview.video.muted')
 page.reload(wait_until='networkidle');assert page.evaluate('window.__pariview.settings')==fit
 results['fitting_and_persistence']=fit
 page.evaluate('window.__pariview.openFit()');page.keyboard.press('Escape');assert not page.locator('#fit-dialog').evaluate('e=>e.open')
 page.locator('[data-tab="research"]').last.click();assert page.locator('#research-cards .research-card').count()==6
 page.locator('label:has(input[value="both"])').click();page.locator('label:has(input[value="no"])').click();page.locator('#recommend-form button[type=submit]').click();page.locator('#start-recommended').click()
 assert page.locator('[data-mode="0"]').get_attribute('aria-pressed')=='true';assert page.locator('[data-mode="0"] .recommend-badge').count()==1
 page.locator('#start-comparison').click()
 for i in range(5):page.locator('#skip-step').click()
 page.locator('#apply-fit').click();assert not page.evaluate('window.__pariview.settings.notices')
 with page.expect_download() as dl:page.locator('#download-profile').click()
 assert dl.value.suggested_filename=='pariview-settings.json'
 page.locator('#reset-settings').click();state=page.evaluate('window.__pariview.settings');assert state['brightness']==85 and state['contrast']==90 and state['volume']==35 and not state['easyCaptions'] and state['saturation']==100
 assert page.evaluate("JSON.parse(localStorage.getItem('pariview-fit-v1')).settings.brightness")==85
 page.locator('#motion-toggle').click();assert page.evaluate('window.__pariview.reduced')
 results['reset']=state
 # Entire default viewing workspace fits; no horizontal overflow at supported sizes.
 viewports=[(1440,900),(1280,720),(768,1024),(390,844)]
 results['viewports']=[]
 for width,height in viewports:
  page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),width
  page.evaluate("document.querySelector('#watch-studio').scrollIntoView({behavior:'instant',block:'start'})")
  box=page.locator('.preferences').bounding_box();bottom=box['y']+box['height'];assert bottom<=height+2,(width,height,bottom)
  results['viewports'].append({'width':width,'height':height,'controlsBottom':round(bottom,1)})
  if width in [1440,390]:page.screenshot(path=str(ROOT.parent/f'assets/verified-studio-{width}.png'))
  if width==390:
   page.evaluate('window.__pariview.openFit()');page.locator('#start-comparison').click();assert page.locator('#fit-next').is_visible();page.keyboard.press('Escape')
   page.locator('[data-tab="chrome"]').first.click();assert page.locator('.mobile-install-note').is_visible();assert page.locator('a[download]').is_hidden()
   page.locator('[data-tab="studio"]').first.click();page.screenshot(path=str(ROOT.parent/'assets/verified-hero-mobile.png'))
 results.update(errors=errors,failed_resources=bad);assert not errors;assert not bad
 b.close()
(ROOT/'validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in results.items() if k!='five_profiles'},ensure_ascii=False,indent=2))
