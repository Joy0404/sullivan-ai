import {ROLE, SERVER, VERSION} from './config.js';
const storage = chrome.storage.session;
await storage.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'});
await chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'});
let generation = 0;
chrome.storage.onChanged.addListener((changes,area)=>{
  if(area==='session' && changes.session && !changes.session.newValue){generation++;window.dispatchEvent(new Event('sullivan-signed-out'));}
});
const headers = ()=>({'X-Sullivan-Client':ROLE,'X-Sullivan-Version':VERSION,'X-Local-Request':'1'});
const base64url = bytes => btoa(String.fromCharCode(...bytes)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');

export async function forgetSession(){
  await chrome.storage.local.remove('rememberedAuth');
  await storage.remove('session');
}
async function adopt(data,remember=false,rotating=false){
  const session=data.access_token?{...data,token:data.access_token}:data;
  if(session.user?.role!==ROLE || typeof session.token!=='string')throw new Error('로그인 정보를 확인하지 못했습니다.');
  if(!rotating)generation++;
  await storage.set({session});
  if(remember && session.refresh_token)await chrome.storage.local.set({rememberedAuth:{refresh_token:session.refresh_token,family_id:session.family_id}});
  else await chrome.storage.local.remove('rememberedAuth');
  return session;
}
async function tokenRequest(payload){
  let response;
  try{
    response=await fetch(SERVER+`/extension/v1/${ROLE}/token`,{method:'POST',credentials:'omit',cache:'no-store',
      headers:{...headers(),'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({
        ...payload,client_id:chrome.runtime.id,redirect_uri:chrome.identity.getRedirectURL('oauth')}),signal:AbortSignal.timeout(20000)});
  }catch{throw new Error('인증 서버에 연결하지 못했습니다. 연결 후 다시 시도하세요.');}
  const data=await response.json().catch(()=>({}));
  if(!response.ok){const error=new Error(typeof data.detail==='string'?data.detail:'다시 로그인해 주세요.');error.status=response.status;throw error;}
  return data;
}
async function refreshAccess(staleToken=null){
  return navigator.locks.request('sullivan-refresh',async()=>{
    const {session}=await storage.get('session');
    const {rememberedAuth}=await chrome.storage.local.get('rememberedAuth');
    if(session?.token && session.token!==staleToken && session.expires_at>Date.now()/1000+20)return session;
    const credential=session?.refresh_token||rememberedAuth?.refresh_token;
    if(!credential)return session||null;
    try{
      const data=await tokenRequest({grant_type:'refresh_token',refresh_token:credential});
      return await adopt(data,Boolean(rememberedAuth),true);
    }catch(error){if(error.status===401)await forgetSession();throw error;}
  });
}
export async function request(path,{method='GET',body,anonymous=false,timeout=20000}={}){
  if(!/^\/(local\/|extension\/v1\/)/.test(path)||path.includes('..')||path.includes('?')||path.includes('#'))throw new Error('지원하지 않는 요청입니다.');
  let {session}=await storage.get('session');
  if(!anonymous && session?.refresh_token && session.expires_at<=Date.now()/1000+20)session=await refreshAccess(session.token);
  const ticket=generation, multipart=body instanceof FormData;
  async function send(token){
    const head=headers();if(!multipart)head['Content-Type']='application/json';
    if(!anonymous){if(!token)throw new Error('먼저 로그인해 주세요.');head.Authorization=`Bearer ${token}`;}
    try{return await fetch(SERVER+path,{method,headers:head,credentials:'omit',cache:'no-store',signal:AbortSignal.timeout(timeout),body:body===undefined?undefined:multipart?body:JSON.stringify(body)});}
    catch{throw new Error('서버에 연결하지 못했습니다. 서버 실행과 인터넷 연결을 확인해 주세요.');}
  }
  let response=await send(session?.token);
  if(response.status===401 && !anonymous && session?.refresh_token){
    session=await refreshAccess(session.token);response=await send(session?.token);
  }
  const data=await response.json().catch(()=>({}));
  if(ticket!==generation)throw new Error('로그인 상태가 변경되었습니다. 다시 시도해 주세요.');
  if(!response.ok){
    if(response.status===401&&!anonymous){const latest=await storage.get('session');if(latest.session?.token===session?.token)await forgetSession();}
    const error=new Error(typeof data.detail==='string'?data.detail:'요청 내용을 확인해 주세요.');error.status=response.status;throw error;
  }
  return data;
}
export async function signIn(credentials,register=false){
  const data=await request(`/extension/v1/${ROLE}/${register?'register':'session'}`,{method:'POST',body:{...credentials,role:ROLE},anonymous:true});
  return (await adopt(data)).user;
}
export async function browserSignIn(remember=false){
  const verifier=base64url(crypto.getRandomValues(new Uint8Array(32)));
  const challenge=base64url(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(verifier))));
  const state=base64url(crypto.getRandomValues(new Uint8Array(32)));
  const redirect=chrome.identity.getRedirectURL('oauth');
  const url=new URL(SERVER+`/extension/auth/${ROLE}/authorize`);
  url.search=new URLSearchParams({client_id:chrome.runtime.id,redirect_uri:redirect,code_challenge:challenge,code_challenge_method:'S256',state,response_type:'code'});
  let callback;
  try{callback=await chrome.identity.launchWebAuthFlow({url:url.href,interactive:true});}
  catch{throw new Error('브라우저 로그인을 완료하지 못했습니다. 창을 다시 열어 로그인하세요.');}
  const returned=new URL(callback), expected=new URL(redirect);
  if(returned.origin!==expected.origin||returned.pathname!==expected.pathname||returned.searchParams.get('state')!==state||!returned.searchParams.get('code'))throw new Error('로그인 반환 정보를 확인하지 못했습니다.');
  const data=await tokenRequest({grant_type:'authorization_code',code:returned.searchParams.get('code'),code_verifier:verifier});
  return (await adopt(data,remember)).user;
}
export async function signOut(){await request(`/extension/v1/${ROLE}/session`,{method:'DELETE'});await forgetSession();}
export async function restore(){
  let {session}=await storage.get('session');
  if(!session){const {rememberedAuth}=await chrome.storage.local.get('rememberedAuth');if(rememberedAuth)session=await refreshAccess();}
  if(!session)return null;
  return request(`/extension/v1/${ROLE}/session`);
}
export {ROLE};
