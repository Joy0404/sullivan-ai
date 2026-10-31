// The API serves this page, so every request uses a same-origin relative path.
const API = "";
const MAX_UPLOAD_VIDEO_BYTES = 100 * 1024 * 1024;
const SAMPLE_VIDEO_URL = "https://www.youtube.com/watch?v=R0dqsl3Vgns";
const SAMPLE_CATALOG = {
  science: {
    title: "천문학 특강 7강 · 별의 진화",
    subject: "통합과학 · 천문학",
    videoUrl: SAMPLE_VIDEO_URL,
    embedUrl: "https://www.youtube-nocookie.com/embed/R0dqsl3Vgns?enablejsapi=1&rel=0&disablekb=1",
    announcement: "별의 진화",
  },
  history: {
    title: "중3 역사 · 왜란과 호란의 발발과 영향",
    subject: "중학교 역사 · 조선 후기",
    videoUrl: "https://www.youtube.com/watch?v=thJxqtTgSNY&list=PLD5ojEfJUayNED1OvOabV8P9WVroE92Qm&index=20",
    embedUrl: "https://www.youtube-nocookie.com/embed/thJxqtTgSNY?enablejsapi=1&rel=0&disablekb=1",
    announcement: "왜란과 호란의 발발과 영향",
  },
};
const state = {
  session: null,
  snapshot: null,
  health: null,
  videoUrl: null,
  linkedPlaybackKind: null,
  pendingLinkResult: null,
  youtubePlayer: null,
  youtubeTimer: null,
  analysisTimer: null,
  analysisPercent: 0,
  analysisLocalOnly: false,
  isSample: false,
  activeSampleId: null,
  localVideoFile: null,
  currentSavedLectureId: null,
  lectureCompleted: false,
  savedLectures: [],
  announcedGaps: new Set(),
  lastPlaybackMs: null,
  speechInProgress: false,
  currentSentenceId: null,
  speechToken: 0,
  resumeAfterSpeech: false,
  bookmarks: [],
  lastChatOutput: null,
  currentConceptId: null,
  currentParagraphId: null,
  underlinedParagraphIds: new Set(),
  conceptSequenceTimer: null,
  conceptSequenceToken: 0,
  conceptSequenceActive: false,
  demoAccessCode: "",
  agentTurnPending: false,
  freeControlMode: false,
  freeSpaceTapAt: 0,
  freeSpaceTapTimer: null,
  spaceVoice: {
    holdTimer: null,
    target: null,
    activated: false,
    released: false,
    finalized: false,
    recognition: null,
    transcript: "",
    error: "",
    wasPlaying: false,
    audioContext: null,
    keyHeld: false,
    guidePlaying: false,
    pressStartedAt: 0,
    lastShortTapAt: 0,
    shortTapCount: 0,
    shortTapTimer: null,
    guideCancelTap: false,
    guideSkipTimer: null,
    recognitionRestartTimer: null,
    recognitionFatal: false,
    skipGuideNextHold: false,
  },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

function escapeHtml(value) {
  const node = document.createElement("div");
  node.textContent = value ?? "";
  return node.innerHTML;
}

function announce(message) {
  $("#live-region").textContent = "";
  window.setTimeout(() => { $("#live-region").textContent = message; }, 20);
}

function uid(prefix) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
}

