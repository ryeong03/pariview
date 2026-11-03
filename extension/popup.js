const $ = s => document.querySelector(s);
let profile = null;
let enabled = true;
let source = PariViewSettings.home;
let targetTabId = null;
let requestId = '';
let frames = new Map();
let statusTimer;

function formatTime(iso) {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : `${d.getMonth() + 1}월 ${d.getDate()}일 ${d.toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit' })}에 가져왔어요`;
}

function showStatus(code, title, desc, detail = '') {
  const box = $('.status');
  box.dataset.state = code;
  $('#status-title').textContent = title;
  $('#status-desc').textContent = desc;
  $('#status-detail').textContent = detail;
  $('#status-detail').hidden = !detail;
}

function renderStatus() {
  const reports = [...frames.values()];
  const all = reports.flatMap(r => r.videos);
  const playing = all.filter(v => !v.paused && !v.ended);
  const relevant = playing.length ? playing : all;
  if (!profile) return showStatus('no-profile', '아직 가져온 설정이 없어요', 'PariView에서 설정을 저장하면 이 브라우저로 가져와요');
  if (all.some(v => v.reloadRequired)) return showStatus('reload-required', '영상을 새로고침해주세요', '영상의 소리 보호 방식이 바뀌었어요 페이지를 새로고침하면 원본 소리로 재생해요');
  if (!enabled) return showStatus('off', 'PariView 적용을 껐어요', '저장한 설정은 유지돼요 다시 켜면 영상에 적용돼요');
  if (reports.some(r => r.app)) return showStatus('app', 'PariView와 연결됐어요', '여기서는 웹의 미리보기 설정을 사용해요 저장한 뒤 유튜브에서 확인해주세요');
  if (!reports.length) return showStatus('unavailable', '이 탭에 연결되지 않았어요', '유튜브 등 영상 페이지를 열거나 새로고침해주세요 브라우저 내부 페이지에는 적용할 수 없어요');
  if (!all.length) return showStatus('no-video', '이 탭에 영상이 없어요', '영상을 열면 저장한 화면 설정이 적용돼요');
  if (relevant.every(v => v.error)) return showStatus('media-error', '영상을 불러오지 못했어요', '플레이어의 오류를 확인하거나 페이지를 새로고침해주세요');
  if (relevant.every(v => v.ready < 2)) return showStatus('loading', '영상을 기다리고 있어요', '영상이 준비되면 적용 상태를 확인할 수 있어요');
  const muted = relevant.every(v => v.muted);
  const detail = !playing.length ? '영상이 일시정지되어 있어요' : muted ? '플레이어가 음소거 상태예요 소리를 들으려면 플레이어에서 해제해주세요' : '';
  const applied = relevant.filter(v => v.audio === 'applied').length;
  if (applied === relevant.length) return showStatus('applied', '화면과 소리 설정을 적용 중이에요', '밝기·색감과 지원되는 소리 효과에 저장한 값을 사용해요', detail);
  const blocked = relevant.filter(v => ['protected', 'cross-origin', 'stream', 'unavailable'].includes(v.audio));
  if (blocked.length) {
    const reason = blocked.some(v => v.audio === 'protected') ? '보호된 영상' : blocked.some(v => v.audio === 'cross-origin') ? '소리 접근을 허용하지 않는 영상' : '이 영상';
    return showStatus(applied ? 'partial' : 'visual-only', applied ? '일부 영상은 화면만 적용돼요' : '화면 설정만 적용 중이에요', `${reason}에는 소리 효과를 적용할 수 없어 원본 소리를 유지해요`, detail);
  }
  if (relevant.some(v => v.audio === 'gesture')) return showStatus('gesture', '화면 설정을 적용 중이에요', '소리도 맞추려면 영상 페이지를 한 번 누르고 재생해주세요', detail);
  return showStatus('paused', '화면 설정을 적용 중이에요', '영상을 재생하면 지원되는 소리 설정도 적용돼요', detail);
}

function renderSaved() {
  const s = PariViewSettings.normalize(profile?.settings);
  $('#empty').hidden = !!s;
  $('#ready').hidden = !s;
  if (s) {
    $('#v-brightness').textContent = `${s.brightness}%`;
    $('#v-contrast').textContent = `${s.contrast}%`;
    $('#v-volume').textContent = `${s.volume}%`;
    $('#v-compression').textContent = s.compression ? '켜짐' : '꺼짐';
    $('#v-details').textContent = `채도 ${s.saturation}% · 따뜻함 ${s.warmth}% · 높은 소리 완화 ${s.highCut}% · 말소리 대역 강조 ${s.dialogueBoost ? '켜짐' : '꺼짐'}`;
    $('#updated').textContent = formatTime(profile.updatedAt);
  }
  $('#enabled').setAttribute('aria-checked', String(enabled));
  renderStatus();
}

function requestStatus(tabId = targetTabId) {
  targetTabId = tabId;
  if (tabId == null) { renderStatus(); return; }
  requestId = crypto.randomUUID();
  frames = new Map();
  clearTimeout(statusTimer);
  chrome.tabs.sendMessage(tabId, { type: 'pariview-status', requestId }, () => { void chrome.runtime.lastError; });
  statusTimer = setTimeout(renderStatus, 200);
}

chrome.runtime.onMessage.addListener((message, sender) => {
  if (message?.type !== 'pariview-status-result' || message.requestId !== requestId || sender.tab?.id !== targetTabId) return;
  frames.set(sender.frameId, message.status);
  // Collect iframe replies before announcing a result to avoid "no video" flicker
  clearTimeout(statusTimer);
  statusTimer = setTimeout(renderStatus, 100);
});

function openPariView() {
  let url = PariViewSettings.home;
  try { const parsed = new URL(source); if (['http:', 'https:'].includes(parsed.protocol)) url = parsed.href; } catch { /* Use the public app */ }
  chrome.tabs.create({ url });
}
$('#open-empty').onclick = openPariView;
$('#open-ready').onclick = openPariView;
$('#enabled').onclick = () => {
  chrome.storage.local.set({ enabled: !enabled });
};
chrome.storage.local.get(['profile', 'enabled', 'source'], r => {
  profile = PariViewSettings.normalize(r.profile?.settings) ? r.profile : null;
  enabled = r.enabled !== false;
  source = r.source || PariViewSettings.home;
  renderSaved();
});
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local') return;
  if (changes.profile) profile = PariViewSettings.normalize(changes.profile.newValue?.settings) ? changes.profile.newValue : null;
  if (changes.enabled) enabled = changes.enabled.newValue !== false;
  if (changes.source) source = changes.source.newValue || PariViewSettings.home;
  renderSaved();
  requestStatus();
});
chrome.tabs.query({ active: true, currentWindow: true }, tabs => requestStatus(tabs[0]?.id));
setInterval(() => requestStatus(), 1000);
