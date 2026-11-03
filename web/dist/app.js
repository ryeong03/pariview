import {animate} from './vendor/anime.esm.min.js';
import {createBrand} from './brand.js';
import {createFalcon} from './mascot.js';
import {research} from './research.js';
import {defaults,ranges,toggles,modes,normalize,modeSettings} from './settings.js';
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const KEY='pariview-fit-v1',mediaQuery=matchMedia('(prefers-reduced-motion: reduce)');
let reduced=mediaQuery.matches,original=false,muted=true,settings={...defaults},saved=false,recommendation=null;
try{const data=JSON.parse(localStorage.getItem(KEY));if(data?.settings){settings=normalize(data.settings);saved=true;}}catch{}
const video=$('#film');
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
 $('#profile-state').textContent=saved?'내 설정이 저장되어 있어요':'아직 피팅 전이에요';
 $('#fit-status').textContent=original?'원본 비교':saved?'저장한 설정':'조절 중';
 if(!settings.autoBrightness)sceneLift=1;applyLook();routeAudio();renderCaptions();renderChart();
 if(!settings.notices){$('#event-notice').hidden=true;$('#view-event-notice').hidden=true;}
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
$('#reset-settings').onclick=()=>{video.pause();settings={...defaults};recommendation=null;original=false;sceneLift=1;furthestTime=0;video.currentTime=0;$('#recommend-form').reset();$('#recommend-result').hidden=true;save('화면·소리·자막과 저장한 설정을 기본값으로 초기화했어요');updateTime();};
function showSettingTab(id,focus=false){
 $$('[data-setting-tab]').forEach(b=>{const on=b.dataset.settingTab===id;b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;$('#settings-'+b.dataset.settingTab).hidden=!on;if(on&&focus)b.focus();});
}
$$('[data-setting-tab]').forEach((b,i,all)=>{b.onclick=()=>showSettingTab(b.dataset.settingTab);b.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const n=e.key==='Home'?0:e.key==='End'?all.length-1:(i+(e.key==='ArrowRight'?1:-1)+all.length)%all.length;showSettingTab(all[n].dataset.settingTab,true);};});
function renderPlay(){$('#play-button').setAttribute('aria-label',video.paused?'영상 재생':'영상 일시정지');$('#play-button use').setAttribute('href',video.paused?'#i-play':'#i-pause');}
async function play(){try{if(!muted)initAudio();await video.play();}catch{notify('영상을 재생하지 못했어요 다시 눌러주세요');}}
$('#play-button').onclick=()=>video.paused?play():video.pause();
$('#mute-button').onclick=()=>{muted=!muted;if(!muted)initAudio();video.muted=muted;$('#mute-button').setAttribute('aria-pressed',String(muted));$('#mute-button').setAttribute('aria-label',muted?'음소거 해제':'음소거');$('#mute-label').textContent=muted?'OFF':'ON';};
function formatTime(s){return String(Math.floor(s/60)).padStart(2,'0')+':'+String(Math.floor(s%60)).padStart(2,'0');}
function initialFrame(){video.currentTime=0;$('#seek').max=video.duration;$('#duration').textContent=formatTime(video.duration);updateTime();}

