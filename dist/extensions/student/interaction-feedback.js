// Session-only command feedback. Never pass user content into labels or reasons.
const ACTION_LABELS = Object.freeze({
  play: '강의 재생', pause: '강의 일시정지', stop: '전체 중지', seek: '강의 위치 이동',
  status: '현재 상태 확인', help: '도움말 확인', listen: '음성 명령 듣기',
  question: '강의 질문', describe: '준비된 설명 읽기', summary: '준비된 요약 읽기',
  save: '학습 기록 저장', command: '강의 요청',
});
const PHASE_LABELS = Object.freeze({
  idle: '대기', listening: '듣는 중', recognized: '해석됨', running: '처리 중',
  success: '완료', fail: '실패', cancel: '취소',
});
const REASONS = Object.freeze({
  unsupported: '현재 도움말에서 지원하는 명령을 확인하세요.',
  unrecognized: '다시 말하거나 타자로 입력하세요.',
  no_lecture: '먼저 배정된 강의를 여세요.',
  player_unavailable: '영상 연결 상태를 확인하세요.',
  microphone_denied: '마이크 권한을 확인하거나 타자로 입력하세요.',
  microphone_unavailable: '음성 입력 대신 타자로 입력하세요.',
  network: '연결 상태를 확인하고 다시 시도하세요.',
  failed: '실행하지 못했습니다. 현재 상태를 확인하고 다시 시도하세요.',
  cancelled: '요청을 취소했습니다.',
});
const TERMINAL = new Set(['success', 'fail', 'cancel']);
const ownKey = (dictionary, value) => typeof value === 'string' && Object.hasOwn(dictionary, value);

/** Recognize only short, unambiguous supported controls; leave learning questions alone. */
export function classifyLocalCommand(text) {
  if (typeof text !== 'string' || text.length > 100) return null;
  const value = text.normalize('NFC').trim().replace(/[.!?~]+$/u, '').replace(/\s+/gu, '');
  const phrases = {
    status: ['현재상태', '지금상태', '무슨작업중', '최근명령', '현재상태알려줘', '지금뭐하고있어', '현재작업알려줘'],
    help: ['사용법', '도움말', '지금할수있는명령', '사용법알려줘', '도움말알려줘', '단축키알려줘'],
    play: ['재생', '재생해', '재생해줘', '재생해주세요', '영상재생', '강의재생', '계속재생', '다시재생', '영상틀어줘', '강의틀어줘'],
    pause: ['일시정지', '일시정지해', '일시정지해줘', '일시정지해주세요', '영상일시정지', '강의일시정지'],
    stop: ['중지', '정지', '멈춰', '멈춰줘', '중지해', '중지해줘', '전체중지', '전체중지해줘', '영상중지', '강의중지', '영상정지', '강의정지'],
  };
  for (const [type, examples] of Object.entries(phrases)) {
    if (examples.includes(value)) return Object.freeze({type});
  }
  if (['10초전', '10초전으로', '10초뒤로', '뒤로10초'].includes(value)) return Object.freeze({type: 'seek', deltaMs: -10000});
  if (['10초후', '10초후로', '10초앞으로', '앞으로10초'].includes(value)) return Object.freeze({type: 'seek', deltaMs: 10000});
  return null;
}

