import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {webcrypto} from 'node:crypto';
const code=readFileSync(new URL('../apps/extensions/student/remote-login-worker.js',import.meta.url),'utf8')
  .replace(/^import .*?;\n/,"const SERVER='https://fixture.invalid',VERSION='test';\n")
  .replaceAll('export async function','async function').replaceAll('export function','function');
const device={device_id:'d'.repeat(32),device_secret:'s'.repeat(43),client_id:'a'.repeat(32),student_id:'A',student_name:'학생',guardian_name:'보호자'};
const grant=()=>({access_token:'issued-A',refresh_token:'renew-A',family_id:'family-A',expires_at:Date.now()/1000+900,user:{id:'A',role:'student'}});
const response=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
const deferred=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {resolve,promise};};
async function harness(fetcher,initial={}){
  const areas={local:{remoteLoginDevice:structuredClone(device)},session:{...initial}},locks=new Map(),calls=[],opened=[];
  const area=name=>({async setAccessLevel(){},async get(keys){return Object.fromEntries((Array.isArray(keys)?keys:[keys]).map(key=>[key,structuredClone(areas[name][key])]))},
    async set(values){Object.assign(areas[name],structuredClone(values));},async remove(keys){for(const key of Array.isArray(keys)?keys:[keys])delete areas[name][key];}});
  const chrome={storage:{local:area('local'),session:area('session')},runtime:{id:'a'.repeat(32),getURL:path=>'chrome-extension://fixture/'+path,getContexts:async()=>[]},tabs:{create:async options=>opened.push(options)}};
  const context={chrome,crypto:webcrypto,AbortSignal,fetch:async(url,options)=>{calls.push({url,options,body:JSON.parse(options.body||'{}')});return fetcher(url,options,calls);},
    navigator:{locks:{request(name,fn){const next=(locks.get(name)||Promise.resolve()).catch(()=>{}).then(fn);locks.set(name,next);return next;}}}};
  const api=await vm.runInNewContext(`(async()=>{${code};return {pollRemoteLogin,install,disable};})()`,context);
  return {api,chrome,areas,calls,opened,withRefreshLock:fn=>context.navigator.locks.request('sullivan-refresh',fn)};
}
let failed=0;
async function check(name,run){try{await run();console.log(name,'PASS');}catch(error){failed++;console.error(name,'FAIL',error);}}
await check('remote login adopts matching student and acknowledges after storage',async()=>{
  const h=await harness(async(url,options,calls)=>{
    if(calls.length===1)return response({state:'issued',session:grant()});
    assert.equal(h.areas.session.session.user.id,'A');return response({state:'waiting'});
  });
  await h.api.pollRemoteLogin();assert.equal(h.areas.session.session.remote_device,device.device_id);
  assert.equal(h.areas.local.rememberedAuth.user_id,'A');assert.equal(h.opened.length,1);
  assert.deepEqual(h.calls.map(call=>call.body.presence),['ready','signed_in']);
});
await check('late remote grant cannot replace a newly signed-in account',async()=>{
  const gate=deferred(),started=deferred();
  const h=await harness(async(url)=>{if(url.endsWith('/poll')){started.resolve();return gate.promise;}return response({ok:true});});
  const work=h.api.pollRemoteLogin();await started.promise;
  h.areas.session.session={token:'B',auth_epoch:'B',user:{id:'B',role:'student'}};
  gate.resolve(response({state:'issued',session:grant()}));await work;
  assert.equal(h.areas.session.session.user.id,'B');assert.equal(h.opened.length,0);
  assert.equal(h.calls.filter(call=>call.options.method==='DELETE').length,1);
});
await check('disabling device fences an in-flight grant',async()=>{
  const gate=deferred(),started=deferred();
  const h=await harness(async url=>{if(url.endsWith('/poll')){started.resolve();return gate.promise;}return response({ok:true});});
  const work=h.api.pollRemoteLogin();await started.promise;await h.api.disable();
  gate.resolve(response({state:'issued',session:grant()}));await work;
  assert.equal(h.areas.session.session,undefined);assert.equal(h.areas.local.remoteLoginDevice,undefined);assert.equal(h.opened.length,0);
});
await check('logout fence prevents late remote sign-in resurrection',async()=>{
  const gate=deferred(),started=deferred();
  const h=await harness(async url=>{if(url.endsWith('/poll')){started.resolve();return gate.promise;}return response({ok:true});});
  const work=h.api.pollRemoteLogin();await started.promise;h.areas.session.remoteFence='logged-out';
  gate.resolve(response({state:'issued',session:grant()}));await work;
  assert.equal(h.areas.session.session,undefined);assert.equal(h.opened.length,0);
});
await check('another active or remembered account blocks remote login',async()=>{
  for(const remembered of [false,true]){
    const h=await harness(async(url,options)=>{assert.equal(JSON.parse(options.body).presence,'other_account');return response({state:'other_account'});});
    if(remembered)h.areas.local.rememberedAuth={refresh_token:'B',user_id:'B'};
    else h.areas.session.session={token:'B',user:{id:'B',role:'student'}};
    await h.api.pollRemoteLogin();assert.equal(h.opened.length,0);assert.equal(h.areas.session.session?.user.id,remembered?undefined:'B');
  }
});
await check('revoked device clears its session but preserves another account',async()=>{
  for(const id of ['A','B']){
    const h=await harness(async()=>response({detail:'revoked'},401),{session:{token:id,user:{id,role:'student'},remote_device:id==='A'?device.device_id:undefined}});
    await h.api.pollRemoteLogin();assert.equal(h.areas.local.remoteLoginDevice,undefined);
    assert.equal(h.areas.session.session?.user.id,id==='A'?undefined:'B');
  }
});
await check('wrong-account issued token fails closed',async()=>{
  const h=await harness(async url=>url.endsWith('/poll')?response({state:'issued',session:{...grant(),user:{id:'B',role:'student'}}}):response({ok:true}));
  await assert.rejects(h.api.pollRemoteLogin(),/일치하지/);assert.equal(h.areas.session.session,undefined);assert.equal(h.opened.length,0);
});
await check('paused or absent enrollment makes no request',async()=>{
  const h=await harness(async()=>{throw new Error('Unexpected network request');});
  h.areas.local.remoteLoginDevice.paused=true;await h.api.pollRemoteLogin();delete h.areas.local.remoteLoginDevice;await h.api.pollRemoteLogin();assert.equal(h.calls.length,0);
});
await check('account switch during acknowledgment cannot open student view',async()=>{
  const gate=deferred(),started=deferred();
  const h=await harness(async(url,options,calls)=>{if(calls.length===1)return response({state:'issued',session:grant()});if(url.endsWith('/poll')){started.resolve();return gate.promise;}return response({ok:true});});
  const work=h.api.pollRemoteLogin();await started.promise;
  h.areas.session.session={token:'B',auth_epoch:'B',user:{id:'B',role:'student'}};
  gate.resolve(response({state:'waiting'}));await work;
  assert.equal(h.areas.session.session.user.id,'B');assert.equal(h.opened.length,0);
});
await check('concurrent UI and alarm polls share one pending request',async()=>{
  const gate=deferred(),started=deferred();let fetches=0;
  const h=await harness(async()=>{fetches++;started.resolve();return gate.promise;});
  const one=h.api.pollRemoteLogin();await started.promise;const two=h.api.pollRemoteLogin();
  gate.resolve(response({state:'waiting'}));await Promise.all([one,two]);assert.equal(fetches,1);
});
await check('successful reconnect clears obsolete transport error',async()=>{
  let failedOnce=false;
  const h=await harness(async()=>{if(!failedOnce){failedOnce=true;return response({detail:'network fixture'},503);}return response({state:'waiting'});});
  await h.api.pollRemoteLogin();assert.equal(h.areas.session.remoteLoginStatusKind,'error');
  await h.api.pollRemoteLogin();assert.equal(h.areas.session.remoteLoginStatus,'');assert.equal(h.areas.session.remoteLoginStatusKind,'info');
  assert.equal(h.areas.local.remoteLoginDevice.device_id,device.device_id);
});
await check('saved-login restoration completes before remote session decision',async()=>{
  const gate=deferred(),started=deferred();
  const h=await harness(async(url,options)=>{assert.equal(JSON.parse(options.body).presence,'signed_in');return response({state:'already_signed_in'});});
  const restoring=h.withRefreshLock(async()=>{started.resolve();await gate.promise;h.areas.session.session={token:'restored-A',expires_at:Date.now()/1000+900,user:{id:'A',role:'student'}};});
  await started.promise;const remote=h.api.pollRemoteLogin();
  for(let i=0;i<15;i++)await Promise.resolve();assert.equal(h.calls.length,0);
  gate.resolve();await Promise.all([restoring,remote]);
  assert.equal(h.areas.session.session.token,'restored-A');assert.equal(h.opened.length,0);
});
if(failed)process.exitCode=1;
