// Dock motion (Anime.js): the "세부 설정" button gets a rotating chevron and a spring press,
// and the detailed rows stagger in when the panel opens. State is still owned by app.js
// (aria-expanded + .preferences.expanded); this module only animates what it observes.
import {animate, stagger, createSpring} from './vendor/anime.esm.min.js';

const reduced = () => document.body.classList.contains('reduce-motion') || matchMedia('(prefers-reduced-motion: reduce)').matches;

function init() {
  const button = document.querySelector('#expand-settings');
  const panel = document.querySelector('.preferences');
  if (!button || !panel) return;

  // Keep app.js's text ("세부 설정 펼치기 ↓" / "접기 ↑") but render the arrow as a rotatable chevron.
  const chevron = document.createElement('span');
  chevron.className = 'chev';
  chevron.setAttribute('aria-hidden', 'true');
  chevron.innerHTML = '<svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>';
  const label = document.createElement('span');
  label.className = 'lbl';
  const syncLabel = () => {
    const text = button.textContent.replace(/[↓↑]/g, '').trim();
    if (label.textContent !== text) label.textContent = text;
    if (!button.contains(label)) { button.textContent = ''; button.append(label, chevron); }
  };
  syncLabel();

  const setChevron = (open, animated) => {
    const rotate = open ? 180 : 0;
    if (!animated || reduced()) { chevron.style.transform = `rotate(${rotate}deg)`; return; }
    animate(chevron, { rotate, duration: 420, ease: createSpring({ stiffness: 260, damping: 18 }) });
  };
  setChevron(button.getAttribute('aria-expanded') === 'true', false);

  const revealRows = () => {
    if (reduced()) return;
    const rows = [...panel.querySelectorAll('.advanced-setting')].filter(el => getComputedStyle(el).display !== 'none');
    if (!rows.length) return;
    animate(rows, { opacity: [0, 1], translateY: [10, 0], duration: 360, delay: stagger(45), ease: 'out(3)' });
  };

  // app.js rewrites textContent and aria-expanded on click; observe instead of re-binding the click.
  new MutationObserver(mutations => {
    const changed = mutations.some(m => m.type === 'attributes' || m.type === 'childList' || m.type === 'characterData');
    if (!changed) return;
    syncLabel();
    const open = button.getAttribute('aria-expanded') === 'true';
    setChevron(open, true);
    if (open) revealRows();
  }).observe(button, { attributes: true, attributeFilter: ['aria-expanded'], childList: true, characterData: true, subtree: true });

  button.addEventListener('pointerdown', () => { if (!reduced()) animate(button, { scale: [1, 0.96], duration: 120, ease: 'out(2)' }); });
  button.addEventListener('pointerup', () => { if (!reduced()) animate(button, { scale: 1, duration: 320, ease: createSpring({ stiffness: 320, damping: 16 }) }); });
  button.addEventListener('pointerleave', () => { if (!reduced()) animate(button, { scale: 1, duration: 200 }); });
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
