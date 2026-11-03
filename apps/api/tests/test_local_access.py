import pytest
from fastapi.testclient import TestClient
from app.main import app

HEAD={'X-Local-Request':'1'}
@pytest.fixture
def family(monkeypatch):
    monkeypatch.setenv('SULLIVAN_ROLE_AUTH','1')
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    guardian=TestClient(app,headers=HEAD)
    assert guardian.post('/local/setup',json={'username':'guardian','password':'audit-pass-123','name':'보호자'}).status_code==200
    students=[]
    for i in (1,2):
        identity=guardian.post('/local/students',json={'username':f'student{i}','password':'audit-pass-123','name':f'학생{i}'}).json()['id']
        client=TestClient(app,headers=HEAD)
        assert client.post('/local/login',json={'username':f'student{i}','password':'audit-pass-123'}).status_code==200
        students.append((identity,client))
    return guardian,students

def prepare(g,students):
    session=g.post('/v1/lectures',json={'title':'관계대명사','subject':'영어','problem_mode':True}).json()['session_id']
    r=g.post(f'/v1/lectures/{session}/analysis',json={'passage_text':'첫 문단입니다.\n\n다음 문단입니다.','transcript_segments':[{'segment_id':'t1','start_ms':0,'end_ms':5000,'text':'관계대명사를 설명합니다.','confidence':.99}]})
    assert r.status_code==200
    p=g.post('/local/lectures',json={'title':'관계대명사','subject':'영어','students':students,'session_id':session,'playback':{'kind':'none'}})
    assert p.status_code==200,p.text
    return p.json()['id'],session

def test_auth_assignment_readiness_progress_and_onboarding(family):
    g,students=family;s1,c1=students[0];s2,c2=students[1]
    assert TestClient(app).get('/v1/lectures/x').status_code==401
    assert c1.post('/v1/lectures',json={'title':'blocked'}).status_code==403
    ident,session=prepare(g,[s1])
    assert c1.get('/local/lectures').json()==[]
    assert c1.get('/local/lectures/'+ident).status_code==403
    assert c1.put('/local/lectures/'+ident+'/ready').status_code==403
    assert g.put('/local/lectures/'+ident+'/ready').status_code==200
    assert c1.get('/local/lectures').json()[0]['id']==ident
    assert c2.get('/local/lectures/'+ident).status_code==403
    assert c1.get('/v1/lectures/'+session).status_code==403
    assert c1.delete('/local/lectures/'+ident).status_code==403
    assert c1.post('/local/students',json={'username':'extra','password':'audit-pass-123'}).status_code==403
    assert c1.put('/local/lectures/'+ident+'/progress',json={'position_ms':12000,'note':'메모','underlined':['p1']}).status_code==200
    assert c1.post('/local/onboarding').status_code==200
    assert c1.post('/local/logout').status_code==200
    assert c1.get('/local/me').status_code==401
    assert c1.post('/local/login',json={'username':'student1','password':'audit-pass-123'}).status_code==200
    assert c1.get('/local/me').json()['onboarded']==1
    assert c1.get('/local/lectures/'+ident).json()['progress']['position_ms']==12000
    assert g.put('/local/students/'+s1+'/settings',json={'reset_onboarding':True}).status_code==200
    assert c1.get('/local/me').json()['onboarded']==0
    assert c1.post('/local/lectures/'+ident+'/agent-turn',json={'message':'요약'}).status_code==403

def test_login_role_choice_is_checked_before_session_creation(family):
    g,students=family
    client=TestClient(app,headers=HEAD)
    bad=client.post('/local/login',json={'username':'student1','password':'audit-pass-123','role':'guardian'})
    assert bad.status_code==403
    assert client.get('/local/me').status_code==401
    good=client.post('/local/login',json={'username':'student1','password':'audit-pass-123','role':'student'})
    assert good.status_code==200 and good.json()['role']=='student'
    assert client.post('/local/students',json={'username':'blocked','password':'audit-pass-123'}).status_code==403

