import {controlVideo} from './video-control.js';
import {initializeRemoteLoginWorker} from './remote-login-worker.js';
initializeRemoteLoginWorker();
chrome.sidePanel.setPanelBehavior({openPanelOnActionClick: false}).catch(console.error);
chrome.action.onClicked.addListener(tab=>{
  // Open during the actual action gesture, then focus the student document.
  chrome.sidePanel.open({windowId:tab.windowId}).then(()=>chrome.runtime.sendMessage({type:'student-focus-panel'})).catch(console.error);
});
const storage = chrome.storage.session;
let queue = Promise.resolve();

async function release(lease) {
  if (lease?.tabId) await chrome.scripting.executeScript({target: lease.documentId ? {tabId: lease.tabId, documentIds: [lease.documentId]} : {tabId: lease.tabId},
    func: controlVideo, args: ['release', null, lease.frameUrl || lease.url]}).catch(() => {});
}
function samePage(actual,expected){
  const a=new URL(actual),b=new URL(expected);
  const id=url=>url.hostname==='youtu.be'?url.pathname.split('/')[1]:/(^|\.)(youtube\.com|youtube-nocookie\.com)$/.test(url.hostname)
    ?url.pathname==='/watch'?url.searchParams.get('v'):url.pathname.match(/^\/(?:embed|shorts|e)\/([^/]+)/)?.[1]:null;
  return id(b)?id(a)===id(b)&&a.protocol==='https:':a.href===b.href;
}
async function locate(lease){
  let results;
  try{results=await chrome.scripting.executeScript({target:{tabId:lease.tabId,allFrames:true},func:controlVideo,args:['probe',null,null]});}
  catch{results=await chrome.scripting.executeScript({target:{tabId:lease.tabId},func:controlVideo,args:['probe',null,null]});}
  const found=results.filter(row=>row.result?.found).sort((a,b)=>b.result.score-a.result.score)[0];
  if(found){
    if(found.result.drm)throw new Error('보호된 영상은 직접 제어할 수 없습니다. 사이트에서 재생하고 준비된 자료를 이용하세요.');
    lease.documentId=found.documentId;lease.frameId=found.frameId;lease.frameUrl=found.result.url;return;
  }
  const requested=[...new Set(results.flatMap(row=>row.result?.permissionOrigins||[]))].slice(0,8);
  const missing=[];
  for(const origin of requested){
    try{const url=new URL(origin);if(['http:','https:'].includes(url.protocol)&&!url.username&&!url.password&&!await chrome.permissions.contains({origins:[origin]}))missing.push(origin);}catch{}
  }
  throw Object.assign(new Error(missing.length?'영상 제공 사이트의 추가 연결 허용이 필요합니다.':'강의 플레이어를 찾지 못했습니다. 사이트에서 영상을 연 뒤 다시 연결하세요.'),{permissionOrigins:missing});
}
async function handle(message) {
  const {session, playbackLease} = await storage.get(['session', 'playbackLease']);
  if (!session || session.user?.role !== 'student') throw new Error('학생 계정으로 다시 로그인하세요.');
  if (typeof message.view !== 'string' || message.view.length > 80) throw new Error('잘못된 재생 요청입니다.');
  if (message.action === 'claim') {
    await release(playbackLease);
    if (playbackLease?.view !== message.view) chrome.runtime.sendMessage({type: 'student-lease-lost', view: playbackLease?.view}).catch(() => {});
    let tabId = null;
    if (message.url) {
      const url = new URL(message.url);
      if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password) throw new Error('지원하는 원본 주소가 필요합니다.');
      if (message.open) {
        const tab = await chrome.tabs.create({url: url.href}); tabId = tab.id;
      } else {
        const [tab] = await chrome.tabs.query({active: true, lastFocusedWindow: true});
        tabId = tab?.id;
      }
      if (!tabId) throw new Error('원본 강의 탭을 선택하고 다시 연결하세요.');
    }
    await storage.set({playbackLease: {view: message.view, tabId, url: message.url || null, fence: 0}});
    return {ok: true};
  }
  const lease = playbackLease;
  if (!lease || lease.view !== message.view) throw new Error('다른 학습 화면에서 재생을 사용 중입니다. 이 화면에서 다시 연결하세요.');
  if (!Number.isSafeInteger(message.fence) || message.fence < lease.fence) throw new Error('중지한 재생 요청입니다.');
  if (!['state', 'play', 'pause', 'seek', 'release', 'audio'].includes(message.action)) throw new Error('지원하지 않는 재생 조작입니다.');
  lease.fence = message.fence;
  await storage.set({playbackLease: lease});
  if (message.action === 'release') {
    await release(lease); await storage.remove('playbackLease'); return {ok: true};
  }
  if (!lease.tabId) return {ok: true};
  const tab=await chrome.tabs.get(lease.tabId);
  if(!samePage(tab.url==='about:blank'?tab.pendingUrl||tab.url:tab.url,lease.url))throw new Error('연결한 강의 주소가 변경됐습니다. 강의를 다시 연결하세요.');
  if(!lease.documentId){await locate(lease);await storage.set({playbackLease:lease});}
  const target = lease.documentId ? {tabId: lease.tabId, documentIds: [lease.documentId]} : {tabId: lease.tabId};
  const [result] = await chrome.scripting.executeScript({target, func: controlVideo,
    args: [message.action, message.value ?? null, lease.frameUrl || lease.url]});
  if (result?.result?.error) throw new Error(result.result.error);
  if (!result?.result || !Number.isFinite(result.result.positionMs) || typeof result.result.paused !== 'boolean') throw new Error('플레이어의 재생 상태를 확인하지 못했습니다. 강의 탭을 확인하고 다시 연결하세요.');
  if (lease.documentId && lease.documentId !== result.documentId) throw new Error('강의 페이지가 새로 열렸습니다. 다시 연결하세요.');
  lease.documentId = result.documentId;
  await storage.set({playbackLease: lease});
  return result.result;
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  if (message?.type !== 'student-media' || sender.id !== chrome.runtime.id || !sender.url?.startsWith(chrome.runtime.getURL(''))) return false;
  queue = queue.catch(() => {}).then(() => handle(message));
  queue.then(result => respond({ok: true, result}), error => respond({ok: false, error: error.message,permissionOrigins:error.permissionOrigins||[]}));
  return true;
});
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'session' && changes.session && !changes.session.newValue) {
    queue = queue.catch(() => {}).then(async () => {
      const {playbackLease} = await storage.get('playbackLease');
      await release(playbackLease); await storage.remove('playbackLease');
    });
  }
});
chrome.commands.onCommand.addListener(async command => {
  if (command === 'stop-learning') {
    queue = queue.catch(() => {}).then(async () => {
      const {playbackLease} = await storage.get('playbackLease');
      if (playbackLease) { playbackLease.fence++; await storage.set({playbackLease}); await release(playbackLease); }
      chrome.runtime.sendMessage({type: 'student-stop', fence: playbackLease?.fence}).catch(() => {});
    });
  }
});
