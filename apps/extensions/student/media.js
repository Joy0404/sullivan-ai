export class StudentMedia {
  constructor(video) { this.video = video; this.view = crypto.randomUUID(); this.fence = 0; this.kind = null; this.verified = false; this.url = null; this.generation = 0; this.ready = false; }
  async send(action, value, fence = this.fence) {
    const response = await chrome.runtime.sendMessage({type: 'student-media', view: this.view, action, value, fence});
    if (!response?.ok) throw new Error(response?.error || '강의 연결을 확인하세요.');
    return response.result;
  }
  async connect(url, open = false) {
    const ticket = this.generation;
    await this.claim(url, open);
    if (ticket !== this.generation) throw new Error('강의 연결을 취소했습니다.');
    this.kind = 'remote'; this.verified = true;
    // A newly opened site may need time to mount its video. No playback starts here.
    let error;
    for (let attempt = 0; attempt < 20; attempt++) {
      if (ticket !== this.generation) throw new Error('강의 연결을 취소했습니다.');
      try { await this.send('pause'); return; } catch (problem) { error = problem; await new Promise(resolve => setTimeout(resolve, 500)); }
    }
    this.kind = null; this.verified = false; throw error;
  }
  async claim(url = null, open = false) {
    const response = await chrome.runtime.sendMessage({type: 'student-media', view: this.view, action: 'claim', url, open});
    if (!response?.ok) throw new Error(response?.error || '학습 화면을 연결할 수 없습니다.');
  }
  async claimForSpeech() {
    if (!this.kind) await this.claim();
    else await this.send('state');
  }
  async local(file, identity) {
    const ticket = this.generation;
    if (!file || !file.type.startsWith('video/')) throw new Error('재생할 영상 파일을 선택하세요.');
    if (identity?.sha256 && file.size > 100000000) throw new Error('분석한 원본과 크기가 다릅니다. 같은 파일을 선택하세요.');
    if (identity?.sha256) {
      const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', await file.arrayBuffer()))].map(n => n.toString(16).padStart(2, '0')).join('');
      if (hash !== identity.sha256 || file.size !== identity.size_bytes) throw new Error('분석한 원본과 다른 파일입니다. 자동 해설을 연결하지 않았습니다.');
    }
    if (ticket !== this.generation) throw new Error('파일 연결을 취소했습니다.');
    await this.claim();
    if (ticket !== this.generation) throw new Error('파일 연결을 취소했습니다.');
    this.kind = 'local'; this.verified = Boolean(identity?.sha256);
    this.url = URL.createObjectURL(file); this.video.src = this.url; this.video.hidden = false;
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => { cleanup(); reject(new Error('영상 정보를 읽지 못했습니다. 형식과 파일을 확인하세요.')); }, 10000);
      const loaded = () => { cleanup(); resolve(); };
      const failed = () => { cleanup(); reject(new Error('이 브라우저에서 재생할 수 없는 영상입니다.')); };
      const cleanup = () => { clearTimeout(timer); this.video.removeEventListener('loadedmetadata', loaded); this.video.removeEventListener('error', failed); };
      this.video.addEventListener('loadedmetadata', loaded); this.video.addEventListener('error', failed);
    });
  }
  async state() {
    if (!this.kind) return {positionMs: 0, paused: true, verified: false};
    if (this.kind === 'remote') return this.send('state');
    await this.send('state'); // Enforce one active learning view for local video too.
    return {positionMs: Math.round(this.video.currentTime * 1000), paused: this.video.paused,
      durationMs: Number.isFinite(this.video.duration) ? Math.round(this.video.duration * 1000) : null, ended: this.video.ended, ad: false, verified: this.verified};
  }
  async play(fence = this.fence) {
    if (!this.kind || !this.ready) throw new Error('원본 강의 또는 로컬 영상을 먼저 연결하세요.');
    await this.send('play', null, fence);
    if (this.kind === 'local' && fence === this.fence) await this.video.play();
  }
  async pause(invalidate = true) {
    if (invalidate) this.fence++;
    this.video.pause();
    if (this.kind) await this.send('pause');
  }
  async seek(ms) {
    if (!this.kind) throw new Error('영상을 먼저 연결하세요.');
    await this.send('seek', Math.max(0, ms));
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
    this.generation++; this.ready = false;
    this.fence++; this.video.pause();
    this.send('release').catch(() => {});
    this.video.removeAttribute('src'); this.video.load(); this.video.hidden = true;
    this.captions([], false);
    if (this.url) URL.revokeObjectURL(this.url);
    this.url = null; this.kind = null; this.verified = false;
    this.view = crypto.randomUUID(); this.fence = 0;
  }
}
