(() => {
  const KEY = 'pariview-fit-v1';
  const { normalize } = PariViewSettings;
  const isApp = !!document.querySelector('meta[name="pariview-app"][content="1"]');
  const state = { enabled: true, settings: null };
  const graphs = new Set();
  const graphByVideo = new WeakMap();
  const audioErrors = new WeakMap();
  const encrypted = new WeakSet();
  let ctx = null;
  let style = null;
  let preparingAudio = null;
  let refreshQueued = false;

  const active = () => state.enabled && !!state.settings && !isApp;
  const videos = () => [...document.querySelectorAll('video')];

  function syncSavedProfile() {
    let data;
    try { data = JSON.parse(localStorage.getItem(KEY)); } catch { /* Storage can be disabled */ }
    const payload = { source: location.origin + location.pathname };
    if (normalize(data?.settings)) {
      // Only saved values cross this bridge, never the app's temporary preview
      payload.profile = { settings: data.settings, updatedAt: data.updatedAt || new Date().toISOString() };
    }
    chrome.storage.local.set(payload, () => {
      const error = chrome.runtime.lastError;
      document.documentElement.dataset.pariviewExtension = error ? 'error' : payload.profile ? 'synced' : 'connected';
      document.dispatchEvent(new Event('pariview-extension-ready'));
    });
  }

  function applyVisual() {
    if (!active()) { style?.remove(); style = null; return; }
    if (!style?.isConnected) {
      style = document.createElement('style');
      style.id = 'pariview-extension-style';
      (document.head || document.documentElement).appendChild(style);
    }
    const { brightness, contrast, saturation, warmth } = state.settings;
    const css = `video{filter:brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%) sepia(${warmth * .35}%) !important}`;
    if (style.textContent !== css) style.textContent = css;
  }

  // Do not take over protected/opaque media: Web Audio can otherwise silence it
  function audioSupport(v) {
    if (v.mediaKeys || encrypted.has(v)) return 'protected';
    if (v.error) return 'media-error';
    if (v.srcObject) return 'stream';
    const src = v.currentSrc;
    if (!src || v.readyState < 2) return 'loading';
    try {
      const url = new URL(src, location.href);
      if (url.protocol === 'data:') return 'supported';
      if (url.origin === location.origin) return 'supported';
      // A successful CORS-enabled fetch is usable, unlike an opaque cross-origin fetch
      if (v.crossOrigin && ['http:', 'https:'].includes(url.protocol)) return 'supported';
    } catch { /* Unknown media source */ }
    return 'cross-origin';
  }

  function route(g) {
    const on = active() && audioSupport(g.video) === 'supported';
    const want = !on ? 'bypass' : state.settings.compression ? 'compressed' : 'direct';
    if (g.route !== want) {
      g.source.disconnect();
      g.eq.disconnect();
      g.comp.disconnect();
      if (want === 'bypass') {
        // Exact effect bypass: even the 20 kHz low-pass must leave the signal path
        g.source.connect(ctx.destination);
      } else {
        g.source.connect(g.lowpass);
        if (want === 'compressed') { g.eq.connect(g.comp); g.comp.connect(g.gain); }
        else g.eq.connect(g.gain);
      }
      g.route = want;
    }
    if (on) {
      const now = ctx.currentTime;
      g.gain.gain.setTargetAtTime(state.settings.volume / 100, now, .08);
      g.lowpass.frequency.setTargetAtTime(20000 * Math.pow(.16, state.settings.highCut / 100), now, .08);
      g.eq.gain.setTargetAtTime(state.settings.dialogueBoost ? 4 : 0, now, .08);
    }
  }

  function attachAudio(v) {
    if (!active() || v.paused || audioSupport(v) !== 'supported' || ctx?.state !== 'running') return;
    const existing = graphByVideo.get(v);
    if (existing) { graphs.add(existing); route(existing); return; }
    if (audioErrors.has(v)) return;
    try {
      const gain = ctx.createGain();
      gain.gain.value = state.settings.volume / 100;
      const comp = ctx.createDynamicsCompressor();
      comp.threshold.value = -25; comp.knee.value = 22; comp.ratio.value = 5;
      comp.attack.value = .008; comp.release.value = .25;
      const lowpass = ctx.createBiquadFilter(); lowpass.type = 'lowpass'; lowpass.Q.value = .5;
      const eq = ctx.createBiquadFilter(); eq.type = 'peaking'; eq.frequency.value = 3000; eq.Q.value = 1;
      const source = ctx.createMediaElementSource(v);
      lowpass.connect(eq);
      gain.connect(ctx.destination);
      const g = { video: v, source, gain, comp, lowpass, eq, route: '' };
      graphByVideo.set(v, g);
      graphs.add(g);
      route(g);
    } catch {
      // Another player/extension may already own a MediaElementAudioSourceNode
      audioErrors.set(v, 'unavailable');
    }
  }

  function prepareAudio() {
    if (preparingAudio || !active() || !videos().some(v => !v.paused && audioSupport(v) === 'supported')) return;
    if (!navigator.userActivation?.hasBeenActive) return;
    try { ctx ||= new AudioContext(); } catch { return; }
    // Wait until running BEFORE creating a media source, to avoid autoplay silence
    preparingAudio = Promise.resolve().then(async () => {
      try {
        if (ctx.state !== 'running') await ctx.resume();
        if (ctx.state === 'running') videos().forEach(attachAudio);
      } catch { /* The popup asks for a gesture instead of claiming success */ }
      finally { preparingAudio = null; }
    });
  }

  function refresh() {
    applyVisual();
    graphs.forEach(g => {
      if (!g.video.isConnected) {
        g.source.disconnect(); g.eq.disconnect(); g.comp.disconnect();
        g.route = ''; graphs.delete(g);
      } else route(g);
    });
    prepareAudio();
  }

  function scheduleRefresh() {
    if (refreshQueued) return;
    refreshQueued = true;
    queueMicrotask(() => { refreshQueued = false; refresh(); });
  }

  function videoStatus(v) {
    const support = audioSupport(v);
    const g = graphByVideo.get(v);
    let audio = 'waiting';
    if (!active()) audio = 'off';
    else if (g && support !== 'supported' && support !== 'loading') audio = 'reload-required';
    else if (support !== 'supported') audio = support;
    else if (audioErrors.has(v)) audio = 'unavailable';
    else if (g && ctx.state === 'running' && g.route !== 'bypass') audio = 'applied';
    else if (!navigator.userActivation?.hasBeenActive || ctx?.state !== 'running') audio = 'gesture';
    else if (v.paused) audio = 'paused';
    return { visual: active(), audio, reloadRequired: !!g && !['supported', 'loading'].includes(support), paused: v.paused, muted: v.muted || v.volume === 0, ended: v.ended, ready: v.readyState, error: !!v.error };
  }

  // Each frame replies independently, so embedded videos are included in the popup
  chrome.runtime.onMessage.addListener((message, _sender, respond) => {
    if (message?.type !== 'pariview-status') return;
    const status = { app: isApp, enabled: state.enabled, saved: !!state.settings, videos: videos().filter(v => v.getClientRects().length).map(videoStatus) };
    chrome.runtime.sendMessage({ type: 'pariview-status-result', requestId: message.requestId, status }, () => { void chrome.runtime.lastError; });
    respond({ received: true });
  });

  chrome.storage.local.get(['profile', 'enabled'], r => {
    if (chrome.runtime.lastError) return;
    state.settings = normalize(r.profile?.settings);
    state.enabled = r.enabled !== false;
    refresh();
  });
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local') return;
    if (changes.profile) state.settings = normalize(changes.profile.newValue?.settings);
    if (changes.enabled) state.enabled = changes.enabled.newValue !== false;
    refresh();
  });

  if (isApp) {
    syncSavedProfile();
    document.addEventListener('pariview-saved', syncSavedProfile);
    addEventListener('storage', e => { if (e.key === KEY) syncSavedProfile(); });
    return;
  }

  for (const type of ['play', 'playing', 'loadedmetadata', 'loadeddata', 'emptied', 'error', 'encrypted']) {
    document.addEventListener(type, e => {
      if (!(e.target instanceof HTMLVideoElement)) return;
      if (type === 'encrypted') encrypted.add(e.target);
      scheduleRefresh();
    }, true);
  }
  const onGesture = () => {
    // A key/pointer event may be about to start playback, so media events also retry
    if (ctx && ctx.state !== 'running') ctx.resume().catch(() => {});
    prepareAudio();
  };
  addEventListener('pointerdown', onGesture, true);
  addEventListener('keydown', onGesture, true);
  addEventListener('pageshow', scheduleRefresh);
  document.addEventListener('yt-navigate-finish', scheduleRefresh);
  new MutationObserver(records => {
    if (records.some(r => [...r.addedNodes, ...r.removedNodes].some(n => n.nodeType === 1 && (n.matches('video') || n.querySelector('video'))))) scheduleRefresh();
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
