// Speech owns a cancellation generation. Old completion callbacks can never resume a stopped lesson.
export class StudentSpeech {
  constructor(media, settings, output) { this.media = media; this.settings = settings; this.output = output; this.generation = 0; this.active = false; }
  cancel(preserveResume = false) { this.generation++; this.active = false; this.pending?.(); this.pending = null;this.media.cancelPendingPlay?.(); if (!preserveResume) this.resumeIntent = null; globalThis.speechSynthesis?.cancel(); }
  async say(text, {resume = true, purpose='lesson'} = {}) {
    this.beforeSpeak?.(purpose);
    this.cancel(true); const ticket = this.generation; this.active = true;
    const fence = this.media.fence,intendedPlaying=this.media.wantsPlayback;
    try {
    await this.media.claimForSpeech?.();
    if (ticket !== this.generation) return;
    const state = await this.media.state();
    if (ticket !== this.generation) return;
    const wasPlaying = !state.paused || intendedPlaying || (this.resumeIntent?.fence === fence && this.resumeIntent.playing);
    this.resumeIntent = {fence, playing: wasPlaying};
    await this.media.pause(false);
    if (ticket !== this.generation) return;
    this.output(text,{purpose});
    const settings = this.settings();
    if (settings.reader_mode) {
      this.active = false; this.resumeIntent = null;this.media.wantsPlayback=false; return; // Screen-reader users resume explicitly after reading.
    }
    if(!globalThis.speechSynthesis||!globalThis.SpeechSynthesisUtterance){
      this.output(text,{unavailable:true});
      throw new Error('앱 음성을 사용할 수 없습니다. 읽기 영역에서 내용을 확인하거나 외부 스크린리더를 사용하세요.');
    }
      const spokenText=String(text).replace(/(\d)\.(?=\d)/g,'$1점');
      const chunks=(globalThis.SullivanSpeechProfile?.speechChunks(spokenText)||[spokenText]).flatMap(part=>part.match(/[\s\S]{1,180}/g)||[]);
      for (const [index,chunk] of chunks.entries()) {
        if (ticket !== this.generation) return;
        await new Promise((resolve, reject) => {
          const finish = error => {
            clearTimeout(timer);
            if (this.pending === cancel) this.pending = null;
            error ? reject(error) : resolve();
          };
          const cancel = () => finish();
          const timer = setTimeout(() => finish(new Error('음성 응답 시간이 초과됐습니다.')), 60000);
          this.pending = cancel;
          const utterance = new SpeechSynthesisUtterance(chunk);
          utterance.lang = 'ko-KR'; utterance.rate = settings.speech_rate; utterance.volume = settings.speech_volume;
          const profile={warm:[1,.99],calm:[.94,.98],clear:[1.02,1.01]}[settings.speech_style]||[1,1];
          const opening=index===0&&chunks.length>1,closing=index===chunks.length-1&&chunks.length>1;
          utterance.rate=Math.max(.75,Math.min(1.25,settings.speech_rate*profile[0]*(opening?.98:closing?.97:1)));
          utterance.pitch=Math.max(.8,Math.min(1.2,(settings.speech_pitch||1)*profile[1]*(closing?.98:1)));
          const voices=globalThis.speechSynthesis.getVoices?.()||[];
          const voice=globalThis.SullivanSpeechProfile?.select(voices,settings.voice_uri)||voices.find(v=>v.voiceURI===settings.voice_uri)||voices.find(v=>String(v.lang).toLowerCase().startsWith('ko'));
          if (voice) utterance.voice = voice;
          utterance.onend = () => finish();
          utterance.onerror = event => finish(new Error(event.error));
          speechSynthesis.resume?.();
          speechSynthesis.speak(utterance);
        });
        if(index<chunks.length-1&&ticket===this.generation)await new Promise(resolve=>{
          const timer=setTimeout(()=>{if(this.pending===cancel)this.pending=null;resolve();},/[.!?]$/.test(chunk)?130:70);
          const cancel=()=>{clearTimeout(timer);resolve();};this.pending=cancel;
        });
      }
      if (ticket === this.generation && this.media.fence === fence && resume && wasPlaying) await this.media.play(fence);
      if (ticket === this.generation){this.resumeIntent = null;if(!resume)this.media.wantsPlayback=false;}
    } catch (error) { if (ticket === this.generation) { this.resumeIntent = null; throw error; } }
    finally { if (ticket === this.generation) this.active = false; }
  }
}

