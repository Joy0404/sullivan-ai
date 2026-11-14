import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import local_access, main
from app.core.lecture_agent import LectureAgent
from app.models import AnalysisPackageInput
from test_extension_access import PASSWORD, family, headers

BASE = '/extension/v1/guardian'
SUBTITLE = '1\n00:00:01,000 --> 00:00:04,000\n별은 중력으로 모여 형성됩니다.\n'


def test_extension_publishes_arbitrary_page_and_spa_route_without_analysis(family):
    client, guardian, student_id, student = family
    gh = headers('guardian', guardian['token'])
    url = 'https://lecture.example/course?id=7#/lesson/3'
    job = prepare(client, gh, link={'url':url,'rights_confirmed':True,'request_analysis':False})
    assert job['state']=='completed'
    assert job['playback']=={'kind':'external','normalized_url':url}
    published=client.post(BASE+'/preparations/'+job['id']+'/publish',headers=gh,json={'students':[student_id]})
    assert published.status_code==200, published.text
    lesson=client.get('/extension/v1/student/lectures/'+published.json()['id'],headers=headers('student',student['token']))
    assert lesson.status_code==200
    assert lesson.json()['playback']['kind']=='external'
    assert lesson.json()['playback']['normalized_url']==url


def test_extension_link_only_playback_is_not_claimed_as_analysis(family,monkeypatch):
    client,guardian,student_id,student=family
    monkeypatch.setenv('GEMINI_API_KEY','')
    gh=headers('guardian',guardian['token'])
    job=prepare(client,gh,assets=[],link={'url':'https://lecture.example/watch/7','rights_confirmed':True,'request_analysis':False})
    assert job['state']=='completed' and '분석은 실행하지 않았습니다' in job['message']
    assert not job['snapshot']['transcript_segments'] and job['snapshot']['safe_description_count']==0
    published=client.post(BASE+'/preparations/'+job['id']+'/publish',headers=gh,json={'students':[student_id]})
    assert published.status_code==200,published.text
    result=client.get('/extension/v1/student/lectures/'+published.json()['id'],headers=headers('student',student['token']))
    assert result.status_code==200 and result.json()['playback']['kind']=='external'
    with local_access.db() as con:con.execute('UPDATE lectures SET chat_allowed=1 WHERE id=?',(published.json()['id'],))
    monkeypatch.setenv('GEMINI_API_KEY','fixture-key-not-used')
    response=client.post('/local/lectures/'+published.json()['id']+'/agent-turn',headers=headers('student',student['token']),json={'message':'내용 요약'})
    assert response.status_code==400 and '내용 질문에는' in response.text
    preview=client.post(BASE+'/preparations/'+job['id']+'/agent-turn',headers=gh,json={'message':'내용 요약','analysis_consent':True})
    assert preview.status_code==400 and '링크 등록은 영상 분석이 아닙니다' in preview.text


def test_large_local_playback_registration_stores_metadata_not_media(family,monkeypatch):
    client,guardian,student_id,student=family
    monkeypatch.setenv('GEMINI_API_KEY','')
    gh=headers('guardian',guardian['token'])
    metadata={'name':'large-lecture.mkv','size_bytes':2_000_000_000}
    job=prepare(client,gh,assets=[],local_file=metadata)
    assert job['state']=='completed' and '원본은 전송하지 않았고' in job['message']
    assert job['playback']=={'kind':'local-reference',**metadata}
    assert not job['snapshot']['transcript_segments'] and job['snapshot']['safe_description_count']==0
    result=client.post(BASE+'/preparations/'+job['id']+'/publish',headers=gh,json={'students':[student_id]})
    assert result.status_code==200,result.text
    lesson=client.get('/extension/v1/student/lectures/'+result.json()['id'],headers=headers('student',student['token']))
    assert lesson.status_code==200 and lesson.json()['media_identity']=={'kind':'local-reference',**metadata}
    with local_access.db() as con:
        row=con.execute('SELECT playback FROM preparations WHERE id=?',(job['id'],)).fetchone()[0]
        assert json.loads(row)=={'kind':'local-reference',**metadata}


