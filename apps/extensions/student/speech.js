// Speech owns a cancellation generation. Old completion callbacks can never resume a stopped lesson.
export class StudentSpeech {
  constructor(media, settings, output) { this.media = media; this.settings = settings; this.output = output; this.generation = 0; this.active = false; }
  cancel(preserveResume = false) { this.generation++; this.active = false; this.pending?.(); this.pending = null; if (!preserveResume) this.resumeIntent = null; globalThis.speechSynthesis?.cancel(); }
  async say(text, {resume = true} = {}) {
    this.cancel(true); const ticket = this.generation; this.active = true;
    const fence = this.media.fence;
    try {
    await this.media.claimForSpeech?.();
    if (ticket !== this.generation) return;
    const state = await this.media.state();
    if (ticket !== this.generation) return;
    const wasPlaying = !state.paused || (this.resumeIntent?.fence === fence && this.resumeIntent.playing);
    this.resumeIntent = {fence, playing: wasPlaying};
    await this.media.pause(false);
    if (ticket !== this.generation) return;
    this.output(text);
    const settings = this.settings();
    if (settings.reader_mode || !globalThis.speechSynthesis || !globalThis.SpeechSynthesisUtterance) {
      this.active = false; this.resumeIntent = null; return; // Screen-reader users resume explicitly after reading.
    }
      for (const chunk of String(text).match(/[\s\S]{1,180}/g) || []) {
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
          utterance.pitch = settings.speech_pitch || 1;
          const voice = globalThis.speechSynthesis.getVoices?.().find(voice => voice.voiceURI === settings.voice_uri);
          if (voice) utterance.voice = voice;
          utterance.onend = () => finish();
          utterance.onerror = event => finish(new Error(event.error));
          speechSynthesis.speak(utterance);
        });
      }
      if (ticket === this.generation && this.media.fence === fence && resume && wasPlaying) await this.media.play(fence);
      if (ticket === this.generation) this.resumeIntent = null;
    } catch (error) { if (ticket === this.generation) { this.resumeIntent = null; throw error; } }
    finally { if (ticket === this.generation) this.active = false; }
  }
}
