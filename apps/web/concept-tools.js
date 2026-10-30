(function createSullivanConcepts(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.SullivanConcepts = api;
})(typeof window !== "undefined" ? window : globalThis, () => {
  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[\s·ㆍ.,!?()[\]{}:;/'"_-]+/g, "")
      .trim();
  }

  function conceptsForSnapshot(snapshot = {}) {
    if (Array.isArray(snapshot.concept_index) && snapshot.concept_index.length) {
      return snapshot.concept_index
        .filter((item) => item?.keyword && Number.isFinite(item.timestamp_ms))
        .map((item, index) => ({
          concept_id: item.concept_id || `concept-${index + 1}`,
          keyword: item.keyword,
          aliases: Array.isArray(item.aliases) ? item.aliases : [],
          category: item.category || "핵심 개념",
          timestamp_ms: item.timestamp_ms,
          end_ms: Number.isFinite(item.end_ms) && item.end_ms > item.timestamp_ms
            ? item.end_ms
            : item.timestamp_ms + 10_000,
          lecturer_point: item.lecturer_point || item.lecturer_quote || "강사가 이 개념을 설명하는 구간입니다.",
          ai_explanation: item.ai_explanation || item.definition || item.lecturer_point || "강의 근거를 다시 확인해 주세요.",
          flow: item.flow || "",
          related_keywords: Array.isArray(item.related_keywords) ? item.related_keywords : [],
          importance: Number(item.importance || 0.8),
        }))
        .sort((a, b) => a.timestamp_ms - b.timestamp_ms);
    }

    const glossary = snapshot.study_guide?.glossary || [];
    const segments = snapshot.transcript_segments || [];
    return glossary.map((item, index) => {
      const segment = segments.find((candidate) => normalize(candidate.text).includes(normalize(item.term)));
      return {
        concept_id: `derived-${index + 1}`,
        keyword: item.term,
        aliases: [],
        category: "핵심 용어",
        timestamp_ms: segment?.start_ms || index * 10_000,
        end_ms: segment?.end_ms || index * 10_000 + 10_000,
        lecturer_point: segment?.text || item.definition,
        ai_explanation: item.definition,
        flow: "",
        related_keywords: [],
        importance: 0.75,
      };
    });
  }

  function searchableText(concept) {
    return normalize([
      concept.keyword,
      concept.category,
      concept.flow,
      concept.lecturer_point,
      concept.ai_explanation,
      ...(concept.aliases || []),
      ...(concept.related_keywords || []),
    ].join(" "));
  }

  function search(concepts = [], query = "") {
    const needle = normalize(query);
    if (!needle || ["전체", "전체흐름", "핵심", "중요"].includes(needle)) {
      return [...concepts].sort((a, b) => b.importance - a.importance || a.timestamp_ms - b.timestamp_ms);
    }
    const broadTerms = {
      원인: ["원인", "배경", "발발"],
      전개: ["전개", "과정", "흐름", "순서"],
      결과: ["결과", "영향", "의의"],
      인물: ["인물", "왕", "장군", "의병", "정치"],
      비교: ["비교", "차이", "공통"],
    };
    const tokens = broadTerms[needle] || [needle];
    return concepts
      .map((concept) => {
        const haystack = searchableText(concept);
        const keyword = normalize(concept.keyword);
        let score = 0;
        tokens.forEach((token) => {
          const normalizedToken = normalize(token);
          if (keyword === normalizedToken) score += 100;
          else if (keyword.includes(normalizedToken) || normalizedToken.includes(keyword)) score += 60;
          if (haystack.includes(normalizedToken)) score += 20;
        });
        return { concept, score: score + concept.importance };
      })
      .filter((item) => item.score > 1)
      .sort((a, b) => b.score - a.score || a.concept.timestamp_ms - b.concept.timestamp_ms)
      .map((item) => item.concept);
  }

  function mentioned(concepts = [], message = "") {
    const normalizedMessage = normalize(message);
    return concepts.filter((concept) => [concept.keyword, ...(concept.aliases || [])]
      .some((term) => {
        const normalizedTerm = normalize(term);
        return normalizedTerm.length >= 2 && normalizedMessage.includes(normalizedTerm);
      }));
  }

  function categories(concepts = []) {
    return [...new Set(concepts.map((item) => item.category).filter(Boolean))];
  }

  return { normalize, conceptsForSnapshot, search, mentioned, categories };
});
