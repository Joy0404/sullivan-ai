// Serialized by chrome.scripting into the isolated world. No account data enters this function.
export async function controlVideo(action, value, expected) {
  try {
  const here = new URL(location.href), wanted = new URL(expected);
  const youtube = url => /(^|\.)youtube\.com$/.test(url.hostname) && url.pathname === '/watch' ? url.searchParams.get('v') : null;
  const same = youtube(wanted) ? youtube(here) === youtube(wanted) && here.protocol === 'https:'
    : here.origin === wanted.origin && here.pathname === wanted.pathname && here.search === wanted.search;
  if (!same) throw new Error('연결한 강의 주소가 변경됐습니다. 강의를 다시 연결하세요.');
  const video = document.querySelector('video.html5-main-video') || document.querySelector('video');
  if (!video || video.mediaKeys) throw new Error('이 페이지의 영상 플레이어는 지원하지 않습니다.');
  const ad = Boolean(document.querySelector('.html5-video-player.ad-showing'));
  const key = '__sullivanStudentVideo';
  const lease = globalThis[key] || (globalThis[key] = {});
  clearTimeout(lease.timer);
  if (action !== 'release') lease.timer = setTimeout(() => video.pause(), 4000);
  if (action === 'pause' || action === 'release') video.pause();
  if (action === 'play') await video.play();
  if (action === 'audio') {
    if (!Number.isFinite(value?.volume) || value.volume < 0 || value.volume > 1 || typeof value.muted !== 'boolean') throw new Error('음량 범위를 확인하세요.');
    video.volume = value.volume; video.muted = value.muted;
  }
  if (action === 'seek') {
    if (ad || !Number.isFinite(video.duration) || !Number.isFinite(value)) throw new Error('광고·실시간 영상에서는 구간 이동을 지원하지 않습니다.');
    video.currentTime = Math.max(0, Math.min(video.duration, value / 1000));
  }
  return {positionMs: Math.round(video.currentTime * 1000), durationMs: Number.isFinite(video.duration) ? Math.round(video.duration * 1000) : null,
    paused: video.paused, ended: video.ended, ad, verified: true};
  } catch (error) { return {error: error.message}; }
}
