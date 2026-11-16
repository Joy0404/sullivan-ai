import json
from uuid import uuid4

import pytest
from app import local_access
from test_extension_access import family, headers, PASSWORD


@pytest.fixture
def lesson(family):
    client, guardian, student_id, student = family
    gh, sh = headers('guardian', guardian['token']), headers('student', student['token'])
    ident = client.post('/local/samples/science/assign', headers=gh, json={'students': [student_id]}).json()['id']
    return client, gh, sh, student_id, ident


def path(ident):
    return f'/extension/v1/student/lectures/{ident}'


def write(client, ident, sh, body='학생이 직접 쓴 나의 풀이', source=None, revision=0, note_id='note-one'):
    return client.put(path(ident)+'/notes/'+note_id, headers=sh,
                      json={'body': body, 'started_ms': 12000, 'source': source, 'revision': revision})


def source_ref(source):
    return {key: source[key] for key in ('kind', 'id', 'fingerprint')}


def test_multiple_notes_edit_delete_search_export_and_private_source(lesson):
    client, gh, sh, sid, ident = lesson
    candidates = client.get(path(ident)+'/note-sources', headers=sh).json()
    assert candidates
    result = write(client, ident, sh, source=source_ref(candidates[0]))
    assert result.status_code == 200
    assert result.json()['revision'] == 1
    assert write(client, ident, sh, note_id='second', body='두 번째 자유 필기').status_code == 200
    assert write(client, ident, sh, revision=1, source=source_ref(candidates[0]), body='수정한 풀이').json()['revision'] == 2
    assert len(client.get(path(ident)+'/notes', headers=sh).json()) == 2
    source = client.get(path(ident)+'/notes/note-one/source', headers=sh).json()
    assert source['available'] and source['source']['text'] == candidates[0]['text']
    text = client.get(path(ident)+'/notes-export', headers=sh).json()['text']
    assert '수정한 풀이' in text and '연결 원문 (읽기 전용)' in text
    result = client.request('DELETE', path(ident)+'/notes/second', headers=sh, json={'revision': 1})
    assert result.status_code == 200
    assert len(client.get(path(ident)+'/notes', headers=sh).json()) == 1
    summary = client.get('/local/students/'+sid+'/progress', headers=gh)
    assert '수정한 풀이' not in summary.text


def test_other_student_guardian_and_cookie_cannot_read_notes(lesson):
    client, gh, sh, sid, ident = lesson
    assert write(client, ident, sh).status_code == 200
    client.post('/local/students', headers=gh, json={'username':'another','password':PASSWORD,'name':'다른 학생'})
    other = client.post('/extension/v1/student/session', headers=headers('student'), json={'username':'another','password':PASSWORD}).json()
    oh = headers('student', other['token'])
    assert client.get(path(ident)+'/notes', headers=oh).json() == []
    assert client.get(path(ident)+'/notes/note-one/source', headers=oh).status_code == 404
    assert '학생이 직접 쓴' not in client.get(path(ident)+'/notes-export', headers=oh).text
    assert write(client, ident, oh).status_code == 403
    assert client.get(path(ident)+'/notes', headers=gh).status_code == 403
    client.post('/local/login', headers={'X-Local-Request':'1'}, json={'username':'student','password':PASSWORD})
    assert client.get(path(ident)+'/notes', headers={'X-Sullivan-Client':'student'}).status_code == 401


def test_retries_are_idempotent_and_conflicting_changes_preserve_saved_work(lesson):
    client, gh, sh, sid, ident = lesson
    assert write(client, ident, sh).json()['revision'] == 1
    assert write(client, ident, sh).json()['revision'] == 1
    assert write(client, ident, sh, body='다른 화면 편집', revision=1).json()['revision'] == 2
    assert write(client, ident, sh, body='오래된 초안', revision=1).status_code == 409
    assert client.get(path(ident)+'/notes', headers=sh).json()[0]['body'] == '다른 화면 편집'
    assert client.request('DELETE', path(ident)+'/notes/note-one', headers=sh, json={'revision':1}).status_code == 409


def test_progress_and_personal_solutions_are_preserved(lesson):
    client, gh, sh, sid, ident = lesson
    progress = {'position_ms':42000,'note':'기존 메모','bookmarks':[{'id':'old','timestamp_ms':2000,'note':'보존'}],'underlined':['old-paragraph']}
    client.put('/local/lectures/'+ident+'/progress', headers=sh, json=progress)
    assert write(client, ident, sh, body='내 풀이: x = 3, 내 정답 기록').status_code == 200
    assert write(client, ident, sh, body=progress['note'], note_id='legacy-copy').status_code == 200
    restored = client.get('/local/lectures/'+ident, headers=sh).json()['progress']
    assert all(restored[key] == value for key, value in progress.items())
    assert '내 풀이: x = 3' in client.get(path(ident)+'/notes-export', headers=sh).json()['text']


