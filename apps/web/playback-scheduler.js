(function createSullivanPlayback(root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.SullivanPlayback = api;
})(typeof window !== "undefined" ? window : globalThis, () => {
  const AUTOMATIC_ACTIONS = new Set(["INTERRUPT", "DESCRIBE_AT_BREAK"]);

  function automaticGaps(gaps = [], announcedIds = new Set()) {
    return gaps
      .filter((gap) => (
        gap?.safe_to_speak &&
        gap.public_description &&
        AUTOMATIC_ACTIONS.has(gap.action) &&
        !announcedIds.has(gap.gap_id)
      ))
      .sort((a, b) => a.timestamp_ms - b.timestamp_ms);
  }

  function selectDueGap({
    gaps = [],
    announcedIds = new Set(),
    previousMs = null,
    currentMs,
    earlyToleranceMs = 650,
    lateToleranceMs = 5_000,
    seekJumpMs = 12_000,
  }) {
    if (!Number.isFinite(currentMs)) return null;
    const candidates = automaticGaps(gaps, announcedIds);
    if (!candidates.length) return null;

    if (!Number.isFinite(previousMs)) {
      return candidates.find((gap) => (
        gap.timestamp_ms >= currentMs - lateToleranceMs &&
        gap.timestamp_ms <= currentMs + earlyToleranceMs
      )) || null;
    }

    if (currentMs < previousMs - 1_000) return null;
    const delta = currentMs - previousMs;
    if (delta > seekJumpMs) {
      return candidates.find((gap) => (
        gap.timestamp_ms >= currentMs - lateToleranceMs &&
        gap.timestamp_ms <= currentMs + earlyToleranceMs
      )) || null;
    }

    return candidates.find((gap) => (
      gap.timestamp_ms > previousMs - earlyToleranceMs &&
      gap.timestamp_ms <= currentMs + earlyToleranceMs &&
      currentMs - gap.timestamp_ms <= lateToleranceMs
    )) || null;
  }

  function nextAutomaticGap(gaps = [], announcedIds = new Set(), afterMs = 0) {
    return automaticGaps(gaps, announcedIds).find((gap) => gap.timestamp_ms >= afterMs - 500) || null;
  }

  return { automaticGaps, selectDueGap, nextAutomaticGap };
});
