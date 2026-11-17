/* Space sequence timing. The caller owns scope, text editing and button activation. */
(function(root) {
  function create({hold, release, taps, doubleTap = () => {}, cancel = () => {}, setTimer = setTimeout, clearTimer = clearTimeout, holdMs = 600, gapMs = 420}) {
    let down = false, held = false, count = 0, holdTimer, tapTimer;
    function reset() { clearTimer(holdTimer); clearTimer(tapTimer); down = held = false; count = 0; }
    return {
      down() {
        if (down) return;
        down = true; held = false; clearTimer(tapTimer);
        holdTimer = setTimer(() => { held = true; count = 0; hold(); }, holdMs);
      },
      up() {
        if (!down) return;
        down = false; clearTimer(holdTimer);
        if (held) { held = false; release(); return; }
        count += 1;
        // Stopping output is safe immediately; a third tap may still open typing.
        if (count === 2) doubleTap();
        // Commit only after the entire sequence, including a possible third tap.
        tapTimer = setTimer(() => { const n = count; count = 0; taps(n); }, gapMs);
      },
      cancel() { reset(); cancel(); },
    };
  }
  const api = {create};
  root.SullivanSpaceGesture = api;
  if (typeof module !== 'undefined') module.exports = api;
})(typeof window === 'undefined' ? globalThis : window);
