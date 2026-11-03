import {research, clinicalFrameworks, sensoryPatterns, therapyStudies, designProposals} from './research.js';

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
}

function sourceLink(source) {
  return `<a href="${escapeHTML(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(source.label)} <span aria-hidden="true">↗</span><span class="research-sr-only"> 새 창</span></a>`;
}

export function renderResearchPage() {
  const root = document.querySelector('#research-view');
  root.querySelector('#research-cards').innerHTML = research.map((study, index) => `
    <article class="research-card" data-evidence-category="${study.category}" id="evidence-${study.id}">
      <div class="evidence-card-top"><span class="tag">${escapeHTML(study.tag)}</span><span class="evidence-number">${String(index + 1).padStart(2, '0')}</span></div>
      <h3>${escapeHTML(study.title)}</h3>
      <div class="evidence-meta"><span>${escapeHTML(study.method)}</span><span>${escapeHTML(study.sample)}</span></div>
      <div class="evidence-finding"><span class="evidence-label">연구에서 확인</span><p>${escapeHTML(study.text)}</p></div>
      <div class="evidence-design"><span class="evidence-label">설계에 반영</span><p>${escapeHTML(study.design)}</p></div>
      <details class="evidence-details">
        <summary>연구의 범위와 출처 <span class="details-symbol" aria-hidden="true">+</span></summary>
        <div class="evidence-detail-body"><span class="evidence-label">연구 대상과 범위</span><p>${escapeHTML(study.limitation)}</p>
          <div class="evidence-citation"><span class="reading-level">${escapeHTML(study.reading)}</span><strong>${escapeHTML(study.ref)}</strong><p lang="${study.id === 'white-noise' ? 'ko' : 'en'}">${escapeHTML(study.citation)}</p>
          <span class="source-identifier">${escapeHTML(study.doi ? 'DOI ' + study.doi : study.sourceNote)}</span></div>
        </div>
      </details>
      <div class="evidence-source">${sourceLink({label: study.ref, url: study.url})}</div>
    </article>`).join('');

  const filters = root.querySelector('#research-filters');
  const filterLabels = {all:'전체', difference:'개인차', control:'통제권', audiovisual:'시청각', prediction:'사전 안내'};
  filters.innerHTML = Object.entries(filterLabels).map(([key, label]) => {
    const count = key === 'all' ? research.length : research.filter(study => study.category === key).length;
    return `<button type="button" data-evidence-filter="${key}" aria-pressed="${key === 'all'}" aria-controls="research-cards">${label}<span>${count}</span></button>`;
  }).join('');
  filters.addEventListener('click', event => {
    const button = event.target.closest('[data-evidence-filter]');
    if (!button) return;
    const selected = button.dataset.evidenceFilter;
    filters.querySelectorAll('button').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    let count = 0;
    root.querySelectorAll('.research-card').forEach(card => {
      card.hidden = selected !== 'all' && card.dataset.evidenceCategory !== selected;
      if (!card.hidden) count++;
    });
    root.querySelector('#research-count').textContent = `${filterLabels[selected]} · ${count}편`;
  });

  root.querySelector('#clinical-frameworks').innerHTML = clinicalFrameworks.map(item => `
    <article class="clinical-framework" id="framework-${item.id}">
      <div class="clinical-index"><span>${item.number}</span><h3>${escapeHTML(item.field)}</h3></div>
      <div class="clinical-content"><h4>${escapeHTML(item.title)}</h4>
        <div class="clinical-columns"><div><span class="evidence-label">평가·연구에서 참고</span><p>${escapeHTML(item.evidence)}</p></div><div><span class="evidence-label">PariView의 설계 제안</span><p>${escapeHTML(item.design)}</p></div></div>
        <p class="clinical-boundary">${escapeHTML(item.boundary)}</p>
        <div class="clinical-sources">${item.sources.map(sourceLink).join('')}</div>
      </div>
    </article>`).join('');

  root.querySelector('#sensory-patterns').innerHTML = sensoryPatterns.map(pattern => `
    <div class="sensory-pattern"><h4>${escapeHTML(pattern.name)}</h4><p>${escapeHTML(pattern.description)}</p></div>`).join('');
  root.querySelector('#therapy-studies').innerHTML = therapyStudies.map(study => `
    <article class="therapy-study"><h4>${escapeHTML(study.title)}</h4><p class="therapy-sample">${escapeHTML(study.sample)}</p><p>${escapeHTML(study.finding)}</p><p class="therapy-boundary">${escapeHTML(study.boundary)}</p>${sourceLink({label:study.ref, url:study.url})}</article>`).join('');
  root.querySelector('#design-proposals').innerHTML = designProposals.map(proposal => `
    <article class="design-proposal"><span class="proposal-number">${proposal.number}</span><h3>${escapeHTML(proposal.title)}</h3><p>${escapeHTML(proposal.text)}</p><blockquote>${escapeHTML(proposal.question)}</blockquote><div class="proposal-basis"><span class="evidence-label">참고한 근거</span><p>${escapeHTML(proposal.basis)}</p>${sourceLink({label:proposal.source, url:proposal.url})}</div></article>`).join('');

  root.querySelectorAll('[data-research-jump]').forEach(button => {
    button.addEventListener('click', () => {
      const target = root.querySelector('#' + button.dataset.researchJump);
      const reduceMotion = document.body.classList.contains('reduce-motion') || matchMedia('(prefers-reduced-motion: reduce)').matches;
      target.focus({preventScroll:true});
      target.scrollIntoView({behavior: reduceMotion ? 'instant' : 'smooth', block:'start'});
    });
  });
}
