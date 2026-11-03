// A registered store item is not necessarily available for installation yet.
// Enable the store route only after its public listing has been verified.
export function initExtensionConnection({openChrome, reducedMotion}) {
  const $ = selector => document.querySelector(selector);
  const mobile = matchMedia('(max-width:700px)');
  let storeUrl = null;
  let releaseStatus = 'draft';
  const copy = {
    none: ['아직 연결되지 않았어요', '설치한 뒤 이 페이지를 새로고침하면 연결돼요'],
    connected: ['확장 프로그램이 연결됐어요', '마음에 드는 설정을 저장하면 확장 프로그램에 전달돼요'],
    synced: ['설정이 확장 프로그램에 저장됐어요', '실제 적용 여부는 유튜브에서 PariView 아이콘을 눌러 확인해요'],
    error: ['확장 프로그램에 설정을 저장하지 못했어요', '확장 프로그램을 확인한 뒤 이 페이지를 새로고침해 주세요']
  };

  function render() {
    const reported = document.documentElement.dataset.pariviewExtension;
    const state = Object.hasOwn(copy, reported) ? reported : 'none';
    let [title, description] = copy[state];
    if (mobile.matches && state === 'none') {
      title = 'PC 크롬에서 연결할 수 있어요';
      description = 'PC에서 설치하면 저장한 설정을 다른 영상에도 쓸 수 있어요';
    }
    $('#extension-status').dataset.state = state;
    $('#extension-status-title').textContent = title;
    $('#extension-status-desc').textContent = description;
    const connected = state === 'connected' || state === 'synced';
    const primary = $('#extension-connect');
    primary.querySelector('span').textContent = connected
      ? storeUrl ? '크롬 확장 프로그램 바로가기' : '확장 프로그램 설치 안내'
      : '크롬 확장 프로그램 연결하기';

    for (const link of [primary, $('#extension-store-link'), $('#extension-shortcut')]) {
      link.href = storeUrl || '#chrome';
      if (storeUrl) {
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
      } else {
        link.removeAttribute('target');
        link.removeAttribute('rel');
      }
    }
    $('#extension-store-link').hidden = !storeUrl;
    $('#extension-store-instructions').hidden = !storeUrl;
    $('#extension-release-note').hidden = !!storeUrl;
    $('#extension-release-note').textContent = releaseStatus === 'review'
      ? 'Chrome 웹스토어 심사 중이에요 지금은 아래 설치 안내로 연결할 수 있어요'
      : '지금은 아래 설치 안내에서 확장 프로그램을 연결할 수 있어요';
  }

  function openInstallGuide(event) {
    if (storeUrl) return;
    event.preventDefault();
    if ($('#chrome-view').hidden) openChrome();
    $('#extension-manual-install').open = true;
    $('#extension-installation').scrollIntoView({behavior: reducedMotion() ? 'instant' : 'smooth', block: 'start'});
    $('#extension-install-title').focus({preventScroll:true});
  }

  for (const link of [$('#extension-connect'), $('#extension-shortcut')]) {
    link.addEventListener('click', openInstallGuide);
  }
  $('#extension-refresh').addEventListener('click', () => location.reload());
  document.addEventListener('pariview-extension-ready', render);
  mobile.addEventListener('change', render);
  render();

  fetch('./extension-release.json', {cache:'no-store'})
    .then(response => response.ok ? response.json() : null)
    .then(release => {
      if (!release) return;
      releaseStatus = release.status;
      if (release.status === 'published' && release.storeUrl) {
        const url = new URL(release.storeUrl);
        if (url.protocol === 'https:' && url.hostname === 'chromewebstore.google.com'
          && /^[a-p]{32}$/.test(release.itemId || '')
          && url.pathname.startsWith('/detail/')
          && url.pathname.split('/').filter(Boolean).at(-1) === release.itemId) {
          storeUrl = url.href;
        }
      }
      $('#extension-manual-install').open = !storeUrl;
      render();
    })
    .catch(() => { /* The working local installation guide remains available */ });
}
