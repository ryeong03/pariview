import {animate} from './vendor/anime.esm.min.js';
import {createBrand} from './brand.js';
import {createFalcon} from './mascot.js';
import {research} from './research.js';
import {scenes} from './scenes.js';
import {initRecommendation} from './recommendation.js';
import {initInteractions} from './interactions.js';
import {initExtensionConnection} from './extension-connect.js';
import {renderResearchPage} from './research-page.js';
import {defaults,ranges,toggles,modes,normalize,modeSettings} from './settings.js';
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const KEY='pariview-fit-v1',mediaQuery=matchMedia('(prefers-reduced-motion: reduce)');
let noticeEvents=[],noticeShown=null;
let reduced=mediaQuery.matches,original=false,muted=true,settings={...defaults},saved=false,recommendation=null;
try{const data=JSON.parse(localStorage.getItem(KEY));if(data?.settings){settings=normalize(data.settings);saved=true;}}catch{}
const video=$('#film');
let currentScene=scenes[0],pendingScenePlay=false,captionHistoryKey='';
const escapeHTML=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
createBrand($('#brand-symbol'),()=>reduced).catch(()=>{});
createBrand($('#brand-wordmark'),()=>reduced).catch(()=>{});
let audioContext,source,gain,compressor,lowpass,speechEQ,audioRoute='';
function notify(message){$('#toast').textContent=message;gsap.killTweensOf('#toast');gsap.to('#toast',{opacity:1,y:-5,duration:reduced?0:.2});gsap.to('#toast',{opacity:0,y:0,duration:.3,delay:3});}
function initAudio(){
 if(audioContext){audioContext.resume();return;}
 const AC=window.AudioContext||window.webkitAudioContext;if(!AC)return;
 audioContext=new AC();source=audioContext.createMediaElementSource(video);gain=audioContext.createGain();compressor=audioContext.createDynamicsCompressor();
 compressor.threshold.value=-25;compressor.knee.value=22;compressor.ratio.value=5;compressor.attack.value=.008;compressor.release.value=.25;
 lowpass=audioContext.createBiquadFilter();lowpass.type='lowpass';lowpass.Q.value=.5;
 speechEQ=audioContext.createBiquadFilter();speechEQ.type='peaking';speechEQ.frequency.value=3000;speechEQ.Q.value=1;
 source.connect(lowpass);lowpass.connect(speechEQ);gain.connect(audioContext.destination);routeAudio();audioContext.resume();
}
function routeAudio(opts=settings,bypass=original){
 if(!source)return;
 const route=!bypass&&opts.compression?'compressed':'original';
 if(audioRoute!==route){speechEQ.disconnect();compressor.disconnect();if(route==='compressed'){speechEQ.connect(compressor);compressor.connect(gain);}else speechEQ.connect(gain);audioRoute=route;}
 const now=audioContext.currentTime;
 lowpass.frequency.setTargetAtTime(bypass?20000:20000*Math.pow(.16,opts.highCut/100),now,.08);
 speechEQ.gain.setTargetAtTime(!bypass&&opts.dialogueBoost?4:0,now,.08);
 gain.gain.setTargetAtTime(opts.volume/100,now,.08);
}
function fillRange(el){el.style.setProperty('--pct',100*(Number(el.value)-Number(el.min))/(Number(el.max)-Number(el.min))+'%');}
let sceneLift=1,furthestTime=0;
function applyLook(){
 video.style.filter=original?'none':`brightness(${settings.brightness*sceneLift}%) contrast(${settings.contrast}%) saturate(${settings.saturation}%) sepia(${settings.warmth*.35}%)`;
}
function reflect(){
 for(const key of Object.keys(ranges)){const el=$('#'+key);if(!el)continue;el.value=settings[key];$('#'+key+'-value').value=settings[key]+(key==='captionSize'?'px':'%');fillRange(el);}
 for(const key of toggles){$('#'+key)?.classList.toggle('on',settings[key]);$('#'+key)?.setAttribute('aria-checked',String(settings[key]));}
 $('#custom-mode').classList.toggle('active',!original);$('#original-mode').classList.toggle('active',original);
 $('#custom-mode').setAttribute('aria-pressed',String(!original));$('#original-mode').setAttribute('aria-pressed',String(original));
 $('#profile-state').textContent=saved?'내 PariView 설정이 저장돼 있어요':'아직 피팅 전이에요';
 $('#fit-status').textContent=original?'원본 비교':saved?'저장한 설정':'조절 중';
 if(!settings.autoBrightness)sceneLift=1;applyLook();routeAudio();renderCaptions();renderChart();
 if(!settings.notices||original){$('#event-notice').hidden=true;$('#view-event-notice').hidden=true;noticeShown=null;}
 syncNoticeToggle();
}
for(const key of Object.keys(ranges))$('#'+key)?.addEventListener('input',e=>{settings[key]=Number(e.target.value);original=false;saved=false;reflect();});
for(const key of toggles)$('#'+key)?.addEventListener('click',()=>{settings[key]=!settings[key];original=false;saved=false;reflect();});
$('#custom-mode').onclick=()=>{original=false;reflect();};
$('#original-mode').onclick=()=>{original=true;reflect();notify('원본 화면과 소리 변화를 비교해요 전체 음량은 유지해요');};
function save(message='설정을 저장했어요 연결된 확장 프로그램에도 전달해요'){
 try{localStorage.setItem(KEY,JSON.stringify({settings,updatedAt:new Date().toISOString()}));document.dispatchEvent(new Event('pariview-saved'));saved=true;reflect();notify(message);}catch{notify('저장 공간을 사용할 수 없어요 현재 설정은 계속 적용돼요');}
}
$('#save-settings').onclick=()=>save();
$('#expand-settings').onclick=()=>{const on=$('.preferences').classList.toggle('expanded');$('#expand-settings').setAttribute('aria-expanded',String(on));$('#expand-settings').textContent=on?'세부 설정 접기 ↑':'세부 설정 펼치기 ↓';};
$('#reset-settings').onclick=()=>{video.pause();settings={...defaults};recommendation=null;comparisonHistory=[];original=false;sceneLift=1;furthestTime=0;video.currentTime=0;$('#recommend-form').reset();$('#recommend-result').hidden=true;save('화면·소리·자막과 저장한 설정을 기본값으로 초기화했어요');updateTime();};
function showSettingTab(id,focus=false){
 $$('[data-setting-tab]').forEach(b=>{const on=b.dataset.settingTab===id;b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;$('#settings-'+b.dataset.settingTab).hidden=!on;if(on&&focus)b.focus();});
}
$$('[data-setting-tab]').forEach((b,i,all)=>{b.onclick=()=>showSettingTab(b.dataset.settingTab);b.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const n=e.key==='Home'?0:e.key==='End'?all.length-1:(i+(e.key==='ArrowRight'?1:-1)+all.length)%all.length;showSettingTab(all[n].dataset.settingTab,true);};});
function renderPlay(){$('#play-button').setAttribute('aria-label',video.paused?'영상 재생':'영상 일시정지');$('#play-button use').setAttribute('href',video.paused?'#i-play':'#i-pause');}
async function play(){try{if(!muted)initAudio();await video.play();}catch{notify('영상을 재생하지 못했어요 다시 눌러주세요');}}
$('#play-button').onclick=()=>video.paused?play():video.pause();
$('#mute-button').onclick=()=>{muted=!muted;if(!muted)initAudio();video.muted=muted;$('#mute-button').setAttribute('aria-pressed',String(muted));$('#mute-button').setAttribute('aria-label',muted?'음소거 해제':'음소거');$('#mute-label').textContent=muted?'OFF':'ON';};
function formatTime(s){return String(Math.floor(s/60)).padStart(2,'0')+':'+String(Math.floor(s%60)).padStart(2,'0');}
function initialFrame(){
 video.currentTime=0;const d=Number.isFinite(video.duration)?video.duration:currentScene.duration;
 $('#seek').max=d;$('#duration').textContent=formatTime(d);$('#track-middle').textContent=formatTime(d/2);$('#track-end').textContent=formatTime(d);updateTime();
 if(pendingScenePlay){pendingScenePlay=false;play();}
}

