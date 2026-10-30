(function createSullivanPassages(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.SullivanPassages = api;
})(typeof window !== "undefined" ? window : globalThis, () => {
  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[\s·ㆍ.,!?()[\]{}:;/'"_-]+/g, "")
      .trim();
  }

  function paragraphsForSnapshot(snapshot = {}) {
    return (snapshot.passage?.paragraphs || [])
      .filter((paragraph) => Array.isArray(paragraph.sentences) && paragraph.sentences.length)
      .map((paragraph, index) => {
        const sentences = paragraph.sentences
          .filter((sentence) => sentence?.text)
          .map((sentence, sentenceIndex) => ({
            ...sentence,
            sentence_index: sentence.sentence_index || sentenceIndex + 1,
          }));
        const timestamp = sentences.find((sentence) => Number.isFinite(sentence.timestamp_ms))?.timestamp_ms;
        return {
          ...paragraph,
          paragraph_id: paragraph.paragraph_id || `paragraph-${index + 1}`,
          paragraph_index: paragraph.paragraph_index || index + 1,
          flow_role: paragraph.flow_role || `핵심 내용 ${index + 1}`,
          timestamp_ms: Number.isFinite(timestamp) ? timestamp : 0,
          sentences,
          text: sentences.map((sentence) => sentence.text).join(" "),
        };
      })
      .sort((a, b) => a.paragraph_index - b.paragraph_index);
  }

  function paragraphSpeech(paragraph) {
    if (!paragraph) return "";
    return `${paragraph.paragraph_index}문단, ${paragraph.flow_role}. ${paragraph.text}`;
  }

  function flowSpeech(paragraphs = []) {
    if (!paragraphs.length) return "긴 지문 흐름이 없습니다.";
    const flow = paragraphs.map((paragraph) => `${paragraph.paragraph_index}문단 ${paragraph.flow_role}`).join(", 다음은 ");
    return `긴 지문은 모두 ${paragraphs.length}문단입니다. 흐름은 ${flow} 순서입니다.`;
  }

  function findByOrdinal(paragraphs, query) {
    const normalized = normalize(query);
    const koreanOrdinals = {
      첫문단: 1, 첫번째문단: 1, 일문단: 1,
      둘째문단: 2, 두번째문단: 2, 이문단: 2,
      셋째문단: 3, 세번째문단: 3, 삼문단: 3,
      넷째문단: 4, 네번째문단: 4, 사문단: 4,
      다섯째문단: 5, 다섯번째문단: 5, 오문단: 5,
    };
    const numericMatch = String(query || "").match(/(\d+)\s*문단/);
    const index = numericMatch
      ? Number(numericMatch[1])
      : Object.entries(koreanOrdinals).find(([term]) => normalized.includes(term))?.[1];
    return Number.isFinite(index) ? paragraphs.find((paragraph) => paragraph.paragraph_index === index) : null;
  }

  function resolveCommand({ paragraphs = [], query = "", currentId = null, underlinedIds = new Set() }) {
    const normalized = normalize(query);
    if (!normalized) return { type: "empty", items: [], speech: "문단 명령을 말하거나 입력해 주세요." };

    if (normalized.includes("밑줄") || normalized.includes("표시한문단") || normalized.includes("저장한문단")) {
      const items = paragraphs.filter((paragraph) => underlinedIds.has(paragraph.paragraph_id));
      return items.length
        ? { type: "underlined", items, speech: `밑줄 친 ${items.length}개 문단을 다시 읽겠습니다. ${items.map(paragraphSpeech).join(" ")}` }
        : { type: "not-found", items: [], speech: "아직 밑줄 친 문단이 없습니다. 문단 카드에서 밑줄 표시를 먼저 눌러 주세요." };
    }

    if (["전체흐름", "지문흐름", "문단흐름", "긴지문흐름"].some((term) => normalized.includes(term))) {
      return { type: "flow", items: paragraphs, speech: flowSpeech(paragraphs) };
    }

    const currentIndex = Math.max(0, paragraphs.findIndex((paragraph) => paragraph.paragraph_id === currentId));
    if (normalized.includes("다음문단")) {
      const item = paragraphs[Math.min(paragraphs.length - 1, currentIndex + 1)];
      return item ? { type: "paragraph", items: [item], speech: paragraphSpeech(item) } : { type: "not-found", items: [], speech: "다음 문단이 없습니다." };
    }
    if (normalized.includes("앞문단") || normalized.includes("이전문단")) {
      const item = paragraphs[Math.max(0, currentIndex - 1)];
      return item ? { type: "paragraph", items: [item], speech: paragraphSpeech(item) } : { type: "not-found", items: [], speech: "이전 문단이 없습니다." };
    }
    if (normalized.includes("현재문단") || normalized.includes("이문단")) {
      const item = paragraphs[currentIndex];
      return item ? { type: "paragraph", items: [item], speech: paragraphSpeech(item) } : { type: "not-found", items: [], speech: "선택된 문단이 없습니다." };
    }

    const ordinal = findByOrdinal(paragraphs, query);
    if (ordinal) return { type: "paragraph", items: [ordinal], speech: paragraphSpeech(ordinal) };

    const matches = paragraphs.filter((paragraph) => normalize(`${paragraph.flow_role} ${paragraph.text}`).includes(normalized));
    return matches.length
      ? { type: "paragraph", items: matches, speech: matches.map(paragraphSpeech).join(" ") }
      : { type: "not-found", items: [], speech: `“${query}”과 연결된 문단을 찾지 못했습니다. 2문단, 다음 문단, 전체 흐름, 밑줄 친 문단처럼 말해 주세요.` };
  }

  return { normalize, paragraphsForSnapshot, paragraphSpeech, flowSpeech, resolveCommand };
});
