import {ROLE, request, forgetSession} from './client.js';
import {$, node, button, bindForm, task, status} from './ui.js';

function showCodes(codes) {
  $('recovery-output').hidden = false;
  $('recovery-codes').value = codes.join('\n');
  if (window.dispatchEvent(new CustomEvent('sullivan-recovery-ready', {cancelable:true}))) {
    $('recovery-title').focus();
    status('복구 코드를 만들었습니다. 아래에서 파일로 저장하세요. 이전에 발급한 코드는 더 이상 사용할 수 없습니다.');
  }
}
export function initializeAccounts() {
  bindForm('signup-form', async credentials => {
    const result = await request(`/extension/v1/${ROLE}/accounts`, {method:'POST', anonymous:true,
      body:{...credentials, role:ROLE}});
    window.dispatchEvent(new CustomEvent('sullivan-account-created'));
    $('signup-form').reset(); showCodes(result.recovery_codes);
    $('username').value = result.username;
  });
  bindForm('recover-form', async payload => {
    const result = await request(`/extension/v1/${ROLE}/recover`, {method:'POST', anonymous:true, body:payload});
    $('recover-form').reset(); status(result.message);
  });
  bindForm('recovery-form', async payload => {
    const result = await request(`/extension/v1/${ROLE}/recovery-codes`, {method:'POST', body:payload});
    $('recovery-form').reset(); showCodes(result.recovery_codes);
  });
  $('download-recovery').addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([`Sullivan AI ${ROLE} 복구 코드\n각 코드는 한 번만 사용할 수 있습니다.\n\n${$('recovery-codes').value}\n`], {type:'text/plain;charset=utf-8'}));
    const link=node('a','',{href:url,download:`sullivan-${ROLE}-recovery.txt`}); link.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000); status('복구 코드 파일을 내보냈습니다.');
  });
  $('clear-recovery').addEventListener('click',()=>{
    $('recovery-codes').value=''; $('recovery-output').hidden=true;
    if(window.dispatchEvent(new CustomEvent('sullivan-recovery-cleared',{cancelable:true})))
      ($('account-controls').hidden?$('login-title'):$('account-title')).focus();
  });
  $('devices-refresh').addEventListener('click',()=>task($('devices-refresh'),async()=>{
    const devices=await request(`/extension/v1/${ROLE}/devices`);
    $('devices').replaceChildren(...devices.map(device=>{
      const item=node('li');
      item.append(node('p',`로그인 시작 ${new Date(device.created*1000).toLocaleString('ko-KR')}`),button('이 기기의 로그인 종료',async()=>{
        await request(`/extension/v1/${ROLE}/devices/${device.id}`,{method:'DELETE'});
        const {session}=await chrome.storage.session.get('session');
        if(session?.family_id===device.id)await forgetSession();
        else { item.remove(); $('account-title').focus(); status('선택한 기기의 로그인을 종료했습니다.'); }
      })); return item;
    }));
    if(!devices.length)$('devices').append(node('li','갱신 가능한 로그인 기기가 없습니다. 기존 로그인은 전체 로그아웃으로 종료할 수 있습니다.'));
    status(`갱신 가능한 로그인 ${devices.length}개입니다.`);
  }));
  $('logout-all').addEventListener('click',()=>{ $('logout-all-confirm').hidden=false; $('logout-all-yes').focus(); });
  $('logout-all-no').addEventListener('click',()=>{ $('logout-all-confirm').hidden=true; $('logout-all').focus(); });
  $('logout-all-yes').addEventListener('click',()=>task($('logout-all-yes'),async()=>{
    await request(`/extension/v1/${ROLE}/logout-all`,{method:'POST'}); await forgetSession(); status('모든 기기의 로그인을 종료했습니다.');
  }));
}
