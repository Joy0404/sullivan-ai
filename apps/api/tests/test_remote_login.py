"""Consented device login: real API/SQLite, no external services or user DB.

Interleaving hooks stop at authentication/transaction boundaries rather than
using timing sleeps. Only the enrolled student's extension receives a session.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import sqlite3
from threading import Barrier
import time

from fastapi.testclient import TestClient
import pytest

from app import extension_accounts, local_access, remote_login
from app.main import app
from test_extension_access import family, headers, PASSWORD
from test_extension_accounts import CLIENT, exchange, oauth, refresh


BASE = '/extension/v1'
ENROLL = BASE + '/student/remote-login/devices'
POLL = BASE + '/student/remote-login/poll'


def support_path(student_id: str) -> str:
    return f'{BASE}/guardian/students/{student_id}/remote-login'


def enroll(client: TestClient, token: str) -> dict:
    response = client.post(ENROLL, headers=headers('student', token),
                           json={'client_id': CLIENT, 'confirm': True})
    assert response.status_code == 201, response.text
    return response.json()


def proof(enrollment: dict) -> dict:
    return {key: enrollment[key] for key in ('device_id', 'device_secret', 'client_id')}


def poll(client: TestClient, enrollment: dict, presence: str = 'ready'):
    return client.post(POLL, headers=headers('student'),
                       json=proof(enrollment) | {'presence': presence})


def start(client: TestClient, guardian: dict, student_id: str) -> dict:
    response = client.post(support_path(student_id),
                           headers=headers('guardian', guardian['token']))
    assert response.status_code == 200, response.text
    return response.json()


def test_enrollment_needs_student_consent_connection_and_matching_origin(family):
    client, guardian, student_id, student = family
    sh = headers('student', student['token'])
    body = {'client_id': CLIENT, 'confirm': True}
    assert client.post(ENROLL, headers=sh, json=body | {'confirm': False}).status_code == 400
    assert client.post(ENROLL, headers=headers('student'), json=body).status_code == 401
    assert client.post(ENROLL, headers=headers('guardian', guardian['token']), json=body).status_code == 403
    assert client.post(ENROLL, headers=sh | {'Origin': 'chrome-extension://' + 'b' * 32}, json=body).status_code == 403
    assert client.post(ENROLL, headers=sh, json=body | {'client_id': 'b' * 32}).status_code == 403
    assert client.post(ENROLL, headers={key: value for key, value in sh.items() if key != 'Origin'}, json=body).status_code == 403
    with local_access.db() as con:
        assert con.execute('SELECT COUNT(*) FROM remote_login_devices').fetchone()[0] == 0
    assert client.post(BASE + '/student/connections/unlink', headers=sh,
                       json={'student': student_id, 'confirm': True}).status_code == 200
    assert client.post(ENROLL, headers=sh, json=body).status_code == 409


def test_proof_hashed_and_guardian_has_only_own_device_status(family):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    assert enrollment['student_id'] == student_id
    with local_access.db() as con:
        stored = con.execute('SELECT secret FROM remote_login_devices WHERE id=?',
                             (enrollment['device_id'],)).fetchone()[0]
        assert stored == hashlib.sha256(enrollment['device_secret'].encode()).hexdigest()
        assert enrollment['device_secret'] != stored
    other = client.post(BASE + '/guardian/register', headers=headers('guardian'),
                        json={'username': 'other_guardian', 'password': PASSWORD}).json()
    for method in (client.get, client.post, client.delete):
        assert method(support_path(student_id), headers=headers('guardian', other['token'])).status_code == 403
    status = start(client, guardian, student_id)
    assert status['enabled'] and status['state'] == 'pending'
    assert set(status) == {'enabled', 'state', 'request_id', 'expires_at', 'online', 'presence'}
    serialized = json.dumps(status)
    assert all(secret not in serialized for secret in (
        enrollment['device_secret'], student['token'], 'access_token', 'refresh_token'))


def test_pending_request_idempotent_and_expiry_requires_a_new_request(family):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    first = start(client, guardian, student_id)
    assert start(client, guardian, student_id)['request_id'] == first['request_id']
    with local_access.db() as con:
        row = con.execute('SELECT * FROM remote_login_requests').fetchone()
        assert row['expires'] - row['created'] == pytest.approx(300)
        assert con.execute('SELECT COUNT(*) FROM remote_login_requests').fetchone()[0] == 1
        con.execute('UPDATE remote_login_requests SET expires=?', (time.time() - 1,))
    assert poll(client, enrollment).json() == {'state': 'waiting'}
    state = client.get(support_path(student_id), headers=headers('guardian', guardian['token'])).json()
    assert state['state'] == 'expired'
    second = start(client, guardian, student_id)
    assert second['request_id'] != first['request_id']
    assert poll(client, enrollment).json()['state'] == 'issued'


def test_single_use_issue_is_distinct_from_student_login_acknowledgment(family):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    request = start(client, guardian, student_id)
    issued = poll(client, enrollment).json()
    assert issued['state'] == 'issued'
    session = issued['session']
    assert session['user']['id'] == student_id and session['user']['role'] == 'student'
    assert session['expires_in'] == 900
    assert client.get('/local/me', headers=headers('student', session['access_token'])).status_code == 200
    assert client.get('/local/me', headers=headers('guardian', session['access_token'])).status_code == 401
    assert poll(client, enrollment).json() == {'state': 'waiting'}
    state = start(client, guardian, student_id)
    assert state['state'] == 'issued' and state['request_id'] == request['request_id']
    assert poll(client, enrollment, 'signed_in').json() == {'state': 'waiting'}
    state = client.get(support_path(student_id), headers=headers('guardian', guardian['token'])).json()
    assert state['state'] == 'completed'
    with local_access.db() as con:
        assert con.execute('SELECT COUNT(*) FROM auth_families WHERE user=?', (student_id,)).fetchone()[0] == 1


@pytest.mark.parametrize('presence,expected_state', [('other_account', 'other_account'), ('signed_in', 'already_signed_in')])
def test_existing_or_other_account_presence_never_receives_session(family, presence, expected_state):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    start(client, guardian, student_id)
    response = poll(client, enrollment, presence)
    assert response.status_code == 200 and response.json() == {'state': expected_state}
    with local_access.db() as con:
        assert con.execute('SELECT COUNT(*) FROM auth_families').fetchone()[0] == 0


def test_bad_proof_or_client_cannot_consume_pending_request(family):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    pending = start(client, guardian, student_id)
    body = proof(enrollment)
    for update, expected in (({'device_secret': 'x' * 43}, 401),
                             ({'device_id': '0' * 32}, 401),
                             ({'client_id': 'b' * 32}, 403)):
        assert client.post(POLL, headers=headers('student'), json=body | update).status_code == expected
    alternate_origin = headers('student') | {'Origin': 'chrome-extension://' + 'b' * 32}
    assert client.post(POLL, headers=alternate_origin, json=body | {'client_id': 'b' * 32}).status_code == 401
    assert start(client, guardian, student_id)['request_id'] == pending['request_id']
    assert poll(client, enrollment).json()['state'] == 'issued'


def test_production_client_allowlist_applies_to_device_enrollment_and_poll(family, monkeypatch):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    monkeypatch.setenv('SULLIVAN_PRODUCTION', '1')
    monkeypatch.setenv('SULLIVAN_PUBLIC_URL', 'https://sullivan.example')
    monkeypatch.setenv('SULLIVAN_EXTENSION_CLIENTS', json.dumps({'student': 'b' * 32, 'guardian': CLIENT}))
    assert client.post(ENROLL, headers=headers('student', student['token']),
                       json={'client_id': CLIENT, 'confirm': True}).status_code == 403
    assert poll(client, enrollment).status_code == 403


def test_two_concurrent_polls_issue_exactly_one_session(family):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    start(client, guardian, student_id)
    barrier = Barrier(2)

    def concurrent_poll() -> dict:
        with TestClient(app, base_url='http://127.0.0.1') as caller:
            barrier.wait(timeout=5)
            result = poll(caller, enrollment)
            assert result.status_code == 200, result.text
            return result.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: concurrent_poll(), range(2)))
    assert sorted(result['state'] for result in results) == ['issued', 'waiting']
    assert sum('session' in result for result in results) == 1
    with local_access.db() as con:
        assert con.execute('SELECT COUNT(*) FROM auth_families WHERE user=?', (student_id,)).fetchone()[0] == 1
        assert con.execute('SELECT state FROM remote_login_requests').fetchone()[0] == 'issued'


def test_failed_session_issue_rolls_back_consumption_and_all_credentials(family, monkeypatch):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    start(client, guardian, student_id)
    original = remote_login.token_pair

    def fail_after_inserts(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError('injected token issuance failure')

    monkeypatch.setattr(remote_login, 'token_pair', fail_after_inserts)
    failed = poll(client, enrollment)
    assert failed.status_code == 500
    assert 'injected token issuance failure' not in failed.text
    with local_access.db() as con:
        assert con.execute('SELECT state FROM remote_login_requests').fetchone()[0] == 'pending'
        assert con.execute('SELECT COUNT(*) FROM auth_families').fetchone()[0] == 0
        assert con.execute('SELECT COUNT(*) FROM refresh_tokens').fetchone()[0] == 0
        assert con.execute('SELECT family FROM remote_login_devices').fetchone()[0] is None
    monkeypatch.setattr(remote_login, 'token_pair', original)
    assert poll(client, enrollment).json()['state'] == 'issued'


def test_normal_logout_keeps_explicit_support_and_revokes_old_session(family):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    start(client, guardian, student_id)
    session = poll(client, enrollment).json()['session']
    assert poll(client, enrollment, 'signed_in').status_code == 200
    signed = headers('student', session['access_token'])
    assert client.delete(BASE + '/student/session', headers=signed).status_code == 200
    assert client.get('/local/me', headers=signed).status_code == 401
    assert refresh(client, 'student', session['refresh_token']).status_code == 401
    assert client.get(support_path(student_id), headers=headers('guardian', guardian['token'])).json()['enabled']
    start(client, guardian, student_id)
    resumed = poll(client, enrollment).json()['session']
    assert resumed['family_id'] != session['family_id']
    assert client.get('/local/me', headers=headers('student', resumed['access_token'])).status_code == 200


def test_normal_logout_cancels_old_request_but_allows_fresh_guardian_request(family):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    initial = start(client, guardian, student_id)
    assert client.delete(BASE + '/student/session', headers=headers('student', student['token'])).status_code == 200
    state = client.get(support_path(student_id), headers=headers('guardian', guardian['token'])).json()
    assert state['enabled'] and state['state'] == 'cancelled'
    assert 'session' not in poll(client, enrollment).json()
    replacement = start(client, guardian, student_id)
    assert replacement['request_id'] != initial['request_id']
    issued = poll(client, enrollment).json()['session']
    # Discarding an issued response also preserves the separately approved device.
    assert client.delete(BASE + '/student/session', headers=headers('student', issued['access_token'])).status_code == 200
    assert refresh(client, 'student', issued['refresh_token']).status_code == 401
    assert client.get(support_path(student_id), headers=headers('guardian', guardian['token'])).json()['state'] == 'cancelled'
    start(client, guardian, student_id)
    assert poll(client, enrollment).json()['session']['user']['id'] == student_id


@pytest.mark.parametrize('action', ['unlink', 'student_logout_all', 'guardian_logout_all',
                                    'student_recover', 'guardian_recover', 'device_family',
                                    'guardian_disable', 'student_disable'])
@pytest.mark.parametrize('request_state', ['pending', 'issued'])
def test_security_actions_revoke_device_proof_and_pending_or_issued_grants(family, action, request_state):
    client, guardian, student_id, student = family
    initial = exchange(client, 'student', oauth(client, 'student', 'student')).json() if action == 'device_family' else None
    enrollment = enroll(client, initial['access_token'] if initial else student['token'])
    pending = start(client, guardian, student_id)
    session = poll(client, enrollment).json()['session'] if request_state == 'issued' else None
    sh = headers('student', student['token'])
    gh = headers('guardian', guardian['token'])
    if action == 'unlink':
        result = client.post(BASE + '/student/connections/unlink', headers=sh,
                             json={'student': student_id, 'confirm': True})
    elif action.endswith('_logout_all'):
        role = action.split('_')[0]
        result = client.post(f'{BASE}/{role}/logout-all', headers=sh if role == 'student' else gh)
    elif action.endswith('_recover'):
        role = action.split('_')[0]
        codes = client.post(f'{BASE}/{role}/recovery-codes', headers=sh if role == 'student' else gh,
                            json={'password': PASSWORD}).json()['recovery_codes']
        result = client.post(f'{BASE}/{role}/recover', headers=headers(role),
                             json={'username': role, 'code': codes[0], 'password': PASSWORD + '-new'})
    elif action == 'device_family':
        result = client.delete(BASE + '/student/devices/' + (session or initial)['family_id'], headers=sh)
    elif action == 'guardian_disable':
        result = client.delete(support_path(student_id), headers=gh)
    else:
        result = client.post(BASE + '/student/remote-login/disable', headers=headers('student'), json=proof(enrollment))
    assert result.status_code == 200, result.text
    assert poll(client, enrollment).status_code == 401
    if session:
        assert client.get('/local/me', headers=headers('student', session['access_token'])).status_code == 401
        assert refresh(client, 'student', session['refresh_token']).status_code == 401
    with local_access.db() as con:
        assert con.execute('SELECT revoked FROM remote_login_devices WHERE id=?',
                           (enrollment['device_id'],)).fetchone()[0] == 1
        assert con.execute('SELECT state FROM remote_login_requests WHERE id=?',
                           (pending['request_id'],)).fetchone()[0] == 'cancelled'
    if action.startswith('guardian_') and action != 'guardian_disable':
        gh = headers('guardian', client.post(BASE + '/guardian/session', headers=headers('guardian'),
                     json={'username': 'guardian', 'password': PASSWORD + '-new' if action.endswith('_recover') else PASSWORD}).json()['token'])
    assert client.post(support_path(student_id), headers=gh).status_code in (403, 409)


def test_revoking_enrollment_auth_family_blocks_support_before_first_remote_login(family):
    client, guardian, student_id, _ = family
    session = exchange(client, 'student', oauth(client, 'student', 'student')).json()
    enrollment = enroll(client, session['access_token'])
    start(client, guardian, student_id)
    assert client.delete(BASE + '/student/devices/' + session['family_id'],
                         headers=headers('student', session['access_token'])).status_code == 200
    assert poll(client, enrollment).status_code == 401
    assert refresh(client, 'student', session['refresh_token']).status_code == 401
    assert client.post(support_path(student_id), headers=headers('guardian', guardian['token'])).status_code == 409


@pytest.mark.parametrize('same_login_family', [False, True])
def test_replacement_revokes_old_proof_and_keeps_enrolling_session(family, same_login_family):
    client, guardian, student_id, _ = family
    session = exchange(client, 'student', oauth(client, 'student', 'student')).json()
    first = enroll(client, session['access_token'])
    start(client, guardian, student_id)
    current = session if same_login_family else exchange(client, 'student', oauth(client, 'student', 'student')).json()
    second = enroll(client, current['access_token'])
    assert first['device_id'] != second['device_id']
    assert poll(client, first).status_code == 401
    assert client.get('/local/me', headers=headers('student', current['access_token'])).status_code == 200
    if not same_login_family:
        assert client.get('/local/me', headers=headers('student', session['access_token'])).status_code == 401
    assert poll(client, second).json() == {'state': 'waiting'}
    start(client, guardian, student_id)
    assert poll(client, second).json()['state'] == 'issued'
    with local_access.db() as con:
        assert con.execute('SELECT COUNT(*) FROM remote_login_devices WHERE revoked=0 AND student=?',
                           (student_id,)).fetchone()[0] == 1


@pytest.mark.parametrize('approved', [False, True])
def test_pairing_has_separate_device_login_support_consent(family, approved):
    client, guardian, _, _ = family
    signup = client.post(BASE + '/student/accounts', headers=headers('student'),
                         json={'username': 'independent_remote', 'password': PASSWORD})
    assert signup.status_code == 201
    student = client.post(BASE + '/student/session', headers=headers('student'),
                          json={'username': 'independent_remote', 'password': PASSWORD}).json()
    sh = headers('student', student['token'])
    code = client.post(BASE + '/guardian/connections/code',
                       headers=headers('guardian', guardian['token'])).json()['code']
    preview = client.post(BASE + '/student/connections/preview', headers=sh, json={'code': code}).json()
    confirmed = client.post(BASE + '/student/connections/confirm', headers=sh,
                            json={'request_id': preview['request_id'], 'confirm': True,
                                  'remote_login': approved, 'client_id': CLIENT})
    assert confirmed.status_code == 200, confirmed.text
    assert ('remote_login' in confirmed.json()) == approved
    with local_access.db() as con:
        assert con.execute('SELECT COUNT(*) FROM remote_login_devices WHERE student=?',
                           (student['user']['id'],)).fetchone()[0] == int(approved)
        assert con.execute('SELECT guardian FROM users WHERE id=?',
                           (student['user']['id'],)).fetchone()[0] == guardian['user']['id']
    if approved:
        start(client, guardian, student['user']['id'])
        assert poll(client, confirmed.json()['remote_login']).json()['session']['user']['id'] == student['user']['id']


def test_failed_opt_in_enrollment_rolls_back_pairing_and_keeps_code_usable(family):
    client, guardian, _, _ = family
    assert client.post(BASE + '/student/accounts', headers=headers('student'),
                       json={'username': 'pair_retry', 'password': PASSWORD}).status_code == 201
    student = client.post(BASE + '/student/session', headers=headers('student'),
                          json={'username': 'pair_retry', 'password': PASSWORD}).json()
    sh = headers('student', student['token'])
    code = client.post(BASE + '/guardian/connections/code',
                       headers=headers('guardian', guardian['token'])).json()['code']
    preview = client.post(BASE + '/student/connections/preview', headers=sh, json={'code': code}).json()
    body = {'request_id': preview['request_id'], 'confirm': True, 'remote_login': True, 'client_id': 'b' * 32}
    assert client.post(BASE + '/student/connections/confirm', headers=sh, json=body).status_code == 403
    with local_access.db() as con:
        assert con.execute('SELECT guardian FROM users WHERE id=?', (student['user']['id'],)).fetchone()[0] is None
        assert con.execute('SELECT COUNT(*) FROM remote_login_devices').fetchone()[0] == 0
    retried = client.post(BASE + '/student/connections/confirm', headers=sh, json=body | {'client_id': CLIENT})
    assert retried.status_code == 200 and 'remote_login' in retried.json()


def test_stale_enrollment_authentication_cannot_outlive_logout_all(family, monkeypatch):
    client, _, student_id, student = family
    original = remote_login.require

    def revoke_after_auth(request, role=None):
        user = original(request, role)
        with local_access.db() as con:
            con.execute('BEGIN IMMEDIATE')
            extension_accounts.revoke_user(con, user['id'])
        return user

    monkeypatch.setattr(remote_login, 'require', revoke_after_auth)
    result = client.post(ENROLL, headers=headers('student', student['token']),
                         json={'client_id': CLIENT, 'confirm': True})
    assert result.status_code == 401
    with local_access.db() as con:
        assert con.execute('SELECT COUNT(*) FROM remote_login_devices WHERE student=?', (student_id,)).fetchone()[0] == 0


def test_stale_guardian_auth_cannot_enqueue_a_remote_login(family, monkeypatch):
    client, guardian, student_id, student = family
    enrollment = enroll(client, student['token'])
    original = remote_login.require

    def expire_after_auth(request, role=None):
        user = original(request, role)
        with local_access.db() as con:
            con.execute('DELETE FROM extension_sessions WHERE user=?', (user['id'],))
        return user

    monkeypatch.setattr(remote_login, 'require', expire_after_auth)
    response = client.post(support_path(student_id), headers=headers('guardian', guardian['token']))
    assert response.status_code == 401
    assert poll(client, enrollment).json() == {'state': 'waiting'}
    with local_access.db() as con:
        assert con.execute('SELECT COUNT(*) FROM remote_login_requests').fetchone()[0] == 0


def test_logout_all_locks_before_scanning_even_when_no_device_exists(family, monkeypatch):
    client, _, student_id, student = family
    original = remote_login.revoke_devices
    observed = []

    def check_lock(con, **kwargs):
        if kwargs.get('user') == student_id:
            # Without this lock an enrollment can commit after the empty scan
            # and survive the subsequent session deletions in revoke_user.
            observed.append(con.in_transaction)
            assert con.in_transaction, 'Device revocation must lock before its initial SELECT'
            competitor = sqlite3.connect(os.environ['SULLIVAN_ACCOUNTS_DB'], timeout=0)
            try:
                with pytest.raises(sqlite3.OperationalError, match='locked'):
                    competitor.execute('BEGIN IMMEDIATE')
            finally:
                competitor.rollback()
                competitor.close()
        return original(con, **kwargs)

    monkeypatch.setattr(remote_login, 'revoke_devices', check_lock)
    response = client.post(BASE + '/student/logout-all', headers=headers('student', student['token']))
    assert response.status_code == 200 and observed == [True]
    assert client.post(ENROLL, headers=headers('student', student['token']),
                       json={'client_id': CLIENT, 'confirm': True}).status_code == 401