def prepare(client, gh, **overrides):
    payload = {'title': '준비한 강의', 'assets': [
        {'name': '지문.txt', 'kind': 'passage', 'content': '첫 문단입니다.\n\n둘째 문단입니다.'},
        {'name': '자막.srt', 'kind': 'subtitle', 'content': SUBTITLE}]}
    payload.update(overrides)
    response = client.post(BASE + '/preparations', headers=gh, json=payload)
    assert response.status_code == 202, response.text
    job = client.get(BASE + '/preparations/' + response.json()['id'], headers=gh)
    assert job.status_code == 200
    return job.json()


@pytest.mark.parametrize('url',['https://www.youtube.com/watch?v=OtherVideo123','https://lecture.example/watch#/lesson/7'])
def test_authenticated_extension_analysis_is_not_limited_to_demo_samples(family,monkeypatch,url):
    client,guardian,_,_=family
    calls=[]
    async def analyzer(source,**kwargs):
        calls.append(source)
        return AnalysisPackageInput(passage_text='명시적 동의와 인증을 검사하는 공급자 경계 자료입니다.')
    monkeypatch.setenv('GEMINI_API_KEY','fixture-not-used')
    monkeypatch.setattr(main,'analyze_video_link',analyzer)
    job=prepare(client,headers('guardian',guardian['token']),assets=[],link={
        'url':url,'rights_confirmed':True,'request_analysis':True,'analysis_consent':True})
    assert job['state']=='completed',job
    assert calls==[url]


@pytest.mark.parametrize('credential',['forged','student'])
def test_arbitrary_analysis_requires_real_guardian_before_provider_or_quota(family,monkeypatch,credential):
    client,guardian,_,student=family
    calls=[]
    async def analyzer(*args,**kwargs):calls.append('provider');raise AssertionError('unauthorized provider call')
    monkeypatch.setenv('GEMINI_API_KEY','fixture-not-used')
    monkeypatch.setattr(main,'analyze_video_link',analyzer)
    monkeypatch.setattr(main.limiter,'consume',lambda *args:calls.append('quota'))
    created=client.post('/v1/lectures',headers=headers('guardian',guardian['token']),json={'title':'인증 경계','subject':'일반','problem_mode':True})
    assert created.status_code==201,created.text
    session=created.json()['session_id']
    auth=headers('guardian','forged') if credential=='forged' else headers('student',student['token'])
    response=client.post('/v1/lectures/'+session+'/video-link',headers=auth,json={
        'url':'https://lecture.example/watch#/lesson/7','rights_confirmed':True,
        'request_analysis':True,'analysis_consent':True})
    assert response.status_code in (401,403),response.text
    assert not calls


def test_total_material_limit_has_actionable_error_without_echo(family):
    client, guardian, _, _ = family
    gh=headers('guardian',guardian['token'])
    secret='DO_NOT_ECHO_PRIVATE_MATERIAL'
    payload={'title':'자료 전체 제한 검사','assets':[{'name':f'{i}.txt','kind':'passage','content':secret+'가'*260000} for i in range(4)]}
    response=client.post(BASE+'/preparations',headers=gh,json=payload)
    assert response.status_code==422
    assert '자료 전체' in response.json()['detail'] and '100만' in response.json()['detail']
    assert secret not in response.text and 'input' not in response.json()
    # Other validation errors retain the generic safe response.
    invalid=client.post(BASE+'/preparations',headers=gh,json={'title':'','assets':payload['assets'][:1]})
    assert invalid.status_code==422 and invalid.json()['detail']=='요청 형식을 확인해 주세요.'


def test_materials_durable_results_and_atomic_publication(family, monkeypatch):
    client, guardian, student_id, student = family
    gh = headers('guardian', guardian['token'])
    sh = headers('student', student['token'])
    job = prepare(client, gh)
    assert job['state'] == 'completed'
    assert job['snapshot']['passage']['sentence_count'] == 2
    assert job['snapshot']['transcript_segments'][0]['start_ms'] == 1000
    # A fresh agent has no prior in-memory sessions: publication must use DB only.
    monkeypatch.setattr(main, 'agent', LectureAgent())
    assigned = client.post(BASE + '/preparations/' + job['id'] + '/publish', headers=gh, json={'students': [student_id]})
    assert assigned.status_code == 200, assigned.text
    ident = assigned.json()['id']
    again = client.post(BASE + '/preparations/' + job['id'] + '/publish', headers=gh, json={'students': [student_id]})
    assert again.json()['id'] == ident and again.json()['already_published']
    assert len(client.get('/local/lectures', headers=sh).json()) == 1
    assert client.get('/local/lectures/' + ident, headers=sh).json()['snapshot']['passage']['sentence_count'] == 2


