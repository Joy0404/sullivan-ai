"""Generate a short self-authored board/graph demonstration, never user media.

The fixture's prepared transcript/observations are deterministic sample data;
the generation step does not call Gemini or analyse the produced clip.
"""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT=Path(__file__).resolve().parents[1]


def generate(output=ROOT/'samples'):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    phases=[('01. Same information already spoken','2x + 1 = 7',0,5),
            ('02. Board differs from lecturer: screen says 7','2x + 1 = 7',5,10),
            ('03. Confirmed trend; axis unit unclear','graph',10,17),
            ('04. Board unreadable','2x + ? = ?',17,23)]
    fontpath=next((str(p) for p in (Path('/System/Library/Fonts/Supplemental/Arial.ttf'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')) if p.exists()),None)
    font=ImageFont.truetype(fontpath,54) if fontpath else ImageFont.load_default(size=54)
    small=ImageFont.truetype(fontpath,23) if fontpath else ImageFont.load_default(size=23)
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg=shutil.which('ffmpeg') or get_ffmpeg_exe()
    except ImportError:
        ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg:raise RuntimeError('Generate once with ffmpeg or imageio-ffmpeg; the packaged MP4 needs neither tool to play.')
    with tempfile.TemporaryDirectory(prefix='sullivan-public-demo-') as temporary:
        temp=Path(temporary)
        for index,(title,text,start,end) in enumerate(phases):
            frame=Image.new('RGB',(960,540),'#f5f7fb');draw=ImageDraw.Draw(frame)
            draw.text((35,30),'Sullivan AI | PREPARED DEMONSTRATION',font=small,fill='#19324d')
            draw.text((35,88),title,font=small,fill='#19324d')
            if text=='graph':
                draw.line([(150,420),(150,175)],fill='#19324d',width=5);draw.line([(150,420),(790,420)],fill='#19324d',width=5)
                draw.line([(160,400),(310,370),(460,305),(620,260),(780,190)],fill='#145daf',width=7)
                draw.text((460,450),'time',font=small,fill='#19324d')
                unit=Image.new('RGB',(105,50),'#f5f7fb');ImageDraw.Draw(unit).text((10,10),'unit',font=small,fill='#19324d')
                frame.paste(unit.filter(ImageFilter.GaussianBlur(8)),(35,185))
            else:
                draw.text((220,240),text,font=font,fill='#19324d')
                if index==3:frame=frame.filter(ImageFilter.GaussianBlur(16))
            ImageDraw.Draw(frame).text((35,500),'Self-authored sample. No uploaded lecture was analysed.',font=small,fill='#19324d')
            frame.save(temp/f'phase-{index}.png')
        listing=''.join(f"file '{(temp/f'phase-{i}.png').as_posix()}'\nduration {end-start}\n" for i,(_,_,start,end) in enumerate(phases))+f"file '{(temp/'phase-3.png').as_posix()}'\n"
        (temp/'frames.txt').write_text(listing)
        # Local synthetic lecturer speech uses only our newly written short text.
        # Never copy uploaded audio or a protected lecture into this public asset.
        if not shutil.which('say'):raise RuntimeError('This optional generator uses macOS say; the packaged public MP4 is ready to play on any supported Chrome platform.')
        audio_inputs=[]
        for index,text in enumerate(('이 엑스 더하기 일은 칠입니다.','이 엑스 더하기 일은 팔입니다.','그래프를 보겠습니다.')):
            path=temp/f'teacher-{index}.aiff'
            subprocess.run(['say','-v','Yuna','-r','180','-o',str(path),text],check=True)
            audio_inputs+=['-i',str(path)]
        audio_filter='[1:a]adelay=0|0[a1];[2:a]adelay=5500|5500[a2];[3:a]adelay=10500|10500[a3];[a1][a2][a3]amix=inputs=3:duration=longest:normalize=0,apad[voice]'
        subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(temp/'frames.txt'),
            *audio_inputs,'-filter_complex',audio_filter,'-map','0:v','-map','[voice]','-t','23','-vf','fps=12,format=yuv420p','-c:v','libx264','-c:a','aac','-movflags','+faststart','-y',str(output/'accessibility-demo.mp4')],check=True)
    verified={'verification':'confirmed','visible_evidence':['직접 작성한 공개 시연 화면'],'recommended_action':'INTERRUPT'}
    package={'transcript_segments':[
        {'segment_id':'same-speech','start_ms':0,'end_ms':3500,'text':'2x + 1 = 7입니다.','confidence':1},
        {'segment_id':'different-speech','start_ms':5500,'end_ms':8500,'text':'2x + 1 = 8입니다.','confidence':1},
        {'segment_id':'graph-speech','start_ms':10500,'end_ms':12000,'text':'그래프를 보겠습니다.','confidence':1}],
      'visual_observations':[
        {'observation_id':'demo-same','timestamp_ms':1000,'screen_type':'board','kind':'formula','text':'2x + 1 = 7','confidence':.99,'importance':.99,'metadata':{**verified,'recommended_action':'INDEX_ONLY'}},
        {'observation_id':'demo-difference','timestamp_ms':6500,'screen_type':'board','kind':'formula','text':'2x + 1 = 7','confidence':.99,'importance':.99,'metadata':verified},
        {'observation_id':'demo-partial','timestamp_ms':12500,'screen_type':'graph','kind':'graph','text':'','confidence':.99,'importance':.99,'metadata':verified,'components':[
          {'component_id':'trend','kind':'graph','text':'그래프는 시간이 지날수록 값이 증가합니다.','confidence':.99,'verification':'confirmed','visible_evidence':['우상향 선'],'location':'center'},
          {'component_id':'axis-unit','kind':'number','text':'','confidence':.2,'verification':'uncertain','visible_evidence':[],'location':'vertical_axis_unit'}]},
        {'observation_id':'demo-whole','timestamp_ms':18500,'screen_type':'board','kind':'formula','text':'','confidence':.2,'importance':.99,'metadata':{'verification':'unverified','uncertain_location':'whole_board'}}],
      'passage_text':None,'highlighted_texts':[], 'study_guide':{}}
    (output/'accessibility-demo.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n')
    (output/'accessibility-demo.srt').write_text('1\n00:00:00,000 --> 00:00:03,500\n2x + 1 = 7입니다.\n\n2\n00:00:05,500 --> 00:00:08,500\n2x + 1 = 8입니다.\n\n3\n00:00:10,500 --> 00:00:12,000\n그래프를 보겠습니다.\n')
    (output/'accessibility-demo.txt').write_text('직접 작성한 판서 차이·부분 보류 시연용 사전 준비 샘플입니다.\n영상과 발화·관측 데이터를 새로 만들었으며 Gemini로 분석했다고 표시하지 않습니다.\n0초: 같은 식은 자동 해설 없이 지나갑니다.\n6.5초: 음성의 8과 화면의 7이 달라 화면의 식을 설명합니다.\n12.5초: 증가 추세는 설명하고 세로축의 단위만 보류합니다.\n18.5초: 장면 전체의 판서를 보류합니다.\n')
    assets=[{'path':'accessibility-demo'+suffix,'provenance':'generated' if suffix=='.mp4' else 'self-authored','license':'CC0-1.0 (self-authored mathematical text and graphics; locally synthesized demonstration speech)'} for suffix in ('.json','.srt','.txt','.mp4')]
    (output/'public-manifest.json').write_text(json.dumps({'schema_version':1,'description':'Self-authored deterministic accessibility demonstration; no uploaded user media or paid analysis','assets':assets},ensure_ascii=False,indent=2)+'\n')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'samples');args=parser.parse_args();print(generate(args.output))