function formatTime(milliseconds) {
  const total = Math.max(0, Math.floor((milliseconds || 0) / 1000));
  const minutes = Math.floor(total / 60);
  const seconds = String(total % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

async function api(path, options = {}) {
  let response;
  try {
    const isFormData = options.body instanceof FormData;
    response = await fetch(`${API}${path}`, {
      ...options,
      headers: { ...(isFormData ? {} : { "Content-Type": "application/json" }), ...(options.headers || {}) },
    });
  } catch {
    throw new Error("분석 서버에 연결할 수 없습니다. 인터넷 연결을 확인하고 잠시 뒤 다시 시도해 주세요.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `요청 실패 (${response.status})`);
  }
  return response.json();
}

async function checkApi() {
  try {
    const health = await api("/health");
    state.health = health;
    $("#api-dot").classList.add("ok");
    $("#api-state").textContent = health.raw_video_storage === "disabled" ? "분석 엔진 연결 · 영상 비저장" : "분석 엔진 연결";
    if (health.real_analysis_access !== "trial-code-required") {
      $("#demo-access-help").textContent = "이 서버에서는 실제 AI 분석이 꺼져 있습니다. 샘플·보관함·로컬 보조 대화는 그대로 이용할 수 있어요.";
    }
  } catch {
    $("#api-state").textContent = "API 실행 필요";
  }
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0MB";
  if (bytes < 1024 ** 2) return `${Math.ceil(bytes / 1024)}KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)}MB`;
  return `${(bytes / 1024 ** 3).toFixed(1)}GB`;
}

const analysisMessages = [
  "영상과 이용 권한을 확인하고 임시 분석 입력을 준비하는 중입니다.",
  "강사 음성과 주요 발화를 시간대별로 분석하는 중입니다.",
  "판서·슬라이드·도표의 시각정보를 확인하는 중입니다.",
  "Gemini가 후보 장면을 다시 보며 판서·해설의 일치를 독립 검증하는 중입니다.",
  "실시간 화면 해설과 요약 음성 가이드를 생성하는 중입니다.",
];

const localPreparationMessages = [
  "원본 영상은 브라우저에 둔 채 재생 준비를 확인하는 중입니다.",
  "자막과 보조 학습자료를 안전하게 읽는 중입니다.",
  "제공된 분석 결과의 확신도와 정답 차단 정책을 확인하는 중입니다.",
  "시간 정보와 화면 해설을 연결하는 중입니다.",
  "요약, 학습 노트, 음성 탐색 기능을 준비하는 중입니다.",
];

function showAnalysisProgress(isLocalVideo = false) {
  state.analysisPercent = 4;
  state.analysisLocalOnly = isLocalVideo;
  $("#analysis-overlay").classList.remove("hidden");
  $("#analysis-title").textContent = isLocalVideo ? "강의 자료를 준비하고 있습니다" : "강의 영상을 분석하고 있습니다";
  updateAnalysisProgress(state.analysisPercent, isLocalVideo ? "원본 영상은 브라우저에 둔 채 재생 준비를 확인하는 중입니다." : analysisMessages[0]);
  window.clearInterval(state.analysisTimer);
  state.analysisTimer = window.setInterval(() => {
    if (state.analysisPercent >= 92) return;
    const increment = state.analysisPercent < 40 ? 3 : state.analysisPercent < 75 ? 2 : 1;
    updateAnalysisProgress(Math.min(92, state.analysisPercent + increment));
  }, 900);
}

function updateAnalysisProgress(percent, customMessage = null) {
  const nextPercent = Math.max(0, Math.min(100, Math.round(percent)));
  state.analysisPercent = Math.max(state.analysisPercent, nextPercent);
  const step = Math.min(4, Math.floor(state.analysisPercent / 20));
  const messages = state.analysisLocalOnly ? localPreparationMessages : analysisMessages;
  $("#analysis-stage").textContent = customMessage || messages[step];
  $("#analysis-progress-bar").style.width = `${state.analysisPercent}%`;
  $("#analysis-percentage").textContent = `${state.analysisPercent}%`;
  $("#analysis-progress").setAttribute("aria-valuenow", String(state.analysisPercent));
  $$("#analysis-steps li").forEach((item, index) => {
    item.classList.toggle("done", index < step);
    item.classList.toggle("active", index === step);
  });
}

async function finishAnalysisProgress(message = "분석이 완료되었습니다. 접근성 가이드를 활성화합니다.") {
  window.clearInterval(state.analysisTimer);
  updateAnalysisProgress(100, message);
  await new Promise((resolve) => window.setTimeout(resolve, 750));
  $("#analysis-overlay").classList.add("hidden");
}

function hideAnalysisProgress() {
  window.clearInterval(state.analysisTimer);
  $("#analysis-overlay").classList.add("hidden");
}

function syncAnalysisConsent() {
  const consent = $("#local-video-ai-consent input");
  const hasSource = Boolean($("#video-file").files[0] || $("#video-url").value.trim());
  consent.disabled = !hasSource;
  if (!hasSource) consent.checked = false;
}

$("#video-file").addEventListener("change", (event) => {
  const file = event.target.files[0];
  syncAnalysisConsent();
  const tooLarge = file && file.size > MAX_UPLOAD_VIDEO_BYTES;
  $("#video-file-name").textContent = file
    ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)}MB · 로컬 재생${tooLarge ? " · 100MB를 넘어 실제 AI 분석은 할 수 없습니다" : ""}`
    : "선택된 영상 없음 — 샘플 모드로도 실행할 수 있습니다.";
});

$("#video-url").addEventListener("input", (event) => {
  const value = event.target.value.trim();
  const stateLabel = $("#video-link-state");
  stateLabel.textContent = value ? "링크 입력됨" : "링크 미입력";
  stateLabel.classList.toggle("ready", Boolean(value));
  syncAnalysisConsent();
});

$("#material-files").addEventListener("change", (event) => {
  const files = [...event.target.files];
  $("#material-preview").innerHTML = files.length
    ? files.map((file) => `<li>${escapeHtml(file.name)} <span>${Math.ceil(file.size / 1024)}KB</span></li>`).join("")
    : "<li>선택된 자료 없음</li>";
});

$("#lecture-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await startSession(false);
});

$$('[data-sample-id]').forEach((button) => button.addEventListener("click", async () => {
  await openSampleSession(button.dataset.sampleId);
}));

async function openSampleSession(sampleId = "science") {
  const config = SAMPLE_CATALOG[sampleId] || SAMPLE_CATALOG.science;
  const sampleData = window.SULLIVAN_SAMPLE_LIBRARY?.[sampleId];
  if (!sampleData) return alert("선택한 샘플 데이터를 불러오지 못했습니다.");
  const sampleButtons = $$('[data-sample-id]');
  sampleButtons.forEach((button) => { button.disabled = true; });
  state.isSample = true;
  state.demoAccessCode = $("#demo-access-code").value.trim();
  state.activeSampleId = sampleId;
  state.localVideoFile = null;
  state.currentSavedLectureId = null;
  state.lectureCompleted = false;
  state.announcedGaps.clear();
  state.currentParagraphId = null;
  state.underlinedParagraphIds.clear();
  state.session = {
    session_id: uid("sample"),
    title: config.title,
    subject: config.subject,
    source_label: "YouTube 공개 샘플 · 사전 준비된 접근성 분석",
    preferred_mode: "slides",
    problem_mode: false,
    created_at: new Date().toISOString(),
    status: "active",
    policy_version: "internet-lecture-access-v1",
  };
  state.snapshot = JSON.parse(JSON.stringify(sampleData));
  state.snapshot.session = state.session;
  state.pendingLinkResult = {
    normalized_url: config.videoUrl,
    playback_kind: "youtube",
    playback_url: config.embedUrl,
    analysis_status: "registered-only",
    message: "사전에 준비된 접근성 샘플을 불러왔습니다.",
  };

  $("#setup-view").classList.add("hidden");
  $("#agent-view").classList.remove("hidden");
  $("#lecture-title").textContent = state.session.title;
  $("#lecture-title").setAttribute("tabindex", "-1");
  $("#lecture-title").focus();
  $("#lecture-meta").textContent = `${state.session.subject} · ${state.session.source_label}`;
  renderAll();
  announce(`${config.announcement} 샘플을 바로 열었습니다. 분석 서버 연결 없이 이용할 수 있습니다.`);
  sampleButtons.forEach((button) => { button.disabled = false; });
  setupLinkPlayback(state.pendingLinkResult).catch((error) => {
    $("#lecture-youtube").classList.add("hidden");
    $("#video-placeholder").classList.remove("hidden");
    $("#video-placeholder strong").textContent = "샘플 학습 노트 준비 완료";
    $("#video-placeholder p").textContent = "영상 플레이어를 불러오지 못했지만 해설·요약·학습 노트는 바로 사용할 수 있습니다.";
    $("#linked-playback-note").classList.remove("hidden");
    $("#linked-playback-note").textContent = error.message;
  });
}

async function startSession(useDemo) {
  const form = new FormData($("#lecture-form"));
  const videoUrl = useDemo ? SAMPLE_VIDEO_URL : String(form.get("video_url") || "").trim();
  const videoFile = useDemo ? null : $("#video-file").files[0];
  const analysisConsent = !useDemo && form.get("local_gemini_consent") === "on";
  const accessCode = String(form.get("demo_access_code") || "").trim();
  const submitButtons = $$("#lecture-form button");
  submitButtons.forEach((button) => { button.disabled = true; });
  state.isSample = useDemo;
  state.demoAccessCode = accessCode;
  let cleanupWarning = "";
  state.activeSampleId = useDemo ? "science" : null;
  state.localVideoFile = null;
  state.currentSavedLectureId = null;
  state.lectureCompleted = false;
  state.currentParagraphId = null;
  state.underlinedParagraphIds.clear();
  state.pendingLinkResult = null;
  if (!useDemo) showAnalysisProgress(Boolean(videoFile) && !analysisConsent);
  try {
    if (videoFile && analysisConsent && videoFile.size > MAX_UPLOAD_VIDEO_BYTES) {
      throw new Error("실제 AI 분석은 100MB 이하 영상만 가능합니다. 분석을 시작하지 않았습니다.");
    }
    if (!useDemo && videoUrl && !analysisConsent) {
      throw new Error("실제 AI 분석을 하려면 분석 동의에 직접 체크해 주세요.");
    }
    if (analysisConsent && !accessCode) {
      throw new Error("실제 AI 분석에는 체험 코드가 필요합니다. 샘플은 코드 없이 이용할 수 있어요.");
    }
    state.session = await api("/v1/lectures", {
      method: "POST",
      body: JSON.stringify({
        title: useDemo ? "천문학 특강 7강 · 별의 진화" : form.get("title"),
        subject: useDemo ? "통합과학 · 천문학" : form.get("subject"),
        source_label: useDemo ? "YouTube 공개 샘플 · 사전 준비된 접근성 분석" : form.get("source_label"),
        preferred_mode: useDemo ? "slides" : form.get("preferred_mode"),
        problem_mode: form.get("problem_mode") === "on",
      }),
    });
    if (!useDemo) updateAnalysisProgress(14, "분석 세션을 만들고 입력 자료를 안전하게 연결했습니다.");

    if (videoFile && videoUrl) throw new Error("영상 파일과 링크 중 하나만 선택해 주세요.");
    if (videoFile) {
      const videoAsset = await registerVideo(videoFile);
      if (analysisConsent) {
        updateAnalysisProgress(28, "동의한 원본을 Gemini에 임시 전송해 실제 발화와 화면을 분석하고 있습니다.");
        state.snapshot = await analyzeLocalVideoFile(
          videoFile,
          videoAsset.asset_id,
          form.get("rights_confirmed") === "on",
          accessCode,
        );
        if (state.snapshot.cleanup_status === "delete-failed") cleanupWarning = state.snapshot.cleanup_message;
        updateAnalysisProgress(82, "음성 전사와 판서·슬라이드 관측을 독립 시각 근거로 다시 검증했습니다.");
      } else {
        updateAnalysisProgress(32, "원본을 전송하지 않고 브라우저 안에서 재생 준비를 마쳤습니다.");
      }
    }
    if (videoUrl) {
      const linkResult = await registerVideoLink(
        videoUrl,
        useDemo || form.get("rights_confirmed") === "on",
        useDemo ? "" : accessCode,
        !useDemo,
        analysisConsent,
      );
      if (!useDemo && (linkResult.analysis_status !== "completed" || !linkResult.snapshot)) {
        throw new Error(linkResult.message);
      }
      state.pendingLinkResult = linkResult;
      if (linkResult.snapshot) state.snapshot = linkResult.snapshot;
      if (!useDemo) updateAnalysisProgress(78, "음성과 화면 분석 결과를 안전 정책에 따라 검증하고 있습니다.");
    }

    const packages = [];
    for (const file of [...$("#material-files").files]) {
      const result = await registerMaterial(file);
      if (result) packages.push(result);
    }
    if (!useDemo && $("#material-files").files.length) updateAnalysisProgress(84, "자막과 학습자료를 시간순으로 정리했습니다.");

    for (const analysisPackage of packages) {
      state.snapshot = await api(`/v1/lectures/${state.session.session_id}/analysis`, {
        method: "POST",
        body: JSON.stringify(analysisPackage),
      });
    }
    if (!useDemo && packages.length) updateAnalysisProgress(94, "화면 해설, 요약, 핵심 탐색 정보를 구성했습니다.");

    if (useDemo) {
      state.snapshot = await api(`/v1/lectures/${state.session.session_id}/demo-analysis`, { method: "POST" });
    } else if (!state.snapshot) {
      state.snapshot = await api(`/v1/lectures/${state.session.session_id}`);
    }

    if (!useDemo) {
      const hasAnalysis = state.snapshot?.active_mode && state.snapshot.active_mode !== "waiting";
      await finishAnalysisProgress(cleanupWarning
        ? "분석 결과는 받았지만 임시 영상 삭제를 확인하지 못했습니다."
        : hasAnalysis
          ? "분석이 완료되었습니다. 접근성 가이드를 활성화합니다."
          : "재생 준비가 완료되었습니다. 자동 해설에는 자막 또는 분석 JSON이 필요합니다.");
      if (cleanupWarning) alert(`분석 결과는 받았지만 삭제가 끝나지 않았습니다. ${cleanupWarning}`);
    }

    $("#setup-view").classList.add("hidden");
    $("#agent-view").classList.remove("hidden");
    $("#lecture-title").textContent = state.session.title;
  $("#lecture-title").setAttribute("tabindex", "-1");
  $("#lecture-title").focus();
    $("#lecture-meta").textContent = `${state.session.subject} · ${state.session.source_label}${state.session.problem_mode ? " · 문제 모드" : ""}`;
    if (state.pendingLinkResult) await setupLinkPlayback(state.pendingLinkResult);
    renderAll();
    announce(useDemo ? "별의 진화 사전 준비 샘플을 바로 열었습니다." : "강의 자료 준비가 완료되어 접근성 가이드를 활성화했습니다.");
  } catch (error) {
    hideAnalysisProgress();
    alert(`분석 세션을 시작하지 못했습니다. ${error.message}`);
  } finally {
    submitButtons.forEach((button) => { button.disabled = false; });
  }
}

async function registerVideo(file) {
  if (state.videoUrl) URL.revokeObjectURL(state.videoUrl);
  state.localVideoFile = file;
  state.videoUrl = URL.createObjectURL(file);
  const video = $("#lecture-video");
  video.src = state.videoUrl;
  $("#video-placeholder").classList.add("hidden");
  return api(`/v1/lectures/${state.session.session_id}/assets`, {
    method: "POST",
    body: JSON.stringify({
      asset_id: uid("video"),
      name: file.name,
      kind: "video",
      media_type: file.type || "video/mp4",
      size_bytes: file.size,
      metadata: { client_local_playback: true },
    }),
  });
}

async function analyzeLocalVideoFile(file, assetId, rightsConfirmed, accessCode) {
  const payload = new FormData();
  payload.append("video", file, file.name);
  payload.append("asset_id", assetId);
  payload.append("rights_confirmed", String(rightsConfirmed));
  payload.append("cloud_analysis_consent", "true");
  payload.append("access_code", accessCode);
  return api(`/v1/lectures/${state.session.session_id}/video-file-analysis`, {
    method: "POST",
    body: payload,
  });
}

async function registerVideoLink(url, rightsConfirmed, accessCode, requestAnalysis = true, analysisConsent = false) {
  const result = await api(`/v1/lectures/${state.session.session_id}/video-link`, {
    method: "POST",
    body: JSON.stringify({
      url,
      rights_confirmed: rightsConfirmed,
      request_analysis: requestAnalysis,
      analysis_consent: analysisConsent,
      access_code: accessCode || null,
    }),
  });
  return result;
}

async function setupLinkPlayback(result) {
  state.linkedPlaybackKind = result.playback_kind;
  const video = $("#lecture-video");
  const youtube = $("#lecture-youtube");
  video.classList.add("hidden");
  youtube.classList.add("hidden");
  $("#video-placeholder").classList.add("hidden");

  if (result.playback_kind === "direct") {
    video.src = result.playback_url;
    video.classList.remove("hidden");
  } else if (result.playback_kind === "youtube") {
    youtube.classList.remove("hidden");
    await setupYouTubePlayer(result.playback_url);
  } else {
    $("#video-placeholder").classList.remove("hidden");
    $("#video-placeholder strong").textContent = "외부 강의 링크 등록 완료";
    $("#video-placeholder p").textContent = "이 주소는 내장 재생을 지원하지 않아 새 창에서 확인해야 합니다.";
  }

  const note = $("#linked-playback-note");
  note.classList.remove("hidden");
  const sampleName = SAMPLE_CATALOG[state.activeSampleId]?.announcement || "강의";
  note.textContent = state.isSample
    ? `사전 준비된 ${sampleName} 접근성 샘플입니다. 이 실행에서 영상을 새로 분석하지 않았으며, 재생 시간에 맞춰 자동 정지·화면 해설을 체험할 수 있습니다.`
    : "Sullivan AI가 링크 영상의 음성·화면 분석을 완료했습니다. 재생하면 실시간 화면 해설이 자동으로 작동합니다.";
}

async function registerMaterial(file) {
  const extension = file.name.split(".").pop().toLowerCase();
  const text = await file.text();
  let kind = "passage";
  if (["srt", "vtt"].includes(extension)) kind = "subtitle";
  if (extension === "json") kind = "analysis";

  await api(`/v1/lectures/${state.session.session_id}/assets`, {
    method: "POST",
    body: JSON.stringify({
      asset_id: uid(kind),
      name: file.name,
      kind,
      media_type: file.type || "text/plain",
      size_bytes: file.size,
      content_text: kind === "analysis" ? null : text,
    }),
  });

  if (kind !== "analysis") return null;
  try {
    const parsed = JSON.parse(text);
    const candidate = parsed.analysis || parsed;
    if (!candidate.transcript_segments && !candidate.visual_observations && !candidate.passage_text) {
      throw new Error("분석 패키지 필드가 없습니다.");
    }
    return candidate;
  } catch (error) {
    throw new Error(`${file.name} 분석 JSON을 읽을 수 없습니다: ${error.message}`);
  }
}

$("#run-demo-analysis").addEventListener("click", async () => {
  if (!state.session) return;
  if (state.isSample) {
    const sampleId = state.activeSampleId || "science";
    state.snapshot = JSON.parse(JSON.stringify(window.SULLIVAN_SAMPLE_LIBRARY?.[sampleId] || window.SULLIVAN_SAMPLE_DATA));
    state.snapshot.session = state.session;
    state.announcedGaps.clear();
    state.currentParagraphId = null;
    state.underlinedParagraphIds.clear();
    renderAll();
    announce(`사전 준비된 ${SAMPLE_CATALOG[sampleId]?.announcement || "강의"} 샘플을 다시 불러왔습니다.`);
    return;
  }
  try {
    state.snapshot = await api(`/v1/lectures/${state.session.session_id}/demo-analysis`, { method: "POST" });
    state.isSample = true;
    state.announcedGaps.clear();
    renderAll();
    announce("재현 가능한 샘플 분석을 불러왔습니다.");
  } catch (error) { alert(error.message); }
});

function renderAll() {
  if (!state.snapshot) return;
  const { active_mode: mode, safe_description_count: safeCount, held_count: heldCount } = state.snapshot;
  const labels = { board: "판서", passage: "핵심 개념", slides: "슬라이드", mixed: "혼합", waiting: "분석 대기" };
  $("#mode-stat").textContent = labels[mode] || mode;
  $("#description-stat").textContent = safeCount;
  $("#hold-stat").textContent = heldCount;
  $("#agent-status").innerHTML = `<i></i> ${mode === "waiting" ? "어댑터 입력 대기" : `${labels[mode]} 모드 작동 중`}`;
  renderAssets();
  renderTranscript();
  renderTimeline();
  renderPassage();
  renderLongPassage();
  renderReview();
  renderStudyGuide();
  renderBookmarks();
  renderEvidence();
  updateAutoNarrationStatus(0);
}

function renderAssets() {
  const assets = state.snapshot.assets;
  $("#asset-list").innerHTML = assets.length
    ? assets.map((asset) => `<li><span class="source-icon">${asset.kind === "video" ? "▶" : "≡"}</span><div><strong>${escapeHtml(asset.name)}</strong><small>${escapeHtml(asset.note)}</small></div><span class="source-state ${asset.processing_status}">${escapeHtml(asset.processing_status)}</span></li>`).join("")
    : "<li>등록된 자료 없음</li>";
}

function renderTranscript() {
  const segments = state.snapshot.transcript_segments;
  $("#transcript-count").textContent = `${segments.length}개 구간`;
  $("#transcript-list").innerHTML = segments.length
    ? segments.map((segment) => `<button type="button" class="transcript-row" data-time="${segment.start_ms}"><span>${formatTime(segment.start_ms)}</span><p>${escapeHtml(segment.text)}</p></button>`).join("")
    : "자막 또는 분석 결과가 없습니다.";
  $$(".transcript-row").forEach((button) => button.addEventListener("click", () => seekTo(Number(button.dataset.time))));
}

function renderTimeline() {
  const gaps = state.snapshot.visual_gaps;
  const safeGaps = gaps.filter((gap) => gap.safe_to_speak && gap.action !== "SKIP");
  const maxTimestamp = Math.max(40_000, ...gaps.map((gap) => gap.timestamp_ms));
  $("#visual-timeline").innerHTML = `<div class="timeline-track"></div>${safeGaps.map((gap) => {
    const left = Math.min(98, (gap.timestamp_ms / maxTimestamp) * 100);
    return `<button class="timeline-marker ${gap.action.toLowerCase()}" style="left:${left}%" data-gap="${gap.gap_id}" aria-label="${formatTime(gap.timestamp_ms)} ${escapeHtml(gap.public_description)}"><span>${formatTime(gap.timestamp_ms)}</span></button>`;
  }).join("")}`;
  $$(".timeline-marker").forEach((button) => button.addEventListener("click", () => {
    const gap = gaps.find((item) => item.gap_id === button.dataset.gap);
    if (gap) { seekTo(gap.timestamp_ms); narrateGap(gap); }
  }));
}

function loadYouTubeApi() {
  if (window.YT?.Player) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector("script[data-sullivan-youtube-api]");
    const previousReady = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      if (typeof previousReady === "function") previousReady();
      resolve();
    };
    if (existing) {
      window.setTimeout(() => {
        if (window.YT?.Player) resolve();
      }, 250);
      return;
    }
    const script = document.createElement("script");
    script.src = "https://www.youtube.com/iframe_api";
    script.async = true;
    script.dataset.sullivanYoutubeApi = "true";
    script.onerror = () => reject(new Error("YouTube 재생 모듈을 불러오지 못했습니다."));
    document.head.appendChild(script);
  });
}

async function setupYouTubePlayer(playbackUrl) {
  await loadYouTubeApi();
  const parsed = new URL(playbackUrl);
  const videoId = parsed.pathname.split("/").filter(Boolean).pop();
  if (!videoId) throw new Error("YouTube 영상 ID를 확인할 수 없습니다.");
  await new Promise((resolve, reject) => {
    state.youtubePlayer = new window.YT.Player("lecture-youtube", {
      host: "https://www.youtube-nocookie.com",
      videoId,
      playerVars: { rel: 0, enablejsapi: 1, disablekb: 1, origin: window.location.origin },
      events: {
        onReady: () => {
          state.lastPlaybackMs = null;
          window.clearInterval(state.youtubeTimer);
          state.youtubeTimer = window.setInterval(() => {
            const seconds = state.youtubePlayer?.getCurrentTime?.();
            if (Number.isFinite(seconds)) processPlaybackTime(seconds * 1000);
          }, 200);
          updateAutoNarrationStatus(0);
          restoreGlobalSpaceFocus();
          resolve();
        },
        onStateChange: (event) => {
          if (event.data === window.YT?.PlayerState?.PLAYING) {
            const seconds = state.youtubePlayer?.getCurrentTime?.();
            if (Number.isFinite(seconds)) {
              state.lastPlaybackMs = Math.max(0, seconds * 1000 - 700);
              processPlaybackTime(seconds * 1000);
            }
          }
          if (event.data === window.YT?.PlayerState?.ENDED) markLectureComplete();
          updateAutoNarrationStatus(getCurrentPlaybackMs());
          restoreGlobalSpaceFocus();
        },
        onError: () => reject(new Error("YouTube 영상을 재생할 수 없습니다. 공개·임베드 허용 영상인지 확인해 주세요.")),
      },
    });
  });
}

function processPlaybackTime(currentMs) {
  if (!Number.isFinite(currentMs)) return;
  const previousMs = state.lastPlaybackMs;
  state.lastPlaybackMs = currentMs;
  if (!state.snapshot || !$("#auto-narration").checked || state.speechInProgress || state.conceptSequenceActive) return;

  if (Number.isFinite(previousMs) && currentMs < previousMs - 1_000) {
    state.snapshot.visual_gaps
      .filter((gap) => gap.timestamp_ms >= currentMs - 500)
      .forEach((gap) => state.announcedGaps.delete(gap.gap_id));
    updateAutoNarrationStatus(currentMs);
    return;
  }

  const gap = window.SullivanPlayback?.selectDueGap({
    gaps: state.snapshot.visual_gaps,
    announcedIds: state.announcedGaps,
    previousMs,
    currentMs,
  });
  if (gap && isPlaybackRunning()) {
    narrateGap(gap, { automatic: true });
    return;
  }
  updateAutoNarrationStatus(currentMs);
}

function updateAutoNarrationStatus(currentMs = 0, message = null) {
  const badge = $("#agent-status");
  if (!badge || !state.snapshot) return;
  if (message) {
    badge.innerHTML = `<i></i> ${escapeHtml(message)}`;
    return;
  }
  if (!$("#auto-narration").checked) {
    badge.innerHTML = "<i></i> 자동 정지·해설 꺼짐";
    return;
  }
  if (state.speechInProgress) {
    badge.innerHTML = "<i></i> 영상 정지 · 화면 해설 중";
    return;
  }
  const next = window.SullivanPlayback?.nextAutomaticGap(
    state.snapshot.visual_gaps,
    state.announcedGaps,
    currentMs,
  );
  badge.innerHTML = next
    ? `<i></i> 자동 해설 감시 중 · 다음 ${formatTime(next.timestamp_ms)}`
    : "<i></i> 자동 해설 감시 중 · 예정된 해설 완료";
}

function getCurrentPlaybackMs() {
  if (state.linkedPlaybackKind === "youtube") {
    const seconds = state.youtubePlayer?.getCurrentTime?.();
    return Number.isFinite(seconds) ? seconds * 1000 : 0;
  }
  return $("#lecture-video").currentTime * 1000;
}

function isPlaybackRunning() {
  if (state.linkedPlaybackKind === "youtube") {
    return state.youtubePlayer?.getPlayerState?.() === window.YT?.PlayerState?.PLAYING;
  }
  const video = $("#lecture-video");
  return !video.classList.contains("hidden") && !video.paused && !video.ended;
}

function pausePlayback() {
  if (state.linkedPlaybackKind === "youtube") state.youtubePlayer?.pauseVideo?.();
  else $("#lecture-video").pause();
}

function resumePlayback() {
  if (state.linkedPlaybackKind === "youtube") state.youtubePlayer?.playVideo?.();
  else $("#lecture-video").play().catch(() => {});
}

$("#lecture-video").addEventListener("timeupdate", () => {
  processPlaybackTime($("#lecture-video").currentTime * 1000);
});

$("#lecture-video").addEventListener("ended", markLectureComplete);

function markLectureComplete() {
  if (state.lectureCompleted) return;
  state.lectureCompleted = true;
  $("#lecture-complete-card").classList.remove("hidden");
  announce("강의를 끝까지 들었습니다. 원본과 요약을 이 노트북에 저장한 뒤 홈으로 돌아갈 수 있습니다.");
}

function narrateGap(gap, { automatic = false, pauseForDescription = false } = {}) {
  if (!gap?.safe_to_speak || !gap.public_description) return;
  const narrationText = window.SullivanNarration?.compose(gap, getConcepts()) || gap.public_description;
  state.announcedGaps.add(gap.gap_id);
  const wasPlaying = isPlaybackRunning();
  const shouldPause = wasPlaying && (pauseForDescription || automatic);
  if (shouldPause) pausePlayback();
  state.resumeAfterSpeech = shouldPause || state.resumeAfterSpeech;
  $("#current-description").textContent = narrationText;
  $("#description-reason").textContent = `${formatTime(gap.timestamp_ms)} · 앞뒤 맥락을 포함한 짧은 해설 · ${gap.reason}`;
  $("#pause-overlay-label").textContent = shouldPause ? "해설 후 자동 재생" : "현재 화면 해설";
  $("#pause-overlay").classList.toggle("hidden", !shouldPause);
  if (automatic) updateAutoNarrationStatus(gap.timestamp_ms, "영상 정지 · 화면 해설 중");
  announce(narrationText);
  speak(narrationText, () => {
    $("#pause-overlay").classList.add("hidden");
    if (state.resumeAfterSpeech) resumePlayback();
    state.resumeAfterSpeech = false;
    updateAutoNarrationStatus(gap.timestamp_ms + 1);
  });
}

$("#auto-narration").addEventListener("change", (event) => {
  if (!event.currentTarget.checked && state.resumeAfterSpeech) {
    state.speechToken += 1;
    state.speechInProgress = false;
    window.speechSynthesis?.cancel();
    $("#pause-overlay").classList.add("hidden");
    resumePlayback();
    state.resumeAfterSpeech = false;
  }
  updateAutoNarrationStatus(getCurrentPlaybackMs());
  announce(event.currentTarget.checked ? "자동 정지와 화면 해설을 켰습니다." : "자동 정지와 화면 해설을 껐습니다.");
});

$("#describe-now").addEventListener("click", () => {
  const gaps = state.snapshot?.visual_gaps.filter((gap) => gap.safe_to_speak && gap.public_description) || [];
  if (!gaps.length) return announce("설명할 수 있는 검증된 화면정보가 없습니다.");
  const currentMs = getCurrentPlaybackMs();
  const nearest = [...gaps].sort((a, b) => Math.abs(a.timestamp_ms - currentMs) - Math.abs(b.timestamp_ms - currentMs))[0];
  narrateGap(nearest, { pauseForDescription: true });
});

function getConcepts() {
  return window.SullivanConcepts?.conceptsForSnapshot(state.snapshot || {}) || [];
}

function getParagraphs() {
  return window.SullivanPassages?.paragraphsForSnapshot(state.snapshot || {}) || [];
}

function findParagraph(paragraphId) {
  return getParagraphs().find((paragraph) => paragraph.paragraph_id === paragraphId);
}

function findConcept(conceptId) {
  return getConcepts().find((concept) => concept.concept_id === conceptId);
}

function renderPassage() {
  const concepts = getConcepts();
  if (!concepts.length) {
    $("#passage-count").textContent = "개념 대기";
    $("#passage-document").className = "passage-document empty-state";
    $("#passage-document").textContent = "강의 분석이 완료되면 강사가 강조한 핵심 키워드와 흐름이 표시됩니다.";
    return;
  }
  if (!state.currentConceptId || !findConcept(state.currentConceptId)) state.currentConceptId = concepts[0].concept_id;
  const categories = window.SullivanConcepts?.categories(concepts) || [];
  $("#passage-count").textContent = `${concepts.length}개 개념 · ${categories.length}개 유형`;
  $("#passage-document-title").textContent = state.isSample
    ? `${SAMPLE_CATALOG[state.activeSampleId]?.announcement || "강의"} · 핵심 개념`
    : "강사가 강조한 핵심 개념";
  $("#passage-document").className = "passage-document concept-document";
  $("#passage-document").innerHTML = concepts.map((concept) => `
    <article class="concept-item ${state.currentConceptId === concept.concept_id ? "current" : ""}">
      <button type="button" class="concept-select" data-concept="${escapeHtml(concept.concept_id)}">
        <span class="concept-meta"><b>${escapeHtml(concept.category)}</b><time>${formatTime(concept.timestamp_ms)}</time></span>
        <strong>${escapeHtml(concept.keyword)}</strong>
        <p>${escapeHtml(concept.lecturer_point)}</p>
        ${concept.flow ? `<small>${escapeHtml(concept.flow)}</small>` : ""}
      </button>
      <button type="button" class="concept-speak secondary" data-speak-concept="${escapeHtml(concept.concept_id)}" aria-label="${escapeHtml(concept.keyword)} 강사 구간을 듣고 AI 설명 듣기">말하기</button>
    </article>`).join("");
  $$(".concept-select").forEach((button) => button.addEventListener("click", () => selectConcept(button.dataset.concept)));
  $$(".concept-speak").forEach((button) => button.addEventListener("click", () => {
    const concept = findConcept(button.dataset.speakConcept);
    if (concept) playConceptSequence(concept);
  }));
}

function renderLongPassage() {
  const paragraphs = getParagraphs();
  const documentBox = $("#long-passage-document");
  if (!paragraphs.length) {
    $("#long-passage-count").textContent = "문단 대기";
    $("#paragraph-flow").textContent = "";
    documentBox.className = "passage-document empty-state";
    documentBox.textContent = "긴 지문 또는 자막의 문단 분석이 완료되면 문단별 내용과 흐름이 표시됩니다.";
    return;
  }
  if (!state.currentParagraphId || !findParagraph(state.currentParagraphId)) state.currentParagraphId = paragraphs[0].paragraph_id;
  const underlinedCount = paragraphs.filter((paragraph) => state.underlinedParagraphIds.has(paragraph.paragraph_id)).length;
  $("#long-passage-count").textContent = `${paragraphs.length}개 문단 · 밑줄 ${underlinedCount}개`;
  $("#paragraph-flow").innerHTML = paragraphs.map((paragraph, index) => `
    <button type="button" data-flow-paragraph="${escapeHtml(paragraph.paragraph_id)}" aria-label="${paragraph.paragraph_index}문단 ${escapeHtml(paragraph.flow_role)} 선택">
      <span>${paragraph.paragraph_index}</span><strong>${escapeHtml(paragraph.flow_role)}</strong>${index < paragraphs.length - 1 ? "<i aria-hidden=\"true\">→</i>" : ""}
    </button>`).join("");
  documentBox.className = "passage-document paragraph-document";
  documentBox.innerHTML = paragraphs.map((paragraph) => {
    const isUnderlined = state.underlinedParagraphIds.has(paragraph.paragraph_id);
    const isCurrent = state.currentParagraphId === paragraph.paragraph_id;
    return `
      <article class="paragraph-block ${isUnderlined ? "underlined" : ""} ${isCurrent ? "current" : ""}" data-paragraph-card="${escapeHtml(paragraph.paragraph_id)}">
        <header>
          <div><span>${paragraph.paragraph_index}문단 · ${formatTime(paragraph.timestamp_ms)}</span><strong>${escapeHtml(paragraph.flow_role)}</strong></div>
          <div class="paragraph-actions">
            <button type="button" class="paragraph-underline ${isUnderlined ? "active" : ""}" data-underline-paragraph="${escapeHtml(paragraph.paragraph_id)}" aria-pressed="${isUnderlined}">${isUnderlined ? "밑줄 해제" : "밑줄 표시"}</button>
            <button type="button" class="secondary" data-read-paragraph="${escapeHtml(paragraph.paragraph_id)}">문단 듣기</button>
          </div>
        </header>
        <p class="paragraph-text">${paragraph.sentences.map((sentence) => `<button type="button" class="sentence ${sentence.highlighted ? "highlighted" : ""}" data-paragraph-sentence="${escapeHtml(paragraph.paragraph_id)}" data-time="${sentence.timestamp_ms || 0}" aria-label="${paragraph.paragraph_index}문단 ${sentence.sentence_index}번째 문장, ${escapeHtml(sentence.text)}${sentence.highlighted ? ", 강사가 강조한 문장" : ""}"><span>${sentence.sentence_index}</span>${escapeHtml(sentence.text)}${sentence.highlighted ? "<em>강조</em>" : ""}</button>`).join(" ")}</p>
      </article>`;
  }).join("");

  $$('[data-flow-paragraph]').forEach((button) => button.addEventListener("click", () => selectParagraph(button.dataset.flowParagraph)));
  $$('[data-underline-paragraph]').forEach((button) => button.addEventListener("click", () => toggleParagraphUnderline(button.dataset.underlineParagraph)));
  $$('[data-read-paragraph]').forEach((button) => button.addEventListener("click", () => replayParagraphs([findParagraph(button.dataset.readParagraph)].filter(Boolean))));
  $$('[data-paragraph-sentence]').forEach((button) => button.addEventListener("click", () => {
    state.currentParagraphId = button.dataset.paragraphSentence;
    seekTo(Number(button.dataset.time));
    renderLongPassage();
    announce(`${findParagraph(state.currentParagraphId)?.paragraph_index || "선택한"}문단의 강사 구간으로 이동했습니다.`);
  }));
}

function selectParagraph(paragraphId) {
  const paragraph = findParagraph(paragraphId);
  if (!paragraph) return;
  state.currentParagraphId = paragraphId;
  renderLongPassage();
  $("#paragraph-navigation-answer").textContent = `${paragraph.paragraph_index}문단, ${paragraph.flow_role}. 문단 듣기 또는 밑줄 표시를 선택할 수 있습니다.`;
  announce(`${paragraph.paragraph_index}문단 ${paragraph.flow_role}을 선택했습니다.`);
}

function toggleParagraphUnderline(paragraphId) {
  const paragraph = findParagraph(paragraphId);
  if (!paragraph) return;
  state.currentParagraphId = paragraphId;
  const wasUnderlined = state.underlinedParagraphIds.has(paragraphId);
  if (wasUnderlined) state.underlinedParagraphIds.delete(paragraphId);
  else state.underlinedParagraphIds.add(paragraphId);
  renderLongPassage();
  const message = `${paragraph.paragraph_index}문단 밑줄을 ${wasUnderlined ? "해제" : "표시"}했습니다.`;
  $("#paragraph-navigation-answer").textContent = `${message} “밑줄 친 문단 다시 들려줘”라고 요청할 수 있습니다.`;
  announce(message);
}

function replayParagraphs(paragraphs, speechOverride = "") {
  if (!paragraphs.length) return;
  state.currentParagraphId = paragraphs[0].paragraph_id;
  renderLongPassage();
  const text = speechOverride || paragraphs.map((paragraph) => window.SullivanPassages.paragraphSpeech(paragraph)).join(" ");
  $("#paragraph-navigation-answer").textContent = `${paragraphs.map((paragraph) => `${paragraph.paragraph_index}문단`).join(", ")}을 다시 읽고 있습니다.`;
  announce($("#paragraph-navigation-answer").textContent);
  speakWithPlaybackPause(text, "문단 낭독 후 자동 재생");
}

function runParagraphCommand(command) {
  const result = window.SullivanPassages?.resolveCommand({
    paragraphs: getParagraphs(),
    query: command,
    currentId: state.currentParagraphId,
    underlinedIds: state.underlinedParagraphIds,
  });
  if (!result) return;
  $("#paragraph-navigation-answer").textContent = result.speech;
  if (["paragraph", "underlined"].includes(result.type) && result.items.length) {
    replayParagraphs(result.items, result.speech);
  } else if (result.type === "flow") {
    speakWithPlaybackPause(result.speech, "긴 지문 흐름 안내 후 자동 재생");
    announce(result.speech);
  } else {
    announce(result.speech);
  }
}

$("#paragraph-navigation-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const command = new FormData(event.currentTarget).get("command")?.trim();
  if (command) runParagraphCommand(command);
});

$$('[data-paragraph-command]').forEach((button) => button.addEventListener("click", (event) => {
  event.stopPropagation();
  $("#paragraph-navigation-command").value = button.dataset.paragraphCommand;
  $("#paragraph-navigation-form").requestSubmit();
}));

$("#paragraph-voice-command").addEventListener("click", () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) return alert("이 브라우저에서는 음성 명령을 지원하지 않습니다. 명령을 직접 입력해 주세요.");
  const recognition = new Recognition();
  recognition.lang = "ko-KR";
  recognition.interimResults = false;
  $("#paragraph-voice-command").classList.add("listening");
  announce("문단 음성 명령을 듣고 있습니다.");
  recognition.onresult = (event) => {
    $("#paragraph-navigation-command").value = event.results[0][0].transcript;
    $("#paragraph-navigation-form").requestSubmit();
  };
  recognition.onerror = () => announce("문단 음성 명령을 인식하지 못했습니다. 다시 시도해 주세요.");
  recognition.onend = () => $("#paragraph-voice-command").classList.remove("listening");
  recognition.start();
});

function selectConcept(conceptId) {
  const concept = findConcept(conceptId);
  if (!concept) return;
  state.currentConceptId = concept.concept_id;
  renderPassage();
  $("#navigation-answer").textContent = `${concept.keyword}. 강사 설명 ${formatTime(concept.timestamp_ms)}. ${concept.ai_explanation}`;
  announce(`${concept.keyword} 개념을 선택했습니다. 말하기를 누르면 강사 구간 뒤에 AI가 다시 설명합니다.`);
}

function playConceptSequence(concept) {
  stopAllPlaybackAndSpeech({ announceStop: false });
  state.currentConceptId = concept.concept_id;
  state.conceptSequenceToken += 1;
  const token = state.conceptSequenceToken;
  state.conceptSequenceActive = true;
  renderPassage();
  const segmentEndMs = Math.min(concept.end_ms, concept.timestamp_ms + 22_000);
  $("#navigation-answer").textContent = `${concept.keyword}: ${formatTime(concept.timestamp_ms)}부터 강사 설명을 먼저 재생합니다. 이어서 AI가 핵심을 다시 말합니다.`;
  announce(`${concept.keyword} 강사 설명을 먼저 재생합니다.`);
  seekTo(concept.timestamp_ms);
  const sequenceStartedAt = Date.now();
  let lecturerPlaybackStarted = false;
  window.setTimeout(() => {
    if (token !== state.conceptSequenceToken) return;
    resumePlayback();
    window.clearInterval(state.conceptSequenceTimer);
    state.conceptSequenceTimer = window.setInterval(() => {
      if (token !== state.conceptSequenceToken) return;
      const currentMs = getCurrentPlaybackMs();
      const nearSegment = currentMs >= concept.timestamp_ms - 1_500 && currentMs < segmentEndMs;
      if (nearSegment && isPlaybackRunning()) lecturerPlaybackStarted = true;
      if (nearSegment && (isPlaybackRunning() || Date.now() - sequenceStartedAt < 6_000)) return;
      if (!lecturerPlaybackStarted && Date.now() - sequenceStartedAt < 6_000) return;
      window.clearInterval(state.conceptSequenceTimer);
      state.conceptSequenceTimer = null;
      pausePlayback();
      state.conceptSequenceActive = false;
      const aiText = `AI가 핵심을 다시 정리할게요. ${concept.ai_explanation}${concept.flow ? ` 흐름은 ${concept.flow}입니다.` : ""}`;
      const lecturerStatus = lecturerPlaybackStarted
        ? "강사 구간 재생 완료"
        : "영상 플레이어가 재생되지 않아 강사 구간은 건너뜀";
      $("#navigation-answer").textContent = `${concept.keyword} · ${lecturerStatus}. ${aiText}`;
      announce(lecturerPlaybackStarted ? "강사 설명이 끝났습니다. AI 설명을 이어서 재생합니다." : "영상 재생을 시작하지 못해 AI 설명부터 재생합니다.");
      speak(aiText, () => {
        if (token !== state.conceptSequenceToken) return;
        $("#navigation-answer").textContent = `${concept.keyword} 강사 구간과 AI 재설명을 모두 들었습니다. 영상은 멈춘 상태입니다.`;
        announce(`${concept.keyword} 듣기를 마쳤습니다.`);
      });
    }, 200);
  }, 450);
}

$("#navigation-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const command = new FormData(event.currentTarget).get("command")?.trim();
  if (!command || !state.session) return;
  try {
    const concepts = getConcepts();
    const matches = window.SullivanConcepts?.search(concepts, command) || [];
    if (!matches.length) {
      const message = `“${command}”과 직접 연결된 강의 개념을 찾지 못했습니다. 전체 흐름, 원인, 전개, 결과, 인물, 비교 또는 화면에 보이는 핵심 키워드로 다시 말해 주세요.`;
      $("#navigation-answer").textContent = message;
      announce(message);
      return;
    }
    state.currentConceptId = matches[0].concept_id;
    renderPassage();
    const listed = matches.slice(0, 6).map((item) => `${item.keyword} ${formatTime(item.timestamp_ms)}`).join(", ");
    const message = `${matches.length}개를 찾았습니다. ${listed}. 원하는 개념의 말하기 버튼을 누르면 강사 구간 뒤에 AI 설명이 이어집니다.`;
    $("#navigation-answer").textContent = message;
    announce(message);
  } catch (error) { alert(error.message); }
});

$$('[data-command]').forEach((button) => button.addEventListener("click", () => {
  $("#navigation-command").value = button.dataset.command;
  $("#navigation-form").requestSubmit();
}));

$("#read-current").addEventListener("click", () => {
  const concept = findConcept(state.currentConceptId) || getConcepts()[0];
  if (concept) playConceptSequence(concept);
});

$("#stop-concept-sequence").addEventListener("click", () => stopAllPlaybackAndSpeech());

$("#voice-command").addEventListener("click", () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) return alert("이 브라우저에서는 음성 명령을 지원하지 않습니다. 명령을 직접 입력해 주세요.");
  const recognition = new Recognition();
  recognition.lang = "ko-KR";
  recognition.interimResults = false;
  $("#voice-command").classList.add("listening");
  announce("음성 명령을 듣고 있습니다.");
  recognition.onresult = (event) => {
    $("#navigation-command").value = event.results[0][0].transcript;
    $("#navigation-form").requestSubmit();
  };
  recognition.onerror = () => announce("음성 명령을 인식하지 못했습니다. 다시 시도해 주세요.");
  recognition.onend = () => $("#voice-command").classList.remove("listening");
  recognition.start();
});

function renderReview() {
  const review = state.snapshot.review;
  renderReviewList("#review-summary", review.core_summary.map((description, index) => ({ item_id: `summary-${index}`, timestamp_ms: 0, title: `핵심 ${index + 1}`, description })));
  renderReviewList("#review-visual", review.visual_only_information);
  renderReviewList("#review-highlight", review.highlighted_sentences);
  renderReviewList("#review-segments", review.key_segments);
}

function renderReviewList(selector, items) {
  const box = $(selector);
  if (!items.length) { box.className = "review-list empty-state"; box.textContent = "분석 결과 없음"; return; }
  box.className = "review-list";
  box.innerHTML = items.map((item) => `<button type="button" class="review-item" data-time="${item.timestamp_ms || 0}"><span>${item.timestamp_ms ? formatTime(item.timestamp_ms) : "핵심"}</span><div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.description)}</p></div></button>`).join("");
  box.querySelectorAll(".review-item").forEach((button) => button.addEventListener("click", () => {
    seekTo(Number(button.dataset.time));
    speak(button.textContent.trim());
  }));
}

function readSummaryGuide() {
  const review = state.snapshot?.review;
  if (!review) return;
  const text = [
    "오늘의 핵심 내용.", ...review.core_summary,
    "화면으로만 제시된 중요 정보.", ...review.visual_only_information.map((item) => item.description),
    "강사가 강조한 문장.", ...review.highlighted_sentences.map((item) => item.description),
  ].join(" ");
  speakWithPlaybackPause(text, "요약 안내 후 자동 재생");
}

$("#read-review").addEventListener("click", readSummaryGuide);
$("#read-summary-guide").addEventListener("click", readSummaryGuide);

function renderStudyGuide() {
  const guide = state.snapshot?.study_guide || {};
  const fallbackSummary = state.snapshot?.review?.core_summary?.join(" ") || "분석 결과가 준비되면 핵심 요약이 표시됩니다.";
  $("#study-overview").textContent = guide.overview || fallbackSummary;
  $("#concept-map").innerHTML = guide.concept_map?.length
    ? guide.concept_map.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
    : "<li>개념 연결 정보가 없습니다.</li>";
  $("#study-glossary").innerHTML = guide.glossary?.length
    ? guide.glossary.map((item) => `<div><dt>${escapeHtml(item.term)}</dt><dd>${escapeHtml(item.definition)}</dd></div>`).join("")
    : "<div><dt>대기</dt><dd>핵심 용어 정보가 없습니다.</dd></div>";
  $("#recall-questions").innerHTML = guide.recall_questions?.length
    ? guide.recall_questions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
    : "<li>스스로 확인할 질문이 없습니다.</li>";
}

function studyGuideText() {
  const guide = state.snapshot?.study_guide || {};
  return [
    "한눈에 요약.", guide.overview || state.snapshot?.review?.core_summary?.join(" "),
    "개념 연결 지도.", ...(guide.concept_map || []),
    "핵심 용어.", ...(guide.glossary || []).map((item) => `${item.term}. ${item.definition}`),
    "스스로 확인하기.", ...(guide.recall_questions || []),
  ].filter(Boolean).join(" ");
}

$("#read-study-guide").addEventListener("click", () => speakWithPlaybackPause(studyGuideText(), "학습 노트 안내 후 자동 재생"));

function renderBookmarks() {
  const box = $("#bookmark-list");
  if (!state.bookmarks.length) {
    box.className = "bookmark-list empty-state";
    box.textContent = "저장한 노트가 없습니다.";
    return;
  }
  box.className = "bookmark-list";
  box.innerHTML = state.bookmarks.map((item, index) => `<button type="button" class="bookmark-item" data-bookmark="${index}"><span>${formatTime(item.timestamp_ms)}</span><strong>${escapeHtml(item.note)}</strong></button>`).join("");
  box.querySelectorAll(".bookmark-item").forEach((button) => button.addEventListener("click", () => {
    const item = state.bookmarks[Number(button.dataset.bookmark)];
    seekTo(item.timestamp_ms);
    speak(`${formatTime(item.timestamp_ms)} 노트. ${item.note}`);
  }));
}

function addBookmark() {
  if (!state.snapshot) return;
  const noteInput = $("#bookmark-note");
  const note = noteInput.value.trim() || $("#current-description").textContent.trim() || "다시 볼 장면";
  state.bookmarks.push({ timestamp_ms: getCurrentPlaybackMs(), note });
  noteInput.value = "";
  renderBookmarks();
  announce(`${formatTime(state.bookmarks.at(-1).timestamp_ms)} 위치를 학습 노트에 저장했습니다.`);
}

$("#add-bookmark").addEventListener("click", addBookmark);

$("#export-study-notes").addEventListener("click", () => {
  const guide = state.snapshot?.study_guide || {};
  const title = state.session?.title || "Sullivan AI 학습 노트";
  const lines = [
    `# ${title} · 접근성 학습 노트`,
    "", "## 한눈에 요약", "", guide.overview || state.snapshot?.review?.core_summary?.join(" ") || "요약 없음",
    "", "## 개념 연결 지도", "", ...(guide.concept_map || []).map((item) => `- ${item}`),
    "", "## 핵심 용어", "", ...(guide.glossary || []).map((item) => `- **${item.term}**: ${item.definition}`),
    "", "## 스스로 확인하기", "", ...(guide.recall_questions || []).map((item, index) => `${index + 1}. ${item}`),
    "", "## 내 타임스탬프 노트", "", ...state.bookmarks.map((item) => `- ${formatTime(item.timestamp_ms)} ${item.note}`),
    "", "_Sullivan AI가 만든 학습 보조 노트입니다. 원본 강의와 함께 확인하세요._",
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "sullivan-ai-study-notes.md";
  link.click();
  URL.revokeObjectURL(url);
  announce("학습 노트를 Markdown 파일로 저장했습니다.");
});

