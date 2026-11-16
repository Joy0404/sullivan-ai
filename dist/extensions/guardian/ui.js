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
  window.dispatchEvent(new CustomEvent('sullivan-status',{detail:{text,error}}));
}
export async function task(control, action) {
  if (control.disabled || control.dataset.busy) return;
  control.dataset.busy = 'true';
  control.setAttribute('aria-disabled', 'true');
  control.setAttribute('aria-busy', 'true');
  try { await action(); } catch (error) { if(!error.cancelled){if(!error.reported)status(error.message, true);error.field?.focus();} }
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

export async function boot(onUser, onExit = () => {}, {
  beforeUserFocus=()=>{},
  afterUserRender=()=>{},
  signedOutFocus=()=>($('username').getClientRects().length ? $('username') : $('oauth-login')),
  userFocus=()=>$('workspace-title'),
}={}) {
  initializeAccounts();
  let interacted = false;
  let transition = 0;
  let signedOutShown = false;
  const interaction = () => { interacted = true; };
  window.addEventListener('keydown', interaction, {once: true});
  window.addEventListener('pointerdown', interaction, {once: true});
  function signedOut(initial = false) {
    // Storage notifications and the logout action may report the same exit.
    // A second notification must not reset a newly selected login/signup form.
    if (signedOutShown) return;
    signedOutShown = true;
    transition++;
    onExit();
    $('workspace').hidden = true;
    $('auth').hidden = false;
    $('account-name').textContent = '';
    $('logout').hidden = true;
    $('account-controls').hidden = true;
    $('recovery-output').hidden = true; $('recovery-codes').value = '';
    const target=signedOutFocus();
    if (!initial || !interacted || !document.activeElement.getClientRects().length) target?.focus();
  }
  async function signedIn(user, initial = false) {
    if (user.role !== ROLE) throw new Error('이 프로그램의 계정으로 로그인해 주세요.');
    signedOutShown = false;
    beforeUserFocus(user);
    $('auth').hidden = true;
    $('workspace').hidden = false;
    $('logout').hidden = false;
    $('account-controls').hidden = false;
    $('account-name').textContent = user.name;
    afterUserRender(user);
    if (!initial || !interacted || !document.activeElement.getClientRects().length) userFocus()?.focus();
    await onUser(user);
  }
  window.addEventListener('sullivan-signed-out', () => signedOut());
  window.addEventListener('sullivan-remote-signed-in',()=>{
    const ticket=++transition;
    restore().then(async user=>{if(user&&ticket===transition){await signedIn(user);if(ticket===transition)status('보호자 요청으로 로그인했습니다. 강의를 선택하세요.');}})
      .catch(error=>{if(ticket===transition&&!error.cancelled)status(error.message,true);});
  });
  $('oauth-login').addEventListener('click',()=>task($('oauth-login'),async()=>{
    await signedIn(await browserSignIn($('remember-login').checked)); status('브라우저 로그인을 완료했습니다.');
  }));
  bindForm('login-form', async ({username, password}) => {
    const user = await signIn({username, password});
    $('password').value = '';
    await signedIn(user);
    status('로그인했습니다.');
  });
  $('logout').addEventListener('click', () => task($('logout'), async () => {
    await signOut(); signedOut(); status('로그아웃했습니다.');
  }));
  const initialTransition=transition;
  try {
    const user = await restore();
    if(initialTransition===transition){if (user) await signedIn(user, true); else signedOut(true);}
  } catch (error) { if(initialTransition===transition){signedOut(true); status(error.message, true);} }
  return signedIn;
}