def test_non_file_assignment_can_be_ready_in_one_transaction(family):
    g,students=family;s1,student=students[0]
    draft,session=prepare(g,[s1])
    result=g.post('/local/lectures',json={'title':'바로 제공','students':[s1],'session_id':session,'ready':True})
    assert result.status_code==200 and result.json()['ready'] is True
    ident=result.json()['id']
    assert [r['id'] for r in student.get('/local/lectures').json()]==[ident]
    assert student.get('/local/lectures/'+draft).status_code==403
    blocked=g.post('/local/lectures',json={'title':'미저장 원본','students':[s1],'session_id':session,'store_local_media':True,'ready':True})
    assert blocked.status_code==400
    assert len(g.get('/local/lectures').json())==2
    assert g.put('/local/lectures/'+draft+'/ready').status_code==200
    assert len(student.get('/local/lectures').json())==2

@pytest.mark.parametrize('sample',['science','history'])
def test_direct_sample_assignment_without_preview_or_client_snapshot(family,monkeypatch,sample):
    g,students=family;s1,student=students[0];_,other=students[1]
    from app.main import agent
    monkeypatch.setattr(agent,'snapshot',lambda *_:(_ for _ in ()).throw(AssertionError('sample must not use in-memory analysis')))
    r=g.post('/local/samples/'+sample+'/assign',json={'students':[s1]})
    assert r.status_code==200 and r.json()['ready'] is True
    ident=r.json()['id']
    assert student.get('/local/lectures').json()[0]['id']==ident
    opened=student.get('/local/lectures/'+ident)
    assert opened.status_code==200
    assert opened.json()['snapshot']['active_mode']!='waiting'
    assert '샘플' in opened.json()['snapshot']['session']['source_label']
    assert other.get('/local/lectures/'+ident).status_code==403
    assert student.post('/local/samples/'+sample+'/assign',json={'students':[s1]}).status_code==403

def test_sample_catalog_rejects_bad_assignment_without_partial_save(family):
    g,students=family;s1,_=students[0]
    assert g.post('/local/samples/unknown/assign',json={'students':[s1]}).status_code==404
    assert g.post('/local/samples/science/assign',json={'students':['not-owned']}).status_code==403
    assert g.post('/local/samples/science/assign',json={'students':[s1,s1]}).status_code==400
    assert g.get('/local/lectures').json()==[]
    r=g.post('/local/lectures',json={'title':'클라이언트 샘플','students':[s1],'sample_id':'science','snapshot':{'invalid':'UNTRUSTED'},'ready':True})
    assert r.status_code==200
    assert 'UNTRUSTED' not in g.get('/local/lectures/'+r.json()['id']).text

def test_build_identity_and_static_cache_policy(family):
    g,_=family
    status=g.get('/local/status').json()
    assert status['build']=='sullivan-roles-20261102-r2' and status['sample_assignment']=='server-catalog-v1'
    assert status['instance']
    for path in ['/', '/app.js', '/sample-catalog.json']:
        response=g.get(path)
        assert response.status_code==200
        assert response.headers['cache-control']=='no-store'

def test_order_revocation_and_origin(family):
    g,students=family;s1,c1=students[0];s2,c2=students[1]
    a,_=prepare(g,[s1]);b,_=prepare(g,[s1,s2])
    for ident in (a,b):g.put('/local/lectures/'+ident+'/ready')
    assert g.put('/local/order',json={'student':s1,'lectures':[b,a]}).status_code==200
    assert [r['id'] for r in c1.get('/local/lectures').json()]==[b,a]
    assert g.put('/local/order',json={'student':s1,'lectures':[b,b]}).status_code==400
    assert g.put('/local/lectures/'+b,json={'title':'변경','subject':'영어','students':[s2]}).status_code==200
    assert c1.get('/local/lectures/'+b).status_code==403
    assert g.post('/local/students',json={'username':'evil','password':'audit-pass-123'},headers={'Origin':'https://evil.example'}).status_code==403
    assert TestClient(app).post('/local/login',json={'username':'student1','password':'audit-pass-123'}).status_code==403
    assert g.delete('/local/lectures/'+a).status_code==200
    assert c1.get('/local/lectures/'+a).status_code==404