function generateLearningResponse(message) {
  const guide = state.snapshot?.study_guide || {};
  const review = state.snapshot?.review || {};
  const gaps = state.snapshot?.visual_gaps || [];
  const concepts = getConcepts();
  const normalized = message.replace(/\s+/g, " ").trim().toLowerCase();
  const summaryItems = review.core_summary || [];
  const conceptMap = guide.concept_map || [];
  const glossary = guide.glossary || [];
  const questions = guide.recall_questions || [];
  const overview = guide.overview || summaryItems.join(" ") || "현재 강의에서 검증된 요약정보를 찾지 못했습니다.";
  const mentionedConcepts = window.SullivanConcepts?.mentioned(concepts, normalized) || [];
  const searchedConcepts = window.SullivanConcepts?.search(concepts, normalized) || [];
  const topicConcepts = mentionedConcepts.length ? mentionedConcepts : searchedConcepts.slice(0, 5);

  const conceptLines = (items, limit = 12) => items.slice(0, limit).map((item) => (
    `• ${item.keyword} (${formatTime(item.timestamp_ms)}): ${item.ai_explanation}`
  )).join("\n");

  const flowLines = (items) => items.filter((item) => item.flow).slice(0, 8).map((item, index) => (
    `${index + 1}. ${item.keyword}: ${item.flow}`
  )).join("\n");

  if (normalized.includes("정답") || normalized.includes("답 알려")) {
    if (state.session?.problem_mode) {
      const hints = conceptMap.slice(0, 3).map((item, index) => `${index + 1}. ${item}`).join("\n");
      return {
        title: "풀이 방향",
        text: `현재 문제 보호 모드에서는 최종 정답만 보류합니다. 대신 관련 개념과 풀이 순서를 안내합니다.\n${hints || overview}\n전체 화면 설명이 필요한 학습 상황이라면 새 세션에서 문제 보호 모드를 끌 수 있습니다.`,
      };
    }
    const answers = gaps.filter((gap) => gap.kind === "answer" && gap.safe_to_speak && gap.public_description);
    return answers.length
      ? { title: "검증된 정답 화면정보", text: answers.map((item) => `${formatTime(item.timestamp_ms)} ${item.public_description}`).join("\n") }
      : { title: "정답 정보 확인", text: "분석된 강의 자료에는 명시적으로 검증된 정답 정보가 없습니다. Sullivan AI는 확인되지 않은 정답을 추측하지 않습니다." };
  }

  if (normalized.includes("3줄") || normalized.includes("요약")) {
    if (mentionedConcepts.length) {
      return {
        title: `${mentionedConcepts.map((item) => item.keyword).join("·")} 주제 요약`,
        text: mentionedConcepts.slice(0, 3).map((item, index) => `${index + 1}. ${item.ai_explanation}`).join("\n"),
      };
    }
    const requestedCount = Number(normalized.match(/(\d+)줄/)?.[1]) || 3;
    const lines = summaryItems.length >= requestedCount ? summaryItems : [overview, ...conceptMap];
    return { title: `${Math.min(requestedCount, lines.length)}줄 핵심 요약`, text: lines.slice(0, requestedCount).map((item, index) => `${index + 1}. ${item}`).join("\n") };
  }

  if (normalized.includes("키워드") || normalized.includes("용어") || normalized.includes("카드")) {
    return concepts.length
      ? { title: "강사가 강조한 핵심 키워드", text: conceptLines(concepts, 20) }
      : glossary.length
        ? { title: "핵심 용어 카드", text: glossary.map((item) => `• ${item.term}: ${item.definition}`).join("\n") }
        : { title: "핵심 용어 카드", text: "현재 분석 결과에는 검증된 핵심 용어가 없습니다." };
  }

  if (normalized.includes("원인") || normalized.includes("전개") || normalized.includes("결과") || normalized.includes("영향")) {
    const cause = window.SullivanConcepts?.search(concepts, "원인") || [];
    const development = window.SullivanConcepts?.search(concepts, "전개") || [];
    const result = window.SullivanConcepts?.search(concepts, "결과") || [];
    return {
      title: "원인·전개·결과 정리",
      text: [
        `원인. ${cause.slice(0, 4).map((item) => item.ai_explanation).join(" ") || overview}`,
        `전개. ${development.slice(0, 5).map((item) => item.flow || item.ai_explanation).join(" → ") || conceptMap.slice(0, 2).join(" ")}`,
        `결과와 영향. ${result.slice(0, 4).map((item) => item.ai_explanation).join(" ") || summaryItems.at(-1) || overview}`,
      ].join("\n"),
    };
  }

  if (normalized.includes("비교") || normalized.includes("차이") || normalized.includes("공통")) {
    let compareItems = mentionedConcepts.slice(0, 2);
    if (compareItems.length < 2 && state.activeSampleId === "history") {
      compareItems = normalized.includes("북")
        ? [findConcept("history-northern-expedition"), findConcept("history-bukhak")]
        : [findConcept("history-jeongmyo"), findConcept("history-byeongja")];
    }
    if (compareItems.length < 2 && state.activeSampleId === "science") {
      compareItems = [findConcept("star-white-dwarf"), findConcept("star-neutron")];
    }
    compareItems = compareItems.filter(Boolean);
    return compareItems.length >= 2
      ? {
        title: `${compareItems[0].keyword}·${compareItems[1].keyword} 비교`,
        text: `첫째, ${compareItems[0].keyword}. ${compareItems[0].ai_explanation}\n둘째, ${compareItems[1].keyword}. ${compareItems[1].ai_explanation}\n핵심 구분. ${compareItems[0].flow || compareItems[0].keyword} / ${compareItems[1].flow || compareItems[1].keyword}`,
      }
      : { title: "개념 비교", text: "비교할 두 개념을 함께 말해 주세요. 예: 정묘호란과 병자호란 비교, 북벌론과 북학론 비교." };
  }

  if (normalized.includes("시간순") || normalized.includes("연표") || normalized.includes("흐름") || normalized.includes("순서")) {
    const ordered = concepts.filter((item) => item.flow).sort((a, b) => a.timestamp_ms - b.timestamp_ms);
    return {
      title: "강의 흐름과 시간순 정리",
      text: flowLines(mentionedConcepts.length ? mentionedConcepts : ordered) || conceptMap.map((item, index) => `${index + 1}. ${item}`).join("\n"),
    };
  }

  if (normalized.includes("복습") || normalized.includes("계획")) {
    const steps = [
      `1단계 · 전체 흐름 듣기: ${overview}`,
      `2단계 · 개념 연결 확인: ${conceptMap.slice(0, 2).join(" / ") || "개념 지도 확인"}`,
      `3단계 · 중요 장면 다시 듣기: ${(review.key_segments || []).slice(0, 3).map((item) => formatTime(item.timestamp_ms)).join(", ") || "접근성 복습 탭 확인"}`,
      `4단계 · 스스로 설명하기: ${questions[0] || "핵심 내용을 자신의 말로 설명해 보세요."}`,
    ];
    return { title: "맞춤 복습 계획", text: steps.join("\n") };
  }

  if (normalized.includes("퀴즈") || normalized.includes("문제 만들어") || normalized.includes("확인 질문")) {
    const sourceQuestions = mentionedConcepts.length
      ? mentionedConcepts.slice(0, 6).map((item) => `${item.keyword}의 뜻과 강의 흐름 속 역할을 자신의 말로 설명해 보세요.`)
      : questions;
    return sourceQuestions.length
      ? { title: "자기점검 퀴즈", text: `${sourceQuestions.map((item, index) => `${index + 1}. ${item}`).join("\n")}\n\n정답은 먼저 스스로 말한 뒤 핵심 탐색에서 해당 강사 구간을 확인하세요.` }
      : { title: "자기점검 퀴즈", text: `1. ${overview} 이 내용을 자신의 말로 설명해 보세요.` };
  }

  if (normalized.includes("발표") || normalized.includes("발표문")) {
    const presentationConcepts = (mentionedConcepts.length ? mentionedConcepts.map((item) => item.ai_explanation) : conceptMap).slice(0, normalized.includes("3분") ? 7 : 4).join(" 또한, ");
    return {
      title: normalized.includes("3분") ? "3분 발표문" : "1분 발표문",
      text: `안녕하세요. 이번 강의의 핵심 주제를 설명하겠습니다. ${overview} 핵심 내용은 다음과 같습니다. ${presentationConcepts || "강의의 핵심 요약을 중심으로 살펴볼 수 있습니다."} 이 흐름을 기억하면 개별 사건과 개념의 관계도 함께 이해할 수 있습니다. 이상으로 발표를 마치겠습니다.`,
    };
  }

  if (normalized.includes("암기") || normalized.includes("시험") || normalized.includes("표로")) {
    const items = mentionedConcepts.length ? mentionedConcepts : concepts.slice(0, 15);
    return {
      title: "시험 직전 음성 암기표",
      text: items.map((item, index) => `${index + 1}. ${item.keyword} — ${item.flow || item.ai_explanation}`).join("\n"),
    };
  }

  if (normalized.includes("개념 지도") || normalized.includes("마인드맵") || normalized.includes("연결")) {
    return conceptMap.length
      ? { title: "음성형 개념 지도", text: conceptMap.map((item, index) => `${index + 1}단계. ${item}`).join("\n") }
      : { title: "음성형 개념 지도", text: "현재 분석 결과에는 검증된 개념 연결정보가 없습니다." };
  }

  if (normalized.includes("화면") || normalized.includes("장면")) {
    const currentMs = getCurrentPlaybackMs();
    const safeGaps = gaps.filter((gap) => gap.safe_to_speak && gap.public_description);
    const nearest = [...safeGaps].sort((a, b) => Math.abs(a.timestamp_ms - currentMs) - Math.abs(b.timestamp_ms - currentMs))[0];
    return nearest
      ? { title: "현재 장면과 가까운 화면 해설", text: `${formatTime(nearest.timestamp_ms)}. ${nearest.public_description}` }
      : { title: "현재 화면 해설", text: "현재 장면에서 검증된 화면정보를 찾지 못했습니다." };
  }

  if (mentionedConcepts.length) {
    return {
      title: `${mentionedConcepts.map((item) => item.keyword).join("·")} 강의 근거 설명`,
      text: conceptLines(mentionedConcepts, 8),
    };
  }

  const matchedTerm = glossary.find((item) => normalized.includes(item.term.toLowerCase()));
  if (matchedTerm) return { title: matchedTerm.term, text: matchedTerm.definition };

  if (normalized.includes("쉽게") || normalized.includes("설명")) {
    return { title: "쉽게 풀어쓴 강의 설명", text: `${overview}\n핵심 흐름은 ${conceptMap.slice(0, 3).join(", ") || "학습 노트의 개념 지도"}입니다.` };
  }

  return {
    title: "강의 근거로 다시 요청해 주세요",
    text: `“${message}” 요청과 직접 연결된 강의 근거를 찾지 못했습니다. 키워드 하나를 포함해 다시 말해 주세요. 만들 수 있는 형식은 주제별 설명, 두 개념 비교, 시간순 흐름, 원인·전개·결과, 핵심 키워드, 암기표, 복습 계획, 퀴즈, 1분·3분 발표문, 현재 화면 해설입니다.`,
  };
}

