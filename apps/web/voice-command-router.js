(function createSullivanVoiceCommands(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.SullivanVoiceCommands = api;
})(typeof window !== "undefined" ? window : globalThis, () => {
  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[.,!?~·]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function classify(value) {
    const command = normalize(value);
    if (!command) return { type: "empty" };

    if (/(자유 ?모드|수동 ?모드|직접 ?조작 ?모드|키보드 ?모드)/.test(command)) return { type: "free_mode" };
    if (/(멈춰|멈추|일시 ?정지|재생 ?정지|음성 ?중지|말하기 ?중지|그만)/.test(command)) return { type: "pause" };
    if (/(재생해|재생 ?시작|영상 ?시작|강의 ?시작|영상 ?틀|강의 ?틀|계속 ?재생|계속 ?틀|이어 ?재생|다시 ?재생)/.test(command)) return { type: "play" };
    if (/(현재 )?(화면|칠판|슬라이드|그래프).*(해설|설명)|화면 ?해설/.test(command)) return { type: "describe" };
    if (/(자동 ?해설|자동 ?설명).*(켜|시작)/.test(command)) return { type: "auto_narration", enabled: true };
    if (/(자동 ?해설|자동 ?설명).*(꺼|중지|해제)/.test(command)) return { type: "auto_narration", enabled: false };

    if (/(샘플 ?1|과학 ?샘플|별의 ?진화)/.test(command)) return { type: "sample", sampleId: "science" };
    if (/(샘플 ?2|역사 ?샘플|왜란.*호란|호란.*왜란)/.test(command)) return { type: "sample", sampleId: "history" };
    if (/(저장.*홈|저장하고.*홈|강의.*저장.*돌아)/.test(command)) return { type: "save_home" };
    if (/(홈으로|홈에|처음 ?화면|시작 ?화면).*(가|돌아|이동)?/.test(command)) return { type: "home" };

    if (/^(?:이 |이 강의 |강의 )?요약(?:해 ?줘)?$|(?:요약).*(읽|들려|말해|음성)|전체 ?핵심 ?듣기/.test(command)) return { type: "summary_audio" };
    if (/(접근성 ?복습|강의 ?후 ?복습)/.test(command)) return { type: "panel", panelId: "review-panel" };
    if (/(학습 ?노트|요약 ?노트)/.test(command)) return { type: "panel", panelId: "study-panel" };
    if (/(에이 ?아이|ai).*대화|학습 ?대화|채팅/.test(command)) return { type: "panel", panelId: "chat-panel" };
    if (/(판단 ?근거|안전 ?설계)/.test(command)) return { type: "panel", panelId: "evidence-panel" };
    if (/(강의 ?화면|영상 ?화면)/.test(command)) return { type: "panel", panelId: "watch-panel" };
    if (/(핵심 ?탐색|핵심 ?개념 ?탐색)/.test(command) && !/(찾|검색|말해|들려)/.test(command)) return { type: "panel", panelId: "passage-panel" };

    if (/(문단|긴 ?지문|밑줄)/.test(command)) return { type: "paragraph", command: value };
    if (/(핵심|키워드|개념).*(찾|검색|탐색|들려|말해)/.test(command)) return { type: "concept", command: value };
    if (/(저장된|최근) ?강의|지난 ?강의/.test(command)) return { type: "saved", command: value };

    const buttonMatch = command.match(/(.+?)(?:버튼)?\s*(?:눌러|클릭|선택|실행)(?:\s*해줘)?$/);
    if (buttonMatch?.[1]) return { type: "button", label: buttonMatch[1].trim() };
    return { type: "chat", command: value };
  }

  function isDoubleTap(previousMs, currentMs, limitMs = 1000) {
    return Number.isFinite(previousMs)
      && previousMs > 0
      && Number.isFinite(currentMs)
      && currentMs >= previousMs
      && currentMs - previousMs <= limitMs;
  }

  function classifyTapSequence(count, { freeMode = false } = {}) {
    const taps = Math.max(0, Number(count) || 0);
    if (freeMode) return taps >= 2 ? "exit_free_mode" : "toggle_playback";
    if (taps >= 3) return "open_text_command";
    if (taps === 2) return "cancel_guidance";
    return "single_tap";
  }

  return { normalize, classify, isDoubleTap, classifyTapSequence };
});
