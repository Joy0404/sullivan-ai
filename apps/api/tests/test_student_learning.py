import hashlib
import json

from app import local_access, main
from app.models import AnalysisPackageInput
from test_extension_access import PASSWORD, family, headers


def test_student_preferences_preserve_guardian_policy_and_reject_role_changes(family):
    client, guardian, ident, student = family
    gh, sh = headers('guardian', guardian['token']), headers('student', student['token'])
    assert client.put('/local/students/' + ident + '/settings', headers=gh,
                      json={'problem_mode': True}).status_code == 200
    body = {'speech_rate': 1.1, 'speech_volume': .7, 'auto_description': False, 'reader_mode': True, 'focus_voice': True}
    result = client.put('/extension/v1/student/preferences', headers=sh, json=body)
    assert result.status_code == 200
    assert result.json()['settings']['problem_mode'] is True
    assert result.json()['settings']['focus_voice'] is False
    assert client.put('/extension/v1/student/preferences', headers=sh,
                      json=body | {'problem_mode': False}).status_code == 422
    assert client.put('/extension/v1/student/preferences', headers=gh, json=body).status_code == 403
    assert client.put('/extension/v1/student/preferences', headers=headers('student'), json=body).status_code == 401


def test_media_identity_comes_from_consented_file_and_is_assignment_scoped(family, monkeypatch):
    client, guardian, student_id, student = family
    gh, sh = headers('guardian', guardian['token']), headers('student', student['token'])
    original = b'LOCAL_VIDEO_FINGERPRINT_TEST'
    async def analyze(path, **kwargs):
        kwargs['cleanup_report']['provider'] = 'deleted'
        return AnalysisPackageInput(passage_text='지문 근거')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    monkeypatch.setenv('DEMO_ACCESS_CODE', 'test-code')
    monkeypatch.setattr(main, 'analyze_uploaded_video_with_gemini', analyze)
    result = client.post('/extension/v1/guardian/preparations/video-file-analysis', headers=gh,
        data={'title': '원본 식별 강의', 'rights_confirmed': 'true', 'cloud_analysis_consent': 'true', 'access_code': 'test-code'},
        files={'video': ('lecture.mp4', original, 'video/mp4')})
    assert result.status_code == 202
    job = result.json()['id']
    published = client.post('/extension/v1/guardian/preparations/' + job + '/publish', headers=gh,
                             json={'students': [student_id]})
    assert published.status_code == 200, published.text
    lecture = published.json()['id']
    envelope = client.get('/extension/v1/student/lectures/' + lecture, headers=sh)
    assert envelope.status_code == 200
    assert envelope.json()['media_identity']['sha256'] == hashlib.sha256(original).hexdigest()
    assert envelope.json()['media_identity']['size_bytes'] == len(original)
    assert 'LOCAL_VIDEO_FINGERPRINT_TEST' not in envelope.text
    assert client.get('/extension/v1/student/lectures/' + lecture, headers=gh).status_code == 403
    other_id = client.post('/local/students', headers=gh, json={'username': 'otherstudent', 'password': PASSWORD}).json()['id']
    other = client.post('/extension/v1/student/session', headers=headers('student'), json={'username': 'otherstudent', 'password': PASSWORD}).json()
    assert client.get('/extension/v1/student/lectures/' + lecture, headers=headers('student', other['token'])).status_code == 403
    assert client.post('/extension/v1/guardian/lectures/' + lecture + '/withdraw', headers=gh, json={'students': [student_id]}).status_code == 200
    assert client.get('/extension/v1/student/lectures/' + lecture, headers=sh).status_code == 403
    with local_access.db() as con:
        assert 'LOCAL_VIDEO_FINGERPRINT_TEST' not in json.dumps(dict(con.execute('SELECT * FROM lecture_media WHERE lecture=?', (lecture,)).fetchone()))
