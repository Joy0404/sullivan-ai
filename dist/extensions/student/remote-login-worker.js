import {SERVER,VERSION} from './config.js';
const local=chrome.storage.local,storage=chrome.storage.session;
const trusted=Promise.all([local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'}),storage.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'})]);
const headers=()=>({'X-Sullivan-Client':'student','X-Sullivan-Version':VERSION,'X-Local-Request':'1','Content-Type':'application/json'});
const proof=device=>({device_id:device.device_id,device_secret:device.device_secret,client_id:chrome.runtime.id});
async function api(path,body,token){
  const response=await fetch(SERVER+'/extension/v1/student/'+path,{method:'POST',credentials:'omit',cache:'no-store',headers:{...headers(),...(token?{Authorization:'Bearer '+token}:{})},body:JSON.stringify(body),signal:AbortSignal.timeout(15000)});
  const data=await response.json().catch(()=>({}));
  if(!response.ok)throw Object.assign(new Error(typeof data.detail==='string'?data.detail:'로그인 지원 서버 연결을 확인하세요.'),{status:response.status});
  return data;
}
async function state(){const {remoteLoginDevice:device}=await local.get('remoteLoginDevice');return {enabled:Boolean(device&&!device.paused),registered:Boolean(device),student_name:device?.student_name||'',guardian_name:device?.guardian_name||''};}
async function setState(message,kind='info'){await storage.set({remoteLoginStatus:message,remoteLoginStatusKind:kind});}
async function disable(){
  let device;
  await navigator.locks.request('sullivan-auth-state',async()=>{
    device=(await local.get('remoteLoginDevice')).remoteLoginDevice;if(!device)return;
    await local.set({remoteLoginDevice:{...device,paused:true}});await storage.set({remoteFence:crypto.randomUUID()});
    const {session}=await storage.get('session');
    if(session?.remote_device===device.device_id){await local.remove('rememberedAuth');await storage.remove('session');}
  });
  if(!device)return;
  try{await api('remote-login/disable',proof(device));}catch(error){if(error.status!==401)throw new Error('이 기기의 지원은 중지했습니다. 서버 해제를 마치려면 연결 후 같은 해제 버튼을 다시 누르세요.');}
  await navigator.locks.request('sullivan-auth-state',async()=>{if((await local.get('remoteLoginDevice')).remoteLoginDevice?.device_id===device.device_id)await local.remove('remoteLoginDevice');});
  await setState('이 기기의 보호자 로그인 지원을 해제했습니다. 다시 허용하려면 학생이 로그인하세요.');
}
async function install(device){
  await trusted;
  if(device?.client_id!==chrome.runtime.id||!device.device_id||!device.device_secret||!device.student_id)throw new Error('학생 기기 승인 정보를 확인하세요.');
  await navigator.locks.request('sullivan-auth-state',async()=>{
    const {session}=await storage.get('session');
    if(session?.user?.id!==device.student_id)throw new Error('학생 계정이 변경됐습니다. 현재 계정에서 다시 승인하세요.');
    await local.set({remoteLoginDevice:device});await storage.set({remoteFence:crypto.randomUUID()});
  });
  await setState(`${device.student_name} 학생의 이 기기에서 보호자 로그인 요청을 기다립니다.`);
}
async function revokeIssued(session){
  if(!session?.access_token||!session.family_id)return;
  // Discard only the unused session. The student's separately approved device
  // remains available for a later, fresh guardian request.
  await fetch(SERVER+'/extension/v1/student/session',{method:'DELETE',credentials:'omit',headers:{...headers(),Authorization:'Bearer '+session.access_token},signal:AbortSignal.timeout(10000)}).catch(()=>{});
}
let pendingPoll=null;
export function pollRemoteLogin(){
  if(!pendingPoll)pendingPoll=performPoll().finally(()=>{pendingPoll=null;});
  return pendingPoll;
}
async function performPoll(){
  await trusted;
  // Share the existing refresh lock: a browser restart may restore a saved
  // refresh credential while the guardian asks this same profile to sign in.
  return navigator.locks.request('sullivan-remote-login-poll',()=>navigator.locks.request('sullivan-refresh',async()=>{
    const snapshot=await navigator.locks.request('sullivan-auth-state',async()=>({...await storage.get(['session','remoteFence']),...await local.get(['remoteLoginDevice','rememberedAuth'])}));
    const device=snapshot.remoteLoginDevice;if(!device||device.paused)return;
    const session=snapshot.session;
    const other=Boolean(session&&session.user?.id!==device.student_id||!session&&snapshot.rememberedAuth&&snapshot.rememberedAuth.user_id!==device.student_id);
    const presence=other?'other_account':session?.user?.id===device.student_id&&session.expires_at>Date.now()/1000+10?'signed_in':'ready';
    let result;
    try{result=await api('remote-login/poll',{...proof(device),presence});}
    catch(error){
      await navigator.locks.request('sullivan-auth-state',async()=>{
        if((await local.get('remoteLoginDevice')).remoteLoginDevice?.device_id!==device.device_id)return;
        if(error.status===401){
          await local.remove('remoteLoginDevice');await storage.set({remoteFence:crypto.randomUUID()});
          const {session:active}=await storage.get('session');
          if(active?.remote_device===device.device_id){await local.remove('rememberedAuth');await storage.remove('session');}
        }
        await setState(error.message,'error');
      });return;
    }
    if(!result.session){
      await navigator.locks.request('sullivan-auth-state',async()=>{
        if((await local.get('remoteLoginDevice')).remoteLoginDevice?.device_id!==device.device_id)return;
        if(result.state==='other_account')await setState('이 기기에 다른 계정이 로그인되어 있어 보호자 요청을 실행하지 않았습니다.','blocked');
        else if(['error','blocked'].includes((await storage.get('remoteLoginStatusKind')).remoteLoginStatusKind))await setState('');
      });return;
    }
    let adopted=false;
    try{
      await navigator.locks.request('sullivan-auth-state',async()=>{
        const now={...await storage.get(['session','remoteFence']),...await local.get(['remoteLoginDevice','rememberedAuth'])};
        if(other||now.remoteFence!==snapshot.remoteFence||now.remoteLoginDevice?.device_id!==device.device_id||now.remoteLoginDevice?.paused||now.session?.token!==session?.token||now.session?.auth_epoch!==session?.auth_epoch||now.rememberedAuth?.refresh_token!==snapshot.rememberedAuth?.refresh_token)return;
        const granted=result.session;
        if(granted.user?.role!=='student'||granted.user?.id!==device.student_id)throw new Error('학생 계정이 일치하지 않아 원격 로그인을 중지했습니다.');
        await storage.set({session:{...granted,token:granted.access_token,auth_epoch:crypto.randomUUID(),remote_device:device.device_id}});
        await local.set({rememberedAuth:{refresh_token:granted.refresh_token,family_id:granted.family_id,user_id:device.student_id}});adopted=true;
      });
    }finally{if(!adopted)await revokeIssued(result.session);}
    if(!adopted)return;
    const stillCurrent=async()=>navigator.locks.request('sullivan-auth-state',async()=>{
      const current={...await storage.get(['session','remoteFence']),...await local.get('remoteLoginDevice')};
      return current.session?.family_id===result.session.family_id&&current.session?.user?.id===device.student_id&&current.remoteFence===snapshot.remoteFence&&current.remoteLoginDevice?.device_id===device.device_id&&!current.remoteLoginDevice?.paused;
    });
    if(!await stillCurrent()){await revokeIssued(result.session);return;}
    // Acknowledge only after the credential has reached this Chrome profile.
    await api('remote-login/poll',{...proof(device),presence:'signed_in'});
    if(!await stillCurrent()){await revokeIssued(result.session);return;}
    await setState('보호자 요청으로 학생 로그인을 완료했습니다.');
    const contexts=await chrome.runtime.getContexts({contextTypes:['TAB','SIDE_PANEL']});
    if(!contexts.some(context=>context.documentUrl?.startsWith(chrome.runtime.getURL('index.html'))))await chrome.tabs.create({url:chrome.runtime.getURL('index.html')});
  }));
}
export function initializeRemoteLoginWorker(){
  const run=()=>pollRemoteLogin().catch(error=>setState(error.message,'error'));
  const alarm=async()=>{if(!await chrome.alarms.get('student-remote-login'))chrome.alarms.create('student-remote-login',{periodInMinutes:1});};
  chrome.alarms.onAlarm.addListener(value=>{if(value.name==='student-remote-login')run();});
  chrome.runtime.onStartup.addListener(()=>{alarm();run();});chrome.runtime.onInstalled.addListener(()=>{alarm();run();});
  chrome.runtime.onMessage.addListener((message,sender,respond)=>{
    if(!message?.type?.startsWith('student-remote-')||sender.id!==chrome.runtime.id||!sender.url?.startsWith(chrome.runtime.getURL('index.html')))return false;
    const actions={'student-remote-state':state,'student-remote-install':()=>install(message.device),'student-remote-disable':disable,'student-remote-poll':run};
    const action=actions[message.type];if(!action)return false;
    Promise.resolve().then(action).then(result=>respond({ok:true,result}),error=>respond({ok:false,error:error.message}));return true;
  });
  trusted.then(alarm).then(run).catch(()=>{});
}
