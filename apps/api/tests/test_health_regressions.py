"""Disposable API regressions for current policy, concurrent notes and bad input."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
from threading import Barrier

from fastapi.testclient import TestClient
import pytest

from app import local_access, student_notes
from app.adapters.gemini_agent import build_grounded_context
from app.main import app
from app.models import LectureSnapshot
from test_extension_access import family
from test_student_notes import lesson, mutate_snapshot, path, source_ref, write


def test_duplicate_assignment_edit_is_rejected_without_changing_saved_lecture(lesson):
    client, gh, sh, sid, ident = lesson
    before = client.get('/local/lectures/'+ident, headers=gh).json()
    result = client.put('/local/lectures/'+ident, headers=gh,
                        json={'title': '수정하면 안 되는 제목', 'subject': '과목', 'students': [sid, sid]})
    assert result.status_code == 400
    after = client.get('/local/lectures/'+ident, headers=sh)
    assert after.status_code == 200 and after.json()['title'] == before['title']


@pytest.mark.parametrize('payload', [{}, {'message': ''}, {'message': '질문', 'current_time_ms': -1}, []])
def test_bad_student_question_returns_422_without_any_provider_call(lesson, monkeypatch, payload):
    client, gh, sh, sid, ident = lesson
    with local_access.db() as con:
        con.execute('UPDATE lectures SET chat_allowed=1 WHERE id=?', (ident,))
    monkeypatch.setenv('GEMINI_API_KEY', 'fixture-not-a-real-key')
    def forbidden(*args, **kwargs):
        raise AssertionError('invalid questions must not reach provider or consume quota')
    monkeypatch.setattr('app.adapters.gemini_agent.run_agent_turn', forbidden)
    result = client.post('/local/lectures/'+ident+'/agent-turn', headers=sh, json=payload)
    assert result.status_code == 422
    malformed = client.post('/local/lectures/'+ident+'/agent-turn',
                            headers={**sh, 'Content-Type': 'application/json'}, content=b'{broken')
    assert malformed.status_code == 422


def test_stronger_student_problem_mode_scrubs_original_answer_from_speech_and_model_input(lesson):
    client, gh, sh, sid, ident = lesson
    marker = 'PRIVATE_ANSWER_FROM_PREPARED_SPEECH'
    def change(snapshot):
        snapshot['session']['problem_mode'] = False
        gap = dict(snapshot['visual_gaps'][0])
        gap.update(gap_id='answer-origin', kind='answer', action='INTERRUPT', safe_to_speak=True,
                   confidence=.99, public_description=marker, source_text=marker)
        snapshot['visual_gaps'].append(gap)
        snapshot['transcript_segments'].append({'segment_id': 'answer-speech', 'start_ms': 1000,
                                               'end_ms': 2000, 'text': marker, 'confidence': .99})
    mutate_snapshot(ident, change)
    for endpoint in ('/local/lectures/'+ident, path(ident)):
        result = client.get(endpoint, headers=sh)
        assert result.status_code == 200 and marker not in result.text
        value = LectureSnapshot.model_validate(result.json()['snapshot'])
        assert value.session.problem_mode
        assert marker not in json.dumps(build_grounded_context(value))
    assert marker not in client.get(path(ident)+'/note-sources', headers=sh).text


def test_notes_export_reads_current_sources_once_and_rechecks_next_request(lesson, monkeypatch):
    client, gh, sh, sid, ident = lesson
    source = client.get(path(ident)+'/note-sources', headers=sh).json()[0]
    with local_access.db() as con:
        student_notes.table(con)
        con.executemany('INSERT INTO student_notes VALUES(?,?,?,?,?,?,?,?)', [
            (ident, sid, f'bulk-{i}', f'학생 필기 {i}', i*1000, json.dumps(source_ref(source)), 1, '2026-11-16')
            for i in range(60)])
    reads = []
    original = local_access.lecture
    def counted(*args, **kwargs):
        reads.append(args[0])
        return original(*args, **kwargs)
    monkeypatch.setattr(local_access, 'lecture', counted)
    result = client.get(path(ident)+'/notes-export', headers=sh)
    assert result.status_code == 200 and reads == [ident]
    assert result.json()['text'].count(source['text']) == 60
    with local_access.db() as con:
        con.execute('UPDATE lectures SET ready=0 WHERE id=?', (ident,))
    result = client.get(path(ident)+'/notes-export', headers=sh)
    assert result.status_code == 200 and reads == [ident, ident]
    assert source['text'] not in result.json()['text']
    assert all(f'학생 필기 {i}' in result.json()['text'] for i in range(60))


def test_concurrent_note_creation_cannot_exceed_limit(lesson, monkeypatch):
    client, gh, sh, sid, ident = lesson
    ref = source_ref(client.get(path(ident)+'/note-sources', headers=sh).json()[0])
    with local_access.db() as con:
        student_notes.table(con)
        con.executemany('INSERT INTO student_notes VALUES(?,?,?,?,?,?,?,?)', [
            (ident, sid, f'existing-{i}', '보존할 필기', 0, None, 1, '2026-11-16') for i in range(999)])
    barrier = Barrier(2)
    original = student_notes.resolved
    def synchronize(*args, **kwargs):
        result = original(*args, **kwargs)
        barrier.wait(timeout=10)
        return result
    monkeypatch.setattr(student_notes, 'resolved', synchronize)
    def create(index):
        with TestClient(app, base_url='http://127.0.0.1') as other:
            return write(other, ident, sh, source=ref, note_id=f'concurrent-{index}').status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(create, range(2))) == [200, 413]
    assert len(client.get(path(ident)+'/notes', headers=sh).json()) == 1000
    # Capacity must not prevent an owner from updating existing personal work.
    assert write(client, ident, sh, note_id='existing-0', revision=1, body='수정한 필기').status_code == 200


def test_delete_never_reports_success_when_conditional_delete_removed_nothing(lesson, monkeypatch):
    client, gh, sh, sid, ident = lesson
    assert write(client, ident, sh).status_code == 200
    original = local_access.db
    class RevisionChanges:
        def __init__(self, con): self.con = con
        def __getattr__(self, key): return getattr(self.con, key)
        def execute(self, sql, args=()):
            if sql.startswith('DELETE FROM student_notes'):
                assert self.con.in_transaction
                self.con.execute('UPDATE student_notes SET revision=revision+1 WHERE id=?', ('note-one',))
            return self.con.execute(sql, args)
    @contextmanager
    def changing_database():
        with original() as con:
            yield RevisionChanges(con)
    monkeypatch.setattr(local_access, 'db', changing_database)
    result = client.request('DELETE', path(ident)+'/notes/note-one', headers=sh, json={'revision': 1})
    assert result.status_code == 409
    assert len(client.get(path(ident)+'/notes', headers=sh).json()) == 1
