import {request} from './client.js';
import {$,task,status} from './ui.js';
async function send(type,extra={}){
  const response=await chrome.runtime.sendMessage({type,...extra});if(!response?.ok)throw new Error(response?.error||'로그인 지원을 확인하지 못했습니다.');return response.result;
}
export async function installRemoteEnrollment(device){await send('student-remote-install',{device});await update();}
async function update(announce=false){
  const device=await send('student-remote-state');
  const {remoteLoginStatus:message}=await chrome.storage.session.get('remoteLoginStatus');
  const text=device.enabled?`${device.student_name} 학생 · ${device.guardian_name} 보호자의 로그인 요청을 이 기기에서 받을 수 있습니다. 로그아웃 후에도 유지됩니다.`
    :device.registered?'이 기기의 로그인 지원을 중지했습니다. 연결 후 해제 버튼으로 서버 해제를 마치세요.':'이 기기의 보호자 로그인 지원이 꺼져 있습니다. 처음 한 번 로그인하고 연결 승인에서 허용하세요.';
  if($('remote-device-disable')===document.activeElement&&!device.registered)$('remote-access-title').focus();
  $('remote-device-disable').hidden=!device.registered;
  if($('remote-device-status').textContent!==(message||text)){
    $('remote-device-status').textContent=message||text;
    if(announce)window.dispatchEvent(new CustomEvent('sullivan-status',{detail:{text:message||text,error:false}}));
  }
  if(device.enabled&&document.activeElement===$('remote-device-enable'))$('remote-access-title').focus();
  $('remote-device-enable').disabled=device.enabled;
}
export function initializeRemoteLoginUI(){
  $('remote-device-enable').addEventListener('click',()=>task($('remote-device-enable'),async()=>{
    if(!$('remote-consent').checked)throw Object.assign(new Error('로그아웃 후에도 이 기기의 보호자 로그인 지원을 허용할지 확인하세요.'),{field:$('remote-consent')});
    const device=await request('/extension/v1/student/remote-login/devices',{method:'POST',body:{confirm:true,client_id:chrome.runtime.id}});
    await installRemoteEnrollment(device);status('이 기기의 보호자 로그인 지원을 허용했습니다. 다음부터 보호자 화면에서 학생 로그인을 시작할 수 있습니다.');
  }));
  $('remote-device-disable').addEventListener('click',()=>task($('remote-device-disable'),async()=>{await send('student-remote-disable');await update();status('이 기기의 보호자 로그인 지원을 해제했습니다.');}));
  chrome.storage.onChanged.addListener((changes,area)=>{if(area==='local'&&changes.remoteLoginDevice||area==='session'&&changes.remoteLoginStatus)update(true).catch(()=>{});});
  const poll=()=>send('student-remote-poll').catch(()=>{});
  setInterval(poll,5000);poll();update().catch(()=>{});
}