function appendChatMessage(role, title, text) {
  const box = $("#chat-log");
  const message = document.createElement("div");
  message.className = `chat-message ${role}`;
  message.innerHTML = `<strong>${escapeHtml(title)}</strong><p>${escapeHtml(text)}</p>`;
  box.appendChild(message);
  box.scrollTop = box.scrollHeight;
}

function redactAgentText(value) {
  return String(value || "")
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[개인정보 비공개]")
    .replace(/01[016789][ -]?\d{3,4}[ -]?\d{4}/g, "[개인정보 비공개]")
    .replace(/\b\d{6}[ -]?[1-4]\d{6}\b/g, "[개인정보 비공개]");
}

function cleanAgentValue(value) {
  if (typeof value === "string") return redactAgentText(value);
  if (Array.isArray(value)) return value.map(cleanAgentValue);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, cleanAgentValue(item)]));
  }
  return value;
}

function safeSnapshotForAgent() {
  if (!state.snapshot) return null;
  const snapshot = state.snapshot;
  return {
    session: cleanAgentValue(snapshot.session),
    assets: [],
    transcript_segments: (snapshot.transcript_segments || [])
      .filter((item) => Number(item.confidence ?? 1) >= 0.72)
      .map((item) => ({ ...cleanAgentValue(item), text: redactAgentText(item.text) })),
    visual_gaps: (snapshot.visual_gaps || [])
      .filter((gap) => gap.safe_to_speak && gap.public_description && Number(gap.confidence ?? 0) >= 0.72)
      .map((gap) => ({ ...cleanAgentValue(gap), public_description: redactAgentText(gap.public_description), source_text: null })),
    passage: snapshot.passage ? cleanAgentValue(snapshot.passage) : null,
    review: cleanAgentValue(snapshot.review),
    study_guide: cleanAgentValue(snapshot.study_guide || {}),
    active_mode: snapshot.active_mode,
    safe_description_count: snapshot.safe_description_count || 0,
    held_count: snapshot.held_count || 0,
  };
}