def test_blocked_visual_cannot_leak_through_change_guide_or_passage(family):
    g,_=family
    session=g.post('/v1/lectures',json={'title':'안전 검사','problem_mode':True}).json()['session_id']
    r=g.post(f'/v1/lectures/{session}/analysis',json={'visual_observations':[{'observation_id':'low','timestamp_ms':0,'screen_type':'board','kind':'number','text':'unsafe-999','confidence':.5,'importance':1},{'observation_id':'high','timestamp_ms':1000,'screen_type':'board','kind':'number','text':'safe-100','confidence':.99,'importance':1},{'observation_id':'answer','timestamp_ms':2000,'screen_type':'board','kind':'answer','text':'정답은 42입니다.','confidence':.99,'importance':1}],'study_guide':{'overview':'정답은 42입니다.'},'passage_text':'정답은 42입니다.'})
    assert r.status_code==200
    assert 'unsafe-999' not in r.text
    assert '정답은 42' not in r.text
    assert r.json()['visual_gaps'][2]['action']=='HOLD'

def test_login_throttle_and_http_only(family):
    g,_=family;bad=TestClient(app,headers=HEAD)
    for _ in range(5):assert bad.post('/local/login',json={'username':'student1','password':'incorrect-pass'}).status_code==401
    assert bad.post('/local/login',json={'username':'student1','password':'incorrect-pass'}).status_code==429
    response=g.post('/local/login',json={'username':'guardian','password':'audit-pass-123'})
    assert 'HttpOnly' in response.headers['set-cookie']
    assert 'samesite=strict' in response.headers['set-cookie'].lower()


def test_media_key_restricted_and_snapshot_is_authoritative(family,monkeypatch):
    g,students=family;s1,c1=students[0];s2,c2=students[1]
    ident,session=prepare(g,[s1])
    draft=g.post('/local/lectures',json={'title':'파일 강의','subject':'영어','students':[s1],'session_id':session,'store_local_media':True,'playback':{'kind':'local','name':'lesson.webm'}})
    assert draft.status_code==200
    media_id=draft.json()['id']
    assert c1.get('/local/lectures/'+media_id).status_code==403
    g.put('/local/lectures/'+media_id+'/ready')
    r=c1.get('/local/lectures/'+media_id)
    assert r.status_code==200 and len(r.json()['media_key'])==64
    assert c2.get('/local/lectures/'+media_id).status_code==403
    assert 'media_key' not in c1.get('/local/lectures').text
    assert c1.get('/local/students').status_code==403
    assert c1.put('/local/students/'+s1+'/settings',json={}).status_code==403
    assert c1.put('/local/order',json={'student':s1,'lectures':[]}).status_code==403
    assert g.post('/local/lectures',json={'title':'타인 배정','students':['not-owned'],'session_id':session}).status_code==403
    # Client-provided snapshots do not authorize a cloud turn.
    assert c1.post('/local/lectures/'+media_id+'/agent-turn',json={'message':'요약','snapshot':{}}).status_code==403

    monkeypatch.setenv('DEMO_ACCESS_CODE','test-access-code')
    allowed=g.post('/local/lectures',json={'title':'학습 대화','students':[s1],'session_id':session,'chat_consent':True,'access_code':'test-access-code'})
    assert allowed.status_code==200
    allowed_id=allowed.json()['id'];g.put('/local/lectures/'+allowed_id+'/ready')
    # Missing provider configuration falls back before spending a paid-call allowance.
    assert c1.post('/local/lectures/'+allowed_id+'/agent-turn',json={'message':'요약'}).status_code==503


def test_focus_voice_preference_is_guardian_managed(family):
    g,students=family;ident,student=students[0]
    assert g.put('/local/students/'+ident+'/settings',json={'reader_mode':False,'focus_voice':True}).status_code==200
    prefs=student.get('/local/me').json()['settings']
    assert prefs['focus_voice'] is True and prefs['reader_mode'] is False
    assert student.put('/local/students/'+ident+'/settings',json={'focus_voice':False}).status_code==403
    assert student.get('/local/me').json()['settings']['focus_voice'] is True


def test_student_can_persist_only_own_speech_preferences(family):
    g,students=family;ident,c=students[0]
    g.put('/local/students/'+ident+'/settings',json={'problem_mode':True,'auto_description':False})
    r=c.put('/local/preferences',json={'focus_voice':True,'reader_mode':False})
    assert r.status_code==200
    saved=c.get('/local/me').json()['settings']
    assert saved['focus_voice'] and saved['problem_mode'] and not saved['auto_description']
    assert c.put('/local/preferences',json={'focus_voice':True,'reader_mode':False,'problem_mode':False}).status_code==422
    c.post('/local/logout');c.post('/local/login',json={'username':'student1','password':'audit-pass-123'})
    assert c.get('/local/me').json()['settings']['focus_voice'] is True
