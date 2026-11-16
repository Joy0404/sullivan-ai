import {$, status, task} from './ui.js';

const GUIDE_KEY = 'guardian-guide-v1-seen';

// The guide belongs to this extension/profile, independent of server accounts.
export async function initializeGuardianEntry() {
  let seen = false;
  const readError = '설명서 확인 기록을 읽지 못했습니다. 사용 설명서를 확인한 뒤 계속할 수 있습니다.';
  try { seen = (await chrome.storage.local.get(GUIDE_KEY))[GUIDE_KEY] === true; }
  catch { status(readError, true); }
  let guideOpen = !seen, authenticated = false, ready = false, view = 'start';
  // Every new program page starts at the account choices, even with a valid session.
  let entryPending = true;
  let returnFocus = null, recoveryPending = false;
  const guide = $('guardian-guide');
  const headings = {start: 'guardian-start-title', login: 'login-title', signup: 'guardian-signup-title'};
  const panels = {start: 'guardian-start', login: 'guardian-login-view', signup: 'guardian-signup-view'};
  function target() { return authenticated && !entryPending ? $('workspace-title') : view === 'start' ? $('guardian-login-choice') : $(headings[view]); }
  function render() {
    guide.hidden = !guideOpen;
    $('guardian-content').hidden = guideOpen;
    $('guardian-help').hidden = guideOpen;
    $('auth').hidden = !ready || (authenticated && !entryPending);
    $('workspace').hidden = !authenticated || entryPending;
    $('account-controls').hidden = !authenticated || entryPending;
    $('account-name').hidden = entryPending || guideOpen;
    $('logout').hidden = !authenticated || entryPending || guideOpen;
    document.body.classList.toggle('guardian-guide-open', guideOpen);
    for (const [name, id] of Object.entries(panels)) $(id).hidden = view !== name;
    $('auth').setAttribute('aria-labelledby', headings[view]);
    $('guardian-guide-done').textContent = seen ? '이전 화면으로 돌아가기' : '로그인·회원가입으로 계속';
    $('guardian-guide-done').disabled = !ready;
    const waitText = ready ? '시작할 준비가 됐습니다. 아래 버튼으로 계속하거나 전체 설명서를 펼쳐 확인하세요.' : '로그인 상태를 확인하고 있습니다. 잠시 기다려 주세요.';
    if ($('guardian-guide-wait').textContent !== waitText) $('guardian-guide-wait').textContent = waitText;
  }
  function choose(next, focus = true) {
    view = next; render();
    if (focus && !guideOpen) target().focus();
  }
  $('guardian-login-choice').addEventListener('click', () => {
    if (authenticated) {
      entryPending = false; render(); target().focus();
      status('유지된 로그인으로 보호자 화면을 열었습니다.');
    } else choose('login');
  });
  $('guardian-signup-choice').addEventListener('click', () => choose('signup'));
  for (const id of ['guardian-login-back', 'guardian-signup-back']) {
    $(id).addEventListener('click', () => choose('start'));
  }
  $('guardian-help').addEventListener('click', () => {
    returnFocus = document.activeElement;
    guideOpen = true; render(); $('guardian-guide-title').focus();
  });
  $('guardian-guide-done').addEventListener('click', () => task($('guardian-guide-done'), async () => {
    let saveFailed = false;
    if (!seen) {
      try { await chrome.storage.local.set({[GUIDE_KEY]: true}); }
      catch { saveFailed = true; }
      seen = true;
    }
    guideOpen = false; render();
    if (recoveryPending && !$('recovery-output').hidden) {
      recoveryPending = false; $('recovery-title').focus();
      status('복구 코드를 만들었습니다. 복구 코드 영역에서 파일로 저장하세요.');
    } else if (ready) {
      const previous = returnFocus; returnFocus = null;
      (previous?.isConnected && previous.getClientRects().length ? previous : target()).focus();
    }
    if (saveFailed) status('설명서 확인 기록을 저장하지 못했습니다. 이번에는 계속할 수 있지만 다음 방문에 설명서가 다시 나타날 수 있습니다.', true);
    else if ($('error').textContent === readError) $('error').textContent = '';
  }));
  window.addEventListener('sullivan-account-created', () => { choose('login', false); });
  window.addEventListener('sullivan-recovery-ready', event => {
    if (guideOpen) { event.preventDefault(); recoveryPending = true; }
  });
  window.addEventListener('sullivan-recovery-cleared', event => {
    if (!authenticated || entryPending) { event.preventDefault(); (guideOpen ? $('guardian-guide-title') : target()).focus(); }
  });
  render();
  if (guideOpen) $('guardian-guide-title').focus();
  return {
    signedOutFocus() {
      const wasReady = ready;
      authenticated = false; ready = true; entryPending = true; returnFocus = null; recoveryPending = false;
      choose('start', false);
      if (!wasReady) $('status').textContent = '';
      return guideOpen ? null : target();
    },
    beforeUserFocus() {
      if (ready) entryPending = false;
      if (!ready) $('status').textContent = '';
      authenticated = true; ready = true; returnFocus = null;
      render();
    },
    afterUserRender: render,
    userFocus() { return guideOpen ? null : target(); },
  };
}