// Whole-utterance controls precede question detection, including polite requests.
// A control word inside a lesson question is never permission to operate media.
const REQUEST_END = '(?:해(?:줘|주세요|줘요|줄래요?|주시겠어요|줄수있어|줄수있나요|봐|봐줘)?|시켜(?:줘|주세요|줄래)?|줘|주세요|줘요|줄래요?|주시겠어요|줄수있어|줄수있나요|봐|봐줘|하기)?';
const PREFIX = '(?:(?:지금|바로|잠깐|잠시|좀|제발)){0,3}';
const MODIFIER = '(?:(?:지금|바로|잠깐|잠시|좀|제발|다시|계속|이어)){0,3}';
const STOP_REQUEST = new RegExp(`^${PREFIX}(?:(?:전체|동영상|영상|강의|재생|앱음성|음성|소리|설명|해설|낭독|세줄요약|3줄요약|요약|말하기)(?:을|를|만)?)?${MODIFIER}(?:일시정지|중지|정지|중단|멈춰|멈추|멈춤|그만)${REQUEST_END}$`, 'u');
const PLAY_REQUEST = new RegExp(`^${MODIFIER}(?:(?:동영상|영상|강의)(?:을|를|만)?)?${MODIFIER}(?:재생|시작|틀어|틀)${REQUEST_END}$`, 'u');
const RESUME_REQUEST = new RegExp(`^(?:(?:세줄요약|3줄요약|요약|설명|해설)(?:을|를)?(?:멈추고|중지하고|그만하고))?(?:원래)?(?:강의|영상)(?:로|으로|에)?(?:돌아(?:와|가|오기|가기)|복귀|이어듣기|이어들려|이어듣자|이어)${REQUEST_END}$`, 'u');
const SEEK_REQUEST = new RegExp(`^(?:10초(뒤로|전(?:으로)?|앞으로|후(?:로)?)|(뒤로|앞으로)10초)(?:(?:이동|가|옮겨)${REQUEST_END})?$`, 'u');
const RELATIVE_REQUEST = new RegExp(`^(?:[+-]?\\d+(?:[.,]\\d+)?초(?:뒤로|전(?:으로)?|앞으로|후(?:로)?)|(?:뒤로|앞으로)[+-]?\\d+(?:[.,]\\d+)?초)(?:(?:이동|가|옮겨)${REQUEST_END})?$`, 'u');
const SUPPORT_REQUEST = /^(?:(?:왜|지금|갑자기)){0,2}(?:영상|강의|재생|소리|마이크|음성인식|로그인|연결|앱|프로그램)(?:이|가|은|는)?(?:왜|갑자기|계속|전혀|아예|잘)?(?:안되|안돼|안나|오류|실패|멈췄|멈춰있)(?:어|어요|요|나요|는데요?|죠|지|야|였어|였어요|났어|났어요|했어|했어요|와|와요)?(?:어떻게해|어떻게하지|어떻게해야해|도와줘|방법알려줘)?$/u;
const AMBIGUOUS_REQUEST = /^(?:(?:영상|강의|동영상)(?:을|를)?)?(?:재생|중지|정지|일시정지|멈추|이동)(?:(?:좀|한번|다시|잠깐|잠시|부탁|같은거|그런동작|아무거나|할|해줄|하고)){1,3}$/u;
const EXPLANATION_REQUEST = new RegExp(`(?:설명|알려|말|가르쳐)${REQUEST_END}$`, 'u');
const LECTURE_REQUEST = new RegExp(`^.+강의(?:열어|열기|선택해|선택하기|들려|듣기)${REQUEST_END}$`, 'u');
const BUTTON_REQUEST = new RegExp(`(?:눌러|클릭|선택|실행)${REQUEST_END}$`, 'u');

