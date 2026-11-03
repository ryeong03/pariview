// Scene-adaptive adjustment (alltology UX, 4d17ea6)
// Reads each scene's measured signal map (analysis/sensory_map.py) and nudges the current settings for that scene only
// Never calls save(): the user's saved profile and the extension stay untouched, and "원래대로" restores the exact prior settings
// Needs from app.js: CustomEvent 'pariview-scene' (detail = scene id) and window.__pariview.applyScenePreset(nextSettings)

const RANGES = {brightness: [45, 100], volume: [0, 70], warmth: [0, 60]};
const OFF_KEY = 'pariview-scene-adapt-off';
const clamp = (key, v) => Math.min(RANGES[key][1], Math.max(RANGES[key][0], Math.round(v)));
const median = a => { const s = [...a].sort((x, y) => x - y); return s.length ? s[Math.floor(s.length / 2)] : 0; };
const mean = a => a.reduce((x, y) => x + y, 0) / (a.length || 1);

// Signal features only; these describe the clip, not anyone's comfort
export function sceneFeatures(map) {
  const per45 = n => n * 45 / (map.duration || 45);
  const lufs = (map.curves?.loudness || []).map(p => p[1]).filter(v => v > -70);
  const luma = (map.curves?.luma || []).map(p => p[1]);
  const events = map.events || [];
  return {
    loudness: median(lufs),
    brightness: mean(luma),
    soundChanges: per45(events.filter(e => e.type === '소리 변화').length),
    lightChanges: per45(events.filter(e => e.type === '빛 변화').length)
  };
}

// Only active features (brightness, warmth, volume, compression, dialogueBoost); transitionSoftening is a mock and is never chosen
// Small, explainable rules; each reason names the measured cause and the change, and is kept only if a value actually changes
export function sceneAdjustment(f, s) {
  const rules = [];
  if (f.loudness > -28 && s.volume > 10) rules.push([{volume: clamp('volume', s.volume - 5), compression: true}, '소리가 큰 편이라 조금 줄였어요']);
  if (f.soundChanges >= 10 && f.loudness < -36) rules.push([{dialogueBoost: true, compression: true}, '조용한 대사 사이로 소리가 갑자기 커져서 대사를 또렷하게 했어요']);
  else if (f.soundChanges >= 10) rules.push([{compression: true}, '갑자기 커지는 소리가 많아서 고르게 했어요']);
  if (f.brightness > 120) rules.push([{brightness: clamp('brightness', s.brightness - 8), warmth: clamp('warmth', s.warmth + 10)}, '화면이 밝은 편이라 밝기를 낮추고 색을 따뜻하게 했어요']);
  const next = {}, reasons = [];
  for (const [change, why] of rules) {
    const diff = Object.entries(change).filter(([k, v]) => s[k] !== v);
    if (!diff.length) continue;
    diff.forEach(([k, v]) => { next[k] = v; });
    reasons.push(why);
  }
  return {next, reasons};
}

const same = (a, b) => Object.keys(b).every(k => a[k] === b[k]);
const maps = new Map();
let base = null, applied = null, token = 0, ui = null;

// Restore only keys the module changed and the user has not touched since; everything else keeps its current value
function reverted(current) {
  if (!base || !applied) return current;
  const out = {...current};
  for (const k of Object.keys(applied)) if (applied[k] !== base[k] && current[k] === applied[k]) out[k] = base[k];
  return out;
}
const busy = api => api.original || !!document.querySelector('dialog[open]');

function ensureUi() {
  if (ui) return ui;
  const host = document.querySelector('.stage-header');
  if (!host) return null;
  const button = document.createElement('button');
  button.type = 'button'; button.className = 'scene-adapt-trigger'; button.hidden = true;
  button.setAttribute('aria-haspopup', 'dialog'); button.setAttribute('aria-expanded', 'false');
  button.innerHTML = '<span class="scene-adapt-dot" aria-hidden="true"></span>장면 맞춤';
  const pop = document.createElement('div');
  pop.className = 'scene-adapt-pop'; pop.id = 'scene-adapt-pop'; pop.setAttribute('popover', 'auto'); pop.setAttribute('role', 'dialog'); pop.setAttribute('aria-label', '장면 맞춤 보정');
  pop.innerHTML = '<b>이 장면에 맞춰 바꿨어요</b><ul></ul><div class="scene-adapt-actions"><button type="button" data-adapt="off">장면마다 바꾸지 않기</button><button type="button" data-adapt="undo">원래대로</button></div>';
  button.setAttribute('popovertarget', pop.id);
  const place = () => {
    const r = button.getBoundingClientRect(), w = Math.min(340, innerWidth - 24);
    pop.style.width = w + 'px';
    const h = pop.getBoundingClientRect().height;
    const below = r.bottom + 8, above = r.top - h - 8;
    const preferred = below + h <= innerHeight - 12 ? below : above;
    pop.style.left = Math.max(12, Math.min(r.left, innerWidth - w - 12)) + 'px';
    pop.style.top = Math.max(12, Math.min(preferred, innerHeight - h - 12)) + 'px';
  };
  pop.addEventListener('beforetoggle', e => { if (e.newState === 'open') place(); button.setAttribute('aria-expanded', String(e.newState === 'open')); });
  // The open popover has a measurable height; choose above/below using its actual contents.
  pop.addEventListener('toggle', e => { if (e.newState === 'open') place(); });
  const follow = () => { if (pop.matches(':popover-open')) place(); };
  addEventListener('scroll', follow, {passive: true}); addEventListener('resize', follow);
  pop.addEventListener('click', e => {
    const action = e.target.closest('[data-adapt]')?.dataset.adapt;
    if (!action) return;
    if (action === 'off') { try { sessionStorage.setItem(OFF_KEY, '1'); } catch {} }
    undo(); pop.hidePopover(); button.focus({preventScroll: true});
  });
  (host.querySelector('#choose-scene') || host.firstElementChild).insertAdjacentElement('afterend', button);
  document.body.appendChild(pop);
  return ui = {button, pop};
}

