// Labels follow server-owned processing records; editable source names are never evidence.
export function analysisLabel(status){
  const state=status?.state||'unknown',provider=status?.provider;
  if(state==='completed')return status.run_id&&status.recorded_at
    ?provider==='gemini'?'Gemini 분석 완료':provider==='adapter'?'외부 어댑터 분석 완료':'분석 상태 확인 불가':'분석 상태 확인 불가';
  return {unknown:'분석 상태 확인 불가',not_run:'영상 분석 미실행',sample:'사전 준비 샘플',
    analyzing:provider==='gemini'?'Gemini 분석 중':'영상 분석 중',failed:provider==='gemini'?'Gemini 분석 실패':'영상 분석 실패'}[state]||'분석 상태 확인 불가';
}
