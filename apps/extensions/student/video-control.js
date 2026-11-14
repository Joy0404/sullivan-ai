// Serialized into an isolated world. Never reads account data or lecture text.
export async function controlVideo(action, value, expected) {
  try {
    const key='__sullivanStudentVideo',owned=globalThis[key];
    if(action==='release'){
      clearTimeout(owned?.timer);owned?.video?.pause();delete globalThis[key];return {released:true};
    }
    const here=new URL(location.href);
    if(action!=='probe'){
      const wanted=new URL(expected);
      const youtube=url=>{
        if(url.hostname==='youtu.be')return url.pathname.split('/')[1];
        if(!/(^|\.)(youtube\.com|youtube-nocookie\.com)$/.test(url.hostname))return null;
        return url.pathname==='/watch'?url.searchParams.get('v'):url.pathname.match(/^\/(?:embed|shorts|e)\/([^/]+)/)?.[1];
      };
      const same=youtube(wanted)?youtube(here)===youtube(wanted)&&here.protocol==='https:':here.href===wanted.href;
      if(!same)throw new Error('연결한 강의 주소가 변경됐습니다. 강의를 다시 연결하세요.');
    }
    const origins=new Set(),videos=[],seen=new Set();
    function scan(root){
      if(seen.has(root))return;seen.add(root);
      for(const video of root.querySelectorAll?.('video')||[])videos.push(video);
      for(const element of root.querySelectorAll?.('*')||[]){
        if(element.shadowRoot)scan(element.shadowRoot);
        if(element.tagName==='IFRAME'){
          try{if(element.contentDocument)scan(element.contentDocument);}catch{}
          try{const url=new URL(element.src,here.href);if(['http:','https:'].includes(url.protocol)&&url.origin!==here.origin)origins.add(url.origin+'/*');}catch{}
        }
      }
    }
    function rank(video){
      const rect=video.getBoundingClientRect?.()||{width:0,height:0};
      const style=video.ownerDocument?.defaultView?.getComputedStyle?.(video);
      const visible=rect.width>0&&rect.height>0&&!video.hidden&&style?.visibility!=='hidden'&&style?.display!=='none'&&style?.opacity!=='0';
      return (video.matches?.('video.html5-main-video')?1e12:0)+(visible?1e9:0)
        +Math.min(1e7,Math.max(0,rect.width*rect.height))*100+(!video.paused?1e6:0)
        +(Number.isFinite(video.duration)?Math.min(video.duration,86400):0);
    }
    let video=owned?.video;
    if(action==='probe'||!video){
      scan(document);
      if(!videos.length){const fallback=document.querySelector?.('video.html5-main-video')||document.querySelector?.('video');if(fallback)videos.push(fallback);}
      video=videos.sort((a,b)=>rank(b)-rank(a))[0];
    }
    if(action==='probe')return {found:Boolean(video),score:video?rank(video):0,url:here.href,permissionOrigins:[...origins].slice(0,8),drm:Boolean(video?.mediaKeys)};
    if(!video)throw new Error('이 페이지에서 재생할 영상을 찾지 못했습니다. 강의 플레이어를 연 뒤 다시 연결하세요.');
    if(video.isConnected===false)throw new Error('강의 플레이어가 변경됐습니다. 현재 영상을 다시 연결하세요.');
    if(video.mediaKeys)throw new Error('보호된 영상은 확장에서 직접 제어할 수 없습니다. 사이트에서 재생하고 준비된 자료·명령을 이용하세요.');
    const lease=owned||(globalThis[key]={video});lease.video=video;
    clearTimeout(lease.timer);lease.timer=setTimeout(()=>video.pause(),4000);
    const ad=Boolean(document.querySelector?.('.html5-video-player.ad-showing,.vjs-ad-playing,[data-ad-playing="true"]'));
    if(action==='pause')video.pause();
    if(action==='play')await video.play();
    if(action==='audio'){
      if(!Number.isFinite(value?.volume)||value.volume<0||value.volume>1||typeof value.muted!=='boolean')throw new Error('음량 범위를 확인하세요.');
      video.volume=value.volume;video.muted=value.muted;
    }
    if(action==='seek'){
      if(ad||!Number.isFinite(video.duration)||!Number.isFinite(value))throw new Error('광고·실시간 영상에서는 구간 이동을 지원하지 않습니다.');
      video.currentTime=Math.max(0,Math.min(video.duration,value/1000));
    }
    return {positionMs:Math.round(video.currentTime*1000),durationMs:Number.isFinite(video.duration)?Math.round(video.duration*1000):null,
      paused:video.paused,ended:video.ended,ad,verified:true};
  }catch(error){return {error:error.message};}
}