async function requestAgentTurn(message) {
  return api(`/v1/lectures/${state.session.session_id}/agent-turn`, {
    method: "POST",
    body: JSON.stringify({
      message,
      current_time_ms: getCurrentPlaybackMs(),
      snapshot: (state.isSample || state.currentSavedLectureId) ? safeSnapshotForAgent() : null,
      access_code: state.demoAccessCode || null,
      analysis_consent: $("#local-video-ai-consent input").checked,
    }),
  });
}

function nearestSafeGap(timestampMs) {
  const gaps = state.snapshot?.visual_gaps?.filter((gap) => gap.safe_to_speak && gap.public_description) || [];
  return [...gaps].sort((a, b) => Math.abs(a.timestamp_ms - timestampMs) - Math.abs(b.timestamp_ms - timestampMs))[0] || null;
}

function executeAgentAction(result, userMessage, { forceSpeak = false } = {}) {
  const shouldSpeak = forceSpeak || $("#auto-speak-chat").checked || /읽어|말해|음성|설명/.test(userMessage);
  if (result.action === "pause") {
    stopAllPlaybackAndSpeech({ announceStop: false });
    announce(result.response_text);
    return;
  }
  if (result.action === "seek" && Number.isFinite(result.target_timestamp_ms)) {
    seekTo(result.target_timestamp_ms);
    announce(`${formatTime(result.target_timestamp_ms)} 구간으로 이동했습니다.`);
  }
  if (result.action === "describe_current") {
    const gap = nearestSafeGap(result.target_timestamp_ms ?? getCurrentPlaybackMs());
    if (gap) {
      narrateGap(gap, { pauseForDescription: true });
      return;
    }
  }
  if (result.action === "replay_paragraph") {
    const indices = new Set(result.paragraph_indices || []);
    const paragraphs = getParagraphs().filter((paragraph) => indices.has(paragraph.paragraph_index));
    if (paragraphs.length) {
      replayParagraphs(paragraphs);
      return;
    }
  }
  if (result.action === "read_summary" || shouldSpeak) {
    speakWithPlaybackPause(`${result.title}. ${result.response_text}`, "에이전트 안내 후 자동 재생");
  }
}

async function submitChatMessage(message, { forceSpeak = false } = {}) {
  const value = String(message || "").trim();
  if (!value || !state.snapshot || state.agentTurnPending) return;
  appendChatMessage("user", "나", value);
  state.agentTurnPending = true;
  $("#chat-status").textContent = "강의 상태를 관찰하고 다음 행동을 판단하는 중입니다.";
  try {
    const agentResult = await requestAgentTurn(value);
    const result = { title: agentResult.title, text: agentResult.response_text };
    appendChatMessage("assistant", `Gemini Agent · ${result.title}`, `${result.text}\n\n선택 행동: ${agentResult.action}\n판단 근거: ${agentResult.decision_reason}`);
    state.lastChatOutput = result;
    $("#agent-model-status").textContent = "Gemini 행동 에이전트 · 강의 근거로 판단 후 설리번 안전 계층이 실행";
    $("#chat-status").textContent = `${result.title} · ${agentResult.action} 실행 완료`;
    executeAgentAction(agentResult, value, { forceSpeak });
    announce(`${result.title} 결과와 행동을 실행했습니다.`);
  } catch (error) {
    const result = generateLearningResponse(value);
    appendChatMessage("assistant", `Sullivan 로컬 보조 · ${result.title}`, result.text);
    state.lastChatOutput = result;
    $("#agent-model-status").textContent = "로컬 보조 모드 · Gemini 연결 시 행동 에이전트 추론 활성화";
    $("#chat-status").textContent = `${result.title} 생성 완료 · ${error.message}`;
    announce(`${result.title} 결과를 로컬 보조 모드로 생성했습니다.`);
    if (forceSpeak || $("#auto-speak-chat").checked || /읽어|말해|음성/.test(value)) {
      speakWithPlaybackPause(`${result.title}. ${result.text}`, "로컬 보조 응답 후 자동 재생");
    }
  } finally {
    state.agentTurnPending = false;
    $("#save-chat-output").disabled = !state.lastChatOutput;
  }
}

$("#chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = $("#chat-input");
  submitChatMessage(input.value);
  input.value = "";
});

$$('[data-chat-prompt]').forEach((button) => button.addEventListener("click", () => submitChatMessage(button.dataset.chatPrompt)));

$("#chat-voice").addEventListener("click", () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) return alert("이 브라우저에서는 음성 인식을 지원하지 않습니다. 요청을 직접 입력해 주세요.");
  const recognition = new Recognition();
  recognition.lang = "ko-KR";
  recognition.interimResults = false;
  $("#chat-voice").classList.add("listening");
  $("#chat-status").textContent = "요청을 듣고 있습니다. 말씀해 주세요.";
  announce("AI 학습 요청을 듣고 있습니다.");
  recognition.onresult = (event) => {
    const message = event.results[0][0].transcript;
    $("#chat-input").value = message;
    submitChatMessage(message);
    $("#chat-input").value = "";
  };
  recognition.onerror = () => { $("#chat-status").textContent = "음성을 인식하지 못했습니다. 다시 시도해 주세요."; };
  recognition.onend = () => $("#chat-voice").classList.remove("listening");
  recognition.start();
});

$("#save-chat-output").addEventListener("click", () => {
  if (!state.lastChatOutput) return;
  const content = `# ${state.lastChatOutput.title}\n\n${state.lastChatOutput.text}\n\n---\nSullivan AI 강의 기반 학습 결과물`;
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "sullivan-ai-generated-output.md";
  link.click();
  URL.revokeObjectURL(url);
  announce("마지막 학습 결과물을 Markdown 파일로 저장했습니다.");
});

function renderEvidence() {
  const gaps = state.snapshot.visual_gaps;
  const box = $("#evidence-list");
  if (!gaps.length) { box.className = "evidence-list empty-state"; box.textContent = "아직 판단 기록이 없습니다."; return; }
  box.className = "evidence-list";
  box.innerHTML = gaps.map((gap) => `<article class="evidence-row ${gap.action.toLowerCase()}"><div class="decision"><span>${formatTime(gap.timestamp_ms)}</span><strong>${gap.action}</strong></div><div><h3>${gap.safe_to_speak ? escapeHtml(gap.public_description || "자동 해설 생략") : "내용 비공개 · 안전 보류"}</h3><p>${escapeHtml(gap.reason)}</p><small>화면 확신도 ${Math.round(gap.confidence * 100)}% · 중요도 ${Math.round(gap.importance * 100)}% · 발화 중복 ${Math.round(gap.spoken_overlap * 100)}%</small></div></article>`).join("");
}

function seekTo(milliseconds) {
  const video = $("#lecture-video");
  state.lastPlaybackMs = Math.max(0, milliseconds - 700);
  if (state.linkedPlaybackKind === "youtube") {
    state.youtubePlayer?.seekTo?.(Math.max(0, milliseconds / 1000), true);
    return;
  }
  if (!video.getAttribute("src") || !Number.isFinite(video.duration)) return;
  video.currentTime = Math.min(video.duration, Math.max(0, milliseconds / 1000));
}

function seekRelative(deltaMs) {
  seekTo(Math.max(0, getCurrentPlaybackMs() + deltaMs));
  announce(`${deltaMs < 0 ? "뒤로" : "앞으로"} ${Math.abs(deltaMs) / 1000}초 이동했습니다.`);
}

function speakWithPlaybackPause(text, overlayLabel = "음성 안내 후 자동 재생") {
  if (!text) return;
  const wasPlaying = isPlaybackRunning();
  if (wasPlaying) pausePlayback();
  state.resumeAfterSpeech = wasPlaying || state.resumeAfterSpeech;
  $("#pause-overlay-label").textContent = overlayLabel;
  $("#pause-overlay").classList.toggle("hidden", !wasPlaying);
  speak(text, () => {
    $("#pause-overlay").classList.add("hidden");
    if (state.resumeAfterSpeech) resumePlayback();
    state.resumeAfterSpeech = false;
  });
}

function voiceScore(voice) {
  const lang = String(voice.lang || "").toLowerCase();
  const name = String(voice.name || "").toLowerCase();
  let score = lang === "ko-kr" ? 200 : lang.startsWith("ko") ? 150 : 0;
  if (/natural|neural|online/.test(name)) score += 80;
  if (/sunhi|선히/.test(name)) score += 65;
  if (/google.*한국|google.*korean/.test(name)) score += 55;
  if (/yuna|유나/.test(name)) score += 45;
  if (/heami|혜미/.test(name)) score += 35;
  if (voice.localService) score += 5;
  return score;
}

function koreanVoices() {
  if (!("speechSynthesis" in window)) return [];
  return window.speechSynthesis.getVoices()
    .filter((voice) => String(voice.lang || "").toLowerCase().startsWith("ko"))
    .sort((a, b) => voiceScore(b) - voiceScore(a));
}

function refreshVoiceOptions() {
  const select = $("#speech-voice");
  if (!select) return;
  const selected = select.value;
  const voices = koreanVoices();
  select.innerHTML = '<option value="auto">사람에 가까운 음성 자동 선택</option>' + voices.map((voice) => (
    `<option value="${escapeHtml(voice.voiceURI)}">${escapeHtml(voice.name)}</option>`
  )).join("");
  if ([...select.options].some((option) => option.value === selected)) select.value = selected;
  select.disabled = voices.length === 0;
}

function selectedKoreanVoice() {
  const voices = koreanVoices();
  const selected = $("#speech-voice")?.value;
  if (selected && selected !== "auto") {
    return voices.find((voice) => voice.voiceURI === selected) || voices[0] || null;
  }
  return voices[0] || null;
}

