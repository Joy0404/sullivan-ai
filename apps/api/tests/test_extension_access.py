"""Role/client isolation with one cookie jar, plus real assignment/progress flow."""
import hashlib
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import local_access

PASSWORD = 'extension-pass-123'
ORIGIN = 'chrome-extension://' + 'a' * 32


def headers(role, token=None):
    result = {'X-Sullivan-Client': role, 'X-Local-Request': '1', 'Origin': ORIGIN}
    if token:
        result['Authorization'] = 'Bearer ' + token
    return result


@pytest.fixture
def family(monkeypatch):
    monkeypatch.setenv('SULLIVAN_ROLE_AUTH', '1')
    client = TestClient(app, base_url='http://127.0.0.1')
    result = client.post('/extension/v1/guardian/register', headers=headers('guardian'),
                         json={'username': 'guardian', 'password': PASSWORD})
    assert result.status_code == 200, result.text
    guardian = result.json()
    assert not client.cookies
    student = client.post('/local/students', headers=headers('guardian', guardian['token']),
                          json={'username': 'student', 'password': PASSWORD, 'name': '학생'}).json()
    signed_in = client.post('/extension/v1/student/session', headers=headers('student'),
                            json={'username': 'student', 'password': PASSWORD})
    assert signed_in.status_code == 200
    return client, guardian, student['id'], signed_in.json()


def test_independent_sessions_assignment_progress_and_logout(family):
    client, guardian, student_id, student = family
    gh = headers('guardian', guardian['token'])
    sh = headers('student', student['token'])
    assigned = client.post('/local/samples/science/assign', headers=gh, json={'students': [student_id]})
    assert assigned.status_code == 200
    ident = assigned.json()['id']
    assert client.get('/local/lectures', headers=sh).json()[0]['id'] == ident
    opened = client.get('/local/lectures/' + ident, headers=sh)
    assert opened.status_code == 200 and opened.json()['snapshot']['active_mode'] != 'waiting'
    assert client.put('/local/lectures/' + ident + '/progress', headers=sh,
                      json={'position_ms': 52000, 'note': '이어서 학습'}).status_code == 200
    assert client.get('/local/students/' + student_id + '/progress', headers=gh).json()['lectures'][0]['position_ms'] == 52000
    assert client.delete('/extension/v1/guardian/session', headers=gh).status_code == 200
    assert client.get('/local/me', headers=gh).status_code == 401
    assert client.get('/local/me', headers=sh).json()['id'] == student_id
    assert client.get('/local/lectures/' + ident, headers=sh).json()['progress']['note'] == '이어서 학습'
    assert client.delete('/extension/v1/student/session', headers=sh).status_code == 200
    assert client.get('/local/me', headers=sh).status_code == 401


def test_wrong_role_and_cookie_fallback_are_blocked(family):
    client, guardian, _, student = family
    assert client.post('/extension/v1/guardian/session', headers=headers('guardian'),
                       json={'username': 'student', 'password': PASSWORD}).status_code == 403
    assert client.get('/local/me', headers=headers('guardian', student['token'])).status_code == 401
    assert client.post('/local/students', headers=headers('student', student['token']),
                       json={'username': 'blocked', 'password': PASSWORD}).status_code == 403
    # A valid legacy cookie must never rescue an invalid extension credential.
    assert client.post('/local/login', headers={'X-Local-Request': '1'},
                       json={'username': 'guardian', 'password': PASSWORD}).status_code == 200
    assert client.get('/local/me').status_code == 200
    assert client.get('/local/me', headers=headers('guardian', 'invalid')).status_code == 401
    assert client.post('/local/logout', headers=headers('guardian', guardian['token'])).status_code == 403
    assert client.get('/local/me').status_code == 200


def test_other_guardian_cannot_access_assignment(family):
    client, guardian, student_id, student = family
    other = client.post('/extension/v1/guardian/register', headers=headers('guardian'),
                        json={'username': 'other', 'password': PASSWORD}).json()
    gh = headers('guardian', guardian['token'])
    oh = headers('guardian', other['token'])
    ident = client.post('/local/samples/history/assign', headers=gh, json={'students': [student_id]}).json()['id']
    assert client.get('/local/lectures/' + ident, headers=oh).status_code == 403
    assert client.get('/local/students/' + student_id + '/progress', headers=oh).status_code == 403
    assert client.post('/local/samples/history/assign', headers=oh, json={'students': [student_id]}).status_code == 403
    assert client.get('/local/lectures/' + ident, headers=headers('student', student['token'])).status_code == 200


def test_expiry_hash_storage_origin_and_client_binding(family, monkeypatch):
    client, guardian, _, _ = family
    gh = headers('guardian', guardian['token'])
    with local_access.db() as con:
        row = con.execute('SELECT * FROM extension_sessions WHERE client="guardian"').fetchone()
        assert row['token'] == hashlib.sha256(guardian['token'].encode()).hexdigest()
        assert row['token'] != guardian['token']
    bad_origin = gh | {'Origin': 'https://untrusted.example'}
    assert client.get('/local/me', headers=bad_origin).status_code == 403
    assert client.get('/extension/v1/student/session', headers=gh).status_code == 403
    monkeypatch.setenv('SULLIVAN_EXTENSION_ORIGINS', ORIGIN)
    remote = TestClient(app, base_url='https://sullivan.example')
    assert remote.get('/local/me', headers=gh).status_code == 200
    assert remote.post('/extension/v1/guardian/register', headers=headers('guardian'),
                       json={'username': 'remote', 'password': PASSWORD}).status_code == 403
    assert remote.get('/local/me', headers=gh | {'Origin': 'chrome-extension://' + 'b'*32}).status_code == 403
    with local_access.db() as con:
        con.execute('UPDATE extension_sessions SET expires=?', (time.time()-1,))
    assert client.get('/local/me', headers=gh).status_code == 401


def test_login_attempt_limit_persists(family):
    client, *_ = family
    for _ in range(5):
        assert client.post('/extension/v1/student/session', headers=headers('student'),
                           json={'username': 'student', 'password': 'wrong-password'}).status_code == 401
    assert client.post('/extension/v1/student/session', headers=headers('student'),
                       json={'username': 'student', 'password': PASSWORD}).status_code == 429


def test_bearer_guard_stays_enabled_in_legacy_demo_mode(family, monkeypatch):
    client, guardian, _, student = family
    monkeypatch.setenv('SULLIVAN_ROLE_AUTH', '0')
    assert client.get('/local/me', headers=headers('guardian', 'invalid')).status_code == 401
    assert client.post('/v1/lectures', headers=headers('student', student['token']),
                       json={'title': '차단'}).status_code == 403
    gh = headers('guardian', guardian['token'])
    created = client.post('/v1/lectures', headers=gh, json={'title': '내 세션'})
    assert created.status_code == 201
    session = created.json()['session_id']
    assert client.get('/v1/lectures/' + session, headers=gh).status_code == 200
    assert client.get('/v1/lectures/not-mine', headers=gh).status_code == 403
