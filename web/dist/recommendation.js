import {normalize} from './settings.js';
import {prepareRecommendation,composeRecommendation} from './recommendation-engine.js';

const esc = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fetchJSON = async (url, options={}, timeout=12000) => {
  const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),timeout);
  try { const response=await fetch(url,{...options,signal:controller.signal,cache:'no-store'}); if(!response.ok) throw new Error('Unavailable'); return await response.json(); }
  finally {clearTimeout(timer);}
};

export function initRecommendation(hooks={}) {
  if(document.querySelector('#pariview-recommendation')) return;
  const style=document.createElement('link');style.rel='stylesheet';style.href=new URL('./recommendation.css',import.meta.url);document.head.append(style);
  const dialog=document.createElement('dialog');dialog.id='pariview-recommendation';dialog.className='pv-rec';dialog.setAttribute('aria-labelledby','pv-rec-title');
  dialog.innerHTML='<header><span class="pv-rec-brand">PariView <small>연구 기반 추천</small></span><button type="button" class="pv-rec-close" aria-label="추천 닫기">×</button></header><div class="pv-rec-body"></div>';
  document.body.append(dialog);
  const body=dialog.querySelector('.pv-rec-body');
  let catalog,base,draft,result,lastAnswers={},returnFocus,epoch=0,previewing=false,previewAudio,previewNodes,providerConfigured=false;
  let pending=null;
  const catalogReady=fetchJSON(new URL('./recommendation-data.json',import.meta.url),{},5000).then(x=>(catalog=x)).catch(()=>null);
  const pausePreview=()=>{body.querySelector('video')?.pause();previewAudio?.suspend().catch(()=>{});};
  const restore=()=>{pausePreview();if(previewing){hooks.onCancelPreview?.();previewing=false;}};
  const close=()=>{epoch++;restore();dialog.close();returnFocus?.focus();};
  dialog.querySelector('.pv-rec-close').onclick=close;
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});
  dialog.addEventListener('close',restore);

  async function open() {
    returnFocus=document.activeElement;base=normalize(hooks.getSettings?.()||{});draft=null;result=null;providerConfigured=false;
    const thisEpoch=++epoch;
    if(!dialog.open)dialog.showModal();
    body.innerHTML='<h2 id="pv-rec-title">오늘의 시청 환경을 맞춰볼까요?</h2><p class="pv-rec-note" role="status">준비된 설정을 가져오고 있어요</p>';
    const status=fetchJSON('/api/recommendation/status',{},1800).then(x=>{if(epoch===thisEpoch)providerConfigured=x.configured===true;}).catch(()=>{});
    pending=status;
    await catalogReady;
    if(epoch!==thisEpoch||!dialog.open)return;
    if(!catalog){body.innerHTML='<h2 id="pv-rec-title">내 설정에서 시작해요</h2><p>밝기와 소리, 자막을 직접 비교하며 맞출 수 있어요</p><button type="button" class="pv-rec-primary" data-direct>직접 설정하기</button>';body.querySelector('[data-direct]').onclick=()=>{close();document.querySelector('[data-action="fit"]')?.click();};return;}
    renderForm();
  }
  function renderForm() {
    restore();
    const choices=(key,type='radio')=>Object.entries(catalog.inputs[key]).map(([value,label])=>`<label class="pv-rec-choice"><input type="${type}" name="${key}" value="${value}" ${type==='checkbox'?(lastAnswers[key]?.includes(value)?'checked':''):(value===(lastAnswers[key]||Object.keys(catalog.inputs[key])[0])?'checked':'')}><span>${label}</span></label>`).join('');
    const select=(key,title)=>`<label class="pv-rec-select">${title}<select name="${key}">${Object.entries(catalog.inputs[key]).map(([value,label])=>`<option value="${value}" ${lastAnswers[key]===value?'selected':''}>${label}</option>`).join('')}</select></label>`;
    body.innerHTML=`<div class="pv-rec-eyebrow">내 응답 + 연구를 참고한 설계</div><h2 id="pv-rec-title">오늘은 어떻게 보고 싶나요?</h2><p class="pv-rec-intro">신경 쓰이는 항목을 고르면 시작 설정과 다음 비교를 제안해요<br>마음에 드는 값만 골라 적용할 수 있어요</p>
      <form class="pv-rec-form"><fieldset><legend>지금 신경 쓰이는 것은 무엇인가요? <small>여러 개 선택 · 선택하지 않아도 돼요</small></legend><div class="pv-rec-choices">${choices('concerns','checkbox')}</div></fieldset>
      <fieldset><legend>어떤 방향으로 시작할까요?</legend><div class="pv-rec-choices">${choices('goal')}</div></fieldset>
      <details class="pv-rec-environment"><summary>지금의 환경과 자막 선호 <span>선택 사항</span></summary><div class="pv-rec-selects">${select('room','주변 밝기')}${select('device','소리를 듣는 기기')}${select('captionStyle','자막 표현')}</div></details>
      <p class="pv-rec-note">선택한 항목과 설정값으로 추천해요 AI가 연결된 경우 이 정보가 AI 제공자에게 전달돼요 이름이나 진단 정보는 묻지 않아요</p>
      <div class="pv-rec-actions"><button type="button" data-cancel>취소</button><button type="submit" class="pv-rec-primary">시작 설정 제안받기 <span aria-hidden="true">↗</span></button></div><p class="pv-rec-note">추천은 고쳐 쓸 수 있는 출발점이에요 진단·치료·최적값 판정이 아니에요</p><p class="pv-rec-wait" role="status" aria-live="polite"></p></form>`;
    body.querySelector('[data-cancel]').onclick=close;
    body.querySelector('form').onsubmit=async e=>{
      e.preventDefault();const form=e.currentTarget,data=new FormData(form),thisEpoch=epoch;
      lastAnswers=Object.fromEntries(Object.keys(catalog.inputs).map(k=>[k,k==='concerns'?data.getAll(k):data.get(k)]));
      const payload={currentSettings:base,answers:lastAnswers,comparisons:(hooks.getComparisons?.()||[]).slice(-20).map(x=>({axis:x.axis,outcome:x.outcome})),useAI:true};
      const plan=prepareRecommendation(payload,catalog);
      const fallback=()=>composeRecommendation(plan,catalog);
      const submit=form.querySelector('[type="submit"]');submit.disabled=true;form.querySelector('.pv-rec-wait').textContent='선택한 응답으로 제안을 준비하고 있어요';
      await pending;
      let next=fallback();
      if(providerConfigured) {
        try {const response=await fetchJSON('/api/recommendation',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
          if(response.evidenceVersion===catalog.version)next=composeRecommendation(plan,catalog,response.selection,response.source);
        } catch { /* Continue with the reviewed default proposal, without an error modal */ }
      }
      if(epoch!==thisEpoch||!dialog.open)return;
      result=next;draft={...result.settings};renderResult();
    };
  }
  function renderResult() {
    pausePreview();previewAudio?.close().catch(()=>{});previewAudio=null;previewNodes=null;
    const field=(key,info)=>{
      const range=catalog.ranges[key];
      return range?`<label class="pv-rec-control">${info.label}<span><small>시작 ${base[key]}${info.unit}</small><output data-value="${key}">${draft[key]}${info.unit}</output></span><input type="range" data-setting="${key}" min="${range[0]}" max="${range[1]}" step="1" value="${draft[key]}" aria-label="${info.label}"></label>`:
        `<label class="pv-rec-control pv-rec-toggle"><span>${info.label}<small>시작 ${base[key]?'켜짐':'꺼짐'}</small></span><input type="checkbox" data-setting="${key}" ${draft[key]?'checked':''}></label>`;
    };
    body.innerHTML=`<span class="pv-rec-method">${result.source==='ai'?'AI 추천':'연구 기반 기본 제안'}</span><h2 id="pv-rec-title">오늘의 시작 설정이에요</h2><p class="pv-rec-intro">아직 저장하지 않았어요 값을 바꾸거나 미리 본 뒤 선택하세요</p>
      <div class="pv-rec-result-layout"><div><div class="pv-rec-reasons">${result.actions.map(a=>`<article><b>${esc(a.title)}</b><p>${esc(a.reason)}</p><small>설계 참고 ${a.sourceIds.join(' · ')}</small></article>`).join('')}</div>
      <div class="pv-rec-controls">${Object.entries(catalog.controls).map(([key,info])=>field(key,info)).join('')}</div><p class="pv-rec-edited" role="status" aria-live="polite"></p><button type="button" class="pv-rec-text" data-reset>제안받은 값으로 되돌리기</button></div>
      <aside class="pv-rec-preview"><div class="pv-rec-preview-title">적용 전 미리보기</div><video playsinline preload="metadata" muted aria-label="추천 설정 미리보기"></video><p class="pv-rec-caption" aria-live="off"></p><div class="pv-rec-preview-buttons"><button type="button" data-preview>화면 미리보기</button><button type="button" data-listen>소리도 듣기</button><button type="button" data-stop>멈추기</button></div><p class="pv-rec-note">지금 고른 장면으로 확인해요 자막 표현은 준비된 예시이며 배경음 분리·장면 전환 완화는 이 추천에서 바꾸지 않아요</p>
      ${result.nextComparison?`<article class="pv-rec-next"><small>다음에 비교해 볼 항목</small><h3>${esc(result.nextComparison.title)}</h3><p>${esc(result.nextComparison.reason)}</p><button type="button" data-compare>이 항목 비교하기 ↗</button></article>`:'<p class="pv-rec-note">확인한 항목은 다시 묻지 않아요 원하는 값을 직접 수정할 수 있어요</p>'}</aside></div>
      <details class="pv-rec-evidence"><summary>어떤 연구를 참고했나요?</summary><p>${esc(result.boundary)}</p>${result.sources.map(s=>`<article><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${s.id} · ${esc(s.title)} ↗</a><p>${esc(s.basis)}</p><small>${esc(s.limit)}</small></article>`).join('')}<p>추천 이유는 실제 선택한 응답에서 가져오고 연구 설명과 설정 후보는 확인된 자료로 구성했어요</p></details>
      <div class="pv-rec-actions"><button type="button" data-back>응답 다시 고르기</button><button type="button" data-cancel>취소</button><button type="button" class="pv-rec-primary" data-apply>이 설정 적용하고 저장</button></div>`;
    const preview=body.querySelector('video'),main=document.querySelector('#film');
    if(main){preview.src=main.currentSrc||main.src;preview.poster=main.poster;preview.addEventListener('loadedmetadata',()=>{preview.currentTime=Math.min(main.currentTime||0,Math.max(0,preview.duration-1));},{once:true});}
    const update=()=>{
      preview.style.filter=`brightness(${draft.brightness}%) contrast(${draft.contrast}%) saturate(${draft.saturation}%) sepia(${draft.warmth*.35}%)`;
      const caption=body.querySelector('.pv-rec-caption');caption.hidden=!draft.captions;caption.style.fontSize=`${draft.captionSize}px`;caption.textContent=draft.easyCaptions?'자막 예시 · 같은 장면을 비교해요':'자막 예시 · 동일한 장면의 설정을 비교해요';
      if(previewNodes){const n=previewNodes;n.lowpass.frequency.value=20000*Math.pow(.16,draft.highCut/100);n.eq.gain.value=draft.dialogueBoost?4:0;n.gain.gain.value=draft.volume/100;n.eq.disconnect();n.compressor.disconnect();n.eq.connect(draft.compression?n.compressor:n.gain);if(draft.compression)n.compressor.connect(n.gain);}
      if(previewing)hooks.onPreview?.({...draft});
    };
    update();
    body.querySelectorAll('[data-setting]').forEach(input=>input.addEventListener('input',()=>{const key=input.dataset.setting;draft[key]=input.type==='checkbox'?input.checked:Number(input.value);const out=body.querySelector(`[data-value="${key}"]`);if(out)out.textContent=draft[key]+catalog.controls[key].unit;body.querySelector('.pv-rec-edited').textContent='직접 수정한 값이 포함돼요';update();}));
    async function play(withSound){
      if(!preview.src)return;
      if(!previewing){previewing=true;hooks.onPreview?.({...draft});}
      if(withSound){
        const AC=window.AudioContext||window.webkitAudioContext;
        if(!AC){body.querySelector('.pv-rec-edited').textContent='화면 미리보기에서 확인한 뒤 직접 설정에서 소리를 조절할 수 있어요';return;}
        if(!previewAudio){previewAudio=new AC();const source=previewAudio.createMediaElementSource(preview),lowpass=previewAudio.createBiquadFilter(),eq=previewAudio.createBiquadFilter(),compressor=previewAudio.createDynamicsCompressor(),gain=previewAudio.createGain();lowpass.type='lowpass';lowpass.Q.value=.5;eq.type='peaking';eq.frequency.value=3000;eq.Q.value=1;compressor.threshold.value=-25;compressor.knee.value=22;compressor.ratio.value=5;compressor.attack.value=.008;compressor.release.value=.25;source.connect(lowpass);lowpass.connect(eq);gain.connect(previewAudio.destination);previewNodes={lowpass,eq,compressor,gain};update();}
        await previewAudio.resume();
      }
      preview.muted=!withSound;
      try {await preview.play();}catch {body.querySelector('.pv-rec-edited').textContent='미리보기 버튼을 눌러 장면을 확인해 주세요';}
    }
    body.querySelector('[data-preview]').onclick=()=>play(false);body.querySelector('[data-listen]').onclick=()=>play(true);body.querySelector('[data-stop]').onclick=pausePreview;
    body.querySelector('[data-back]').onclick=renderForm;body.querySelector('[data-cancel]').onclick=close;
    body.querySelector('[data-reset]').onclick=()=>{restore();draft={...result.settings};renderResult();};
    const meta=()=>({source:result.source,evidenceVersion:result.evidenceVersion,sourceIds:result.sources.map(s=>s.id),nextComparison:result.nextComparison,edited:Object.keys(draft).some(k=>draft[k]!==result.settings[k])});
    body.querySelector('[data-apply]').onclick=()=>{const next=normalize(draft),info=meta();close();hooks.onApply?.(next,info);};
    const compare=body.querySelector('[data-compare]');if(compare){compare.hidden=!hooks.onCompare;compare.onclick=()=>{const next=normalize(draft),info=meta(),axis=result.nextComparison.axis;close();hooks.onCompare(axis,next,info);};}
    body.scrollTop=0;body.querySelector('#pv-rec-title').setAttribute('tabindex','-1');body.querySelector('#pv-rec-title').focus();
  }
  const trigger=e=>{const target=e.target.closest?.('[data-action="ai-recommend"],[data-recommendation-entry]');if(target){e.preventDefault();open();}};
  document.addEventListener('click',trigger);
  return {open,close};
}
