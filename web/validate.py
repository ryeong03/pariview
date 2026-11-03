from pathlib import Path
from playwright.sync_api import sync_playwright
import json, os
ROOT=Path(__file__).resolve().parent
BASE_URL=os.environ.get('PARIVIEW_BASE_URL','http://127.0.0.1:4178')
results={}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args=['--enable-webgl','--ignore-gpu-blocklist'])
 page=b.new_page(viewport={'width':1440,'height':900})
 # This regression flow keeps the user's settings across scenes with adaptation off.
 # Scene adaptation is checked separately with the real app hooks.
 page.add_init_script("sessionStorage.setItem('pariview-scene-adapt-off','1')")
 errors=[];bad=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:bad.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
 page.goto(BASE_URL,wait_until='networkidle');page.wait_for_function('window.__pariview && window.__wordmark3D && window.__pariviewMascots.length === 2')
 assert page.locator('#film').get_attribute('src')=='assets/scenes/tears-lab.mp4'
 assert page.evaluate('window.__pariview.video.duration')==45
 assert page.evaluate('window.__pariview.scenes.length')==3
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
 # Every licensed scene is 45 seconds and keeps the chosen settings and its own map.
 unchanged=page.evaluate('window.__pariview.settings')
 results['scenes']=[]
 for scene in ['sintel','bunny','tears-lab']:
  page.locator('#choose-scene').click();page.locator(f'[data-scene="{scene}"]').click()
  page.wait_for_function('window.__pariview.video.readyState>=2 && window.__pariview.events.length>0')
  assert page.evaluate('window.__pariview.scene.id')==scene
  assert page.evaluate('window.__pariview.settings')==unchanged
  assert page.evaluate('window.__pariview.video.duration')==45
  page.locator('#seek').fill('30');page.wait_for_timeout(150)
  assert abs(page.evaluate('window.__pariview.video.currentTime')-30)<.1
  if scene=='sintel':
   page.locator('#seek').fill('10');page.wait_for_timeout(150);assert '혼자' in page.locator('#film-caption').inner_text()
  if scene=='bunny':assert page.locator('#film-caption').is_hidden()
  results['scenes'].append(page.evaluate('({id:window.__pariview.scene.id,duration:window.__pariview.video.duration,events:window.__pariview.events.length})'))
 # End card changes the clip; it does not reset the user's settings.
 page.locator('#seek').fill('44.8');page.locator('#play-button').click();page.wait_for_selector('#scene-ended:not([hidden])')
 page.locator('#next-scene').click();page.wait_for_function('window.__pariview.scene.id === "sintel" && !window.__pariview.video.paused')
 assert page.evaluate('window.__pariview.settings')==unchanged
 page.locator('#play-button').click();page.locator('#choose-scene').click();page.locator('[data-scene="tears-lab"]').click();page.wait_for_function('window.__pariview.video.readyState>=2')
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
 page.locator('#play-comparison').click();page.wait_for_function('window.__pariview.comparisonPlaying');page.wait_for_timeout(1000)
 previews=page.locator('.fit-preview').evaluate_all('vs=>vs.map(v=>({paused:v.paused,rate:v.playbackRate,time:v.currentTime}))')
 assert all(not v['paused'] and v['rate']==.75 for v in previews)
 assert abs(previews[0]['time']-previews[1]['time'])<.08
 results['simultaneous_comparison']=previews
 page.locator('#play-comparison').click();assert page.locator('.fit-preview').evaluate_all('vs=>vs.every(v=>v.paused)')
 page.locator('[data-choose="a"]').click();page.locator('#fit-next').click();page.locator('#choose-equal').click();page.locator('#fit-next').click()
 page.locator('[data-listen="a"]').click();page.wait_for_function('!window.__pariview.video.paused',timeout=10000)
 assert page.evaluate('window.__pariview.video.playbackRate')==.75
 page.locator('[data-choose="a"]').click();page.locator('#fit-next').click();page.locator('[data-choose="b"]').click();page.locator('#fit-next').click();page.locator('[data-choose="b"]').click();page.locator('#fit-next').click();page.locator('#result-back').click();page.locator('#fit-next').click();page.locator('#apply-fit').click()
 fit=page.evaluate('window.__pariview.settings');assert fit['brightness']==65 and fit['contrast']==80 and fit['volume']==22 and not fit['compression'] and fit['easyCaptions']
 assert page.evaluate('window.__pariview.video.paused && window.__pariview.video.muted && window.__pariview.video.playbackRate===1')
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
  scene_layouts=[]
  for sid in ['sintel','bunny','tears-lab']:
   page.evaluate('(id)=>window.__pariview.selectScene(id)',sid)
   page.wait_for_function('window.__pariview.video.readyState>=2')
   page.evaluate("document.querySelector('#watch-studio').scrollIntoView({behavior:'instant',block:'start'})")
   details=page.locator('.timeline-details').bounding_box();end=details['y']+details['height']
   assert end<=height+2,(width,height,sid,end)
   scene_layouts.append({'scene':sid,'detailsBottom':round(end,1)})
  box=page.locator('.preferences').bounding_box();bottom=box['y']+box['height'];assert bottom<=height+2,(width,height,bottom)
  results['viewports'].append({'width':width,'height':height,'controlsBottom':round(bottom,1),'sceneLayouts':scene_layouts})
  if width in [1440,390]:page.screenshot(path=str(ROOT.parent/f'assets/verified-studio-{width}.png'))
  if width==390:
   page.evaluate('window.__pariview.openFit()');page.locator('#start-comparison').click();assert page.locator('#fit-next').is_visible();page.keyboard.press('Escape')
   page.locator('[data-tab="chrome"]').first.click();assert page.locator('.mobile-install-note').is_visible();assert page.locator('a[download]').is_hidden()
   page.locator('[data-tab="studio"]').first.click();page.screenshot(path=str(ROOT.parent/'assets/verified-hero-mobile.png'))
 results.update(errors=errors,failed_resources=bad);assert not errors;assert not bad
 b.close()
(ROOT/'validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in results.items() if k!='five_profiles'},ensure_ascii=False,indent=2))
