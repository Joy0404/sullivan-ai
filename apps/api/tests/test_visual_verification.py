"""Exercise the real two-pass adapter with an explicit HTTP provider boundary."""
import asyncio
import json
import httpx
import pytest
from app.adapters import video_link
from app.core.lecture_agent import LectureAgent
from app.models import AnalysisPackageInput,LectureCreate,VisualObservation,VisualComponent


def package(value,*,kind='number',location='formula_right_number',verification='confirmed'):
    return AnalysisPackageInput(visual_observations=[VisualObservation(observation_id='scene',timestamp_ms=1000,screen_type='graph',kind='graph',text='',confidence=.99,importance=.99,
        metadata={'verification':'confirmed','visible_evidence':['우상향 선과 글자'],'recommended_action':'INTERRUPT'},components=[
          VisualComponent(component_id='trend',kind='graph',text='그래프는 시간이 지날수록 값이 증가합니다.',confidence=.99,verification='confirmed',visible_evidence=['우상향 선']),
          VisualComponent(component_id='disputed',kind=kind,text=value,location=location,confidence=.99,verification=verification,visible_evidence=[value])])])


@pytest.mark.parametrize('first,second,kind,location',[
    ('x=7','x=8','formula','formula_right_number'),('x+7','x-7','formula','formula_sign'),
    ('x<7','x<=7','condition','formula_inequality'),('7 m','7 cm','number','vertical_axis_unit'),
    ('이 문장은 원인입니다.','이 문장은 결과입니다.','highlight','underlined_sentence')])
def test_two_readings_disagree_only_disputed_part_is_withheld(first,second,kind,location):
    draft=package(first,kind=kind,location=location);verified=package(second,kind=kind,location=location)
    guarded=video_link._enforce_model_visual_verification(verified,draft)
    assert guarded.visual_observations[0].components[1].verification=='disagreed'
    agent=LectureAgent();session=agent.create_session(LectureCreate(title='판독 경계 검사'))
    snapshot=agent.analyze(session.session_id,guarded)
    gap=snapshot.visual_gaps[0]
    assert gap.safe_to_speak and '값이 증가' in gap.public_description
    assert gap.hold_notices and gap.public_description.count(gap.hold_notices[0].text)==1
    assert first not in gap.public_description and second not in gap.public_description
    assert gap.source_text=='그래프는 시간이 지날수록 값이 증가합니다.'


def test_actual_gemini_http_path_runs_both_passes_and_component_guard(monkeypatch):
    calls=[];draft=package('PRIVATE_READ_7');verified=package('PRIVATE_READ_8')
    def provider(request):
        calls.append(json.loads(request.content))
        value=draft if len(calls)==1 else verified
        return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':value.model_dump_json()}]}}]})
    original=httpx.AsyncClient
    monkeypatch.setattr(video_link.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(provider),**kwargs))
    result=asyncio.run(video_link._analyze_gemini_video_source('https://fixture.example/public.mp4',mime_type='video/mp4',title='HTTP 경계 시험',subject='수학',problem_mode=False,api_key='fixture-not-a-real-key'))
    assert len(calls)==2 and 'components' in calls[0]['contents'][0]['parts'][1]['text']
    agent=LectureAgent();session=agent.create_session(LectureCreate(title='시험 응답'))
    snapshot=agent.analyze(session.session_id,result)
    assert 'PRIVATE_READ' not in snapshot.model_dump_json()
    assert '값이 증가' in snapshot.visual_gaps[0].public_description


def test_highlight_without_matching_original_evidence_is_held():
    source=package('추측한 밑줄 문장',kind='highlight',location='underlined_sentence')
    source.visual_observations[0].components[1].visible_evidence=['어떤 밑줄이 보임']
    agent=LectureAgent();session=agent.create_session(LectureCreate(title='밑줄 확인'))
    snapshot=agent.analyze(session.session_id,source)
    assert '추측한 밑줄 문장' not in snapshot.model_dump_json()
    assert '밑줄 친 문장' in snapshot.visual_gaps[0].public_description