// UI guidance must work before selecting a lecture and without a media lease.
export class StudentAnnouncer {
  constructor(settings, report, busy=()=>false){this.settings=settings;this.report=report;this.busy=busy;this.generation=0;this.utterance=null;}
  cancel(preserve=false){if(this.delegated){this.delegated=false;this.lessonSpeaker?.cancel(preserve);}this.generation++;clearTimeout(this.timer);if(this.utterance){this.utterance.onend=this.utterance.onerror=this.utterance.onstart=null;this.utterance=null;globalThis.speechSynthesis?.cancel();}}
  say(text,{force=false}={}){
    const settings=this.settings();
    if(settings.reader_mode||(!force&&!settings.focus_voice)||this.busy()||!String(text).trim())return;
    this.cancel(true);const ticket=this.generation;
    if(this.lessonReady?.()){
      this.delegated=true;
      this.lessonSpeaker.say(text,{purpose:'guidance'}).catch(error=>{if(ticket===this.generation)this.report(error.message);}).finally(()=>{if(ticket===this.generation)this.delegated=false;});return;
    }
    if(!globalThis.speechSynthesis||!globalThis.SpeechSynthesisUtterance){this.report('앱 음성을 지원하지 않는 브라우저입니다. 외부 스크린리더를 사용하세요.');return;}
    const utterance=new SpeechSynthesisUtterance(String(text).slice(0,1200));this.utterance=utterance;
    utterance.lang='ko-KR';utterance.rate=settings.speech_rate;utterance.volume=settings.speech_volume;utterance.pitch=settings.speech_pitch||1;
    const voices=speechSynthesis.getVoices?.()||[];
    const voice=globalThis.SullivanSpeechProfile?.select(voices,settings.voice_uri)||voices.find(v=>v.voiceURI===settings.voice_uri)||voices.find(v=>v.lang.toLowerCase().startsWith('ko'));
    if(voice)utterance.voice=voice;
    const finish=()=>{if(ticket!==this.generation)return;clearTimeout(this.timer);this.utterance=null;};
    utterance.onstart=()=>{if(ticket===this.generation){clearTimeout(this.timer);this.report('앱 음성 안내가 켜져 있습니다.');this.timer=setTimeout(()=>{if(ticket===this.generation){this.cancel();this.report('음성 안내가 지연되어 중지했습니다.');}},30000);}};
    utterance.onend=finish;
    utterance.onerror=event=>{finish();if(ticket===this.generation&&!['canceled','interrupted'].includes(event.error))this.report('음성을 재생하지 못했습니다. 음성 안내 시작·시험을 누르고 Chrome 음소거와 출력 장치를 확인하세요.');};
    this.timer=setTimeout(()=>{if(ticket===this.generation){this.cancel();this.report('음성 시작을 확인하지 못했습니다. 음성 안내 시작·시험을 눌러 주세요.');}},2500);
    try{speechSynthesis.resume?.();speechSynthesis.speak(utterance);}catch{finish();this.report('음성을 시작하지 못했습니다. 음성 안내 시작·시험을 눌러 주세요.');}
  }
}

export function controlDescription(element){
  const plain=node=>{if(node.nodeType===3)return node.nodeValue;if(node.nodeType!==1||node.matches('input,textarea,select,[aria-hidden=true]'))return '';return [...node.childNodes].map(plain).join(' ');};
  const labelled=element.getAttribute('aria-labelledby');
  let label=labelled?labelled.split(/\s+/).map(id=>element.ownerDocument.getElementById(id)?.textContent||'').join(' '):element.getAttribute('aria-label');
  if(!label)label=element.labels?.length?[...element.labels].map(plain).join(' '):plain(element);
  label=label.replace(/\s+/g,' ').trim();
  if(element.type==='checkbox')label+=element.checked?'. 켜짐.':'. 꺼짐.';
  if(element.tagName==='SELECT')label+=`. ${element.selectedOptions[0]?.textContent||''}`;
  const units={speech_rate:'배',speech_volume:'','speech-pitch':'배','video-volume':''};
  const numeric=Object.hasOwn(units,element.name)?element.name:element.id;
  if(element.type==='number'&&Object.hasOwn(units,numeric)&&element.value!==''&&Number.isFinite(Number(element.value)))label+=`. 현재 ${element.value}${units[numeric]}.`;
  if(element.tagName==='SUMMARY')label+=element.parentElement.open?'. 펼쳐짐.':'. 접힘.';
  if(element.getAttribute('aria-pressed')==='true')label+='. 선택됨.';
  if(element.getAttribute('aria-current'))label+='. 현재 항목.';
  if(element.type==='password')label+='. 비밀번호 입력.';
  return label;
}
