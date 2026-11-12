import {restore, signIn, signOut, browserSignIn, ROLE} from './client.js';
import {initializeAccounts} from './accounts.js';

export const $ = id => document.getElementById(id);
export function node(tag, text, props = {}) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  Object.assign(element, props);
  return element;
}
export function status(text, error = false) {
  $(error ? 'error' : 'status').textContent = text;
  $(error ? 'status' : 'error').textContent = '';
}
export async function task(control, action) {
  if (control.disabled || control.dataset.busy) return;
  control.dataset.busy = 'true';
  control.setAttribute('aria-disabled', 'true');
  control.setAttribute('aria-busy', 'true');
  try { await action(); } catch (error) { status(error.message, true); }
  finally { delete control.dataset.busy; control.removeAttribute('aria-disabled'); control.removeAttribute('aria-busy'); }
}
export function button(text, action) {
  const element = node('button', text, {type: 'button'});
  element.addEventListener('click', () => task(element, action));
  return element;
}
export function values(form) { return Object.fromEntries(new FormData(form)); }
export function bindForm(id, action) {
  $(id).addEventListener('submit', event => {
    event.preventDefault();
    task(event.submitter || $(id).querySelector('button[type=submit]'), () => action(values($(id))));
  });
}

export async function boot(onUser, onExit = () => {}) {
  initializeAccounts();
  let interacted = false;
  const interaction = () => { interacted = true; };
  window.addEventListener('keydown', interaction, {once: true});
  window.addEventListener('pointerdown', interaction, {once: true});
  function signedOut(initial = false) {
    onExit();
    $('workspace').hidden = true;
    $('auth').hidden = false;
    $('account-name').textContent = '';
    $('logout').hidden = true;
    $('account-controls').hidden = true;
    $('recovery-output').hidden = true; $('recovery-codes').value = '';
    if (!initial || !interacted) ($('username').getClientRects().length ? $('username') : $('oauth-login')).focus();
  }
  async function signedIn(user, initial = false) {
    if (user.role !== ROLE) throw new Error('이 프로그램의 계정으로 로그인해 주세요.');
    $('auth').hidden = true;
    $('workspace').hidden = false;
    $('logout').hidden = false;
    $('account-controls').hidden = false;
    $('account-name').textContent = user.name;
    if (!initial || !interacted) $('workspace-title').focus();
    await onUser(user);
  }
  window.addEventListener('sullivan-signed-out', () => signedOut());
  $('oauth-login').addEventListener('click',()=>task($('oauth-login'),async()=>{
    await signedIn(await browserSignIn($('remember-login').checked)); status('브라우저 로그인을 완료했습니다.');
  }));
  bindForm('login-form', async ({username, password}) => {
    const user = await signIn({username, password});
    $('password').value = '';
    status('로그인했습니다.');
    await signedIn(user);
  });
  $('logout').addEventListener('click', () => task($('logout'), async () => {
    await signOut(); signedOut(); status('로그아웃했습니다.');
  }));
  try {
    const user = await restore();
    if (user) await signedIn(user, true); else signedOut(true);
  } catch (error) { signedOut(true); status(error.message, true); }
  return signedIn;
}
