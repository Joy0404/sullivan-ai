// Prepared snapshots do not change while a lesson is open. Normalize once and
// reuse the index for reading, cursor movement, rendering and playback ticks.
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
  return {paragraphs, sentences, sentenceIndices, sentenceParagraphs, concepts, gaps};
}