const events=[{at:2.6,end:4,type:'소리 변화'},{at:5,end:6.7,type:'빛 변화'},{at:8,end:9.6,type:'소리 변화'},{at:10.1,end:11.3,type:'빛 변화'}];
function updateTime(){
 const t=video.currentTime,d=video.duration||12;furthestTime=Math.max(furthestTime,t);
 $('#current-time').textContent=formatTime(t);$('#seek').value=t;fillRange($('#seek'));$('.track-playhead').style.left=`calc(32px + (100% - 32px) * ${t/d})`;
 const next=events.find(e=>e.at>=t&&e.at-t<=3),notice=$('#view-event-notice');notice.hidden=!(next&&settings.notices&&!video.paused);
 if(next)notice.textContent=`${Math.max(1,Math.ceil(next.at-t))}초 뒤 ${next.type} · 시연 구간`;
 renderCaptions();
}
video.addEventListener('timeupdate',updateTime);video.addEventListener('play',()=>{renderPlay();updateTime();});video.addEventListener('pause',()=>{renderPlay();updateTime();});video.addEventListener('seeked',updateTime);
video.addEventListener('ended',()=>{renderPlay();notify('장면이 끝났어요 같은 장면을 다시 비교할 수 있어요');});
video.addEventListener('error',()=>notify('영상 파일을 불러오지 못했어요 연결을 확인해 주세요'));
$('#seek').oninput=e=>{video.currentTime=Number(e.target.value);updateTime();};
$('#fullscreen-button').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('.stage-card').requestFullscreen();}catch{notify('이 브라우저에서는 전체 화면을 지원하지 않아요');}};
const regularCaption='로봇의 기억 동기화와 잠금이 완료됐어요',easyCaption='로봇의 기억을 맞추고 잠갔어요';
function renderCaptions(){
 const text=settings.easyCaptions&&!original?easyCaption:regularCaption,el=$('#film-caption');
 el.hidden=!settings.captions||video.currentTime<3||video.currentTime>=6.5;
 el.innerHTML=`<span>${text}</span>`;el.style.fontSize=settings.captionSize+'px';el.style.fontWeight=settings.boldCaptions?'700':'400';
 $('#caption-history').innerHTML=furthestTime>=3?`<div class="caption-entry"><time>00:03</time><div>${text}<button class="text-link" id="caption-seek">이 대사 다시 보기 ↗</button></div></div>`:'<p class="empty-state">재생한 장면의 대사가 여기에 남아요</p>';
 $('#caption-seek')?.addEventListener('click',()=>seekTo(3));
}
function seekTo(t){video.currentTime=t;updateTime();$('.stage-card').scrollIntoView({behavior:reduced?'instant':'smooth',block:'center'});}
$$('[data-seek]').forEach(b=>b.onclick=()=>seekTo(Number(b.dataset.seek)));
$('#open-recap').onclick=()=>{video.pause();$('#recap-body').innerHTML=video.currentTime<.2?'<p>아직 재생 전이에요 영상을 본 뒤 놓친 내용을 확인해 보세요</p>':video.currentTime<3?'<p>홀로그램이 켜진 연구실이에요<br>주변 장치와 화면이 보이고 있어요</p>':'<p>홀로그램이 켜진 연구실에서<br>로봇의 기억을 맞추고 잠갔다는 말이 들려요</p>';$('#recap-dialog').showModal();};
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
$('#research-cards').innerHTML=research.map(r=>`<article class="research-card"><span class="tag">${r.tag}</span><h2>${r.title}</h2><p>${r.text}</p><p class="inference">설계 해석 → ${r.design}</p><a href="${r.url}" target="_blank" rel="noopener">${r.ref} ↗</a></article>`).join('');
const recommendationRules={sound:{id:'focus',refs:[0,2],why:'큰 소리가 신경 쓰인다고 골라 소리 변화 완화를 켠 모드로 시작해요'},light:{id:'soft',refs:[0,2],why:'밝은 화면이 신경 쓰인다고 골라 밝기와 대비를 낮춘 모드로 시작해요'},both:{id:'gentle',refs:[0,4],why:'소리와 화면이 모두 신경 쓰인다고 골라 두 가지를 함께 낮춰 시작해요'},unsure:{id:'everyday',refs:[0,1],why:'아직 잘 모르겠다면 일상 모드에서 하나씩 비교해 볼 수 있어요'}};
$('#recommend-form').onsubmit=e=>{
 e.preventDefault();const data=new FormData(e.currentTarget),rule=recommendationRules[data.get('concern')];if(!rule)return;
 recommendation={...rule,notices:data.get('notice')==='yes'};const m=modes.find(m=>m.id===rule.id);
 const refs=[...new Set([...rule.refs,3])];$('#recommend-result').innerHTML=`<span class="tag">추천 시작 모드</span><h2>${m.title}</h2><p>${rule.why}</p><div class="recommend-evidence">${refs.map(i=>`<article><b>${research[i].tag}</b><p>${research[i].design}</p><a href="${research[i].url}" target="_blank" rel="noopener">${research[i].ref} ↗</a></article>`).join('')}</div><button id="start-recommended" class="primary">이 모드로 피팅 시작 <svg><use href="#i-arrow"/></svg></button><p class="fit-footnote">추천은 진단이 아니라 비교를 시작할 지점이에요 이 모드 조합이나 설정값의 효과를 논문이 직접 검증한 것은 아니에요</p>`;
 $('#recommend-result').hidden=false;$('#start-recommended').onclick=()=>fitOpen(rule.id);$('#recommend-result').scrollIntoView({behavior:reduced?'instant':'smooth',block:'center'});
};
$('#profile-catalog').innerHTML=modes.map(m=>`<article class="profile-card" style="--mode-color:${m.color}"><h3>${m.en}</h3><p class="profile-ko">${m.title}</p><ul>${m.features.map(f=>`<li>${f}</li>`).join('')}</ul><button class="text-link" data-mode-start="${m.id}">이 프로필로 시작 ↗</button></article>`).join('');
$$('[data-mode-start]').forEach(b=>b.onclick=()=>fitOpen(b.dataset.modeStart));
const extensionCopy={none:['아직 연결되지 않았어요','설치한 뒤 이 페이지를 새로고침하면 연결돼요'],connected:['확장 프로그램이 연결됐어요','감각 피팅 결과를 저장하면 설정이 넘어가요'],synced:['확장 프로그램에 설정이 들어갔어요','지원되는 영상에 저장한 화면·소리 조절값을 적용해요']};
function renderExtension(){const st=document.documentElement.dataset.pariviewExtension||'none';let [t,d]=extensionCopy[st]||extensionCopy.none;if(st==='none'&&matchMedia('(max-width:700px)').matches){t='PC 크롬에서 연결할 수 있어요';d='PC에서 설치하면 저장한 설정을 다른 영상에도 쓸 수 있어요';}$('#extension-status').dataset.state=st;$('#extension-status-title').textContent=t;$('#extension-status-desc').textContent=d;}
document.addEventListener('pariview-extension-ready',renderExtension);renderExtension();
const steps=[
 {key:'brightness',title:'어느 화면 밝기가 더 편한가요?',sub:'같은 장면을 다른 밝기로 비교해 보세요',a:65,b:90,an:'조금 어둡게',bn:'조금 밝게',kind:'visual'},
 {key:'contrast',title:'어느 쪽의 대비가 더 편한가요?',sub:'색과 윤곽이 느껴지는 정도를 골라보세요',a:78,b:105,an:'부드러운 대비',bn:'또렷한 대비',kind:'visual'},
 {key:'volume',title:'어느 소리 크기가 더 편한가요?',sub:'같은 장면을 4초씩 들어보세요 작은 소리부터 시작해요',a:22,b:45,an:'작은 소리',bn:'조금 큰 소리',kind:'audio'},
 {key:'compression',title:'소리의 변화를 어떻게 듣고 싶나요?',sub:'같은 장면에서 소리 크기의 차이를 비교해 보세요',a:true,b:false,an:'변화 폭을 줄여서',bn:'원본 변화 그대로',kind:'audio'},
 {key:'easyCaptions',title:'어느 자막이 더 읽기 편한가요?',sub:'같은 뜻을 담은 두 문장을 비교해 보세요',a:false,b:true,an:'기본 자막',bn:'쉬운 자막',kind:'cognitive'}
];
let fitStep=0,answers=Array(steps.length).fill(null),previewTimeout,returnFocus,fitBase,modeIndex=4,previewEpoch=0;
const phaseNav=phase=>`<div class="fit-steps"><span class="${phase===1?'current':''}"><i>01</i>감각 프로필</span><span class="${phase===2?'current':''}"><i>02</i>선호 비교</span><span class="${phase===3?'current':''}"><i>03</i>시청 환경</span></div>`;
function fitOpen(modeId){returnFocus=document.activeElement;video.pause();fitStep=0;answers=Array(steps.length).fill(null);modeIndex=modes.findIndex(m=>m.id===(typeof modeId==='string'?modeId:recommendation?.id||settings.profileId));if(modeIndex<0)modeIndex=4;fitBase={...settings};$('#fit-dialog').showModal();renderModes();if(!reduced)gsap.fromTo('.fit-modal',{opacity:0,y:10},{opacity:1,y:0,duration:.25});}
function stopPreview(){previewEpoch++;clearTimeout(previewTimeout);$$('.fit-preview').forEach(v=>v.pause());video.pause();video.muted=muted;reflect();}
function fitClose(){stopPreview();$('#fit-dialog').close();returnFocus?.focus();}
$('#close-fit').onclick=fitClose;$('#fit-dialog').addEventListener('cancel',()=>{stopPreview();returnFocus?.focus();});$$('[data-action="fit"]').forEach(el=>el.onclick=()=>fitOpen());
function renderModes(){
 stopPreview();gsap.set('#fit-progress-fill',{width:'10%'});const selected=modes[modeIndex];
 $('#fit-body').innerHTML=phaseNav(1)+`<div class="fit-step-count">나의 출발점 고르기 <span>1 / 3 단계</span></div><h2 class="fit-heading">오늘은 어떻게 보고 싶나요?</h2><p class="fit-subtitle">다섯 가지 프로필 중 가까운 모드를 골라주세요 다음 화면에서 하나씩 비교해요</p><div class="mode-options">${modes.map((m,i)=>`<button class="mode-option ${i===modeIndex?'selected':''}" data-mode="${i}" aria-pressed="${i===modeIndex}">${recommendation?.id===m.id?'<span class="recommend-badge">추천</span>':''}<svg><use href="#i-${m.icon}"/></svg><span class="mode-en">${m.en}</span><b>${m.title}</b><p>${m.desc}</p><span class="mode-check">${i===modeIndex?'✓ 선택했어요':'이 모드로 시작'}</span></button>`).join('')}</div><div class="mode-detail"><b>${selected.en}</b>${selected.features.join(' · ')}${selected.values.backgroundReduction||selected.values.transitionSoftening?'<p class="mock-label">배경음 분리와 장면 전환 완화는 설정 화면을 체험하는 기능 목업이에요</p>':''}</div><div class="fit-actions"><button class="back" id="mode-current">기존 설정에서 비교</button><button class="primary" id="start-comparison">장면 비교하기 <svg><use href="#i-arrow"/></svg></button></div><p class="fit-footnote">특정 진단이나 나이에 따라 정해지는 설정은 아니에요 필요에 맞게 직접 골라요</p>`;
 $$('[data-mode]').forEach(b=>b.onclick=()=>{modeIndex=Number(b.dataset.mode);renderModes();});
 $('#start-comparison').onclick=()=>{fitBase=modeSettings(modes[modeIndex].id,recommendation?.notices??settings.notices);fitStep=0;renderFit();};
 $('#mode-current').onclick=()=>{fitBase={...settings};if(recommendation)fitBase.notices=recommendation.notices;fitStep=0;renderFit();};
}
function renderFit(){
 stopPreview();const s=steps[fitStep];gsap.to('#fit-progress-fill',{width:(25+(fitStep+1)*12)+'%',duration:reduced?0:.2});
 const filter=value=>`brightness(${s.key==='brightness'?value:fitBase.brightness}%) contrast(${s.key==='contrast'?value:fitBase.contrast}%) saturate(${fitBase.saturation}%)`;
 $('#fit-body').innerHTML=phaseNav(2)+`<div class="fit-step-count">${{visual:'화면',audio:'소리',cognitive:'자막'}[s.kind]} 선호 비교 <span>${fitStep+1} / ${steps.length} 비교</span></div><h2 class="fit-heading">${s.title}</h2><p class="fit-subtitle">${s.sub}</p><div class="ab-options">${['a','b'].map(key=>`<article class="ab-option ${answers[fitStep]===key?'selected':''}" data-choice-card="${key}"><div class="option-top"><strong>${key.toUpperCase()}</strong><span>${s[key+'n']}</span></div>${s.kind==='cognitive'?`<div class="caption-preview">${s[key]?easyCaption:regularCaption}</div>`:`<video class="fit-preview" data-preview="${key}" src="assets/movie-hologram.mp4" poster="assets/hologram-still.jpg" preload="metadata" muted playsinline style="filter:${filter(s[key])}" aria-label="동일한 영화 장면 ${key.toUpperCase()}"></video>`}<div class="option-bottom">${s.kind!=='cognitive'?`<button data-listen="${key}">▶ ${key.toUpperCase()} ${s.kind==='audio'?'듣기':'보기'}</button>`:''}<button class="choose" data-choose="${key}" aria-pressed="${answers[fitStep]===key}">${answers[fitStep]===key?'✓ 선택했어요':'이쪽이 더 편해요'}</button></div></article>`).join('')}</div><div class="fit-uncertain"><button id="choose-equal" class="${answers[fitStep]==='equal'?'selected':''}">비슷해요 / 잘 모르겠어요</button><button id="skip-step">건너뛰기</button></div><div class="fit-actions"><button id="fit-back" class="back">← 이전</button><button id="fit-next" class="primary" ${answers[fitStep]===null?'disabled':''}>${fitStep===steps.length-1?'내 설정 확인':'다음으로'} <svg><use href="#i-arrow"/></svg></button></div><p class="fit-footnote">지금의 선호를 알아보는 과정이에요 불편하면 언제든 종료해 주세요<br>감각 역치를 측정하는 검사는 아니에요</p>`;
 $$('[data-choose]').forEach(b=>b.onclick=()=>{answers[fitStep]=b.dataset.choose;renderFit();});$('#choose-equal').onclick=()=>{answers[fitStep]='equal';renderFit();};$('#skip-step').onclick=()=>{answers[fitStep]='skip';advance();};
 $('#fit-back').onclick=()=>{if(fitStep===0)renderModes();else{fitStep--;renderFit();}};$('#fit-next').onclick=advance;
 $$('[data-listen]').forEach(b=>b.onclick=async()=>{
 stopPreview();const epoch=previewEpoch,key=b.dataset.listen,preview=$(`[data-preview="${key}"]`);preview.currentTime=5;preview.muted=true;
 if(s.kind==='audio'){initAudio();if(!audioContext){notify('이 브라우저에서는 소리 비교를 사용할 수 없어요');return;}video.currentTime=5;video.muted=false;routeAudio({...fitBase,[s.key]:s[key]},false);}
 try{await preview.play();if(s.kind==='audio')await video.play();if(epoch!==previewEpoch){preview.pause();video.pause();return;}b.textContent='■ 멈추기';b.onclick=()=>{stopPreview();renderFit();};previewTimeout=setTimeout(()=>{stopPreview();renderFit();},4000);}catch{stopPreview();notify('장면을 재생하지 못했어요 다시 눌러주세요');}
 });
}
function advance(){stopPreview();if(fitStep<steps.length-1){fitStep++;renderFit();}else showResult();}
function getFitResult(){const result={...fitBase};steps.forEach((s,i)=>{if(answers[i]==='a'||answers[i]==='b')result[s.key]=s[answers[i]];});return result;}
function showResult(){
 const result=getFitResult(),mode=modes.find(m=>m.id===result.profileId);gsap.set('#fit-progress-fill',{width:'100%'});
 $('#fit-body').innerHTML=phaseNav(3)+`<div class="fit-result"><div class="result-mark"><svg><use href="#i-glasses"/></svg></div><div class="kicker">${mode.en}</div><h2>오늘의 시청 설정이<br>준비됐어요</h2><p>고른 값을 반영했어요 비슷하거나 건너뛴 항목은 시작 설정을 유지해요</p><div class="result-values"><div><small>화면 밝기</small><strong>${result.brightness}%</strong></div><div><small>화면 대비</small><strong>${result.contrast}%</strong></div><div><small>전체 음량</small><strong>${result.volume}%</strong></div><div><small>음량 변화 완화</small><strong>${result.compression?'켜짐':'꺼짐'}</strong></div><div><small>자막</small><strong>${result.easyCaptions?'쉬운 자막':'기본 자막'}</strong></div></div><button id="apply-fit" class="primary">이 설정으로 시청하기<svg><use href="#i-arrow"/></svg></button><button id="result-back" class="back">← 이전 비교로 돌아가기</button><p class="fit-footnote">편안함이 달라지면 다시 맞춰주세요<br>선택한 시청 설정이며 최적·안전 판정이 아니에요</p></div>`;
 $('#apply-fit').onclick=()=>{settings=result;original=false;save();fitClose();showTab('studio');$('#watch-studio').scrollIntoView({behavior:'instant'});};$('#result-back').onclick=()=>{fitStep=steps.length-1;renderFit();};
}
video.addEventListener('loadedmetadata',initialFrame);if(video.readyState>=1)initialFrame();
reflect();renderPlay();updateTime();
createFalcon($('#hero-falcon'),{reduced:()=>reduced});createFalcon($('#wizard-falcon'),{wizard:true,reduced:()=>reduced});
if(['#research','#chrome'].includes(location.hash))showTab(location.hash.slice(1));
window.__pariview={get settings(){return {...settings}},get original(){return original},get audioRoute(){return audioRoute},get muted(){return muted},get reduced(){return reduced},get recommendation(){return recommendation},video,openFit:fitOpen,modes,showSettingTab};
const introMotion={p:0};const introTween=animate(introMotion,{p:1,duration:1000,ease:'linear',autoplay:false,onUpdate:()=>{if(reduced)return;const h=$('.approved-hero');h.style.opacity=1-introMotion.p*.18;h.style.transform=`translateY(${-introMotion.p*12}px)`;}});
window.addEventListener('scroll',()=>{const h=$('.approved-hero');if(!h||reduced)return;introTween.seek(Math.min(1,Math.max(0,scrollY/Math.max(h.offsetHeight,1)))*1000);},{passive:true});
