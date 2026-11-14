export class CancelledMediaOperation extends Error {
  constructor(){super('이전 학습 화면의 요청을 취소했습니다.');this.cancelled=true;}
}

export class StudentMedia {
  constructor(video) { this.video = video; this.view = crypto.randomUUID(); this.fence = 0; this.kind = null; this.verified = false; this.url = null; this.generation = 0; this.ready = false;this.playRevision=0;this.wantsPlayback=false;this.pendingClaims=new Set(); }
  scope(fence=this.fence){return {view:this.view,generation:this.generation,fence};}
  assertCurrent(scope,{allowPause=false}={}){if(scope.view!==this.view||scope.generation!==this.generation||(!allowPause&&scope.fence!==this.fence))throw new CancelledMediaOperation();}
  cancelPendingPlay(){this.playRevision++;}
  async send(action, value, fence = this.fence, options={}) {
    const scope=this.scope(fence);
    const response = await chrome.runtime.sendMessage({type: 'student-media', view: scope.view, action, value, fence});
    this.assertCurrent(scope,options);
    if (!response?.ok) throw Object.assign(new Error(response?.error || '강의 연결을 확인하세요.'),{permissionOrigins:response?.permissionOrigins||[]});
    return response.result;
  }
  async connect(url, open = false) {
    const scope=this.scope();
    await this.claim(url, open);
    this.assertCurrent(scope);
    this.kind = 'remote'; this.verified = true;
    // A newly opened site may need time to mount its video. No playback starts here.
    let error;
    for (let attempt = 0; attempt < 20; attempt++) {
      this.assertCurrent(scope);
      try { await this.send('pause');this.assertCurrent(scope);return; } catch (problem) { if(problem.cancelled||problem.permissionOrigins?.length)throw problem;error = problem; await new Promise(resolve => setTimeout(resolve, 500)); }
    }
    this.kind = null; this.verified = false; throw error;
  }
  async claim(url = null, open = false) {
    const scope=this.scope();this.pendingClaims.add(scope);
    try{
      const response = await chrome.runtime.sendMessage({type: 'student-media', view: scope.view, action: 'claim', url, open});
      this.assertCurrent(scope);
      if (!response?.ok) throw new Error(response?.error || '학습 화면을 연결할 수 없습니다.');
    }finally{this.pendingClaims.delete(scope);}
  }
  async claimForSpeech() {
    if (!this.kind) await this.claim();
    else await this.send('state');
  }
  async local(file, identity) {
    const scope=this.scope();
    if (!file || !Number.isFinite(file.size) || file.size<=0) throw new Error('내용이 있는 영상 파일을 선택하세요.');
    if (identity?.sha256 && file.size > 100000000) throw new Error('분석한 원본과 크기가 다릅니다. 같은 파일을 선택하세요.');
    if (identity?.sha256) {
      const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', await file.arrayBuffer()))].map(n => n.toString(16).padStart(2, '0')).join('');
      if (hash !== identity.sha256 || file.size !== identity.size_bytes) throw new Error('분석한 원본과 다른 파일입니다. 자동 해설을 연결하지 않았습니다.');
    }
    this.assertCurrent(scope);
    await this.claim();
    this.assertCurrent(scope);
    this.kind = 'local'; this.verified = Boolean(identity?.sha256);
    this.url = URL.createObjectURL(file);
    try { await new Promise((resolve, reject) => {
      const timer = setTimeout(() => { cleanup(); reject(new Error('영상 정보를 읽지 못했습니다. 형식과 파일을 확인하세요.')); }, 10000);
      const loaded = () => { cleanup(); resolve(); };
      const failed = () => { cleanup(); reject(new Error('Chrome이 이 파일의 영상 형식 또는 코덱을 재생하지 못했습니다. 재생 가능한 MP4(H.264/AAC)·WebM 파일을 선택하세요. 준비된 자료는 계속 이용할 수 있습니다.')); };
      const cancelled = () => { cleanup(); reject(new CancelledMediaOperation()); };
      const cleanup = () => { clearTimeout(timer);if(this.pendingLocal===cancelled)this.pendingLocal=null; this.video.removeEventListener('loadedmetadata', loaded); this.video.removeEventListener('error', failed); };
      this.pendingLocal=cancelled;
      this.video.addEventListener('loadedmetadata', loaded); this.video.addEventListener('error', failed);
      this.video.src=this.url;this.video.hidden=false;
    }); } catch(error){if(scope.view===this.view&&scope.generation===this.generation)this.reset();throw error;}
    this.assertCurrent(scope);
  }
  async state({allowPause=false}={}) {
    if (!this.kind) return {positionMs: 0, paused: true, verified: false};
    if (this.kind === 'remote') return this.send('state',undefined,this.fence,{allowPause});
    const snapshot = {positionMs: Math.round(this.video.currentTime * 1000), paused: this.video.paused,
      durationMs: Number.isFinite(this.video.duration) ? Math.round(this.video.duration * 1000) : null, ended: this.video.ended, ad: false, verified: this.verified};
    await this.send('state',undefined,this.fence,{allowPause}); // Past-state snapshots may survive a pause, never a changed view.
    return snapshot;
  }
  async play(fence = this.fence) {
    if (!this.kind || !this.ready) throw new Error('원본 강의 또는 로컬 영상을 먼저 연결하세요.');
    const scope=this.scope(fence),revision=++this.playRevision;
    this.assertCurrent(scope);this.wantsPlayback=true;
    await this.send('play', null, fence);
    this.assertCurrent(scope);
    if(revision!==this.playRevision)throw new CancelledMediaOperation();
    if (this.kind === 'local'){
      try{await this.video.play();}catch(error){this.assertCurrent(scope);if(revision!==this.playRevision)throw new CancelledMediaOperation();throw error;}
      this.assertCurrent(scope);if(revision!==this.playRevision)throw new CancelledMediaOperation();
    }
  }
  async pause(invalidate = true) {
    this.cancelPendingPlay();
    if (invalidate){this.fence++;this.wantsPlayback=false;}
    this.video.pause();
    if (this.kind||[...this.pendingClaims].some(scope=>scope.view===this.view&&scope.generation===this.generation)) await this.send('pause');
  }
  async seek(ms) {
    if (!this.kind) throw new Error('영상을 먼저 연결하세요.');
    const scope=this.scope();this.cancelPendingPlay();
    await this.send('seek', Math.max(0, ms));
    this.assertCurrent(scope);
    if (this.kind === 'local') this.video.currentTime = Math.max(0, Math.min(this.video.duration || 0, ms / 1000));
  }
  async audio(volume, muted) {
    if (!Number.isFinite(volume) || volume < 0 || volume > 1) throw new Error('영상 음량은 0~1로 입력하세요.');
    this.video.volume = volume; this.video.muted = muted;
    if (this.kind) await this.send('audio', {volume, muted});
  }
  captions(segments, enabled) {
    this.video.querySelectorAll('track').forEach(track => track.remove());
    if (this.captionUrl) URL.revokeObjectURL(this.captionUrl);
    if (!segments.length) { this.captionUrl = null; return; }
    const stamp = ms => `${String(Math.floor(ms / 3600000)).padStart(2, '0')}:${String(Math.floor(ms / 60000) % 60).padStart(2, '0')}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}.${String(ms % 1000).padStart(3, '0')}`;
    const cues = segments.filter(s => Number.isFinite(s.start_ms) && s.end_ms > s.start_ms)
      .map(s => `${stamp(s.start_ms)} --> ${stamp(s.end_ms)}\n${s.text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}`).join('\n\n');
    this.captionUrl = URL.createObjectURL(new Blob([`WEBVTT\n\n${cues}\n`], {type: 'text/vtt'}));
    const track = document.createElement('track'); track.kind = 'captions'; track.label = '준비된 한국어 자막'; track.srclang = 'ko'; track.src = this.captionUrl;
    this.video.append(track); track.track.mode = enabled ? 'showing' : 'hidden';
  }
  reset() {
    this.pendingLocal?.();
    this.generation++; this.ready = false;this.cancelPendingPlay();this.wantsPlayback=false;
    this.fence++; this.video.pause();
    this.send('release').catch(() => {});
    this.video.removeAttribute('src'); this.video.load(); this.video.hidden = true;
    this.captions([], false);
    if (this.url) URL.revokeObjectURL(this.url);
    this.url = null; this.kind = null; this.verified = false;
    this.view = crypto.randomUUID(); this.fence = 0;
  }
}
