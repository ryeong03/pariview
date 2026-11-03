const $ = s => document.querySelector(s);

function formatTime(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return `${d.getMonth() + 1}월 ${d.getDate()}일 ${d.toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit' })}에 가져왔어요`;
}

function openPariView(source) {
  if (source) chrome.tabs.create({ url: source });
}

chrome.storage.local.get(['profile', 'enabled', 'source'], ({ profile, enabled, source }) => {
  const s = profile && profile.settings;
  $('#empty').hidden = !!s;
  $('#ready').hidden = !s;
  $('#open-empty').hidden = !source;
  $('#open-empty').onclick = () => openPariView(source);
  $('#open-ready').hidden = !source;
  $('#open-ready').onclick = () => openPariView(source);
  if (!s) return;

  $('#v-brightness').textContent = `${s.brightness}%`;
  $('#v-contrast').textContent = `${s.contrast}%`;
  $('#v-volume').textContent = `${s.volume}%`;
  $('#v-compression').textContent = s.compression === false ? '꺼짐' : '켜짐';
  $('#updated').textContent = formatTime(profile.updatedAt);

  const sw = $('#enabled');
  const render = on => {
    sw.setAttribute('aria-checked', String(on));
    $('#ready h1').textContent = on ? '이 설정으로 영상을 보고 있어요' : '지금은 원래 화면으로 보고 있어요';
  };
  let on = enabled !== false;
  render(on);
  sw.onclick = () => { on = !on; chrome.storage.local.set({ enabled: on }); render(on); };
});
