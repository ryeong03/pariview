from pathlib import Path
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parent
results={}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args=['--enable-webgl','--ignore-gpu-blocklist'])
 page=b.new_page(viewport={'width':1440,'height':1000})
 errors=[];bad=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:bad.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
 page.goto('http://127.0.0.1:4178',wait_until='domcontentloaded');page.wait_for_function('window.__pariview && window.__wordmark3D');page.wait_for_timeout(300)
 assert page.locator('#film').get_attribute('src')=='assets/movie-hologram.mp4'
 assert page.locator('.approved-hero').count()==1 and page.locator('#journey').count()==0
 results['logo']=page.evaluate('window.__wordmark3D.engine')
 page.locator('#brightness').fill('63');assert '63%' in page.locator('#film').get_attribute('style')
 page.locator('#original-mode').click();assert page.evaluate('window.__pariview.original')
 assert page.locator('#film').evaluate('e=>e.style.filter')=='none'
 page.locator('#custom-mode').click();page.locator('#mute-button').click();page.locator('#play-button').click();page.wait_for_timeout(500)
 assert page.evaluate('!window.__pariview.video.paused')
 assert page.evaluate('window.__pariview.audioRoute')=='compressed'
 page.locator('#compression').click();assert page.evaluate('window.__pariview.audioRoute')=='original'
 page.locator('#play-button').click();page.locator('#mute-button').click()
 page.locator('#seek').fill('8');page.wait_for_timeout(200);results['seek_time']=page.evaluate('window.__pariview.video.currentTime')
 assert abs(results['seek_time']-8)<.2
 page.locator('#notices').click();assert page.locator('#view-event-notice').is_hidden()
 page.evaluate('window.__pariview.openFit()');page.locator('[data-mode="gentle"]').count()
 page.locator('[data-mode="0"]').click();page.locator('#start-comparison').click();page.locator('[data-choose="a"]').click();page.locator('#fit-next').click();page.locator('#choose-equal').click();page.locator('#fit-next').click();page.locator('[data-listen="a"]').click();page.wait_for_timeout(150);assert page.evaluate('!window.__pariview.video.paused');page.locator('[data-choose="a"]').click();page.locator('#fit-next').click();page.locator('#skip-step').click();page.locator('#result-back').click();page.locator('[data-choose="b"]').click();page.locator('#fit-next').click();page.locator('#apply-fit').click()
 fit=page.evaluate('window.__pariview.settings');assert fit['brightness']==65 and fit['contrast']==85 and fit['volume']==22 and fit['compression']==False
 assert page.evaluate('window.__pariview.video.paused && window.__pariview.video.muted')
 page.reload(wait_until='domcontentloaded');page.wait_for_function('window.__pariview');assert page.evaluate('window.__pariview.settings')==fit
 results['fitting_and_persistence']=fit
 page.evaluate('window.__pariview.openFit()');page.keyboard.press('Escape');assert not page.locator('#fit-dialog').evaluate('e=>e.open')
 page.locator('[data-tab="research"]').first.click();assert page.locator('#research-cards .research-card').count()==6
 page.locator('[data-tab="studio"]').first.click();page.locator('#motion-toggle').click();assert page.evaluate('window.__pariview.reduced')
 page.screenshot(path=str(ROOT.parent/'assets/web-final-desktop.png'),full_page=True)
 for width in [390,768,1280]:
  page.set_viewport_size({'width':width,'height':844});page.wait_for_timeout(100)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),width
  if width==390:
   page.screenshot(path=str(ROOT.parent/'assets/web-final-mobile.png'),full_page=True)
   page.evaluate('window.__pariview.openFit()');page.locator('#start-comparison').click();assert page.locator('#fit-next').is_visible();page.keyboard.press('Escape')
 results.update(errors=errors,failed_resources=bad,responsive_widths=[390,768,1280,1440]);assert not errors
 b.close()
(ROOT/'validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False,indent=2))
