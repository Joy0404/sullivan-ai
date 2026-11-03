const assert=require('node:assert/strict');
const {create}=require('../apps/web/space-gesture.js');
let now=0,serial=0,timers=new Map(),events=[];
const setTimer=(fn,ms)=>{const id=++serial;timers.set(id,{fn,t:now+ms});return id;};
const clearTimer=id=>timers.delete(id);
function advance(ms){const end=now+ms;for(;;){const next=[...timers].filter(([,r])=>r.t<=end).sort((a,b)=>a[1].t-b[1].t)[0];if(!next)break;now=next[1].t;timers.delete(next[0]);next[1].fn();}now=end;}
const g=create({setTimer,clearTimer,hold:()=>events.push('hold'),release:()=>events.push('release'),taps:n=>events.push(n),cancel:()=>events.push('cancel')});
function tap(){g.down();advance(40);g.up();advance(100);}
tap();assert.deepEqual(events,[]);advance(420);assert.deepEqual(events,[1]);events=[];
tap();tap();assert.deepEqual(events,[]);advance(420);assert.deepEqual(events,[2]);events=[];
tap();tap();tap();assert.deepEqual(events,[]);advance(420);assert.deepEqual(events,[3]);events=[];
g.down();g.down();advance(600);assert.deepEqual(events,['hold']);g.up();assert.deepEqual(events,['hold','release']);advance(800);assert.deepEqual(events,['hold','release']);events=[];
g.down();advance(100);g.cancel();advance(900);assert.deepEqual(events,['cancel']);
console.log('Space gesture: single/double/triple defer, hold/release, repeat and cancel PASS');
