/* Shift alone moves backward; combinations and native text editing stay native. */
window.SullivanKeyboard = (() => {
  const selector = 'a[href],button,input:not([type="hidden"]),select,textarea,summary,iframe,video[controls],audio[controls],[tabindex],[contenteditable="true"]';
  let pending = null, interaction = 0;
  const visible = node => Boolean(node?.isConnected && node.getClientRects().length &&
    !node.closest('[inert],[hidden],[aria-hidden="true"]') &&
    getComputedStyle(node).visibility !== 'hidden' && !node.matches(':disabled'));
  const editable = node => Boolean(node?.closest('textarea,select,[contenteditable="true"],[role="textbox"],input:not([type="checkbox"]):not([type="radio"]):not([type="button"]):not([type="submit"])'));
  function scope() {
    return [...document.querySelectorAll('dialog[open],[role="dialog"][aria-modal="true"]')].reverse().find(visible) || document;
  }
  function controls(root = scope()) {
    return [...root.querySelectorAll(selector)].filter(node => visible(node) && node.tabIndex >= 0)
      .map((node, order) => ({node, order}))
      .sort((a, b) => (a.node.tabIndex > 0 ? a.node.tabIndex : Infinity) -
        (b.node.tabIndex > 0 ? b.node.tabIndex : Infinity) || a.order - b.order)
      .map(entry => entry.node);
  }
  function previous() {
    const root = scope(), list = controls(root), current = document.activeElement;
    if (!list.length) return false;
    const index = list.indexOf(current);
    let target = index > 0 ? list[index - 1] : index === 0 && root !== document ? list.at(-1) : null;
    if (index < 0) target = list.filter(node => node.compareDocumentPosition(current) & Node.DOCUMENT_POSITION_FOLLOWING).at(-1);
    if (!target || target === current) return false;
    target.focus();return document.activeElement === target;
  }
  function focus(targets, ticket) {
    if (ticket !== undefined && ticket !== interaction) return false;
    for (const target of Array.isArray(targets) ? targets : [targets]) {
      const node = typeof target === 'string' ? document.querySelector(target) : target;
      if (visible(node)) {node.focus();return document.activeElement === node;}
    }
    return false;
  }
  document.addEventListener('keydown', event => {
    interaction += 1;
    if (event.key !== 'Shift') {pending = null;return;}
    if (event.repeat) return;
    if (pending || event.altKey || event.ctrlKey || event.metaKey || event.isComposing || editable(document.activeElement)) {
      pending = null;return;
    }
    pending = {code: event.code, origin: document.activeElement};
  }, true);
  document.addEventListener('keyup', event => {
    if (event.key !== 'Shift') return;
    const candidate = pending;pending = null;
    if (!candidate || candidate.code !== event.code || candidate.origin !== document.activeElement ||
        event.shiftKey || event.altKey || event.ctrlKey || event.metaKey || event.isComposing) return;
    if (previous()) event.preventDefault();
  }, true);
  document.addEventListener('pointerdown', () => {interaction += 1;pending = null;}, true);
  document.addEventListener('compositionstart', () => {pending = null;}, true);
  window.addEventListener('blur', () => {pending = null;});
  document.addEventListener('visibilitychange', () => {if (document.hidden) pending = null;});
  return {focus, previous, controls, ticket: () => interaction, revision: 'learning-desk-4'};
})();
