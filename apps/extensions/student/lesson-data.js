// Prepared snapshots do not change while a lesson is open. Normalize once and
// reuse the index for reading, cursor movement, rendering and playback ticks.
const noticeLocations={unknown:'이 장면의 판서',whole_board:'이 장면의 판서',vertical_axis_unit:'세로축의 단위',horizontal_axis_unit:'가로축의 단위',formula_right_number:'식 오른쪽의 숫자',formula_number:'식의 숫자',formula_sign:'식의 부호',formula_inequality:'식의 부등호',underlined_sentence:'밑줄 친 문장',emphasized_text:'강조된 글자',unit:'단위',top_left:'화면 왼쪽 위',top_center:'화면 위쪽 가운데',top_right:'화면 오른쪽 위',center_left:'화면 왼쪽 가운데',center:'화면 가운데',center_right:'화면 오른쪽 가운데',bottom_left:'화면 왼쪽 아래',bottom_center:'화면 아래쪽 가운데',bottom_right:'화면 오른쪽 아래'};
export function safeHoldNoticeText(gap,problemMode=false){
  if(problemMode&&gap.kind==='answer')return '';
  return [...new Set((gap.hold_notices||[]).filter(notice=>notice.code==='visual_uncertain').map(notice=>`‘${Object.hasOwn(noticeLocations,notice.location)?noticeLocations[notice.location]:noticeLocations.unknown}’ 부분은 확실치 않아서 설명을 보류하겠습니다.`))].join(' ');
}
export function createLessonData(snapshot) {
  const paragraphs = SullivanPassages.paragraphsForSnapshot(snapshot);
  const sentences = paragraphs.flatMap(paragraph => paragraph.sentences);
  const sentenceIndices = new Map(sentences.map((sentence, index) => [sentence.sentence_id, index]));
  const sentenceParagraphs = new Map(paragraphs.flatMap(paragraph =>
    paragraph.sentences.map(sentence => [sentence.sentence_id, paragraph.paragraph_id])));
  const concepts = SullivanConcepts.conceptsForSnapshot(snapshot);
  const gaps = (snapshot.visual_gaps || []).filter(gap => gap.safe_to_speak && gap.confidence >= .72
    && gap.public_description && !['HOLD', 'SKIP'].includes(gap.action)
    && !(snapshot.session.problem_mode && gap.kind === 'answer'));
  const notices=(snapshot.visual_gaps||[]).filter(gap=>gap.action==='HOLD'&&!gap.safe_to_speak&&gap.kind!=='decoration'&&(gap.importance??1)>=.35).map(gap=>{
    const text=safeHoldNoticeText(gap,snapshot.session.problem_mode);
    return text?{gap_id:`notice:${gap.gap_id}`,timestamp_ms:gap.timestamp_ms,kind:'uncertainty_notice',notice_only:true,action:'DESCRIBE_AT_BREAK',safe_to_speak:true,confidence:1,public_description:text,source_text:null}:null;
  }).filter(Boolean);
  return {paragraphs, sentences, sentenceIndices, sentenceParagraphs, concepts, gaps, notices, playbackGaps:[...gaps,...notices]};
}