function prepareSpeechText(text) {
  return String(text || "")
    .replace(/H\s*-\s*R/gi, "에이치 알")
    .replace(/\bTTS\b/gi, "티 티 에스")
    .replace(/\bAI\b/gi, "에이 아이")
    .replace(/1592년/g, "천오백구십이 년")
    .replace(/1597년/g, "천오백구십칠 년")
    .replace(/1598년/g, "천오백구십팔 년")
    .replace(/정명가도/g, "정명 가도")
    .replace(/친명배금/g, "친명 배금")
    .replace(/H-R도/gi, "에이치 알 도")
    .replace(/^\s*1[.)]\s*/gm, "첫째, ")
    .replace(/^\s*2[.)]\s*/gm, "둘째, ")
    .replace(/^\s*3[.)]\s*/gm, "셋째, ")
    .replace(/^\s*4[.)]\s*/gm, "넷째, ")
    .replace(/[→⇒]/g, ", 다음으로, ")
    .replace(/[•·]/g, ", ")
    .replace(/\s*\/\s*/g, " 또는 ")
    .replace(/\n+/g, ". ")
    .replace(/\s+/g, " ")
    .replace(/\.{2,}/g, ".")
    .trim();
}

function speechChunks(text, maxLength = 82) {
  const sentences = prepareSpeechText(text).match(/[^.!?]+[.!?]?/g) || [];
  const chunks = [];
  sentences.forEach((sentence) => {
    const clean = sentence.trim();
    if (clean.length <= maxLength) {
      if (clean) chunks.push(clean);
      return;
    }
    let current = "";
    clean.split(/(?<=,)/).forEach((part) => {
      if (current && `${current} ${part}`.length > maxLength) {
        chunks.push(current.trim());
        current = part;
      } else {
        current = `${current} ${part}`.trim();
      }
    });
    if (current) chunks.push(current.trim());
  });
  return chunks;
}

function speak(text, onEnd) {
  if (!text) return;
  if (!("speechSynthesis" in window)) {
    announce(text);
    if (onEnd) onEnd();
    return;
  }
  state.speechToken += 1;
  const token = state.speechToken;
  state.speechInProgress = true;
  window.speechSynthesis.cancel();
  refreshVoiceOptions();
  const chunks = speechChunks(text);
  const voice = selectedKoreanVoice();
  const baseRate = Number($("#speech-rate").value) || 0.95;
  const basePitch = Number($("#speech-pitch")?.value) || 1;
  const volume = Number($("#speech-volume")?.value) || 0.9;
  const style = $("#speech-style")?.value || "warm";
  const styleProfile = {
    warm: { rate: 1, pitch: 0.99 },
    calm: { rate: 0.94, pitch: 0.98 },
    clear: { rate: 1.02, pitch: 1.01 },
  }[style] || { rate: 1, pitch: 1 };
  const rate = Math.max(0.75, Math.min(1.25, baseRate * styleProfile.rate));
  const pitch = Math.max(0.8, Math.min(1.2, basePitch * styleProfile.pitch));
  let index = 0;
  let finished = false;
  const watchdog = window.setTimeout(() => finish(), Math.min(120_000, Math.max(12_000, prepareSpeechText(text).length * 260)));

  function finish() {
    if (finished || token !== state.speechToken) return;
    finished = true;
    window.clearTimeout(watchdog);
    state.speechInProgress = false;
    if (onEnd) onEnd();
  }

  function speakNext() {
    if (token !== state.speechToken) return;
    if (index >= chunks.length) {
      finish();
      return;
    }
    const chunkIndex = index;
    const chunk = chunks[index];
    const utterance = new SpeechSynthesisUtterance(chunk);
    index += 1;
    utterance.lang = "ko-KR";
    const isOpening = chunkIndex === 0 && chunks.length > 1;
    const isClosing = chunkIndex === chunks.length - 1 && chunks.length > 1;
    utterance.rate = Math.max(0.75, Math.min(1.25, rate * (isOpening ? 0.98 : isClosing ? 0.97 : 1)));
    utterance.pitch = Math.max(0.8, Math.min(1.2, pitch * (isClosing ? 0.98 : 1)));
    utterance.volume = volume;
    if (voice) utterance.voice = voice;
    utterance.onend = () => window.setTimeout(speakNext, /[.!?]$/.test(chunk) ? 130 : 70);
    utterance.onerror = () => window.setTimeout(speakNext, 60);
    window.speechSynthesis.speak(utterance);
  }

  if (!chunks.length) finish();
  else {
    // Chromium occasionally drops an utterance that is queued in the same tick
    // as speechSynthesis.cancel(). Give the engine a moment to settle first.
    window.speechSynthesis.resume?.();
    window.setTimeout(speakNext, 100);
  }
}

if ("speechSynthesis" in window) {
  refreshVoiceOptions();
  window.speechSynthesis.addEventListener?.("voiceschanged", refreshVoiceOptions);
}

$("#preview-voice").addEventListener("click", () => {
  speakWithPlaybackPause(
    "안녕하세요. 지금 강의의 흐름을 따라가고 있습니다. 화면에서 꼭 필요한 정보만 짧게 설명한 뒤, 다시 강의로 이어갈게요.",
    "음성 미리 듣기 후 자동 재생",
  );
});

function stopAllPlaybackAndSpeech({ announceStop = true } = {}) {
  const stoppedConceptSequence = state.conceptSequenceActive;
  state.conceptSequenceToken += 1;
  state.conceptSequenceActive = false;
  window.clearInterval(state.conceptSequenceTimer);
  state.conceptSequenceTimer = null;
  state.speechToken += 1;
  state.speechInProgress = false;
  window.speechSynthesis?.cancel();
  pausePlayback();
  $("#pause-overlay").classList.add("hidden");
  state.resumeAfterSpeech = false;
  updateAutoNarrationStatus(getCurrentPlaybackMs());
  if (stoppedConceptSequence) $("#navigation-answer").textContent = "강사 구간과 AI 재설명을 사용자가 중지했습니다. 다시 들으려면 말하기를 누르세요.";
  if (announceStop) announce("영상과 음성 재생을 모두 멈췄습니다.");
}

$("#stop-speech").addEventListener("click", () => stopAllPlaybackAndSpeech());

$$('.nav-button').forEach((button) => button.addEventListener("click", () => {
  $$('.nav-button').forEach((item) => item.classList.toggle("active", item === button));
  $$('.view-panel').forEach((panel) => panel.classList.toggle("hidden", panel.id !== button.dataset.panel));
  $(`#${button.dataset.panel}`).querySelector("h2")?.focus();
}));

const SPACE_COMMAND_GUIDE = "사용할 수 있는 명령은 영상 시작, 영상 멈춤, 현재 화면 해설, 요약 듣기, 핵심 탐색, 문단 다시 듣기, 샘플 1 또는 2, 저장하고 홈으로, 홈으로 돌아가기, 자유 모드입니다. 말하기 어려울 때는 스페이스 키를 빠르게 세 번 눌러 텍스트 명령을 입력할 수 있습니다. 안내를 건너뛰려면 스페이스 키를 다시 길게 누르세요.";

function isEditableSpaceTarget(target) {
  return target instanceof HTMLTextAreaElement
    || (target instanceof HTMLInputElement && ["", "text", "search"].includes(target.type))
    || Boolean(target?.isContentEditable);
}

function restoreGlobalSpaceFocus() {
  window.setTimeout(() => {
    if (document.activeElement?.tagName === "IFRAME") {
      $("#space-command-focus")?.focus({ preventScroll: true });
    }
  }, 0);
}

function updateSpaceVoiceOverlay(active, title = "음성 명령 듣는 중", message = "스페이스 키를 떼면 명령을 실행합니다.") {
  const overlay = $("#space-voice-overlay");
  $("#space-voice-title").textContent = title;
  $("#space-voice-text").textContent = message;
  overlay.classList.toggle("hidden", !active);
}

function prepareSpaceVoiceAudio() {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return null;
  if (!state.spaceVoice.audioContext) state.spaceVoice.audioContext = new AudioContext();
  state.spaceVoice.audioContext.resume?.().catch(() => {});
  return state.spaceVoice.audioContext;
}

function playSpaceVoiceReadyChime() {
  const context = prepareSpaceVoiceAudio();
  if (!context) return;
  const start = context.currentTime + 0.01;
  [880, 1320].forEach((frequency, index) => {
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    const begin = start + index * 0.09;
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(frequency, begin);
    gain.gain.setValueAtTime(0.0001, begin);
    gain.gain.exponentialRampToValueAtTime(0.2, begin + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, begin + 0.08);
    oscillator.connect(gain).connect(context.destination);
    oscillator.start(begin);
    oscillator.stop(begin + 0.09);
  });
}

function insertShortSpace(target) {
  if (target instanceof HTMLTextAreaElement || (target instanceof HTMLInputElement && ["", "text", "search"].includes(target.type))) {
    const start = target.selectionStart ?? target.value.length;
    const end = target.selectionEnd ?? start;
    target.setRangeText(" ", start, end, "end");
    target.dispatchEvent(new Event("input", { bubbles: true }));
    return;
  }
  if (target?.isContentEditable) {
    document.execCommand?.("insertText", false, " ");
    return;
  }
  if (target instanceof HTMLButtonElement || target instanceof HTMLAnchorElement || (target instanceof HTMLInputElement && ["button", "submit", "checkbox", "radio"].includes(target.type))) {
    target.click();
    return;
  }
  if (target instanceof HTMLSelectElement) {
    if (typeof target.showPicker === "function") target.showPicker();
    else target.focus();
    return;
  }
  if (state.snapshot && !$("#agent-view").classList.contains("hidden")) return;
  window.scrollBy({ top: Math.max(240, window.innerHeight * 0.78), behavior: "smooth" });
}

function openVoicePanel(panelId) {
  const button = $(`.nav-button[data-panel="${panelId}"]`);
  if (!button) return false;
  button.click();
  return true;
}

function visibleVoiceButton(label) {
  const normalized = window.SullivanVoiceCommands?.normalize(label) || String(label || "").trim();
  if (!normalized) return null;
  const candidates = $$('button:not([disabled]), a[href], input[type="submit"]')
    .filter((element) => !element.closest(".hidden") && element.getClientRects().length > 0)
    .map((element) => {
      const elementLabel = window.SullivanVoiceCommands?.normalize(
        element.getAttribute("aria-label") || element.textContent || element.value || "",
      ) || "";
      let score = 0;
      if (elementLabel === normalized) score = 100;
      else if (elementLabel.includes(normalized)) score = 70 + normalized.length;
      else if (normalized.includes(elementLabel) && elementLabel.length >= 2) score = 50 + elementLabel.length;
      return { element, score };
    })
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score);
  return candidates[0]?.element || null;
}

function isTextCommandDialogTarget(target) {
  return Boolean(target?.closest?.("#text-command-dialog"));
}

function stopVoiceForTextCommand() {
  window.clearTimeout(state.spaceVoice.holdTimer);
  window.clearTimeout(state.spaceVoice.guideSkipTimer);
  window.clearTimeout(state.spaceVoice.recognitionRestartTimer);
  const recognition = state.spaceVoice.recognition;
  if (recognition) {
    recognition.onresult = null;
    recognition.onerror = null;
    recognition.onend = null;
    try { recognition.abort(); } catch { /* already stopped */ }
  }
  state.speechToken += 1;
  state.speechInProgress = false;
  state.resumeAfterSpeech = false;
  window.speechSynthesis?.cancel();
  updateSpaceVoiceOverlay(false);
  resetSpaceVoiceGesture();
}

function openTextCommandDialog() {
  stopVoiceForTextCommand();
  const dialog = $("#text-command-dialog");
  const input = $("#text-command-input");
  dialog.classList.remove("hidden");
  input.value = "";
  $("#text-command-status").textContent = "명령을 입력하고 Enter를 누르세요. Esc를 누르면 닫습니다.";
  window.setTimeout(() => input.focus({ preventScroll: true }), 0);
  announce("텍스트 명령 입력창을 열었습니다. 바로 입력하고 엔터를 누르세요.");
}

function closeTextCommandDialog({ restoreFocus = true } = {}) {
  $("#text-command-dialog").classList.add("hidden");
  if (restoreFocus) $("#space-command-focus")?.focus({ preventScroll: true });
}

function updateFreeControlModeUi() {
  document.body.classList.toggle("free-control-mode", state.freeControlMode);
  $("#free-mode-indicator").classList.toggle("hidden", !state.freeControlMode);
  $("#space-command-hint").textContent = state.freeControlMode
    ? "한 번: 재생·정지 · 두 번: 자유 모드 종료"
    : "길게: 음성 · 세 번: 텍스트 · 두 번: 중지";
}

function enterFreeControlMode({ resume = false } = {}) {
  window.clearTimeout(state.spaceVoice.shortTapTimer);
  state.spaceVoice.shortTapTimer = null;
  state.spaceVoice.shortTapCount = 0;
  state.spaceVoice.lastShortTapAt = 0;
  state.freeControlMode = true;
  updateFreeControlModeUi();
  if (resume) resumePlayback();
  announce("자유 모드입니다. 마우스 클릭과 화면의 모든 버튼을 직접 사용할 수 있습니다. 스페이스 한 번은 재생과 일시정지, 좌우 화살표는 10초 이동, 스페이스 두 번은 자유 모드 종료입니다.");
}

function exitFreeControlMode({ announceExit = true } = {}) {
  window.clearTimeout(state.freeSpaceTapTimer);
  state.freeSpaceTapTimer = null;
  state.freeSpaceTapAt = 0;
  state.freeControlMode = false;
  updateFreeControlModeUi();
  if (announceExit) announce("자유 모드를 종료하고 에이전트 명령 모드로 돌아왔습니다.");
}

function toggleFreeModePlayback() {
  if (!state.snapshot || $("#agent-view").classList.contains("hidden")) {
    announce("현재 재생할 강의가 없습니다.");
    return;
  }
  if (isPlaybackRunning()) {
    pausePlayback();
    announce("강의를 일시정지했습니다.");
  } else {
    resumePlayback();
    announce("강의를 재생합니다.");
  }
}

function handleFreeModeSpaceTap() {
  const now = performance.now();
  const isSecondTap = window.SullivanVoiceCommands?.isDoubleTap(state.freeSpaceTapAt, now, 650);
  if (isSecondTap) {
    window.clearTimeout(state.freeSpaceTapTimer);
    state.freeSpaceTapTimer = null;
    state.freeSpaceTapAt = 0;
    exitFreeControlMode();
    return;
  }
  state.freeSpaceTapAt = now;
  window.clearTimeout(state.freeSpaceTapTimer);
  state.freeSpaceTapTimer = window.setTimeout(() => {
    state.freeSpaceTapAt = 0;
    state.freeSpaceTapTimer = null;
    const action = window.SullivanVoiceCommands?.classifyTapSequence(1, { freeMode: true });
    if (action === "toggle_playback") toggleFreeModePlayback();
  }, 650);
}

$("#close-text-command").addEventListener("click", () => closeTextCommandDialog());
$("#text-command-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const command = $("#text-command-input").value.trim();
  if (!command) {
    $("#text-command-status").textContent = "명령을 한 글자 이상 입력해 주세요.";
    $("#text-command-input").focus();
    return;
  }
  const wasPlaying = isPlaybackRunning();
  closeTextCommandDialog();
  executeGlobalVoiceCommand(command, wasPlaying, { source: "text" }).catch((error) => {
    announce(`텍스트 명령을 실행하지 못했습니다. ${error.message}`);
  });
});
$("#text-command-dialog").addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  event.preventDefault();
  event.stopPropagation();
  closeTextCommandDialog();
});