def mutate_snapshot(ident, callback):
    with local_access.db() as con:
        snapshot = json.loads(con.execute('SELECT snapshot FROM lectures WHERE id=?',(ident,)).fetchone()[0])
        callback(snapshot)
        con.execute('UPDATE lectures SET snapshot=? WHERE id=?',(json.dumps(snapshot,ensure_ascii=False),ident))


@pytest.mark.parametrize('mode', ['low-confidence','answer','changed-text','withdrawn'])
def test_source_access_and_export_recheck_current_policy_without_cached_text(lesson, mode):
    client, gh, sh, sid, ident = lesson
    candidates = client.get(path(ident)+'/note-sources', headers=sh).json()
    visual = next(candidate for candidate in candidates if candidate['kind']=='visual')
    assert write(client, ident, sh, source=source_ref(visual)).status_code == 200
    def change(snapshot):
        gap=next(g for g in snapshot['visual_gaps'] if g['gap_id']==visual['id'])
        if mode=='low-confidence':gap.update(confidence=.2)
        if mode=='answer':gap.update(kind='answer');snapshot['session']['problem_mode']=True
        if mode=='changed-text':gap.update(public_description='새로 바뀐 공개 설명')
    if mode=='withdrawn':
        with local_access.db() as con:con.execute('UPDATE lectures SET ready=0 WHERE id=?',(ident,))
    else:mutate_snapshot(ident,change)
    source = client.get(path(ident)+'/notes/note-one/source', headers=sh).json()
    assert source['available'] is False and source['source'] is None
    output=client.get(path(ident)+'/notes-export', headers=sh).json()['text']
    assert visual['text'] not in output
    assert '학생이 직접 쓴 나의 풀이' in output
    # Personal notes remain editable after withdrawal; no old source is re-exposed.
    assert write(client, ident, sh, revision=1, source=source_ref(visual), body='내가 수정한 풀이').status_code == 200
    with local_access.db() as con:
        stored=con.execute('SELECT source FROM student_notes WHERE lecture=?',(ident,)).fetchone()[0]
        assert visual['text'] not in stored


def test_unapproved_candidates_never_enter_source_options_or_export(lesson):
    client, gh, sh, sid, ident = lesson
    def change(snapshot):
        prototype=dict(snapshot['visual_gaps'][0])
        for kind,confidence,marker in [('formula',.2,'LOW_CANDIDATE_SECRET'),('answer',.99,'ANSWER_CANDIDATE_SECRET')]:
            gap={**prototype,'gap_id':str(uuid4()),'kind':kind,'confidence':confidence,'public_description':marker,'source_text':marker,'action':'INTERRUPT','safe_to_speak':True}
            snapshot['visual_gaps'].append(gap)
        snapshot['session']['problem_mode']=True
    mutate_snapshot(ident,change)
    result=client.get(path(ident)+'/note-sources', headers=sh)
    assert result.status_code==200
    for marker in ('LOW_CANDIDATE_SECRET','ANSWER_CANDIDATE_SECRET'):assert marker not in result.text
    assert write(client, ident, sh, source={'kind':'visual','id':'forged','fingerprint':'a'*64}).status_code==403
    assert write(client, ident, sh).status_code==200
    for endpoint in ('/notes','/notes-export'):
        text=client.get(path(ident)+endpoint,headers=sh).text
        assert 'LOW_CANDIDATE_SECRET' not in text and 'ANSWER_CANDIDATE_SECRET' not in text


def test_source_text_injection_and_oversize_notes_rejected(lesson):
    client, gh, sh, sid, ident=lesson
    source=source_ref(client.get(path(ident)+'/note-sources',headers=sh).json()[0])
    source['text']='attacker-provided source'
    assert write(client,ident,sh,source=source).status_code==422
    assert write(client,ident,sh,body='a'*30001).status_code==422


def test_personal_notebook_library_survives_assignment_withdrawal_without_source(lesson):
    client, gh, sh, sid, ident=lesson
    source=source_ref(client.get(path(ident)+'/note-sources',headers=sh).json()[0])
    assert write(client,ident,sh,source=source).status_code==200
    with local_access.db() as con:con.execute('DELETE FROM assignments WHERE lecture=? AND student=?',(ident,sid))
    library=client.get('/extension/v1/student/notebooks',headers=sh)
    assert library.status_code==200 and library.json()==[{'id':ident,'title':'배정이 종료된 강의의 내 필기','count':1}]
    assert '학생이 직접 쓴' not in library.text
    assert client.get('/extension/v1/student/notebooks',headers=gh).status_code==403
    assert client.get(path(ident)+'/notes/note-one/source',headers=sh).json()['available'] is False
    assert write(client,ident,sh,body='충돌 초안을 내 새 필기로 복사',note_id='recovery-copy').status_code==200
    assert '충돌 초안을 내 새 필기로 복사' in client.get(path(ident)+'/notes-export',headers=sh).json()['text']
