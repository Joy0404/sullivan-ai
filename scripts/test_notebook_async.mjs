// Exercise real notebook operations with controlled storage/network promises.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
globalThis.crypto ??= webcrypto;
const raw = readFileSync(new URL('../apps/extensions/student/notes.js', import.meta.url), 'utf8').replace(/^import .*;$/mg, '');
const nativeTimers = {set: globalThis.setTimeout, clear: globalThis.clearTimeout};
const deferred = () => {let resolve; const promise = new Promise(done => {resolve = done;}); return {promise, resolve};};
const settle = async () => {for (let i=0; i<20; i++) await Promise.resolve();};
let instance=0;

async function harness() {
  const elements=new Map(), storage={}, server=new Map(), requests=[], timers=new Map(), errors=[];
  let selection={account:'student-a', lecture:'lesson-a'}, timerId=0;
  const state={persistGate:null, removalGate:null, deleteGate:null, sourceGate:null};
  const element=id => {
    if(!elements.has(id)) elements.set(id, {id,value:'',textContent:'',hidden:false,disabled:false,open:false,listeners:{},
      addEventListener(type, fn){this.listeners[type]=fn;}, replaceChildren(...children){this.children=children;},
      focus(){}, setSelectionRange(){}, close(){this.open=false;}, showModal(){this.open=true;}});
    return elements.get(id);
  };
  globalThis.setTimeout=(fn, delay)=>{timers.set(++timerId,{fn,delay});return timerId;};
  globalThis.clearTimeout=id=>timers.delete(id);
  globalThis.chrome={storage:{local:{
    async set(values){const gate=state.persistGate;state.persistGate=null;if(gate)await gate.promise;Object.assign(storage,structuredClone(values));},
    async get(){return structuredClone(storage);},
    async remove(key){const gate=state.removalGate;state.removalGate=null;if(gate)await gate.promise;delete storage[key];}
  }}};
  async function request(path, options={}) {
    requests.push({path,...structuredClone(options)});
    const id=path.split('/').at(-1);
    if(options.method==='PUT') {
      const old=server.get(id), body=options.body;
      if(old && old.body===body.body && old.started_ms===body.started_ms && JSON.stringify(old.source)===JSON.stringify(body.source))return structuredClone(old);
      if((old?.revision||0)!==body.revision)throw Object.assign(new Error('revision conflict'),{status:409});
      const result={...body,id,revision:(old?.revision||0)+1};server.set(id,result);return structuredClone(result);
    }
    if(options.method==='DELETE') {server.delete(id);if(state.deleteGate)await state.deleteGate.promise;return {ok:true};}
    if(path.endsWith('/note-sources')) {
      if(state.sourceGate)await state.sourceGate.promise;
      return [{kind:'sentence',id:'sentence-one',text:'검증된 원문',fingerprint:'a'.repeat(64),label:'1문단'}];
    }
    return [...server.values()].map(value=>structuredClone(value));
  }
  globalThis.__notebookTest={request,$:element,node:(tag,text,props={})=>({tag,text,...props}),task:(_button,action)=>action(),status(){}};
  const source=`const {request,$,node,task,status}=globalThis.__notebookTest;\n${raw}\n// instance ${++instance}`;
  const {createNotebook}=await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
  const notebook=createNotebook({context:()=>selection,position:()=>1000,pause:async()=>{},reportError:error=>errors.push(error)});
  const click=id=>element(id).listeners.click();
  const type=text=>{element('note-body').value=text;element('note-body').listeners.input();};
  await notebook.load();
  return {element,storage,server,requests,timers,errors,state,notebook,click,type,
    switchAccount:async()=>{selection={account:'student-b',lecture:'lesson-b'};notebook.reset();server.clear();await notebook.load();}};
}

try {
  for(const boundary of ['delete-response','storage-removal']) {
    const h=await harness();await h.click('new-note');h.type('삭제할 예전 필기');await h.click('save-note');
    const gate=deferred();h.state[boundary==='delete-response'?'deleteGate':'removalGate']=gate;
    const deletion=h.click('confirm-note-delete');await settle();
    if(boundary==='storage-removal')await h.switchAccount();
    await h.click('new-note');h.type('새 편집기의 학생 본문');
    gate.resolve();await deletion;
    assert.equal(h.element('note-editor').hidden,false,boundary);
    assert.equal(h.element('note-body').value,'새 편집기의 학생 본문',boundary);
    await h.click('save-note');assert.ok([...h.server.values()].some(row=>row.body==='새 편집기의 학생 본문'));
  }
  for(const changed of [false,true]) {
    const h=await harness();await h.click('new-note');h.type('처음 입력');await settle();
    const gate=deferred();h.state.persistGate=gate;
    const auto=[...h.timers.values()].find(timer=>timer.delay===900).fn();await settle();
    if(changed)h.type('저장 대기 중 새로 입력');
    const manual=h.click('save-note');await settle();gate.resolve();await Promise.all([auto,manual]);
    assert.equal(h.errors.length,0);assert.equal(h.element('copy-note-draft').hidden,true);
    const puts=h.requests.filter(request=>request.method==='PUT');
    assert.equal(puts.length,changed?2:1);
    assert.deepEqual(puts.map(request=>request.body.revision),changed?[0,1]:[0]);
    assert.equal([...h.server.values()][0].body,changed?'저장 대기 중 새로 입력':'처음 입력');
  }
  {
    const h=await harness();await h.click('new-note');const gate=deferred();h.state.sourceGate=gate;
    const reading=h.notebook.startAtSource('sentence-one').catch(error=>error);await settle();
    await h.click('new-note');h.type('새로 작성 중인 학생 본문');gate.resolve();
    assert.equal((await reading).cancelled,true);
    assert.equal(h.element('note-body').value,'새로 작성 중인 학생 본문');
    assert.equal(h.element('note-editor').hidden,false);
  }
  for(const switchAccount of [false,true]) {
    const h=await harness();await h.click('new-note');h.type('서버로 보낼 본문');await settle();
    const gate=deferred();h.state.removalGate=gate;
    const saving=h.click('save-note');await settle();
    h.type('정리 응답 대기 중 입력한 새 초안');await settle();
    if(switchAccount)await h.switchAccount();
    gate.resolve();await saving;
    assert.ok(Object.entries(h.storage).some(([key,value])=>key.startsWith('note-draft:student-a:lesson-a:') && value.body==='정리 응답 대기 중 입력한 새 초안' && value.dirty));
    if(!switchAccount){
      assert.equal(h.element('note-body').value,'정리 응답 대기 중 입력한 새 초안');
      assert.ok(h.element('notes-list').children.some(option=>option.text.includes('새 초안')));
    }
  }
  console.log('Notebook async: late deletion, serialized saves, source fences and newer draft cleanup PASS');
} finally {
  globalThis.setTimeout=nativeTimers.set;globalThis.clearTimeout=nativeTimers.clear;
}