/** Student-only routing; preserve the shared web router and original question text. */
export function resolveStudentIntent(text, classifyLegacy) {
  if (typeof text !== 'string' || !text.trim() || text.length > 2000) return Object.freeze({type: 'clarify'});
  const local = classifyLocalCommand(text);
  if (local) return local;
  const value = text.normalize('NFC').trim().replace(/[.,!?~·。？！]+$/gu, '').replace(/\s+/gu, '');
  if (STOP_REQUEST.test(value)) return Object.freeze({type: 'stop'});
  if (PLAY_REQUEST.test(value)) return Object.freeze({type: 'play'});
  if (RESUME_REQUEST.test(value)) return Object.freeze({type: 'resume_lecture'});
  const seek = value.match(SEEK_REQUEST);
  if (seek) return Object.freeze({type: 'seek', deltaMs: ['뒤로', '전', '전으로'].includes(seek[1] || seek[2]) ? -10000 : 10000});
  if (RELATIVE_REQUEST.test(value)) return Object.freeze({type: 'clarify'});
  // Operational support stays local; do not turn help into a paid lesson query.
  if (/^(?:(?:마이크|음성명령|학생앱|보호자앱|앱|프로그램)(?:의)?)?(?:사용법|단축키|조작법)(?:을|를|이|가)?(?:알려줘|설명해줘|뭐야|무엇인가요)?$/u.test(value)
      || SUPPORT_REQUEST.test(value)) return Object.freeze({type: 'help'});
  const legacy = classifyLegacy(text);
  if (legacy.type === 'open_lecture' && LECTURE_REQUEST.test(value)) return legacy;
  if (legacy.type === 'button' && BUTTON_REQUEST.test(value)) return legacy;
  const compound = value.match(/^(.+?)(?:하고|고|한뒤|한후|한다음)(.+)$/u);
  if (compound && (STOP_REQUEST.test(compound[1]) || PLAY_REQUEST.test(compound[1]))) return Object.freeze({type: 'clarify'});
  const interrogative = /무엇|무슨|뭐|어떤|어떻게|언제|어디|얼마나|누구|누가|왜(?!란|곡)|인가요|인가[?？]?$/u.test(text.normalize('NFC'));
  const explanation = /(?:뜻|의미|차이|원리|이유)(?:$|.*(?:설명|알려|말해|가르쳐|궁금|인가|이야|이니|이지|뭐))/u.test(value);
  if (interrogative || explanation) return Object.freeze({type: 'question'});
  if (['play', 'pause', 'stop', 'seek', 'resume_lecture', 'chat'].includes(legacy.type)
      && EXPLANATION_REQUEST.test(value)) return Object.freeze({type: 'question'});
  if (['play', 'pause', 'stop', 'seek', 'resume_lecture'].includes(legacy.type) || AMBIGUOUS_REQUEST.test(value)
      || /(?:앞으로|뒤로).*초|초.*(?:앞으로|뒤로|전으로|후로)/u.test(value)) {
    return Object.freeze({type: 'clarify'});
  }
  return legacy;
}

/**
 * A single latest interaction, scoped to a resettable account/lecture/view epoch.
 * begin() returns an identity-checked ticket. Only actual execution results may
 * call update(ticket, 'success'); this module does not infer execution success.
 * Call reset() on account, lecture, or view changes and on teardown.
 * All snapshots are frozen and contain only fixed public dictionary text.
 */
export function createInteractionFeedback({onChange} = {}) {
  let epoch = 0;
  let operationId = 0;
  let active = null;
  const snapshot = (actionId, phase, reasonCode = '') => {
    const label = actionId ? ACTION_LABELS[actionId] : '';
    const phaseLabel = PHASE_LABELS[phase];
    const reason = REASONS[reasonCode] || '';
    return Object.freeze({
      operationId: active ? operationId : null, epoch, actionId, label, phase, phaseLabel,
      reasonCode, reason,
      summary: actionId ? `${label}: ${phaseLabel}.${reason ? ` ${reason}` : ''}` : '최근 명령이 없습니다.',
    });
  };
  let state = snapshot(null, 'idle');
  const publish = next => {
    state = next;
    if (typeof onChange === 'function') onChange(state);
  };
  return Object.freeze({
    begin(actionId) {
      const safeAction = ownKey(ACTION_LABELS, actionId) ? actionId : 'command';
      operationId += 1;
      active = Object.freeze({operationId, epoch});
      const ticket = active;
      publish(snapshot(safeAction, 'running'));
      return ticket;
    },
    update(ticket, phase, reasonCode = '') {
      if (!active || ticket !== active || TERMINAL.has(state.phase)) return false;
      if (!ownKey(PHASE_LABELS, phase) || phase === 'idle') return false;
      const safeReason = ownKey(REASONS, reasonCode) ? reasonCode : '';
      if (state.phase === phase && state.reasonCode === safeReason) return false;
      publish(snapshot(state.actionId, phase, safeReason));
      return true;
    },
    current() { return state; },
    reset() {
      epoch += 1;
      active = null;
      publish(snapshot(null, 'idle'));
      return state;
    },
  });
}