def test_preparation_preserves_source_and_preferred_mode(family):
    client, guardian, _, _ = family
    gh = headers('guardian', guardian['token'])
    job = prepare(client, gh, source_label='학교 수업', preferred_mode='passage')
    assert job['snapshot']['session']['source_label'] == '학교 수업'
    assert job['snapshot']['session']['preferred_mode'] == 'passage'
    bad = client.post(BASE + '/preparations', headers=gh, json={
        'title': '잘못된 모드', 'preferred_mode': 'unknown',
        'assets': [{'name': 'p.txt', 'kind': 'passage', 'content': '학습자료'}]})
    assert bad.status_code == 422


def test_preview_chat_owner_consent_and_persisted_safe_context(family, monkeypatch):
    from app.adapters import gemini_agent
    from app.models import AgentTurnResponse
    client, guardian, _, student = family
    gh = headers('guardian', guardian['token'])
    job = prepare(client, gh)
    endpoint = BASE + '/preparations/' + job['id'] + '/agent-turn'
    payload = {'message': '첫 문단을 설명해 주세요.', 'analysis_consent': True}
    assert client.post(endpoint, headers=headers('student', student['token']), json=payload).status_code == 403
    other = client.post(BASE + '/register', headers=headers('guardian'), json={'username': 'preview-other', 'password': PASSWORD}).json()
    assert client.post(endpoint, headers=headers('guardian', other['token']), json=payload).status_code == 404
    assert client.post(endpoint, headers=gh, json={'message': '질문'}).status_code == 400
    assert client.post(endpoint, headers=gh, json=payload).status_code == 503
    seen = []
    async def reply(snapshot, **kwargs):
        seen.append(snapshot)
        return AgentTurnResponse(action='answer', title='확인', response_text='첫 문단입니다.', decision_reason='준비 자료', confidence=.99)
    monkeypatch.setenv('GEMINI_API_KEY', 'fixture-key')
    monkeypatch.setattr(gemini_agent, 'run_agent_turn', reply)
    monkeypatch.setattr(main, 'agent', LectureAgent())
    injected = dict(job['snapshot']); injected['session'] = dict(injected['session'], title='UNTRUSTED_CONTEXT')
    result = client.post(endpoint, headers=gh, json={**payload, 'snapshot': injected})
    assert result.status_code == 200, result.text
    assert seen[0].session.title == job['title']
    assert 'UNTRUSTED_CONTEXT' not in seen[0].model_dump_json()
    with local_access.db() as con:
        con.execute("UPDATE preparations SET state='running' WHERE id=?", (job['id'],))
    assert client.post(endpoint, headers=gh, json=payload).status_code == 409


def test_caption_only_preparation_can_be_republished(family):
    client, guardian, student_id, student = family
    gh = headers('guardian', guardian['token'])
    job = prepare(client, gh, assets=[{'name': 'a.vtt', 'kind': 'subtitle', 'content': SUBTITLE}])
    assert job['state'] == 'completed'
    ident = client.post(BASE + '/preparations/' + job['id'] + '/publish', headers=gh, json={'students': [student_id]}).json()['id']
    assert client.post(BASE + '/lectures/' + ident + '/withdraw', headers=gh, json={'students': [student_id]}).status_code == 200
    assert client.put('/local/lectures/' + ident, headers=gh, json={'title': '다시 배정', 'subject': '과학', 'students': [student_id]}).status_code == 200
    assert client.put('/local/lectures/' + ident + '/ready', headers=gh).status_code == 200


def test_preparations_role_owner_and_cookie_isolation(family):
    client, guardian, student_id, student = family
    gh = headers('guardian', guardian['token'])
    job = prepare(client, gh)
    other = client.post(BASE + '/register', headers=headers('guardian'), json={'username': 'other', 'password': PASSWORD}).json()
    oh = headers('guardian', other['token'])
    assert client.get(BASE + '/preparations/' + job['id'], headers=oh).status_code == 404
    assert client.get(BASE + '/preparations', headers=oh).json() == []
    assert client.post(BASE + '/preparations/' + job['id'] + '/publish', headers=oh, json={'students': [student_id]}).status_code == 404
    assert client.get(BASE + '/preparations', headers=headers('student', student['token'])).status_code == 403
    assert client.post('/local/login', headers={'X-Local-Request': '1'}, json={'username': 'guardian', 'password': PASSWORD}).status_code == 200
    assert client.get(BASE + '/preparations', headers=headers('guardian')).status_code == 401