async function executeGlobalVoiceCommand(command, wasPlaying = false, { source = "voice" } = {}) {
  const intent = window.SullivanVoiceCommands?.classify(command) || { type: "chat", command };
  const resumeWithoutSpeech = () => {
    if (wasPlaying) window.setTimeout(() => {
      if (!state.speechInProgress && !state.conceptSequenceActive) resumePlayback();
    }, 120);
  };
  announce(`${source === "text" ? "텍스트" : "음성"} 명령을 실행합니다. ${command}`);

  if (intent.type === "free_mode") {
    enterFreeControlMode({ resume: wasPlaying });
    return;
  }

  if (intent.type === "pause") {
    stopAllPlaybackAndSpeech();
    return;
  }
  if (intent.type === "play") {
    resumePlayback();
    announce("강의를 재생합니다.");
    return;
  }
  if (intent.type === "sample") {
    await openSampleSession(intent.sampleId);
    return;
  }
  if (intent.type === "save_home") {
    await saveCurrentLectureAndReturnHome();
    return;
  }
  if (intent.type === "home") {
    if (!$("#agent-view").classList.contains("hidden")) {
      announce("저장하지 않고 홈 화면으로 돌아갑니다.");
      returnHome();
    }
    else announce("현재 홈 화면입니다.");
    return;
  }
  if (intent.type === "auto_narration") {
    const toggle = $("#auto-narration");
    if (toggle.checked !== intent.enabled) {
      toggle.checked = intent.enabled;
      toggle.dispatchEvent(new Event("change", { bubbles: true }));
    }
    resumeWithoutSpeech();
    return;
  }
  if (intent.type === "describe" && state.snapshot) {
    state.resumeAfterSpeech = wasPlaying || state.resumeAfterSpeech;
    $("#describe-now").click();
    return;
  }
  if (intent.type === "summary_audio" && state.snapshot) {
    state.resumeAfterSpeech = wasPlaying || state.resumeAfterSpeech;
    readSummaryGuide();
    return;
  }
  if (intent.type === "summary_audio" || intent.type === "saved") {
    await runSavedLectureCommand(intent.command || "최근 강의 요약 들려줘");
    return;
  }
  if (intent.type === "panel" && state.snapshot) {
    openVoicePanel(intent.panelId);
    resumeWithoutSpeech();
    return;
  }
  if (intent.type === "paragraph" && state.snapshot) {
    openVoicePanel("passage-panel");
    state.resumeAfterSpeech = wasPlaying || state.resumeAfterSpeech;
    runParagraphCommand(intent.command);
    return;
  }
  if (intent.type === "concept" && state.snapshot) {
    openVoicePanel("passage-panel");
    $("#navigation-command").value = intent.command;
    $("#navigation-form").requestSubmit();
    resumeWithoutSpeech();
    return;
  }
  if (intent.type === "button") {
    const button = visibleVoiceButton(intent.label);
    if (button) {
      state.resumeAfterSpeech = wasPlaying || state.resumeAfterSpeech;
      button.click();
      window.setTimeout(() => {
        if (wasPlaying && !state.speechInProgress && !state.conceptSequenceActive && state.resumeAfterSpeech) {
          state.resumeAfterSpeech = false;
          resumePlayback();
        }
      }, 180);
      return;
    }
  }
  if (state.snapshot) {
    openVoicePanel("chat-panel");
    state.resumeAfterSpeech = wasPlaying || state.resumeAfterSpeech;
    await submitChatMessage(intent.command || command, { forceSpeak: true });
    return;
  }
  await runSavedLectureCommand(command);
}

function resetSpaceVoiceGesture() {
  window.clearTimeout(state.spaceVoice.holdTimer);
  window.clearTimeout(state.spaceVoice.guideSkipTimer);
  window.clearTimeout(state.spaceVoice.recognitionRestartTimer);
  state.spaceVoice.holdTimer = null;
  state.spaceVoice.guideSkipTimer = null;
  state.spaceVoice.recognitionRestartTimer = null;
  state.spaceVoice.target = null;
  state.spaceVoice.activated = false;
  state.spaceVoice.released = false;
  state.spaceVoice.finalized = false;
  state.spaceVoice.recognition = null;
  state.spaceVoice.transcript = "";
  state.spaceVoice.error = "";
  state.spaceVoice.wasPlaying = false;
  state.spaceVoice.keyHeld = false;
  state.spaceVoice.guidePlaying = false;
  state.spaceVoice.pressStartedAt = 0;
  state.spaceVoice.guideCancelTap = false;
  state.spaceVoice.recognitionFatal = false;
}

function cancelVoiceGuidanceAndResume() {
  window.clearTimeout(state.spaceVoice.holdTimer);
  window.clearTimeout(state.spaceVoice.shortTapTimer);
  window.clearTimeout(state.spaceVoice.guideSkipTimer);
  window.clearTimeout(state.spaceVoice.recognitionRestartTimer);
  state.spaceVoice.holdTimer = null;
  state.spaceVoice.shortTapTimer = null;
  state.spaceVoice.lastShortTapAt = 0;
  state.spaceVoice.shortTapCount = 0;
  state.spaceVoice.skipGuideNextHold = false;
  state.spaceVoice.finalized = true;
  const recognition = state.spaceVoice.recognition;
  if (recognition) {
    recognition.onresult = null;
    recognition.onerror = null;
    recognition.onend = null;
    try { recognition.abort(); } catch { /* already stopped */ }
  }
  state.speechToken += 1;
  state.speechInProgress = false;
  state.resumeAfterSpeech = false;
  window.speechSynthesis?.cancel();
  $("#pause-overlay")?.classList.add("hidden");
  updateSpaceVoiceOverlay(false);
  resetSpaceVoiceGesture();
  if (state.snapshot) resumePlayback();
  announce("음성 안내를 멈추고 강의로 돌아갑니다.");
}

function handleQuickSpaceTap(target) {
  const now = performance.now();
  const continuesSequence = window.SullivanVoiceCommands?.isDoubleTap(
    state.spaceVoice.lastShortTapAt,
    now,
    650,
  );
  state.spaceVoice.shortTapCount = continuesSequence ? state.spaceVoice.shortTapCount + 1 : 1;
  state.spaceVoice.lastShortTapAt = now;
  window.clearTimeout(state.spaceVoice.shortTapTimer);

  const immediateAction = window.SullivanVoiceCommands?.classifyTapSequence(state.spaceVoice.shortTapCount);
  if (immediateAction === "open_text_command") {
    state.spaceVoice.shortTapTimer = null;
    state.spaceVoice.lastShortTapAt = 0;
    state.spaceVoice.shortTapCount = 0;
    openTextCommandDialog();
    return;
  }

  state.spaceVoice.shortTapTimer = window.setTimeout(() => {
    const tapCount = state.spaceVoice.shortTapCount;
    const action = window.SullivanVoiceCommands?.classifyTapSequence(tapCount);
    state.spaceVoice.lastShortTapAt = 0;
    state.spaceVoice.shortTapCount = 0;
    state.spaceVoice.shortTapTimer = null;
    if (action === "cancel_guidance") {
      cancelVoiceGuidanceAndResume();
      return;
    }
    if (target) insertShortSpace(target);
  }, 650);
}

function finishSpaceVoiceGesture() {
  if (state.spaceVoice.finalized) return;
  state.spaceVoice.finalized = true;
  const command = state.spaceVoice.transcript.trim();
  const error = state.spaceVoice.error;
  const wasPlaying = state.spaceVoice.wasPlaying;
  updateSpaceVoiceOverlay(false);
  window.setTimeout(resetSpaceVoiceGesture, 0);
  if (command) {
    executeGlobalVoiceCommand(command, wasPlaying).catch((executionError) => {
      announce(`음성 명령을 실행하지 못했습니다. ${executionError.message}`);
      if (wasPlaying) resumePlayback();
    });
  } else {
    announce(error || "인식된 음성 명령이 없습니다. 다시 스페이스 키를 2초간 눌러 주세요.");
    if (wasPlaying) resumePlayback();
  }
}

function startSpaceRecognitionEngine() {
  if (!state.spaceVoice.activated
    || state.spaceVoice.finalized
    || state.spaceVoice.released
    || !state.spaceVoice.keyHeld
    || state.spaceVoice.recognitionFatal) return;
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    state.spaceVoice.error = "이 브라우저는 음성 인식을 지원하지 않습니다. Chrome 또는 Edge에서 실행해 주세요.";
    state.spaceVoice.recognitionFatal = true;
    updateSpaceVoiceOverlay(true, "음성 인식 지원 필요", state.spaceVoice.error);
    return;
  }
  const previousTranscript = state.spaceVoice.transcript.trim();
  const recognition = new Recognition();
  state.spaceVoice.recognition = recognition;
  recognition.lang = "ko-KR";
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.onstart = () => {
    if (state.spaceVoice.recognition !== recognition) return;
    state.spaceVoice.error = "";
    updateSpaceVoiceOverlay(
      true,
      "마이크 켜짐 · 음성 명령 듣는 중",
      state.spaceVoice.transcript || "누르고 있는 동안 말씀하세요. 스페이스 키를 떼면 실행합니다.",
    );
  };
  recognition.onresult = (event) => {
    if (state.spaceVoice.recognition !== recognition) return;
    const currentTranscript = [...event.results]
      .map((result) => result[0]?.transcript || "")
      .join(" ")
      .replace(/\s+/g, " ")
      .trim();
    state.spaceVoice.transcript = [previousTranscript, currentTranscript].filter(Boolean).join(" ").trim();
    updateSpaceVoiceOverlay(true, "음성 명령 듣는 중", state.spaceVoice.transcript || "말씀해 주세요. 키를 떼면 실행합니다.");
  };
  recognition.onerror = (event) => {
    if (state.spaceVoice.recognition !== recognition) return;
    const fatalErrors = ["not-allowed", "service-not-allowed", "audio-capture"];
    state.spaceVoice.recognitionFatal = fatalErrors.includes(event.error);
    if (event.error === "no-speech" || event.error === "aborted") {
      state.spaceVoice.error = "";
      updateSpaceVoiceOverlay(true, "계속 듣는 중", "아직 음성이 들리지 않았습니다. 누른 채로 말씀해 주세요.");
      return;
    }
    const errorMessages = {
      "not-allowed": "마이크 권한이 필요합니다. 브라우저 주소창에서 마이크를 허용해 주세요.",
      "service-not-allowed": "브라우저의 음성 인식 권한이 차단되어 있습니다. 사이트 권한에서 마이크를 허용해 주세요.",
      "audio-capture": "사용할 수 있는 마이크를 찾지 못했습니다. 노트북 마이크 설정을 확인해 주세요.",
      network: "음성 인식 서비스 연결이 잠시 끊겼습니다. 누르고 있으면 다시 연결합니다.",
    };
    state.spaceVoice.error = errorMessages[event.error] || "음성을 인식하지 못했습니다. 누르고 있으면 다시 시도합니다.";
    updateSpaceVoiceOverlay(true, "음성 인식 확인", state.spaceVoice.error);
  };
  recognition.onend = () => {
    if (state.spaceVoice.recognition !== recognition) return;
    state.spaceVoice.recognition = null;
    if (!state.spaceVoice.activated || state.spaceVoice.finalized) return;
    if (state.spaceVoice.released || !state.spaceVoice.keyHeld) {
      finishSpaceVoiceGesture();
      return;
    }
    if (state.spaceVoice.recognitionFatal) {
      updateSpaceVoiceOverlay(true, "마이크 확인 필요", `${state.spaceVoice.error} 스페이스 키를 떼면 종료합니다.`);
      return;
    }
    updateSpaceVoiceOverlay(
      true,
      "음성 입력 유지 중",
      state.spaceVoice.transcript ? `${state.spaceVoice.transcript} · 계속 말씀할 수 있습니다.` : "마이크를 다시 연결하고 있습니다.",
    );
    window.clearTimeout(state.spaceVoice.recognitionRestartTimer);
    state.spaceVoice.recognitionRestartTimer = window.setTimeout(startSpaceRecognitionEngine, 180);
  };
  try {
    recognition.start();
  } catch {
    state.spaceVoice.error = "음성 인식을 시작하지 못했습니다. 마이크 권한을 확인해 주세요.";
    state.spaceVoice.recognitionFatal = true;
    state.spaceVoice.recognition = null;
    updateSpaceVoiceOverlay(true, "마이크 확인 필요", state.spaceVoice.error);
  }
}

function beginSpaceVoiceRecognition() {
  if (!state.spaceVoice.keyHeld || state.spaceVoice.released || state.spaceVoice.finalized) {
    finishSpaceVoiceGesture();
    return;
  }
  state.spaceVoice.recognitionFatal = false;
  playSpaceVoiceReadyChime();
  updateSpaceVoiceOverlay(true, "음성 명령 듣는 중", "두 번째 띠링이 울렸습니다. 누르고 있는 동안 말씀한 뒤 스페이스 키를 떼세요.");
  announce("띠링. 음성 명령을 듣고 있습니다. 말씀한 뒤 스페이스 키를 떼세요.");
  startSpaceRecognitionEngine();
}

function skipGuideAndBeginListening() {
  if (!state.spaceVoice.activated
    || !state.spaceVoice.guidePlaying
    || !state.spaceVoice.keyHeld
    || state.spaceVoice.finalized) return;
  window.clearTimeout(state.spaceVoice.guideSkipTimer);
  state.spaceVoice.guideSkipTimer = null;
  state.spaceVoice.guideCancelTap = false;
  state.spaceVoice.guidePlaying = false;
  state.spaceVoice.released = false;
  state.spaceVoice.transcript = "";
  state.spaceVoice.error = "";
  state.speechToken += 1;
  state.speechInProgress = false;
  window.speechSynthesis?.cancel();
  beginSpaceVoiceRecognition();
}

function finishSpaceCommandGuide() {
  const wasPlaying = state.spaceVoice.wasPlaying;
  state.spaceVoice.skipGuideNextHold = true;
  updateSpaceVoiceOverlay(false);
  resetSpaceVoiceGesture();
  if (wasPlaying) resumePlayback();
  announce("음성 명령 안내를 마쳤습니다. 다시 스페이스 키를 길게 누르면 바로 음성 명령을 말할 수 있습니다.");
}

function startSpaceVoiceRecognition() {
  state.spaceVoice.holdTimer = null;
  state.spaceVoice.activated = true;
  state.spaceVoice.wasPlaying = isPlaybackRunning();
  if (state.spaceVoice.wasPlaying) pausePlayback();
  state.speechToken += 1;
  state.speechInProgress = false;
  state.resumeAfterSpeech = false;
  window.speechSynthesis?.cancel();
  $("#pause-overlay")?.classList.add("hidden");
  if (state.spaceVoice.skipGuideNextHold) {
    state.spaceVoice.skipGuideNextHold = false;
    state.spaceVoice.guidePlaying = false;
    beginSpaceVoiceRecognition();
    return;
  }
  playSpaceVoiceReadyChime();
  state.spaceVoice.guidePlaying = true;
  updateSpaceVoiceOverlay(true, "사용할 수 있는 음성 명령", "안내를 듣는 중입니다. 키를 떼어도 안내는 계속됩니다. 다시 길게 누르면 즉시 음성 명령을 시작합니다.");
  announce("띠링. 사용할 수 있는 음성 명령을 먼저 안내합니다.");
  speak(SPACE_COMMAND_GUIDE, () => {
    window.clearTimeout(state.spaceVoice.guideSkipTimer);
    state.spaceVoice.guideSkipTimer = null;
    state.spaceVoice.guideCancelTap = false;
    state.spaceVoice.guidePlaying = false;
    if (!state.spaceVoice.activated || state.spaceVoice.finalized) return;
    if (!state.spaceVoice.keyHeld || state.spaceVoice.released) {
      finishSpaceCommandGuide();
      return;
    }
    beginSpaceVoiceRecognition();
  });
}

window.addEventListener("keydown", (event) => {
  if ((event.code !== "Space" && event.key !== " ") || event.altKey || event.ctrlKey || event.metaKey || event.isComposing) return;
  if (isTextCommandDialogTarget(event.target)) return;
  event.preventDefault();
  if (event.repeat) return;
  if (state.freeControlMode) return;
  state.spaceVoice.pressStartedAt = performance.now();
  if (state.spaceVoice.activated && state.spaceVoice.guidePlaying && state.spaceVoice.released) {
    state.spaceVoice.keyHeld = true;
    state.spaceVoice.released = false;
    state.spaceVoice.guideCancelTap = true;
    prepareSpaceVoiceAudio();
    window.clearTimeout(state.spaceVoice.guideSkipTimer);
    state.spaceVoice.guideSkipTimer = window.setTimeout(skipGuideAndBeginListening, 650);
    updateSpaceVoiceOverlay(true, "안내 건너뛰기", "조금만 더 누르면 안내를 멈추고 마이크를 켭니다.");
    return;
  }
  if (state.spaceVoice.holdTimer || state.spaceVoice.activated) return;
  state.spaceVoice.keyHeld = true;
  prepareSpaceVoiceAudio();
  state.spaceVoice.target = event.target;
  state.spaceVoice.holdTimer = window.setTimeout(startSpaceVoiceRecognition, 2_000);
});