function hideUi() { if (!ui) return; ui.button.hidden = true; if (ui.pop.matches(':popover-open')) ui.pop.hidePopover(); }

function undo() {
  const api = window.__pariview;
  if (api?.applyScenePreset && base && applied) { const current = api.settings, next = reverted(current); if (!same(current, next)) api.applyScenePreset(next); }
  base = applied = null; token++; hideUi();
}

async function loadMap(scene) {
  if (!maps.has(scene.id)) maps.set(scene.id, fetch(scene.map).then(r => r.json()).catch(() => null));
  return maps.get(scene.id);
}

async function onScene(id) {
  const api = window.__pariview;
  if (!api?.applyScenePreset) return;
  const my = ++token;
  // Undo the previous scene's nudge first (per key) so adjustments never stack
  const current = api.settings, start = reverted(current);
  base = applied = null; hideUi();
  if (!same(current, start)) api.applyScenePreset(start);
  let off = false; try { off = sessionStorage.getItem(OFF_KEY) === '1'; } catch {}
  if (off || busy(api)) return;
  const scene = (api.scenes || []).find(s => s.id === id);
  const map = scene?.map && await loadMap(scene);
  // Bail out if anything moved while the map loaded: another scene, a slider edit, a save, original mode, or an open dialog
  if (!map || my !== token || api.scene?.id !== id || busy(api) || !same(api.settings, start)) return;
  const {next, reasons} = sceneAdjustment(sceneFeatures(map), start);
  if (!reasons.length) return;
  base = {...start}; applied = {...start, ...next};
  api.applyScenePreset({...applied});
  const view = ensureUi();
  if (!view) return;
  view.pop.querySelector('ul').replaceChildren(...reasons.map(t => Object.assign(document.createElement('li'), {textContent: t})));
  view.button.setAttribute('aria-label', '장면 맞춤 보정 켜짐 ' + reasons.join(' '));
  view.button.hidden = false;
}

document.addEventListener('pariview-scene', e => onScene(e.detail));
// A save or reset makes the current values the user's own; drop the undo point and any pending scene request
document.addEventListener('pariview-saved', () => { base = applied = null; token++; hideUi(); });

const style = document.createElement('style');
style.textContent = `.scene-adapt-trigger{display:inline-flex;align-items:center;gap:7px;font:inherit;font-size:13px;font-weight:600;line-height:1;padding:8px 12px;border-radius:50px;border:1px solid #ffc2cd;background:#fff5f7;color:#fa0030;cursor:pointer;white-space:nowrap}
.scene-adapt-trigger[hidden]{display:none}.scene-adapt-trigger:hover{background:#ffecef}.scene-adapt-trigger:focus-visible{outline:3px solid #fa003066;outline-offset:2px}
.scene-adapt-dot{width:7px;height:7px;border-radius:50%;background:#fa0030}
.scene-adapt-pop{position:fixed;inset:auto;margin:0;box-sizing:border-box;max-height:calc(100dvh - 24px);overflow:auto;padding:16px 18px;border:1px solid #e7e8eb;border-radius:14px;background:#fff;color:#0d0e11;box-shadow:0 16px 40px #0d0e1626;font:14px/1.55 Pretendard,system-ui,sans-serif}
.scene-adapt-pop b{font-size:14px}.scene-adapt-pop ul{margin:8px 0 14px;padding-left:18px;color:#4e5968;font-size:13px}.scene-adapt-pop li+li{margin-top:4px}
.scene-adapt-actions{display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap}.scene-adapt-pop button{font:inherit;font-size:13px;padding:8px 14px;border-radius:50px;border:1px solid #d5d7dc;background:#fff;color:#0d0e11;cursor:pointer}
.scene-adapt-pop button[data-adapt=undo]{border-color:#fa0030;background:#fa0030;color:#fff;font-weight:600}
@media(max-width:760px){.scene-adapt-trigger{padding:7px 10px;font-size:12px}}`;
document.head.appendChild(style);
