// The web keeps its broader study tools. The student extension only provides
// a short summary and explicitly labelled, deterministic material lookup.
(function(root){
  const unsupported=/발표문|암기표|복습\s*계획|추가\s*학습\s*도구|학습\s*가이드|(?:핵심\s*)?용어\s*카드|두\s*개념\s*비교|원인\s*전개\s*결과|시간순\s*흐름|퀴즈|개념\s*지도.*(?:만들|생성)/;
  const scope='학생 확장은 강의 듣기·직접 필기·원문 찾기·짧은 요약·강의 근거 질문을 지원합니다. 발표문과 자동 학습 도구 생성은 제공하지 않습니다.';
  root.SullivanLearning={unsupported:message=>unsupported.test(message),scope,respond(snapshot,message){
    if(unsupported.test(message))return {title:'지원 범위',text:scope};
    const summary=(snapshot.review?.core_summary||[]).slice(0,3);
    if(/요약/.test(message))return {title:'짧은 요약',text:summary.join(' ')||'요약할 준비 자료가 없습니다.'};
    const concepts=root.SullivanConcepts.search(root.SullivanConcepts.conceptsForSnapshot(snapshot),message);
    const text=concepts.slice(0,2).map(c=>`${c.keyword}. ${c.ai_explanation}`).join(' ');
    return {title:'준비된 자료에서 확인',text:text||'이 질문에 맞는 근거를 준비된 자료에서 찾지 못했습니다. 내용 찾기에서 원문을 확인하거나 강의 근거 질문을 다시 작성하세요.'};
  }};
})(globalThis);
