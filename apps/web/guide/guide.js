/* The guide stays fully readable if JavaScript is unavailable. */
(() => {
  'use strict';
  const steps = [...document.querySelectorAll('.guide-step')].map(step => {
    const heading = step.querySelector('.step-heading');
    const panel = step.querySelector('.step-content');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'step-toggle';
    button.setAttribute('aria-controls', panel.id);
    const label = document.createElement('span');
    while (heading.firstChild) label.append(heading.firstChild);
    const word = document.createElement('span');
    word.className = 'toggle-word';
    word.setAttribute('aria-hidden', 'true');
    button.append(label, word);
    heading.append(button);
    return {step, panel, button, word};
  });
  const toggleAll = document.getElementById('toggle-all');
  const status = document.getElementById('guide-status');
  const hashStep = () => steps.find(item => '#' + item.step.id === location.hash);
  function setOpen(item, open) {
    item.panel.hidden = !open;
    item.button.setAttribute('aria-expanded', String(open));
    item.word.textContent = open ? '접기' : '펼치기';
  }
  function syncAll() {
    const allOpen = steps.every(item => !item.panel.hidden);
    toggleAll.textContent = allOpen ? '모두 접기' : '모두 펼치기';
    toggleAll.setAttribute('aria-expanded', String(allOpen));
  }
  const initial = hashStep() || steps[0];
  steps.forEach(item => {
    setOpen(item, item === initial);
    item.button.addEventListener('click', () => {
      setOpen(item, item.panel.hidden);
      syncAll();
    });
  });
  toggleAll.setAttribute('aria-controls', steps.map(item => item.panel.id).join(' '));
  toggleAll.hidden = false;
  toggleAll.addEventListener('click', () => {
    const open = steps.some(item => item.panel.hidden);
    steps.forEach(item => setOpen(item, open));
    syncAll();
    status.textContent = open ? '8개 단계를 모두 펼쳤습니다.' : '8개 단계를 모두 접었습니다.';
  });
  function revealHash(focus) {
    const item = hashStep();
    if (!item) return;
    setOpen(item, true);
    syncAll();
    if (focus) item.button.focus({preventScroll: true});
    item.step.scrollIntoView({block: 'start'});
  }
  // A same-step link must also reopen a panel the reader has just collapsed.
  document.querySelectorAll('a[href^="#step-"]').forEach(link => {
    link.addEventListener('click', event => {
      if (link.hash !== location.hash) return;
      event.preventDefault();
      revealHash(true);
    });
  });
  window.addEventListener('hashchange', () => revealHash(true));
  syncAll();
  if (hashStep()) requestAnimationFrame(() => revealHash(false));
})();
