// PariView extension content script
// 1) On the PariView page: copy the saved fit profile into chrome.storage
// 2) On every other page: apply brightness/contrast to <video> and route audio through gain/compressor
(() => {
  const KEY = 'pariview-fit-v1';
  const DEFAULT_VOLUME = 35; // Volume is the same attenuation percentage as the web demo
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

  if (document.querySelector('meta[name="pariview-app"]')) {
    const sync = () => {
      let data = null;
      try { data = JSON.parse(localStorage.getItem(KEY)); } catch {}
      const payload = { source: location.origin + location.pathname };
      if (data && data.settings) {
        payload.profile = { settings: data.settings, updatedAt: data.updatedAt || new Date().toISOString() };
      }
      chrome.storage.local.set(payload, () => {
        document.documentElement.dataset.pariviewExtension = payload.profile ? 'synced' : 'connected';
        document.dispatchEvent(new Event('pariview-extension-ready'));
      });
    };
    sync();
    document.addEventListener('pariview-saved', sync);
    return;
  }

  const state = { enabled: true, settings: null };
  const graphs = new Set();
  const graphByVideo = new WeakMap();
  let ctx = null;
  let style = null;

  const active = () => state.enabled && !!state.settings;

  function normalize(s) {
    if (!s) return null;
    return {
      brightness: clamp(Number(s.brightness) || 85, 45, 100),
      contrast: clamp(Number(s.contrast) || 90, 65, 110),
      volume: clamp(Number.isFinite(Number(s.volume)) ? Number(s.volume) : DEFAULT_VOLUME, 0, 70),
      compression: s.compression !== false,
      saturation: clamp(Number.isFinite(s.saturation) ? s.saturation : 100, 40, 110),
      warmth: clamp(Number.isFinite(s.warmth) ? s.warmth : 0, 0, 60),
      highCut: clamp(Number.isFinite(s.highCut) ? s.highCut : 0, 0, 100),
      dialogueBoost: s.dialogueBoost === true,
    };
  }

  function applyVisual() {
    if (!active()) { style?.remove(); style = null; return; }
    if (!style) {
      style = document.createElement('style');
      style.id = 'pariview-extension-style';
      (document.head || document.documentElement).appendChild(style);
    }
    const { brightness, contrast, saturation, warmth } = state.settings;
    style.textContent = `video{filter:brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%) sepia(${warmth * .35}%) !important}`;
  }

  // Web Audio on cross-origin (no CORS) or DRM media outputs silence, so only touch safe sources
  function audioSafe(v) {
    if (v.mediaKeys) return false;
    const src = v.currentSrc || v.src;
    if (!src) return false;
    if (src.startsWith('blob:') || src.startsWith('data:')) return true;
    try { return new URL(src, location.href).origin === location.origin || !!v.crossOrigin; } catch { return false; }
  }

  function route(g) {
    const on = active();
    const want = on && state.settings.compression ? 'compressed' : 'direct';
    if (g.route !== want) {
      g.eq.disconnect();
      g.comp.disconnect();
      if (want === 'compressed') { g.eq.connect(g.comp); g.comp.connect(g.gain); }
      else g.eq.connect(g.gain);
      g.route = want;
    }
    const target = on ? state.settings.volume / 100 : 1;
    g.gain.gain.setTargetAtTime(target, ctx.currentTime, 0.08);
    g.lowpass.frequency.setTargetAtTime(on ? 20000 * Math.pow(.16, state.settings.highCut / 100) : 20000, ctx.currentTime, .08);
    g.eq.gain.setTargetAtTime(on && state.settings.dialogueBoost ? 4 : 0, ctx.currentTime, .08);
  }

  function attachAudio(v) {
    if (graphByVideo.has(v) || !active() || !audioSafe(v)) return;
    // Without a prior user gesture the AudioContext stays suspended and the video would go silent
    if (navigator.userActivation && !navigator.userActivation.hasBeenActive) return;
    try {
      ctx ||= new AudioContext();
      const source = ctx.createMediaElementSource(v);
      const gain = ctx.createGain();
      const comp = ctx.createDynamicsCompressor();
      comp.threshold.value = -25; comp.knee.value = 22; comp.ratio.value = 5;
      comp.attack.value = 0.008; comp.release.value = 0.25;
      const lowpass = ctx.createBiquadFilter(); lowpass.type = 'lowpass'; lowpass.Q.value = .5;
      const eq = ctx.createBiquadFilter(); eq.type = 'peaking'; eq.frequency.value = 3000; eq.Q.value = 1;
      source.connect(lowpass); lowpass.connect(eq);
      gain.connect(ctx.destination);
      const g = { source, gain, comp, lowpass, eq, route: '' };
      graphByVideo.set(v, g);
      graphs.add(g);
      route(g);
      if (ctx.state === 'suspended') ctx.resume();
    } catch {
      graphByVideo.set(v, null);
    }
  }

  function playingVideos() {
    return [...document.querySelectorAll('video')].filter(v => !v.paused);
  }

  function refresh() {
    applyVisual();
    graphs.forEach(route);
    if (active()) playingVideos().forEach(attachAudio);
  }

  document.addEventListener('play', e => {
    if (e.target instanceof HTMLVideoElement) {
      attachAudio(e.target);
      if (ctx && ctx.state === 'suspended') ctx.resume();
    }
  }, true);

  const onGesture = () => { if (active()) playingVideos().forEach(attachAudio); if (ctx && ctx.state === 'suspended') ctx.resume(); };
  addEventListener('pointerdown', onGesture, true);
  addEventListener('keydown', onGesture, true);

  chrome.storage.local.get(['profile', 'enabled'], r => {
    state.settings = normalize(r.profile && r.profile.settings);
    state.enabled = r.enabled !== false;
    refresh();
  });

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local') return;
    if (changes.profile) state.settings = normalize(changes.profile.newValue && changes.profile.newValue.settings);
    if (changes.enabled) state.enabled = changes.enabled.newValue !== false;
    refresh();
  });
})();
