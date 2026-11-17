// Only practice outcomes are retained; commands, recordings and lesson content never enter state.
export const PRACTICE_VERSION = 1;
const STEPS = Object.freeze([
  Object.freeze({id: 'toggle', label: 'Space 한 번으로 재생·일시정지'}),
  Object.freeze({id: 'stop', label: 'Space 두 번으로 전체 중지'}),
  Object.freeze({id: 'typed', label: 'Space 세 번으로 타자 명령'}),
]);
const STATUS_LABELS = Object.freeze({untried: '미시도', done: '실습 완료', skipped: '나중에 하기'});
const plainRecord = value => value !== null && typeof value === 'object'
  && Object.getPrototypeOf(value) === Object.prototype;
const accountValue = value => (typeof value === 'string' && value.length > 0 && value.length <= 200)
  || (typeof value === 'number' && Number.isSafeInteger(value)) ? value : null;
const own = (object, key) => Object.hasOwn(object, key);

/**
 * Three actual sample interactions, with no simulated success or network access.
 * start() returns an identity ticket (null when unavailable); every observe()
 * needs that exact ticket and lessonId. Capture the ticket before async work.
 * configure/reset/suspend/skip invalidate tickets, including for the same lesson.
 */
export function createPracticeProgress() {
  let accountId = null;
  let statuses = ['untried', 'untried', 'untried'];
  let voiceCompleted = false;
  let active = null;
  let sessionId = 0;
  let played = false;
  let dialogOpened = false;
  const completed = () => statuses.every(value => value === 'done');
  const invalidate = () => { active = null; played = false; dialogOpened = false; };
  const clear = () => { statuses = ['untried', 'untried', 'untried']; voiceCompleted = false; invalidate(); };
  const current = () => {
    const done = completed();
    const skipped = statuses.includes('skipped');
    let instruction = '배정된 사전 준비 샘플을 연결한 뒤 조작 연습을 시작하세요.';
    if (done) instruction = voiceCompleted
      ? '기본 조작과 선택형 음성 입력 연습을 완료했습니다.'
      : '기본 조작 연습을 완료했습니다. 원하면 음성 입력으로 현재 상태를 확인하세요.';
    else if (skipped) instruction = '완료한 단계는 보존했습니다. 나중에 조작 연습을 다시 시작할 수 있습니다.';
    else if (active) instruction = statuses[0] !== 'done'
      ? 'Space 한 번으로 영상을 재생한 다음, 다시 한 번 눌러 일시정지하세요.'
      : statuses[1] !== 'done'
        ? 'Space 두 번으로 전체 중지를 실행하세요.'
        : 'Space 세 번으로 입력창을 열고 현재 상태를 입력해 실행하세요.';
    return Object.freeze({
      version: PRACTICE_VERSION, active: Boolean(active), completed: done, skipped,
      voiceCompleted,
      steps: Object.freeze(STEPS.map((step, index) => Object.freeze({
        ...step, status: statuses[index], statusLabel: STATUS_LABELS[statuses[index]],
      }))),
      instruction,
    });
  };
  const restore = saved => {
    if (!plainRecord(saved) || !own(saved, 'version') || saved.version !== PRACTICE_VERSION
      || !own(saved, 'accountId') || saved.accountId !== accountId || !plainRecord(saved.steps)
      || !own(saved, 'voiceCompleted') || typeof saved.voiceCompleted !== 'boolean') return;
    const values = STEPS.map(step => own(saved.steps, step.id) ? saved.steps[step.id] : null);
    if (!values.every(value => typeof value === 'string' && own(STATUS_LABELS, value))) return;
    // Only ordered completed prefixes followed by one unfinished state can be saved.
    let unfinished = null;
    for (const value of values) {
      if (value === 'done') { if (unfinished !== null) return; }
      else if (unfinished !== null && unfinished !== value) return;
      else unfinished = value;
    }
    if (saved.voiceCompleted && !values.every(value => value === 'done')) return;
    statuses = values;
    voiceCompleted = saved.voiceCompleted;
  };
  return Object.freeze({
    configure(nextAccountId, saved) {
      accountId = accountValue(nextAccountId);
      clear();
      if (accountId !== null) restore(saved);
      return current();
    },
    start({lessonId, sample, connected} = {}) {
      if (accountId === null || sample !== true || connected !== true
        || typeof lessonId !== 'string' || !lessonId) { invalidate(); return null; }
      clear();
      sessionId += 1;
      const ticket = Object.freeze({sessionId});
      active = {lessonId, ticket};
      return ticket;
    },
    observe(event, details = {}) {
      if (!active || details.ticket !== active.ticket || details.lessonId !== active.lessonId) return false;
      if (event === 'toggle' && statuses[0] === 'untried') {
        if (details.playing === true) { played = true; return false; }
        if (details.playing === false && played) { statuses[0] = 'done'; return true; }
      }
      if (event === 'stop' && statuses[0] === 'done' && statuses[1] === 'untried' && details.paused === true) {
        statuses[1] = 'done'; return true;
      }
      if (event === 'dialog' && statuses[1] === 'done' && statuses[2] === 'untried' && details.tripleSpace === true) {
        dialogOpened = true; return false;
      }
      if (event === 'typed_status' && statuses[1] === 'done' && statuses[2] === 'untried' && dialogOpened) {
        statuses[2] = 'done'; return true;
      }
      if (event === 'voice_status' && completed() && !voiceCompleted) {
        voiceCompleted = true; return true;
      }
      return false;
    },
    current,
    serializable() {
      if (accountId === null) return null;
      return Object.freeze({
        version: PRACTICE_VERSION, accountId,
        steps: Object.freeze(Object.fromEntries(STEPS.map((step, index) => [step.id, statuses[index]]))),
        voiceCompleted,
      });
    },
    suspend() { invalidate(); return current(); },
    skip() { statuses = statuses.map(value => value === 'done' ? value : 'skipped'); invalidate(); return current(); },
    reset() { clear(); return current(); },
  });
}