// Each excerpt has its own measured light and sound map
let events=[],mapEpoch=0;
function describeEvent(e){return e.type==='빛 변화'?`밝기 ${e.direction||'변화'} ${Math.abs(e.jumpY)}`:(e.fromSilence?`무음에서 ${e.peakLufs}LUFS`:`+${e.riseLu}LU · ${e.peakLufs}LUFS`);}
function renderSensoryMap(map){
 const d=map.duration||currentScene.duration;
 const lane=(type,sel)=>{const box=$(sel);if(!box)return;box.innerHTML=events.map((e,i)=>e.type===type?`<i style="left:${(100*e.at/d).toFixed(2)}%;width:${Math.max(1.5,100*(e.end-e.at)/d).toFixed(2)}%" data-event="${i}" title="${e.at.toFixed(1)}초 ${describeEvent(e)}"></i>`:'').join('');};
 lane('소리 변화','.sensory-track .lane:not(.light-lane)>div');lane('빛 변화','.sensory-track .light-lane>div');
 const label=$('.sensory-track .track-title small');label.textContent='영상 신호로 측정한 구간';label.title=`${map.method.sound}\n${map.method.light}\n${map.method.note}`;
}
async function loadSensoryMap(){
 const epoch=++mapEpoch;events=[];noticeEvents=[];noticeShown=null;
 $$('.sensory-track .lane>div').forEach(el=>el.replaceChildren());
 const label=$('.sensory-track .track-title small');label.textContent='변화 구간 불러오는 중';label.title='';
 try{const response=await fetch(currentScene.map);if(!response.ok)throw Error('map');const map=await response.json();if(epoch!==mapEpoch)return;events=map.events;noticeEvents=prepareNotices(map);renderSensoryMap(map);updateTime();}
 catch{if(epoch===mapEpoch)label.textContent='변화 구간을 불러오지 못했어요';}
}
function renderSceneOptions(){
 $('#scene-options').innerHTML=scenes.map(scene=>`<button class="scene-option" data-scene="${scene.id}" aria-pressed="${scene.id===currentScene.id}"><img src="${scene.poster}" alt="" loading="lazy"><span class="scene-option-copy"><span class="scene-meta">${scene.film} · ${scene.duration}초</span><strong>${scene.title}</strong><span class="scene-description">${scene.description}</span><span class="scene-choice">${scene.id===currentScene.id?'선택한 장면':'이 장면으로 비교 →'}</span></span></button>`).join('');
}
function reflectScene(){
 $('.studio-grid').style.setProperty('--scene-ratio',currentScene.ratio);
 $('#scene-film-title').textContent=currentScene.film;$('#scene-counter').textContent=`${scenes.indexOf(currentScene)+1} / ${scenes.length}`;
 const link=$('#scene-original');link.href=currentScene.original;link.textContent=currentScene.originalLabel;
 $('#scene-credit').textContent=currentScene.attribution;$('#scene-excerpt').textContent=currentScene.excerpt;
 $('#scene-chapters').innerHTML=currentScene.chapters.map(c=>`<button data-seek="${c.at}"><time>${formatTime(c.at)}</time><span>${escapeHTML(c.title)}</span><span>↗</span></button>`).join('');
 $('#next-scene').textContent=`다음 장면 보기 →`;
 renderSceneOptions();
}
function selectScene(id,autoplay=false){
 const scene=scenes.find(item=>item.id===id);if(!scene)return;
 video.pause();currentScene=scene;furthestTime=0;sceneLift=1;captionHistoryKey='';pendingScenePlay=autoplay;
 $('#scene-ended').hidden=true;$('#view-event-notice').hidden=true;
 video.playbackRate=1;video.muted=muted;video.poster=scene.poster;video.src=scene.src;
 $('#seek').max=scene.duration;$('#duration').textContent=formatTime(scene.duration);$('#track-middle').textContent=formatTime(scene.duration/2);$('#track-end').textContent=formatTime(scene.duration);
 reflectScene();reflect();loadSensoryMap();video.load();updateTime();
 $('#scene-announcement').textContent=`${scene.film} ${scene.duration}초 장면을 선택했어요`;
 document.dispatchEvent(new CustomEvent('pariview-scene',{detail:scene.id}));
}
$('#choose-scene').onclick=()=>{video.pause();renderSceneOptions();$('#scene-dialog').showModal();};
$('#close-scene').onclick=()=>$('#scene-dialog').close();
$('#scene-options').onclick=e=>{const button=e.target.closest('[data-scene]');if(!button)return;$('#scene-dialog').close();if(button.dataset.scene!==currentScene.id)selectScene(button.dataset.scene);$('#choose-scene').focus({preventScroll:true});};
$('#next-scene').onclick=()=>selectScene(scenes[(scenes.indexOf(currentScene)+1)%scenes.length].id,true);
$('#replay-scene').onclick=()=>{video.currentTime=0;$('#scene-ended').hidden=true;play();};
// Pre-change notices (alltology UX 4d17ea6): only map.noticeEvents (strong changes, 5 s apart), shown for the last 3 s before each change
const NOTICE_LEAD=3;
function prepareNotices(map){
 const lights=(map.events||[]).filter(e=>e.type==='빛 변화');
 return (Array.isArray(map.noticeEvents)?map.noticeEvents:[]).map(n=>{
  const light=n.type==='소리 변화'?null:lights.find(e=>e.at>=n.at-.15&&e.at<=(n.end??n.at)+.15);
  return {...n,direction:light?.direction||''};
 });
}
function noticeCopy(n){
 const dir=n.direction==='어두워짐'?'어두워져요':'밝아져요';
 if(n.type==='소리 변화')return {title:'큰 소리 변화',sub:'소리가 갑자기 커져요',icons:['i-sound']};
 if(n.type==='빛 변화')return {title:'큰 빛 변화',sub:`화면이 갑자기 ${dir}`,icons:[n.direction==='어두워짐'?'i-moon':'i-sun']};
 return {title:'큰 빛·소리 변화',sub:`화면이 ${n.direction==='어두워짐'?'어두워지고':'밝아지고'} 소리도 커져요`,icons:[n.direction==='어두워짐'?'i-moon':'i-sun','i-sound']};
}
function renderNotice(t){
 const el=$('#view-event-notice'),next=noticeEvents.find(n=>n.at>t&&n.at-t<=NOTICE_LEAD);
 const show=!!next&&settings.notices&&!original&&!video.paused&&!$('#fit-dialog').open;
 if(!show){el.hidden=true;if(!next)noticeShown=null;return;}
 const sec=Math.max(1,Math.ceil(next.at-t));
 if(noticeShown!==next){
  noticeShown=next;const c=noticeCopy(next);
  el.dataset.kind=next.type==='소리 변화'?'sound':next.type==='빛 변화'?'light':'both';
  el.innerHTML=`<span class="notice-count" aria-hidden="true"><b>${sec}</b><small>초 뒤</small></span><span class="notice-icons" aria-hidden="true">${c.icons.map(i=>`<svg><use href="#${i}"/></svg>`).join('')}</span><span class="notice-text" aria-hidden="true"><b>${c.title}</b><small>${c.sub}</small></span><span class="sr-only">곧 ${c.title} ${c.sub}</span>`;
 } else el.querySelector('.notice-count b').textContent=sec;
 el.hidden=false;
}
function syncNoticeToggle(){
 const b=$('#notice-toggle');if(!b)return;
 b.setAttribute('aria-pressed',String(!!settings.notices));b.classList.toggle('on',!!settings.notices);
 b.querySelector('i').textContent=settings.notices?'ON':'OFF';
}
$('#notice-toggle')?.addEventListener('click',()=>{settings.notices=!settings.notices;saved=false;reflect();if(settings.notices)renderNotice(video.currentTime||0);});
function updateTime(){
 const t=video.currentTime||0,d=Number.isFinite(video.duration)?video.duration:currentScene.duration;
 if(!$('#fit-dialog').open)furthestTime=Math.max(furthestTime,t);
 $('#current-time').textContent=formatTime(t);$('#seek').value=t;fillRange($('#seek'));$('.track-playhead').style.left=`calc(32px + (100% - 32px) * ${t/d})`;
 renderNotice(t);
 if(t<d-.1)$('#scene-ended').hidden=true;
 renderCaptions();
}
video.addEventListener('timeupdate',updateTime);video.addEventListener('play',()=>{renderPlay();updateTime();});video.addEventListener('pause',()=>{renderPlay();updateTime();});video.addEventListener('seeked',updateTime);
video.addEventListener('ended',()=>{renderPlay();$('#scene-ended').hidden=false;});
video.addEventListener('error',()=>notify('영상 파일을 불러오지 못했어요 연결을 확인해 주세요'));
$('#seek').oninput=e=>{video.currentTime=Number(e.target.value);updateTime();};
$('#fullscreen-button').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('.stage-card').requestFullscreen();}catch{notify('이 브라우저에서는 전체 화면을 지원하지 않아요');}};
function comparisonCaption(){return currentScene.captions.find(c=>c.start>=0&&c.end>c.start+2)||scenes[0].captions[0];}
function renderCaptions(){
 const easy=settings.easyCaptions&&!original,el=$('#film-caption'),cue=currentScene.captions.find(c=>video.currentTime>=c.start&&video.currentTime<c.end);
 el.hidden=!settings.captions||!cue;
 const text=cue?(easy?cue.easy:cue.text):'';if(el.textContent!==text){el.replaceChildren();const span=document.createElement('span');span.textContent=text;el.append(span);}
 el.style.fontSize=settings.captionSize+'px';el.style.fontWeight=settings.boldCaptions?'700':'400';el.style.color=settings.captionYellow&&!original?'#ffe03d':'';
 const seen=currentScene.captions.filter(c=>furthestTime>=c.start),key=`${currentScene.id}-${seen.length}-${easy}`;
 if(key===captionHistoryKey)return;captionHistoryKey=key;
 $('#caption-history').innerHTML=seen.length?seen.map((c,i)=>`<div class="caption-entry"><time>${formatTime(c.start)}</time><div>${escapeHTML(easy?c.easy:c.text)}<button class="text-link" ${i===0?'id="caption-seek"':''} data-caption-at="${c.start}">이 대사 다시 보기 ↗</button></div></div>`).join(''):`<p class="empty-state">${currentScene.captions.length?'재생한 장면의 대사가 여기에 남아요':'이 장면에는 대사가 없어요 장면 기록으로 다시 살펴볼 수 있어요'}</p>`;
}
function seekTo(t){if($('#recap-dialog').open)$('#recap-dialog').close();video.currentTime=t;updateTime();$('.stage-card').scrollIntoView({behavior:reduced?'instant':'smooth',block:'center'});}
$('#caption-history').onclick=e=>{const b=e.target.closest('[data-caption-at]');if(b)seekTo(Number(b.dataset.captionAt));};
$('#scene-chapters').onclick=e=>{const b=e.target.closest('[data-seek]');if(b)seekTo(Number(b.dataset.seek));};
$('#open-recap').onclick=()=>{video.pause();const chapter=currentScene.chapters.filter(c=>c.at<=video.currentTime).at(-1);$('#recap-body').innerHTML=`<p>${video.currentTime<.2?'아직 재생 전이에요 영상을 본 뒤 놓친 내용을 확인해 보세요':escapeHTML(chapter?.recap||'')}</p>`;$('#recap-dialog').showModal();};
$('#close-recap').onclick=()=>$('#recap-dialog').close();$('#recap-return').onclick=()=>{$('#recap-dialog').close();play();};
// Only the local, licensed demo is sampled for automatic dark-scene compensation.
const probe=document.createElement('canvas');probe.width=64;probe.height=28;const probeCtx=probe.getContext('2d',{willReadFrequently:true});let watched=0,lastWatch=performance.now(),reminded=false;
setInterval(()=>{
 const now=performance.now();if(!video.paused)watched+=(now-lastWatch)/1000;lastWatch=now;
 if(settings.breakReminder&&watched>=1200&&!reminded){notify('20분 동안 시청했어요 잠깐 쉬어가도 좋아요');reminded=true;}
 if(!settings.autoBrightness||original||video.readyState<2||$('#fit-dialog').open)return;
 try{probeCtx.drawImage(video,0,0,64,28);const data=probeCtx.getImageData(0,0,64,28).data;let sum=0;for(let i=0;i<data.length;i+=4)sum+=data[i]*.2126+data[i+1]*.7152+data[i+2]*.0722;const avg=sum/(64*28);const target=Math.min(1.22,Math.max(1,75/Math.max(avg,1)));sceneLift+=(target-sceneLift)*.2;applyLook();}catch{}
},250);
function renderChart(){
 const values=[settings.brightness/100,settings.contrast/110,settings.saturation/110,settings.volume/70];
 const labels=['밝기','대비','색','음량'];const coords=(r,i)=>[200+Math.sin(i*Math.PI/2)*r,130-Math.cos(i*Math.PI/2)*r];
 let s='';for(const r of [25,50,75,100])s+=`<polygon points="${labels.map((_,i)=>coords(r,i).join(',')).join(' ')}" fill="none" stroke="#d5d7db" stroke-width="1"/>`;
 labels.forEach((l,i)=>{const [x,y]=coords(100,i),[tx,ty]=coords(118,i);s+=`<path d="M200 130L${x} ${y}" stroke="#e7e8eb"/><text x="${tx}" y="${ty+4}" text-anchor="middle" font-family="Pretendard" font-size="13" fill="#6b7684">${l}</text>`;});
 s+=`<polygon points="${values.map((v,i)=>coords(v*100,i).join(',')).join(' ')}" fill="#fa00301c" stroke="#fa0030" stroke-width="2"/>`;
 $('#profile-chart').innerHTML=s;
}
$('#download-profile').onclick=()=>{const report={name:'PariView 시청 설정',settings,createdAt:new Date().toISOString(),note:'선호에 따른 설정이며 감각 역치나 의료적 검사 결과가 아님',mockupOnly:['backgroundReduction','transitionSoftening']};const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='pariview-settings.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
function setMotion(value){reduced=value;document.body.classList.toggle('reduce-motion',value);$('#motion-toggle').setAttribute('aria-pressed',String(value));$('#motion-toggle').lastChild.textContent=value?'모션 줄이기 켜짐':'모션 줄이기';if(value){$('.approved-hero').style.opacity='1';$('.approved-hero').style.transform='none';}document.dispatchEvent(new Event('pariview-motion-change'));}
$('#motion-toggle').onclick=()=>setMotion(!reduced);mediaQuery.addEventListener('change',e=>setMotion(e.matches));setMotion(reduced);
function showTab(tab){
 if(!['studio','research','chrome'].includes(tab))tab='studio';video.pause();
 for(const id of ['studio','research','chrome'])$('#'+id+'-view').hidden=id!==tab;
 $('#page-name').textContent={studio:'시청 스튜디오',research:'설계의 근거',chrome:'크롬에서 쓰기'}[tab];
 $$('.nav-item[data-tab]').forEach(el=>el.classList.toggle('active',el.dataset.tab===tab));history.replaceState(null,'','#'+tab);window.scrollTo({top:0,behavior:'instant'});
 if(!reduced)gsap.fromTo(`#${tab}-view`,{opacity:.3,y:8},{opacity:1,y:0,duration:.35,clearProps:'all'});
}
$$('[data-tab]').forEach(el=>el.onclick=e=>{e.preventDefault();showTab(el.dataset.tab);});
renderResearchPage();
const recommendationRules={sound:{id:'focus',refs:[0,2],why:'큰 소리가 신경 쓰인다고 골라 소리 변화 완화를 켠 모드로 시작해요'},light:{id:'soft',refs:[0,2],why:'밝은 화면이 신경 쓰인다고 골라 밝기와 대비를 낮춘 모드로 시작해요'},both:{id:'gentle',refs:[0,4],why:'소리와 화면이 모두 신경 쓰인다고 골라 두 가지를 함께 낮춰 시작해요'},unsure:{id:'everyday',refs:[0,1],why:'아직 잘 모르겠다면 일상 모드에서 하나씩 비교해 볼 수 있어요'}};
$('#recommend-form').onsubmit=e=>{
 e.preventDefault();const data=new FormData(e.currentTarget),rule=recommendationRules[data.get('concern')];if(!rule)return;
 recommendation={...rule,notices:data.get('notice')==='yes'};const m=modes.find(m=>m.id===rule.id);
 const refs=[...new Set([...rule.refs,3])];$('#recommend-result').innerHTML=`<span class="tag">추천 시작 모드</span><h2>${m.title}</h2><p>${rule.why}</p><div class="recommend-evidence">${refs.map(i=>`<article><b>${research[i].tag}</b><p>${research[i].design}</p><a href="${research[i].url}" target="_blank" rel="noopener">${research[i].ref} ↗</a></article>`).join('')}</div><button id="start-recommended" class="primary">이 모드로 피팅 시작 <svg><use href="#i-arrow"/></svg></button><p class="fit-footnote">추천은 비교를 시작할 지점이에요 장면을 비교하며 언제든 바꿀 수 있어요</p>`;
 $('#recommend-result').hidden=false;$('#start-recommended').onclick=()=>fitOpen(rule.id);$('#recommend-result').scrollIntoView({behavior:reduced?'instant':'smooth',block:'center'});
};
$('#profile-catalog').innerHTML=modes.map(m=>`<article class="profile-card" style="--mode-color:${m.color}"><h3>${m.en}</h3><p class="profile-ko">${m.title}</p><ul>${m.features.map(f=>`<li>${f}</li>`).join('')}</ul><button class="text-link" data-mode-start="${m.id}">이 프로필로 시작 ↗</button></article>`).join('');
$$('[data-mode-start]').forEach(b=>b.onclick=()=>fitOpen(b.dataset.modeStart));
initExtensionConnection({openChrome:()=>showTab('chrome'),reducedMotion:()=>reduced});
const steps=[
 {key:'brightness',title:'어느 화면 밝기가 더 편한가요?',sub:'같은 장면을 다른 밝기로 비교해 보세요',a:65,b:90,an:'조금 어둡게',bn:'조금 밝게',kind:'visual'},
 {key:'contrast',title:'어느 쪽의 대비가 더 편한가요?',sub:'색과 윤곽이 느껴지는 정도를 골라보세요',a:78,b:105,an:'부드러운 대비',bn:'또렷한 대비',kind:'visual'},
 {key:'volume',title:'어느 소리 크기가 더 편한가요?',sub:'같은 장면을 0.75배속으로 들어보세요 작은 소리부터 시작해요',a:22,b:45,an:'작은 소리',bn:'조금 큰 소리',kind:'audio'},
 {key:'compression',title:'소리의 변화를 어떻게 듣고 싶나요?',sub:'같은 장면에서 소리 크기의 차이를 비교해 보세요',a:true,b:false,an:'변화 폭을 줄여서',bn:'원본 변화 그대로',kind:'audio'},
 {key:'easyCaptions',title:'어느 자막이 더 읽기 편한가요?',sub:'같은 뜻을 담은 두 문장을 비교해 보세요',a:false,b:true,an:'기본 자막',bn:'쉬운 자막',kind:'cognitive'}
];
let fitStep=0,answers=Array(steps.length).fill(null),previewTimeout,returnFocus,fitBase,modeIndex=4,previewEpoch=0,previewSync,previewAbort,previewPlaying=false,previewAudioKey=null,fitReturnTime=0;
const COMPARISON_RATE=.75,COMPARISON_SECONDS=8;
let comparisonHistory=[];
function recordChoice(value){answers[fitStep]=value;comparisonHistory.push({axis:steps[fitStep].key,outcome:value});comparisonHistory=comparisonHistory.slice(-20);}
const phaseNav=phase=>`<div class="fit-steps"><span class="${phase===1?'current':''}"><i>01</i>감각 프로필</span><span class="${phase===2?'current':''}"><i>02</i>선호 비교</span><span class="${phase===3?'current':''}"><i>03</i>시청 환경</span></div>`;
function fitOpen(modeId){returnFocus=document.activeElement;fitReturnTime=video.currentTime;video.pause();fitStep=0;answers=Array(steps.length).fill(null);modeIndex=modes.findIndex(m=>m.id===(typeof modeId==='string'?modeId:recommendation?.id||settings.profileId));if(modeIndex<0)modeIndex=4;fitBase={...settings};$('#fit-dialog').showModal();renderModes();if(!reduced)gsap.fromTo('.fit-modal',{opacity:0,y:10},{opacity:1,y:0,duration:.25});}
function refreshPreviewControls(){
 const both=$('#play-comparison');if(both){both.textContent=previewPlaying?'■ 두 화면 일시정지':'▶ 두 화면 함께 보기';both.setAttribute('aria-pressed',String(previewPlaying));}
 $$('[data-listen]').forEach(button=>{const active=previewPlaying&&previewAudioKey===button.dataset.listen;button.textContent=active?'■ 멈추기':`▶ ${button.dataset.listen.toUpperCase()} 듣기`;button.setAttribute('aria-pressed',String(active));});
}
function stopPreview(){
 previewEpoch++;previewAbort?.abort();clearTimeout(previewTimeout);clearInterval(previewSync);previewPlaying=false;previewAudioKey=null;
 $$('.fit-preview').forEach(v=>v.pause());video.pause();video.playbackRate=1;video.muted=muted;refreshPreviewControls();reflect();
}
function fitClose(){stopPreview();$('#fit-dialog').close();video.currentTime=fitReturnTime;updateTime();returnFocus?.focus();}
$('#close-fit').onclick=fitClose;$('#fit-dialog').addEventListener('cancel',e=>{e.preventDefault();fitClose();});$$('[data-action="fit"]').forEach(el=>el.onclick=()=>fitOpen());
function waitForMedia(media,condition,event,signal){
 if(condition())return Promise.resolve();
 return new Promise((resolve,reject)=>{
  const finish=error=>{clearTimeout(timeout);media.removeEventListener(event,ready);media.removeEventListener('error',failed);signal.removeEventListener('abort',aborted);error?reject(error):resolve();};
  const ready=()=>{if(condition())finish();},failed=()=>finish(Error('media')),aborted=()=>finish(new DOMException('Stopped','AbortError'));
  const timeout=setTimeout(()=>finish(Error('timeout')),15000);
  media.addEventListener(event,ready);media.addEventListener('error',failed);signal.addEventListener('abort',aborted,{once:true});if(signal.aborted)aborted();
 });
}
async function preparePreview(media,start,signal){
 await waitForMedia(media,()=>media.readyState>=1,'loadedmetadata',signal);
 media.playbackRate=COMPARISON_RATE;media.preservesPitch=true;media.currentTime=start;
 await waitForMedia(media,()=>!media.seeking,'seeked',signal);
 await waitForMedia(media,()=>media.readyState>=3,'canplay',signal);
}
async function startComparison(audioKey=null){
 if(previewPlaying&&previewAudioKey===audioKey){stopPreview();return;}
 stopPreview();const epoch=previewEpoch,start=currentScene.previewAt,previews=$$('.fit-preview'),s=steps[fitStep];
 previewAbort=new AbortController();const signal=previewAbort.signal,media=[...previews];
 previews.forEach(v=>{v.muted=true;});
 if(audioKey){initAudio();if(!audioContext){notify('이 브라우저에서는 소리 비교를 사용할 수 없어요');return;}video.muted=false;routeAudio({...fitBase,[s.key]:s[audioKey]},false);media.push(video);}
 try{
  await Promise.all(media.map(v=>preparePreview(v,start,signal)));if(epoch!==previewEpoch)return;
  await Promise.all(media.map(v=>v.play()));if(epoch!==previewEpoch){media.forEach(v=>v.pause());return;}
  previewPlaying=true;previewAudioKey=audioKey;refreshPreviewControls();
  const leader=audioKey?video:previews[0];
  previewSync=setInterval(()=>{
   if(epoch!==previewEpoch)return;
   if(leader.currentTime>=start+COMPARISON_SECONDS){stopPreview();return;}
   media.forEach(v=>{if(v!==leader&&!v.seeking&&Math.abs(v.currentTime-leader.currentTime)>.06)v.currentTime=leader.currentTime;});
  },100);
  previewTimeout=setTimeout(()=>{if(epoch===previewEpoch)stopPreview();},COMPARISON_SECONDS/COMPARISON_RATE*1000+2000);
 }catch(error){if(epoch!==previewEpoch||error.name==='AbortError')return;stopPreview();notify('장면을 재생하지 못했어요 다시 눌러주세요');}
}
function renderModes(){
 stopPreview();gsap.set('#fit-progress-fill',{width:'10%'});const selected=modes[modeIndex];
 $('#fit-body').innerHTML=phaseNav(1)+`<div class="fit-step-count">나의 출발점 고르기 <span>1 / 3 단계</span></div><h2 class="fit-heading">오늘은 어떻게 보고 싶나요?</h2><p class="fit-subtitle">다섯 가지 프로필 중 가까운 모드를 골라주세요 다음 화면에서 하나씩 비교해요</p><div class="mode-options">${modes.map((m,i)=>`<button class="mode-option ${i===modeIndex?'selected':''}" data-mode="${i}" aria-pressed="${i===modeIndex}">${recommendation?.id===m.id?'<span class="recommend-badge">추천</span>':''}<svg><use href="#i-${m.icon}"/></svg><span class="mode-en">${m.en}</span><b>${m.title}</b><p>${m.desc}</p><span class="mode-check">${i===modeIndex?'✓ 선택했어요':'이 모드로 시작'}</span></button>`).join('')}</div><div class="mode-detail"><b>${selected.en}</b>${selected.features.join(' · ')}</div><div class="fit-actions"><button class="back" id="mode-current">기존 설정에서 비교</button><button class="primary" id="start-comparison">장면 비교하기 <svg><use href="#i-arrow"/></svg></button></div><p class="fit-footnote">필요에 맞게 직접 고르고 언제든 바꿀 수 있어요</p>`;
 $$('[data-mode]').forEach(b=>b.onclick=()=>{modeIndex=Number(b.dataset.mode);renderModes();});
 $('#start-comparison').onclick=()=>{fitBase=modeSettings(modes[modeIndex].id,recommendation?.notices??settings.notices);fitStep=0;renderFit();};
 $('#mode-current').onclick=()=>{fitBase={...settings};if(recommendation)fitBase.notices=recommendation.notices;fitStep=0;renderFit();};
}
function renderFit(){
 stopPreview();const s=steps[fitStep],caption=comparisonCaption();gsap.to('#fit-progress-fill',{width:(25+(fitStep+1)*12)+'%',duration:reduced?0:.2});
 const filter=value=>`brightness(${s.key==='brightness'?value:fitBase.brightness}%) contrast(${s.key==='contrast'?value:fitBase.contrast}%) saturate(${fitBase.saturation}%)`;
 const context=s.kind==='cognitive'&&!currentScene.captions.length?'대사가 없는 장면이라 Tears of Steel의 자막 예시로 비교해요':`${currentScene.film} · ${s.kind==='cognitive'?'같은 대사의 두 표현':'같은 장면 · 0.75배속'}`;
 $('#fit-body').innerHTML=phaseNav(2)+`<div class="fit-step-count">${{visual:'화면',audio:'소리',cognitive:'자막'}[s.kind]} 선호 비교 <span>${fitStep+1} / ${steps.length} 비교</span></div><h2 class="fit-heading">${s.title}</h2><p class="fit-subtitle">${s.sub}<span class="comparison-context">${context}</span></p><div class="ab-options">${['a','b'].map(key=>`<article class="ab-option ${answers[fitStep]===key?'selected':''}" data-choice-card="${key}"><div class="option-top"><strong>${key.toUpperCase()}</strong><span>${s[key+'n']}</span></div>${s.kind==='cognitive'?`<div class="caption-preview">${escapeHTML(s[key]?caption.easy:caption.text)}</div>`:`<video class="fit-preview" data-preview="${key}" src="${currentScene.src}" poster="${currentScene.poster}" preload="auto" muted playsinline style="filter:${filter(s[key])}" aria-label="동일한 영화 장면 ${key.toUpperCase()}"></video>`}<div class="option-bottom">${s.kind==='audio'?`<button data-listen="${key}" aria-pressed="false">▶ ${key.toUpperCase()} 듣기</button>`:''}<button class="choose" data-choose="${key}" aria-pressed="${answers[fitStep]===key}">${answers[fitStep]===key?'✓ 선택했어요':'이쪽이 더 편해요'}</button></div></article>`).join('')}</div>${s.kind==='visual'?'<div class="comparison-transport"><button id="play-comparison" aria-pressed="false">▶ 두 화면 함께 보기</button><span>0.75배속 · 같은 순간을 함께 비교해요</span></div>':''}<div class="fit-uncertain"><button id="choose-equal" class="${answers[fitStep]==='equal'?'selected':''}">비슷해요</button><button id="choose-unsure" class="${answers[fitStep]==='unsure'?'selected':''}">잘 모르겠어요</button><button id="skip-step">건너뛰기</button></div><div class="fit-actions"><button id="fit-back" class="back">← 이전</button><button id="fit-next" class="primary" ${answers[fitStep]===null?'disabled':''}>${fitStep===steps.length-1?'내 설정 확인':'다음으로'} <svg><use href="#i-arrow"/></svg></button></div><p class="fit-footnote">지금의 선호를 알아보는 과정이에요 불편하면 언제든 종료해 주세요</p>`;
 $$('.fit-preview').forEach(v=>{v.playbackRate=COMPARISON_RATE;v.preservesPitch=true;});
 $$('[data-choose]').forEach(b=>b.onclick=()=>{recordChoice(b.dataset.choose);renderFit();});$('#choose-equal').onclick=()=>{recordChoice('equal');renderFit();};$('#choose-unsure').onclick=()=>{recordChoice('unsure');renderFit();};$('#skip-step').onclick=()=>{recordChoice('skip');advance();};
 $('#fit-back').onclick=()=>{if(fitStep===0)renderModes();else{fitStep--;renderFit();}};$('#fit-next').onclick=advance;
 $('#play-comparison')?.addEventListener('click',()=>startComparison());
 $$('[data-listen]').forEach(b=>b.onclick=()=>startComparison(b.dataset.listen));
}
function advance(){stopPreview();if(fitStep<steps.length-1){fitStep++;renderFit();}else showResult();}
function getFitResult(){const result={...fitBase};steps.forEach((s,i)=>{if(answers[i]==='a'||answers[i]==='b')result[s.key]=s[answers[i]];});return result;}
function showResult(){
 const result=getFitResult(),mode=modes.find(m=>m.id===result.profileId);gsap.set('#fit-progress-fill',{width:'100%'});
 $('#fit-body').innerHTML=phaseNav(3)+`<div class="fit-result"><div class="result-mark"><svg><use href="#i-glasses"/></svg></div><div class="kicker">${mode.en}</div><h2>오늘의 시청 설정이<br>준비됐어요</h2><p>고른 값을 반영했어요 비슷하거나 건너뛴 항목은 시작 설정을 유지해요</p><div class="result-values"><div><small>화면 밝기</small><strong>${result.brightness}%</strong></div><div><small>화면 대비</small><strong>${result.contrast}%</strong></div><div><small>전체 음량</small><strong>${result.volume}%</strong></div><div><small>음량 변화 완화</small><strong>${result.compression?'켜짐':'꺼짐'}</strong></div><div><small>자막</small><strong>${result.easyCaptions?'쉬운 자막':'기본 자막'}</strong></div></div><button id="apply-fit" class="primary">이 설정으로 시청하기<svg><use href="#i-arrow"/></svg></button><button id="result-back" class="back">← 이전 비교로 돌아가기</button><p class="fit-footnote">편안함이 달라지면 언제든 다시 맞춰주세요</p></div>`;
 $('#apply-fit').onclick=()=>{settings=result;original=false;save();fitClose();showTab('studio');$('#watch-studio').scrollIntoView({behavior:'instant'});};$('#result-back').onclick=()=>{fitStep=steps.length-1;renderFit();};
}
video.addEventListener('loadedmetadata',initialFrame);if(video.readyState>=1)initialFrame();
reflectScene();loadSensoryMap();reflect();renderPlay();updateTime();
createFalcon($('#hero-falcon'),{reduced:()=>reduced});createFalcon($('#wizard-falcon'),{wizard:true,reduced:()=>reduced});
if(['#research','#chrome'].includes(location.hash))showTab(location.hash.slice(1));
window.__pariview={get settings(){return {...settings}},get original(){return original},get audioRoute(){return audioRoute},get muted(){return muted},get reduced(){return reduced},get recommendation(){return recommendation},video,openFit:fitOpen,modes,showSettingTab,scenes,selectScene,get scene(){return currentScene},get events(){return events},get comparisonPlaying(){return previewPlaying},applyScenePreset(next){settings=normalize(next);saved=false;sceneLift=1;reflect();}};
let recommendationSnapshot=null;
const recommendationUI=initRecommendation({
 getSettings:()=>({...settings}),
 getComparisons:()=>comparisonHistory.map(item=>({...item})),
 onPreview:next=>{
  if(!recommendationSnapshot)recommendationSnapshot={settings:{...settings},original,saved,time:video.currentTime,muted,sceneLift};
  video.pause();settings=normalize(next);original=false;sceneLift=1;reflect();
 },
 onCancelPreview:()=>{
  if(!recommendationSnapshot)return;const snapshot=recommendationSnapshot;recommendationSnapshot=null;
  video.pause();settings=snapshot.settings;original=snapshot.original;saved=snapshot.saved;sceneLift=snapshot.sceneLift;video.currentTime=snapshot.time;video.muted=snapshot.muted;reflect();updateTime();
 },
 onApply:next=>{
  recommendationSnapshot=null;video.pause();settings=normalize(next);original=false;sceneLift=1;save('고른 시작 설정을 저장했어요');showTab('studio');$('#watch-studio').scrollIntoView({behavior:'instant'});
 },
 onCompare:(axis,next)=>{
  recommendationSnapshot=null;fitOpen();fitBase=normalize(next);fitStep=Math.max(0,steps.findIndex(step=>step.key===axis));renderFit();
 }
});
document.addEventListener('click',event=>{if(event.target.closest('[data-action="ai-recommend"],[data-recommendation-entry]'))video.pause();},true);
window.__pariview.recommendationUI=recommendationUI;
initInteractions(()=>reduced);
const introMotion={p:0};const introTween=animate(introMotion,{p:1,duration:1000,ease:'linear',autoplay:false,onUpdate:()=>{if(reduced)return;const h=$('.approved-hero');h.style.opacity=1-introMotion.p*.18;h.style.transform=`translateY(${-introMotion.p*12}px)`;}});
window.addEventListener('scroll',()=>{const h=$('.approved-hero');if(!h||reduced)return;introTween.seek(Math.min(1,Math.max(0,scrollY/Math.max(h.offsetHeight,1)))*1000);},{passive:true});
