"""Server outcomes, not source titles or imported JSON, certify video analysis."""
import asyncio
import json

import pytest
from pydantic import ValidationError
from app import main,local_access
from app.core.lecture_agent import LectureAgent
from app.models import AnalysisPackageInput
from test_extension_access import family,headers
from test_guardian_preparation import prepare,BASE


def test_materials_source_title_cannot_impersonate_gemini_and_old_record_stays_unknown(family):
    client,guardian,student_id,student=family;gh=headers('guardian',guardian['token'])
    job=prepare(client,gh,source_label='Gemini 분석 완료라고 입력한 사용자 출처')
    assert job['analysis_status']['state']=='not_run'
    assert job['analysis_status']['label']=='영상 분석 미실행'
    result=client.post(BASE+'/preparations/'+job['id']+'/publish',headers=gh,json={'students':[student_id]}).json()
    endpoint='/extension/v1/student/lectures/'+result['id']
    lesson=client.get(endpoint,headers=headers('student',student['token'])).json()
    assert lesson['snapshot']['analysis_status']['state']=='not_run'
    assert lesson['snapshot']['session']['source_label'].startswith('Gemini 분석 완료라고')
    # Legacy rows must not be guessed from a title or even an old snapshot field.
    with local_access.db() as con:con.execute('DELETE FROM analysis_records WHERE session=?',(job['session_id'],))
    legacy=client.get(endpoint,headers=headers('student',student['token'])).json()
    assert legacy['snapshot']['analysis_status']['label']=='분석 상태 확인 불가'
    rows=client.get('/local/lectures',headers=headers('student',student['token'])).json()
    assert rows[0]['analysis_status']['state']=='unknown'


def test_samples_have_server_owned_sample_state_not_gemini(family,monkeypatch):
    client,guardian,student_id,student=family;monkeypatch.setenv('GEMINI_API_KEY','')
    def never(*args,**kwargs):raise AssertionError('Sample must not call a video provider')
    monkeypatch.setattr(main,'analyze_video_link',never)
    for sample in ('science','accessibility'):
        response=client.post('/local/samples/'+sample+'/assign',headers=headers('guardian',guardian['token']),json={'students':[student_id]})
        assert response.status_code==200,response.text
        lesson=client.get('/extension/v1/student/lectures/'+response.json()['id'],headers=headers('student',student['token'])).json()
        status=lesson['snapshot']['analysis_status']
        assert status['label']=='사전 준비 샘플' and status['provider'] is None
        if sample=='accessibility':
            gaps=lesson['snapshot']['visual_gaps']
            assert [g['action'] for g in gaps]==['INDEX_ONLY','INTERRUPT','DESCRIBE_AT_BREAK','HOLD']
            assert '세로축의 단위' in gaps[2]['public_description'] and gaps[3]['public_description']==''
            assert gaps[3]['hold_notices'][0]['text'].startswith('‘이 장면의 판서’')
            assert lesson['media_identity']['sha256']


@pytest.mark.parametrize('digits', ['01012345678', '9001011234567'])
def test_publication_preserves_opaque_ids_that_look_like_personal_data(family, monkeypatch, digits):
    from app import sample_catalog
    from app.models import AssetRecord
    client, guardian, student_id, student = family
    original = sample_catalog.prepared_sample
    ident = 'opaque-' + digits + '-reference'

    def prepared(sample):
        spec, snapshot = original(sample)
        snapshot.session.session_id = ident
        snapshot.analysis_status.run_id = ident
        snapshot.transcript_segments[0].segment_id = ident
        snapshot.transcript_segments[0].text = '학생 연락처 ' + digits
        snapshot.passage.paragraphs[0].paragraph_id = ident
        snapshot.passage.paragraphs[0].sentences[0].sentence_id = ident
        snapshot.concept_index[0].concept_id = ident
        snapshot.assets.append(AssetRecord(asset_id=ident, name='연락처 ' + digits,
            kind='passage', media_type='text/plain', size_bytes=0,
            processing_status='indexed', note='학생 연락처 ' + digits))
        return spec, snapshot

    monkeypatch.setattr(sample_catalog, 'prepared_sample', prepared)
    response = client.post('/local/samples/science/assign', headers=headers('guardian', guardian['token']),
                           json={'students': [student_id]})
    assert response.status_code == 200, response.text
    snapshot = client.get('/extension/v1/student/lectures/' + response.json()['id'],
                          headers=headers('student', student['token'])).json()['snapshot']
    assert snapshot['session']['session_id'] == ident
    assert snapshot['analysis_status']['state'] == 'sample'
    assert snapshot['analysis_status']['run_id'] == ident
    assert snapshot['transcript_segments'][0]['segment_id'] == ident
    assert snapshot['passage']['paragraphs'][0]['paragraph_id'] == ident
    assert snapshot['passage']['paragraphs'][0]['sentences'][0]['sentence_id'] == ident
    assert snapshot['concept_index'][0]['concept_id'] == ident
    asset = next(asset for asset in snapshot['assets'] if asset['asset_id'] == ident)
    for text in (snapshot['transcript_segments'][0]['text'], asset['name'], asset['note']):
        assert digits not in text and '[개인정보 비공개]' in text