window.addEventListener("keyup", (event) => {
  if (event.code !== "Space" && event.key !== " ") return;
  if (isTextCommandDialogTarget(event.target)) return;
  event.preventDefault();
  if (state.freeControlMode) {
    handleFreeModeSpaceTap();
    return;
  }
  if (state.spaceVoice.guideCancelTap) {
    window.clearTimeout(state.spaceVoice.guideSkipTimer);
    state.spaceVoice.guideSkipTimer = null;
    state.spaceVoice.guideCancelTap = false;
    state.spaceVoice.keyHeld = false;
    state.spaceVoice.released = true;
    handleQuickSpaceTap(event.target);
    return;
  }
  if (!state.spaceVoice.activated) {
    window.clearTimeout(state.spaceVoice.holdTimer);
    const target = state.spaceVoice.target;
    const wasQuickTap = performance.now() - state.spaceVoice.pressStartedAt < 700;
    const wasEditable = isEditableSpaceTarget(target);
    resetSpaceVoiceGesture();
    if (target && wasEditable) insertShortSpace(target);
    else if (target && wasQuickTap) handleQuickSpaceTap(target);
    return;
  }
  state.spaceVoice.keyHeld = false;
  state.spaceVoice.released = true;
  if (state.spaceVoice.guidePlaying) return;
  if (state.spaceVoice.recognition) {
    try {
      state.spaceVoice.recognition.stop();
      window.setTimeout(() => {
        if (!state.spaceVoice.finalized && state.spaceVoice.released) finishSpaceVoiceGesture();
      }, 1_000);
    } catch { finishSpaceVoiceGesture(); }
  } else {
    finishSpaceVoiceGesture();
  }
});

window.addEventListener("blur", () => {
  if (document.activeElement?.tagName === "IFRAME") {
    restoreGlobalSpaceFocus();
    return;
  }
  if (!state.spaceVoice.holdTimer && !state.spaceVoice.activated) return;
  // A microphone permission popover also blurs the page. Keep an activated
  // push-to-talk session alive; visibilitychange handles a real tab switch.
  if (state.spaceVoice.activated) return;
  window.clearTimeout(state.spaceVoice.holdTimer);
  resetSpaceVoiceGesture();
});

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState !== "hidden") return;
  if (!state.spaceVoice.holdTimer && !state.spaceVoice.activated) return;
  if (state.spaceVoice.activated) cancelVoiceGuidanceAndResume();
  else resetSpaceVoiceGesture();
});

window.addEventListener("keydown", (event) => {
  if (!state.snapshot || $("#agent-view").classList.contains("hidden")) return;
  if (isTextCommandDialogTarget(event.target)
    || isEditableSpaceTarget(event.target)
    || event.target instanceof HTMLSelectElement) return;
  const key = event.key.toLowerCase();
  const plainArrow = !event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey;
  if (event.altKey && key === "d") {
    event.preventDefault();
    $("#describe-now").click();
  } else if (event.altKey && key === "s") {
    event.preventDefault();
    readSummaryGuide();
  } else if (event.altKey && key === "b") {
    event.preventDefault();
    addBookmark();
  } else if ((event.altKey || plainArrow) && event.key === "ArrowLeft") {
    event.preventDefault();
    seekRelative(-10_000);
  } else if ((event.altKey || plainArrow) && event.key === "ArrowRight") {
    event.preventDefault();
    seekRelative(10_000);
  } else if (event.key === "Escape") {
    $("#stop-speech").click();
  }
});

function stopCurrentLectureForNavigation() {
  state.speechToken += 1;
  state.resumeAfterSpeech = false;
  window.speechSynthesis?.cancel();
  pausePlayback();
  if (state.videoUrl) URL.revokeObjectURL(state.videoUrl);
  window.clearInterval(state.youtubeTimer);
  state.youtubePlayer?.destroy?.();
}

function returnHome() {
  if (state.freeControlMode) exitFreeControlMode({ announceExit: false });
  stopCurrentLectureForNavigation();
  window.location.href = `${window.location.pathname}${window.location.search}#saved-library-title`;
  window.location.reload();
}

function playbackRecordForCurrentLecture() {
  if (state.localVideoFile) {
    return {
      kind: "local",
      name: state.localVideoFile.name || "저장된 강의 영상",
      media_type: state.localVideoFile.type || "video/mp4",
      size_bytes: state.localVideoFile.size || 0,
    };
  }
  if (state.pendingLinkResult) {
    return {
      kind: state.pendingLinkResult.playback_kind,
      normalized_url: state.pendingLinkResult.normalized_url || "",
      playback_url: state.pendingLinkResult.playback_url || "",
      name: state.isSample ? `${SAMPLE_CATALOG[state.activeSampleId]?.announcement || "샘플"} 원본 링크` : "강의 원본 링크",
    };
  }
  return { kind: "none", name: "영상 없음" };
}

async function saveCurrentLectureAndReturnHome() {
  if (!state.snapshot || !state.session) return;
  const saveButtons = [$("#save-and-home"), $("#save-complete-and-home")];
  saveButtons.forEach((button) => { button.disabled = true; button.textContent = "저장 중…"; });
  try {
    if (state.localVideoFile) await navigator.storage?.persist?.();
    const now = new Date().toISOString();
    const id = state.currentSavedLectureId || uid("saved-lecture");
    const playback = playbackRecordForCurrentLecture();
    const record = {
      id,
      title: state.session.title,
      subject: state.session.subject,
      source_label: state.session.source_label,
      saved_at: now,
      updated_at: now,
      completed: state.lectureCompleted,
      session: JSON.parse(JSON.stringify(state.session)),
      snapshot: JSON.parse(JSON.stringify(state.snapshot)),
      summary_text: window.SullivanLibrary.summaryText(state.snapshot),
      playback,
      video_blob: state.localVideoFile || null,
      is_sample: state.isSample,
      active_sample_id: state.activeSampleId,
      last_position_ms: getCurrentPlaybackMs(),
    };
    await window.SullivanLibrary.save(record);
    state.currentSavedLectureId = id;
    sessionStorage.setItem("sullivan-library-message", `${state.session.title} 강의의 ${playback.kind === "local" ? "원본 영상과 " : "원본 링크와 "}요약을 이 노트북에 저장했습니다.`);
    returnHome();
  } catch (error) {
    const quotaMessage = error?.name === "QuotaExceededError"
      ? "브라우저 저장 공간이 부족합니다. 큰 영상을 줄이거나 기존 저장 강의를 삭제해 주세요."
      : error.message;
    alert(`강의를 저장하지 못했습니다. ${quotaMessage}`);
    saveButtons.forEach((button, index) => {
      button.disabled = false;
      button.textContent = index === 0 ? "강의 저장하고 홈으로" : "저장하고 홈으로";
    });
  }
}

function savedSourceLabel(record) {
  if (record.playback?.kind === "local") return `원본 영상 ${formatBytes(record.playback.size_bytes)} · 브라우저 저장`;
  if (["youtube", "direct", "external"].includes(record.playback?.kind)) return "원본 링크 · 요약 저장";
  return "요약 저장";
}

async function renderSavedLibrary() {
  const box = $("#saved-lecture-list");
  try {
    state.savedLectures = await window.SullivanLibrary.all();
    const estimate = await navigator.storage?.estimate?.();
    $("#saved-storage-status").textContent = estimate?.quota
      ? `${state.savedLectures.length}개 · ${formatBytes(estimate.usage || 0)} 사용`
      : `${state.savedLectures.length}개 저장`;
    const homeMessage = sessionStorage.getItem("sullivan-library-message");
    if (homeMessage) {
      $("#saved-lecture-answer").textContent = homeMessage;
      sessionStorage.removeItem("sullivan-library-message");
    }
    if (!state.savedLectures.length) {
      box.innerHTML = '<p class="empty-state">저장된 강의가 없습니다. 강의를 마치거나 학습 중에 ‘강의 저장하고 홈으로’를 누르면 여기에 표시됩니다.</p>';
      return;
    }
    box.innerHTML = state.savedLectures.map((record) => `
      <article class="saved-lecture-card" data-saved-card="${escapeHtml(record.id)}">
        <header><div><h3>${escapeHtml(record.title)}</h3><small>${escapeHtml(record.subject || "과목 미지정")}</small></div><time datetime="${escapeHtml(record.updated_at)}">${new Date(record.updated_at || record.saved_at).toLocaleDateString("ko-KR")}</time></header>
        <span class="saved-source-badge">${escapeHtml(savedSourceLabel(record))}</span>
        <p>${escapeHtml(record.summary_text || "저장된 요약 없음").slice(0, 180)}</p>
        <div class="saved-lecture-actions">
          <button type="button" class="primary" data-open-saved="${escapeHtml(record.id)}">강의 다시 열기</button>
          <button type="button" class="secondary" data-read-saved="${escapeHtml(record.id)}">요약 듣기</button>
          <button type="button" class="saved-delete" data-delete-saved="${escapeHtml(record.id)}">삭제</button>
        </div>
      </article>`).join("");
    $$('[data-open-saved]').forEach((button) => button.addEventListener("click", () => openSavedLecture(button.dataset.openSaved)));
    $$('[data-read-saved]').forEach((button) => button.addEventListener("click", () => readSavedSummary(button.dataset.readSaved)));
    $$('[data-delete-saved]').forEach((button) => button.addEventListener("click", () => deleteSavedLecture(button.dataset.deleteSaved)));
  } catch (error) {
    $("#saved-storage-status").textContent = "저장소 사용 불가";
    box.innerHTML = `<p class="empty-state">${escapeHtml(error.message)}</p>`;
  }
}

async function openSavedLecture(id) {
  try {
    const record = await window.SullivanLibrary.get(id);
    if (!record) throw new Error("저장된 강의를 찾을 수 없습니다.");
    state.session = record.session;
    state.demoAccessCode = $("#demo-access-code").value.trim();
    state.snapshot = record.snapshot;
    state.isSample = Boolean(record.is_sample);
    state.activeSampleId = record.active_sample_id || null;
    state.currentSavedLectureId = record.id;
    state.localVideoFile = record.video_blob || null;
    state.lectureCompleted = Boolean(record.completed);
    state.announcedGaps.clear();
    state.currentParagraphId = null;
    state.underlinedParagraphIds.clear();
    state.pendingLinkResult = null;
    $("#setup-view").classList.add("hidden");
    $("#agent-view").classList.remove("hidden");
    $("#lecture-title").textContent = record.title;
    $("#lecture-meta").textContent = `${record.subject || "과목 미지정"} · 내 강의 보관함`;
    $("#lecture-complete-card").classList.toggle("hidden", !state.lectureCompleted);
    renderAll();

    if (record.playback?.kind === "local" && record.video_blob) {
      if (state.videoUrl) URL.revokeObjectURL(state.videoUrl);
      state.videoUrl = URL.createObjectURL(record.video_blob);
      state.linkedPlaybackKind = "local";
      const video = $("#lecture-video");
      video.src = state.videoUrl;
      video.classList.remove("hidden");
      $("#lecture-youtube").classList.add("hidden");
      $("#video-placeholder").classList.add("hidden");
      $("#linked-playback-note").classList.remove("hidden");
      $("#linked-playback-note").textContent = "이 노트북 브라우저에 사용자가 저장한 원본 영상입니다. 서버로 업로드되지 않았습니다.";
      video.addEventListener("loadedmetadata", () => seekTo(record.last_position_ms || 0), { once: true });
    } else if (["youtube", "direct", "external"].includes(record.playback?.kind)) {
      state.pendingLinkResult = {
        normalized_url: record.playback.normalized_url,
        playback_kind: record.playback.kind,
        playback_url: record.playback.playback_url,
        analysis_status: "saved",
      };
      await setupLinkPlayback(state.pendingLinkResult);
      seekTo(record.last_position_ms || 0);
      $("#linked-playback-note").textContent = "보관함에 저장된 원본 링크와 분석 요약을 불러왔습니다. 영상 파일을 복제하거나 내려받지 않았습니다.";
    } else {
      $("#video-placeholder").classList.remove("hidden");
      $("#video-placeholder strong").textContent = "저장된 학습자료";
      $("#video-placeholder p").textContent = "원본 영상 없이 요약과 학습자료를 다시 이용합니다.";
    }
    announce(`${record.title} 저장 강의를 열었습니다. 마지막 위치부터 다시 들을 수 있습니다.`);
  } catch (error) {
    alert(`저장 강의를 열지 못했습니다. ${error.message}`);
  }
}

async function readSavedSummary(id) {
  const record = state.savedLectures.find((item) => item.id === id) || await window.SullivanLibrary.get(id);
  if (!record) return;
  const text = `${record.title} 요약입니다. ${record.summary_text}`;
  $("#saved-lecture-answer").textContent = text;
  announce(`${record.title} 요약을 읽습니다.`);
  speak(text);
}

async function deleteSavedLecture(id) {
  const record = state.savedLectures.find((item) => item.id === id);
  if (!record || !window.confirm(`${record.title}의 저장된 원본과 요약을 이 브라우저에서 삭제할까요?`)) return;
  await window.SullivanLibrary.remove(id);
  $("#saved-lecture-answer").textContent = `${record.title}의 저장된 원본과 요약을 삭제했습니다.`;
  await renderSavedLibrary();
}

async function runSavedLectureCommand(command) {
  const record = window.SullivanLibrary.findRequested(state.savedLectures, command);
  if (!record) {
    const message = state.savedLectures.length
      ? `“${command}”과 연결된 저장 강의를 찾지 못했습니다. 강의 제목이나 ‘최근 강의’를 말해 주세요.`
      : "저장된 강의가 없습니다.";
    $("#saved-lecture-answer").textContent = message;
    announce(message);
    return;
  }
  if (window.SullivanLibrary.requestIntent(command) === "summary") await readSavedSummary(record.id);
  else await openSavedLecture(record.id);
}

$("#saved-lecture-command-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const command = new FormData(event.currentTarget).get("command")?.trim();
  if (command) runSavedLectureCommand(command);
});

$("#saved-lecture-voice").addEventListener("click", () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) return alert("이 브라우저에서는 음성 명령을 지원하지 않습니다. 명령을 직접 입력해 주세요.");
  const recognition = new Recognition();
  recognition.lang = "ko-KR";
  recognition.interimResults = false;
  $("#saved-lecture-voice").classList.add("listening");
  $("#saved-lecture-answer").textContent = "저장된 강의 요청을 듣고 있습니다.";
  recognition.onresult = (event) => {
    $("#saved-lecture-command").value = event.results[0][0].transcript;
    $("#saved-lecture-command-form").requestSubmit();
  };
  recognition.onerror = () => { $("#saved-lecture-answer").textContent = "음성을 인식하지 못했습니다. 다시 시도해 주세요."; };
  recognition.onend = () => $("#saved-lecture-voice").classList.remove("listening");
  recognition.start();
});

$("#save-and-home").addEventListener("click", saveCurrentLectureAndReturnHome);
$("#save-complete-and-home").addEventListener("click", saveCurrentLectureAndReturnHome);

$("#new-session").addEventListener("click", () => {
  if (!window.confirm("현재 강의를 저장하지 않고 홈으로 돌아갈까요?")) return;
  returnHome();
});

window.addEventListener("beforeunload", () => {
  if (state.videoUrl) URL.revokeObjectURL(state.videoUrl);
  window.clearInterval(state.youtubeTimer);
});

checkApi();
renderSavedLibrary();