def test_interrupted_recovery_blocks_partial_result_and_does_not_retry(family):
    client, guardian, student_id, _ = family
    gh = headers('guardian', guardian['token'])
    job = prepare(client, gh)
    with local_access.db() as con:
        con.execute("UPDATE preparations SET state='running', instance='old-process' WHERE id=?", (job['id'],))
    state = client.get(BASE + '/preparations/' + job['id'], headers=gh).json()
    assert state['state'] == 'interrupted' and 'snapshot' not in state
    assert client.post(BASE + '/preparations/' + job['id'] + '/publish', headers=gh, json={'students': [student_id]}).status_code == 409


def test_imported_json_keeps_blocked_text_out_of_db_and_student_outputs(family):
    client, guardian, student_id, student = family
    gh = headers('guardian', guardian['token'])
    job = prepare(client, gh, assets=[], analysis={
        'transcript_segments': [{'segment_id': 't1', 'start_ms': 0, 'end_ms': 2000, 'text': '학습 안내'}],
        'visual_observations': [
            {'observation_id': 'v1', 'timestamp_ms': 2000, 'screen_type': 'board', 'kind': 'answer', 'text': 'SECRET_ANSWER', 'confidence': .99},
            {'observation_id': 'v2', 'timestamp_ms': 3000, 'screen_type': 'board', 'text': 'LOW_CONFIDENCE_SECRET', 'confidence': .4}],
        'passage_text': 'SECRET_ANSWER', 'study_guide': {'overview': 'SECRET_ANSWER'}})
    assert job['state'] == 'completed'
    encoded = json.dumps(job, ensure_ascii=False)
    assert 'SECRET_ANSWER' not in encoded and 'LOW_CONFIDENCE_SECRET' not in encoded
    with local_access.db() as con:
        stored = con.execute('SELECT snapshot FROM preparations WHERE id=?', (job['id'],)).fetchone()[0]
        assert 'SECRET_ANSWER' not in stored and 'LOW_CONFIDENCE_SECRET' not in stored
    ident = client.post(BASE + '/preparations/' + job['id'] + '/publish', headers=gh, json={'students': [student_id]}).json()['id']
    assert 'SECRET_ANSWER' not in client.get('/local/lectures/' + ident, headers=headers('student', student['token'])).text


def test_link_registration_and_analysis_fail_closed(family, monkeypatch):
    client, guardian, _, _ = family
    gh = headers('guardian', guardian['token'])
    monkeypatch.setenv('GEMINI_API_KEY', '')
    link = {'url': 'https://www.youtube.com/watch?v=R0dqsl3Vgns', 'rights_confirmed': True,
            'request_analysis': True, 'analysis_consent': True, 'access_code': 'DO_NOT_PERSIST_CODE'}
    job = prepare(client, gh, link=link)
    assert job['state'] == 'failed' and 'snapshot' not in job
    with local_access.db() as con:
        row = dict(con.execute('SELECT * FROM preparations WHERE id=?', (job['id'],)).fetchone())
        assert 'DO_NOT_PERSIST_CODE' not in json.dumps(row)
    no_consent = client.post(BASE + '/preparations', headers=gh, json={'title': '권한 없음', 'link': link | {'analysis_consent': False}})
    assert no_consent.status_code == 400
    registered = prepare(client, gh, link=link | {'request_analysis': False, 'analysis_consent': False})
    assert registered['state'] == 'completed' and registered['playback']['kind'] == 'youtube'
    invalid = prepare(client, gh, assets=[{'name': 'invalid.srt', 'kind': 'subtitle', 'content': '시간 정보 없음'}])
    assert invalid['state'] == 'failed'