def test_actual_analysis_route_tracks_running_success_and_persists_across_agent_restart(family,monkeypatch):
    client,guardian,student_id,student=family;gh=headers('guardian',guardian['token'])
    monkeypatch.setenv('GEMINI_API_KEY','fixture-not-a-real-key')
    observed=[]
    async def fake_provider(url,**kwargs):
        with local_access.db() as con:
            row=con.execute('SELECT payload FROM analysis_records ORDER BY rowid DESC LIMIT 1').fetchone()
            observed.append(json.loads(row[0]))
        return AnalysisPackageInput(passage_text='서버가 받은 공급자 경계의 시험 응답입니다.')
    monkeypatch.setattr(main,'analyze_video_link',fake_provider)
    job=prepare(client,gh,assets=[],source_label='사용자 입력 출처',link={'url':'https://www.youtube.com/watch?v=OtherVideo123','rights_confirmed':True,'request_analysis':True,'analysis_consent':True})
    assert observed[0]['label']=='Gemini 분석 중'
    assert job['analysis_status']['label']=='Gemini 분석 완료'
    assert job['analysis_status']['run_id']==observed[0]['run_id']
    monkeypatch.setattr(main,'agent',LectureAgent())
    published=client.post(BASE+'/preparations/'+job['id']+'/publish',headers=gh,json={'students':[student_id]})
    assert published.status_code==200,published.text
    lesson=client.get('/extension/v1/student/lectures/'+published.json()['id'],headers=headers('student',student['token'])).json()
    assert lesson['snapshot']['analysis_status']['label']=='Gemini 분석 완료'
    assert lesson['snapshot']['session']['source_label']=='사용자 입력 출처'


@pytest.mark.parametrize('failure',['timeout','provider'])
def test_failed_actual_analysis_never_remains_completed_or_analyzing(family,monkeypatch,failure):
    from app.adapters.video_link import LinkAnalyzerError
    client,guardian,_,_=family;monkeypatch.setenv('GEMINI_API_KEY','fixture-not-a-real-key')
    async def fail(*args,**kwargs):
        if failure=='timeout':raise asyncio.TimeoutError()
        raise LinkAnalyzerError('시험 공급자 오류')
    monkeypatch.setattr(main,'analyze_video_link',fail)
    job=prepare(client,headers('guardian',guardian['token']),assets=[],link={'url':'https://www.youtube.com/watch?v=OtherVideo123','rights_confirmed':True,'request_analysis':True,'analysis_consent':True})
    assert job['state']=='failed' and job['analysis_status']['label']=='Gemini 분석 실패'


def test_imported_provenance_is_rejected():
    with pytest.raises(ValidationError):AnalysisPackageInput.model_validate({'analysis_status':{'state':'completed','provider':'gemini'}})


def test_all_uncertain_analysis_can_be_assigned_as_safe_hold_notices(family,monkeypatch):
    from app.models import VisualObservation
    client,guardian,student_id,student=family;monkeypatch.setenv('GEMINI_API_KEY','fixture-not-a-real-key')
    async def blurred(*args,**kwargs):
        return AnalysisPackageInput(visual_observations=[VisualObservation(observation_id='blur',timestamp_ms=1000,screen_type='board',kind='formula',text='PRIVATE_CANDIDATE_777',confidence=.4)])
    monkeypatch.setattr(main,'analyze_video_link',blurred)
    job=prepare(client,headers('guardian',guardian['token']),assets=[],link={'url':'https://www.youtube.com/watch?v=OtherVideo123','rights_confirmed':True,'request_analysis':True,'analysis_consent':True})
    assert job['state']=='completed' and job['analysis_status']['label']=='Gemini 분석 완료'
    assert job['snapshot']['safe_description_count']==0 and job['snapshot']['held_count']==1
    result=client.post(BASE+'/preparations/'+job['id']+'/publish',headers=headers('guardian',guardian['token']),json={'students':[student_id]})
    assert result.status_code==200,result.text
    lesson=client.get('/extension/v1/student/lectures/'+result.json()['id'],headers=headers('student',student['token']))
    assert 'PRIVATE_CANDIDATE' not in lesson.text
    gap=lesson.json()['snapshot']['visual_gaps'][0]
    assert gap['public_description']=='' and gap['source_text'] is None
    assert gap['hold_notices'][0]['text']=='‘이 장면의 판서’ 부분은 확실치 않아서 설명을 보류하겠습니다.'


def test_manual_analysis_import_replaces_prior_actual_analysis_status(family):
    from app.analysis_provenance import record_status,read_status
    from app.models import LectureCreate
    session=main.agent.create_session(LectureCreate(title='상태 전환 검사'))
    record_status(session.session_id,'analyzing','gemini')
    record_status(session.session_id,'completed','gemini')
    result=main.analyze_lecture(session.session_id,AnalysisPackageInput(passage_text='직접 등록한 자료입니다.'))
    assert result.analysis_status.label=='영상 분석 미실행'
    with local_access.db() as con:
        assert read_status(con,session.session_id).state=='not_run'
    # Preserve the existing import contract for unrelated extension fields.
    assert AnalysisPackageInput.model_validate({'legacy_extra':'ignored'}).passage_text is None
