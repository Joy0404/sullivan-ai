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