def test_actual_link_route_reuses_existing_provider_contract(family, monkeypatch):
    client, guardian, _, _ = family
    gh = headers('guardian', guardian['token'])
    calls = []
    async def analyzer(url, **kwargs):
        calls.append((url, kwargs))
        return AnalysisPackageInput(passage_text='외부 공급자 대신 제공하는 검증용 분석 결과입니다.')
    monkeypatch.setenv('GEMINI_API_KEY', 'fake-test-key')
    monkeypatch.delenv('DEMO_ACCESS_CODE',raising=False)
    monkeypatch.setattr(main, 'analyze_video_link', analyzer)
    job = prepare(client, gh, assets=[], link={'url': 'https://www.youtube.com/watch?v=R0dqsl3Vgns',
        'rights_confirmed': True, 'request_analysis': True, 'analysis_consent': True})
    assert job['state'] == 'completed', job
    assert len(calls) == 1 and calls[0][1]['problem_mode'] is True
    assert calls[0][1]['api_key_override'] == 'fake-test-key'
    assert job['playback']['kind'] == 'youtube'


def test_settings_edit_order_withdrawal_and_progress_preservation(family):
    client, guardian, student_id, student = family
    gh, sh = headers('guardian', guardian['token']), headers('student', student['token'])
    identifiers = []
    for title in ('첫 강의', '둘째 강의'):
        job = prepare(client, gh, title=title)
        identifiers.append(client.post(BASE + '/preparations/' + job['id'] + '/publish', headers=gh, json={'students': [student_id]}).json()['id'])
    ident = identifiers[0]
    assert client.put('/local/lectures/' + ident, headers=gh, json={'title': '수정된 강의', 'subject': '국어', 'students': [student_id]}).status_code == 200
    assert client.put('/local/order', headers=gh, json={'student': student_id, 'lectures': identifiers[::-1]}).status_code == 200
    assert [l['id'] for l in client.get('/local/lectures', headers=sh).json()] == identifiers[::-1]
    assert client.put('/local/students/' + student_id + '/settings', headers=gh, json={'speech_rate': 1.15, 'reader_mode': True}).status_code == 200
    assert client.get('/local/me', headers=sh).json()['settings']['speech_rate'] == 1.15
    assert client.put('/local/lectures/' + ident + '/progress', headers=sh, json={'note': '개인 메모', 'position_ms': 2000}).status_code == 200
    assert client.post(BASE + '/lectures/' + ident + '/withdraw', headers=gh, json={'students': [student_id]}).status_code == 200
    assert client.get('/local/lectures/' + ident, headers=sh).status_code == 403
    with local_access.db() as con:
        assert '개인 메모' in con.execute('SELECT payload FROM progress WHERE lecture=?', (ident,)).fetchone()[0]
    assert client.post(BASE + '/lectures/' + ident + '/withdraw', headers=gh, json={'students': [student_id]}).status_code == 400


@pytest.mark.parametrize('cleanup_failure', [False, True])
def test_consented_video_uses_existing_analyzer_and_cleans_raw_file(family, monkeypatch, cleanup_failure):
    client, guardian, _, _ = family
    gh = headers('guardian', guardian['token'])
    paths = []
    async def analyzer(path, **kwargs):
        paths.append(Path(path))
        assert Path(path).read_bytes() == b'ORIGINAL_VIDEO_SENTINEL'
        kwargs['cleanup_report']['provider'] = 'delete-failed' if cleanup_failure else 'deleted'
        return AnalysisPackageInput(passage_text='실제 분석 어댑터를 대신한 테스트 결과입니다.')
    monkeypatch.setenv('GEMINI_API_KEY', 'fake-test-key')
    monkeypatch.delenv('DEMO_ACCESS_CODE',raising=False)
    monkeypatch.setattr(main, 'analyze_uploaded_video_with_gemini', analyzer)
    response = client.post(BASE + '/preparations/video-file-analysis', headers=gh,
        data={'title': '파일 분석', 'rights_confirmed': 'true', 'cloud_analysis_consent': 'true'},
        files={'video': ('lecture.mp4', b'ORIGINAL_VIDEO_SENTINEL', 'video/mp4')})
    assert response.status_code == 202, response.text
    job = client.get(BASE + '/preparations/' + response.json()['id'], headers=gh).json()
    assert job['state'] == ('failed' if cleanup_failure else 'completed')
    assert paths and all(not path.exists() for path in paths)
    with local_access.db() as con:
        stored = json.dumps(dict(con.execute('SELECT * FROM preparations WHERE id=?', (job['id'],)).fetchone()))
        assert 'ORIGINAL_VIDEO_SENTINEL' not in stored and 'test-code' not in stored
    denied = client.post(BASE + '/preparations/video-file-analysis', headers=gh,
        data={'title': '동의 없음'}, files={'video': ('lecture.mp4', b'no', 'video/mp4')})
    assert denied.status_code == 400
