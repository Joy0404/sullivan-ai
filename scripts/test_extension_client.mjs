import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';

const code = readFileSync(new URL('../apps/extensions/shared/client.js',import.meta.url),'utf8')
  .replace(/^import .*?;\n/,"const ROLE='student',SERVER='https://test.invalid',VERSION='test';\n")
  .replaceAll('export async function','async function').replace('export {ROLE};','');
const fresh = (id='A') => ({token:`token-${id}`,refresh_token:`refresh-${id}`,expires_at:Date.now()/1000+1000,user:{id,role:'student'}});
async function harness(fetcher) {
  let session={...fresh(),expires_at:0},rememberedAuth,remoteFence,notify=true;const listeners=[],locks=new Map();
  const area=kind=>({async setAccessLevel(){},async get(key){return {[key]:structuredClone(kind==='session'?(key==='remoteFence'?remoteFence:session):rememberedAuth)};},
    async set(data){if(kind==='session'){if('remoteFence' in data)remoteFence=data.remoteFence;if(!('session' in data))return;const old=session;session=structuredClone(data.session);if(notify)listeners.forEach(fn=>fn({session:{oldValue:old,newValue:session}},'session'));}else if('rememberedAuth' in data)rememberedAuth=data.rememberedAuth;},
    async remove(){if(kind==='session'){const old=session;session=undefined;listeners.forEach(fn=>fn({session:{oldValue:old}},'session'));}else rememberedAuth=undefined;}});
  const chrome={runtime:{id:'fixture'},identity:{getRedirectURL(){return 'https://fixture.chromiumapp.org/oauth';}},storage:{session:area('session'),local:area('local'),onChanged:{addListener(fn){listeners.push(fn);}}}};
  const context={chrome,window:new EventTarget(),Event,FormData,AbortSignal,URL,URLSearchParams,Uint8Array,crypto:webcrypto,btoa,fetch:fetcher,
    navigator:{locks:{request(name,fn){const next=(locks.get(name)||Promise.resolve()).catch(()=>{}).then(fn);locks.set(name,next);return next;}}}};
  const api=await vm.runInNewContext(`(async()=>{${code};return {request,forgetSession,restore,signOut};})()`,context);
  return {api,chrome,get session(){return session;},get remoteFence(){return remoteFence;},async switchTo(next,deliver=true){notify=deliver;await chrome.storage.session.set({session:next});notify=true;}};
}
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve};};
const response=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
const settle=async()=>{for(let i=0;i<40;i++)await Promise.resolve();};
let failed=0;
async function check(name,run){try{await run();console.log(name,'PASS');}catch(error){failed++;console.error(name,'FAIL',error.message);}}

await check('refresh cannot revive logged-out session',async()=>{
  const gate=deferred(),started=deferred();const h=await harness(async url=>{if(url.endsWith('/token')){started.resolve();return gate.promise;}return response({});});
  const work=h.api.request('/local/me').catch(e=>e);await started.promise;await h.api.forgetSession();gate.resolve(response(fresh()));await work;
  assert.equal(h.session,undefined);
});
await check('failed old refresh cannot clear another account',async()=>{
  const gate=deferred(),started=deferred();const h=await harness(async()=>{started.resolve();return gate.promise;});
  const work=h.api.request('/local/me').catch(e=>e);await started.promise;await h.switchTo(fresh('B'));gate.resolve(response({detail:'expired'},401));await work;
  assert.equal(h.session?.user.id,'B');
});
await check('old 401 cannot replay write with new account token',async()=>{
  const gate=deferred(),started=deferred(),tokens=[];
  const h=await harness(async(url,options)=>{tokens.push(options.headers.Authorization);if(tokens.length===1){started.resolve();return gate.promise;}return response({});});
  await h.switchTo(fresh());
  const work=h.api.request('/local/lectures/shared/progress',{method:'PUT',body:{note:'A private note'}}).catch(e=>e);
  await started.promise;await h.switchTo(fresh('B'));gate.resolve(response({},401));const result=await work;
  assert.deepEqual(tokens,['Bearer token-A']);assert.equal(result.cancelled,true);
});
await check('concurrent expiry rotates only once',async()=>{
  let rotations=0;const h=await harness(async url=>url.endsWith('/token')?(rotations++,response({...fresh(),token:'rotated-A'})):response({ok:true}));
  await Promise.all([h.api.request('/local/me'),h.api.request('/local/lectures')]);await settle();assert.equal(rotations,1);
});
await check('delayed storage event cannot replay an old write',async()=>{
  const gate=deferred(),started=deferred(),tokens=[];
  const h=await harness(async(url,options)=>{tokens.push(options.headers.Authorization);if(tokens.length===1){started.resolve();return gate.promise;}return response({});});
  await h.switchTo(fresh());
  const work=h.api.request('/local/lectures/shared/progress',{method:'PUT',body:{note:'A only'}}).catch(e=>e);
  await started.promise;await h.switchTo(fresh('B'),false);gate.resolve(response({},401));const result=await work;
  assert.deepEqual(tokens,['Bearer token-A']);assert.equal(result.cancelled,true);
});
await check('delayed storage event cannot return another account response',async()=>{
  const gate=deferred(),started=deferred();const h=await harness(async()=>{started.resolve();return gate.promise;});
  await h.switchTo(fresh());const work=h.api.request('/local/me').catch(e=>e);
  await started.promise;await h.switchTo(fresh('B'),false);gate.resolve(response({private:'A only'}));
  assert.equal((await work).cancelled,true);
});
await check('new request from stale view cannot borrow a silently changed account',async()=>{
  let calls=0;const h=await harness(async()=>{calls++;return response({});});
  await h.switchTo(fresh('B'),false);
  const result=await h.api.request('/local/lectures/shared/progress',{method:'PUT',body:{note:'Old view A'}}).catch(e=>e);
  assert.equal(calls,0);assert.equal(result.cancelled,true);
});
await check('refresh preserves remote device association',async()=>{
  const h=await harness(async url=>url.endsWith('/token')?response(fresh()):response({ok:true}));
  await h.switchTo({...fresh(),expires_at:0,remote_device:'approved-device'});
  await h.api.request('/local/me');assert.equal(h.session.remote_device,'approved-device');
});
await check('logout fences remote login before awaiting server response',async()=>{
  const gate=deferred(),started=deferred();const h=await harness(async()=>{started.resolve();return gate.promise;});
  await h.switchTo(fresh());const work=h.api.signOut();await started.promise;
  assert.equal(typeof h.remoteFence,'string');assert.equal(h.session.user.id,'A');
  gate.resolve(response({ok:true}));await work;assert.equal(h.session,undefined);
});
if(failed)process.exitCode=1;
