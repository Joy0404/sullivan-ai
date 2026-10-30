(function createSullivanNarration(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.SullivanNarration = api;
})(typeof window !== "undefined" ? window : globalThis, () => {
  const CONTEXTS = {
    "gap-star-nebula-flow": ["지금은 별이 태어나는 첫 단계를 설명하는 부분입니다.", "이 흐름이 원시별의 중심 온도가 오르는 이유로 이어집니다."],
    "gap-star-birth-board": ["지금은 별이 태어나 주계열성이 되는 판서 흐름을 설명하는 부분입니다.", "화살표의 순서와 중심 온도 약 천만 켈빈을 함께 기억하면 됩니다."],
    "gap-star-main-sequence-balance": ["지금은 주계열성이 안정된 이유를 설명하고 있습니다.", "안쪽 힘과 바깥쪽 힘이 같다는 점이 핵심입니다."],
    "gap-star-lifetime-scale": ["지금은 별의 질량과 수명을 비교하는 부분입니다.", "그래서 질량이 큰 별이 더 빠르게 진화합니다."],
    "gap-star-mass-fork": ["이제 별의 진화 경로가 질량에 따라 갈라집니다.", "이어지는 두 경로를 나누어 들어 보세요."],
    "gap-star-sun-path": ["먼저 태양과 질량이 비슷한 별의 경로입니다.", "이 경로의 마지막 천체는 백색 왜성입니다."],
    "gap-star-path-compare": ["방금 태양형 별의 경로를 보았고, 이제 큰 별과 비교합니다.", "분기 단계와 마지막 천체를 구분하면 됩니다."],
    "gap-star-massive-path": ["이번에는 질량이 큰 별의 경로입니다.", "초신성 뒤에는 마지막 천체가 다시 갈릴 수 있습니다."],
    "gap-star-remnant-scale": ["지금은 별이 남기는 마지막 천체를 비교하고 있습니다.", "초기 질량이 클수록 더 강한 붕괴로 이어집니다."],
    "gap-star-elements": ["마지막으로 별에서 만들어진 원소의 순환을 정리합니다.", "퍼진 물질은 다음 세대 별과 행성의 재료가 됩니다."],

    "gap-history-three-states": ["먼저 전쟁 직전 동아시아 세 나라의 상황을 비교합니다.", "이 배경이 임진왜란이 일어난 이유로 이어집니다."],
    "gap-history-cause-chain": ["지금은 일본이 조선을 침략한 배경을 설명하고 있습니다.", "이 원인 뒤에 정명가도 요구와 실제 침입이 이어집니다."],
    "gap-history-invasion-route": ["이제 일본군의 빠른 북상 과정을 따라가는 부분입니다.", "이후에는 조선 수군과 의병의 대응을 보게 됩니다."],
    "gap-history-hakikjin": ["지금은 이순신 수군의 전투 방식을 설명하고 있습니다.", "이 진형은 한산도 해전의 승리와 연결됩니다."],
    "gap-history-supply": ["방금 수군의 승리를 보았고, 이제 그 영향이 중요합니다.", "보급 차단이 일본군의 육상 진격을 약화시켰습니다."],
    "gap-history-three-victories": ["지금은 전세를 바꾼 대표적인 승리를 묶어 정리합니다.", "전투 이름과 지휘관을 짝지어 기억하면 됩니다."],
    "gap-history-war-timeline": ["이제 임진왜란 전체 기간을 시간순으로 정리합니다.", "재침략인 정유재란을 거쳐 노량 해전에서 끝납니다."],
    "gap-history-war-effects": ["전쟁의 전개가 끝났고, 이제 세 나라에 남은 영향을 봅니다.", "다음에는 조선의 전후 복구 정책으로 이어집니다."],
    "gap-history-reconstruction": ["지금은 광해군의 전후 복구 정책을 설명하고 있습니다.", "복구 뒤에는 명과 후금 사이의 외교가 핵심이 됩니다."],
    "gap-history-neutral-diplomacy": ["이제 명은 약해지고 후금은 강해지는 상황입니다.", "광해군은 두 세력 사이에서 조선의 실리를 택했습니다."],
    "gap-history-horan-compare": ["두 차례 호란의 전개를 본 뒤 결과를 비교하는 부분입니다.", "형제 관계와 군신 관계의 차이가 핵심입니다."],
    "gap-history-policy-flow": ["마지막으로 조선의 대외 정책 변화를 한 흐름으로 묶습니다.", "정책 이름과 등장 순서를 함께 기억하면 됩니다."],
  };

  function cleanSentence(value) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    if (!text) return "";
    return /[.!?。]$/.test(text) ? text : `${text}.`;
  }

  function nearestConcept(concepts, timestampMs) {
    return [...(concepts || [])]
      .filter((item) => Number.isFinite(item.timestamp_ms) && item.timestamp_ms <= timestampMs + 25_000)
      .sort((a, b) => Math.abs(a.timestamp_ms - timestampMs) - Math.abs(b.timestamp_ms - timestampMs))[0] || null;
  }

  function nextConcept(concepts, timestampMs) {
    return [...(concepts || [])]
      .filter((item) => Number.isFinite(item.timestamp_ms) && item.timestamp_ms > timestampMs + 25_000)
      .sort((a, b) => a.timestamp_ms - b.timestamp_ms)[0] || null;
  }

  function contextFor(gap, concepts = []) {
    const prepared = CONTEXTS[gap?.gap_id];
    if (prepared) return { lead: prepared[0], bridge: prepared[1], prepared: true };
    const current = nearestConcept(concepts, gap?.timestamp_ms || 0);
    const next = nextConcept(concepts, gap?.timestamp_ms || 0);
    return {
      lead: current ? `지금은 ${current.keyword}, 이 개념을 설명하는 부분입니다.` : "",
      bridge: next ? `다음 핵심은 ${next.keyword}입니다.` : "",
      prepared: false,
    };
  }

  function compose(gap, concepts = []) {
    if (!gap?.public_description) return "";
    const context = contextFor(gap, concepts);
    return [context.lead, gap.public_description, context.bridge]
      .map(cleanSentence)
      .filter(Boolean)
      .join(" ");
  }

  return { CONTEXTS, contextFor, compose };
});
