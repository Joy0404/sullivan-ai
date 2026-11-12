import base64
import hashlib
import json
import re
import time
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import local_access
from test_extension_access import family, headers, PASSWORD

CLIENT='a'*32
REDIRECT=f'https://{CLIENT}.chromiumapp.org/oauth'
VERIFIER='v'*43
BASE='/extension/v1'


def oauth(client,role,username,password=PASSWORD):
    challenge=base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).decode().rstrip('=')
    page=client.get(f'/extension/auth/{role}/authorize',params={'client_id':CLIENT,'redirect_uri':REDIRECT,'code_challenge':challenge,'state':'state'*10,'code_challenge_method':'S256'})
    assert page.status_code==200,page.text
    assert page.headers['referrer-policy']=='same-origin'
    ticket=re.search('name="ticket" value="([^"]+)"',page.text)[1]
    result=client.post(f'/extension/auth/{role}/authorize',headers={'Origin':'http://127.0.0.1'},data={'ticket':ticket,'username':username,'password':password},follow_redirects=False)
    assert result.status_code==303,result.text
    query=parse_qs(urlsplit(result.headers['location']).query)
    assert query['state']==['state'*10]
    return query['code'][0]


def exchange(client,role,code,verifier=VERIFIER):
    return client.post(f'{BASE}/{role}/token',headers=headers(role),data={'grant_type':'authorization_code','client_id':CLIENT,'redirect_uri':REDIRECT,'code':code,'code_verifier':verifier})


def refresh(client,role,token):
    return client.post(f'{BASE}/{role}/token',headers=headers(role),data={'grant_type':'refresh_token','client_id':CLIENT,'redirect_uri':REDIRECT,'refresh_token':token})


def test_pkce_single_use_verifier_redirect_rotation_and_reuse_revocation(family):
    client,guardian,_,student=family
    code=oauth(client,'guardian','guardian')
    assert exchange(client,'guardian',code,'wrong'*10).status_code==400
    granted=exchange(client,'guardian',code)
    assert granted.status_code==200,granted.text
    token=granted.json()
    assert token['expires_in']==900
    assert exchange(client,'guardian',code).status_code==400
    assert client.get('/local/me',headers=headers('guardian',token['access_token'])).status_code==200
    rotated=refresh(client,'guardian',token['refresh_token'])
    assert rotated.status_code==200
    assert rotated.json()['refresh_token']!=token['refresh_token']
    assert client.get('/local/me',headers=headers('guardian',token['access_token'])).status_code==401
    assert refresh(client,'guardian',token['refresh_token']).status_code==401
    assert client.get('/local/me',headers=headers('guardian',rotated.json()['access_token'])).status_code==401
    # Guardian re-use revokes only that family, not student or legacy sessions.
    assert client.get('/local/me',headers=headers('student',student['token'])).status_code==200
    assert client.get('/local/me',headers=headers('guardian',guardian['token'])).status_code==200


def test_authorization_origin_cookie_and_registered_redirect_are_required(family):
    client,*_=family
    challenge=base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).decode().rstrip('=')
    params={'client_id':CLIENT,'redirect_uri':REDIRECT,'code_challenge':challenge,'state':'s'*43}
    assert client.get('/extension/auth/guardian/authorize',params=params|{'redirect_uri':'https://evil.example/callback'}).status_code==400
    assert client.get('/extension/auth/guardian/authorize',params=params|{'code_challenge_method':'plain'}).status_code==400
    page=client.get('/extension/auth/guardian/authorize',params=params)
    ticket=re.search('name="ticket" value="([^"]+)"',page.text)[1]
    assert 'frame-ancestors' in page.headers['content-security-policy']
    data={'ticket':ticket,'username':'guardian','password':PASSWORD}
    assert client.post('/extension/auth/guardian/authorize',headers={'Origin':'https://evil.example'},data=data).status_code==403
    other=TestClient(app,base_url='http://127.0.0.1')
    assert other.post('/extension/auth/guardian/authorize',headers={'Origin':'http://127.0.0.1'},data=data).status_code==403


def test_independent_signup_pair_confirmation_and_unlink_preserve_private_records(family):
    client,guardian,_,_=family
    gh=headers('guardian',guardian['token'])
    signed=client.post(BASE+'/student/accounts',headers=headers('student'),json={'username':'independent','password':PASSWORD,'name':'독립 학생'})
    assert signed.status_code==201
    assert len(signed.json()['recovery_codes'])==8
    student=client.post(BASE+'/student/session',headers=headers('student'),json={'username':'independent','password':PASSWORD}).json()
    sh=headers('student',student['token'])
    assert student['user']['guardian'] is None
    code=client.post(BASE+'/guardian/connections/code',headers=gh).json()['code']
    preview=client.post(BASE+'/student/connections/preview',headers=sh,json={'code':code})
    assert preview.status_code==200
    assert preview.json()['guardian_name']=='보호자'
    assert client.get('/local/students',headers=gh).json()[-1]['id']!=student['user']['id']
    assert client.post(BASE+'/student/connections/confirm',headers=sh,json={'request_id':preview.json()['request_id'],'confirm':False}).status_code==400
    approved=client.post(BASE+'/student/connections/confirm',headers=sh,json={'request_id':preview.json()['request_id'],'confirm':True})
    assert approved.status_code==200
    assert client.post(BASE+'/student/connections/preview',headers=sh,json={'code':code}).status_code==400
    ident=client.post('/local/samples/science/assign',headers=gh,json={'students':[student['user']['id']]}).json()['id']
    assert client.put('/local/lectures/'+ident+'/progress',headers=sh,json={'note':'비공개 메모','position_ms':4000}).status_code==200
    unlinked=client.post(BASE+'/student/connections/unlink',headers=sh,json={'student':student['user']['id'],'confirm':True})
    assert unlinked.status_code==200
    assert client.get('/local/lectures/'+ident,headers=sh).status_code==403
    assert client.get('/local/students/'+student['user']['id']+'/progress',headers=gh).status_code==403
    with local_access.db() as con:
        assert '비공개 메모' in con.execute('SELECT payload FROM progress WHERE student=?',(student['user']['id'],)).fetchone()[0]


def test_pairing_expiry_other_student_and_guardian_cannot_confirm_or_unlink(family):
    client,guardian,student_id,student=family
    gh,sh=headers('guardian',guardian['token']),headers('student',student['token'])
    code=client.post(BASE+'/guardian/connections/code',headers=gh).json()['code']
    preview=client.post(BASE+'/student/connections/preview',headers=sh,json={'code':code}).json()['request_id']
    client.post(BASE+'/student/accounts',headers=headers('student'),json={'username':'another','password':PASSWORD})
    another=client.post(BASE+'/student/session',headers=headers('student'),json={'username':'another','password':PASSWORD}).json()
    ah=headers('student',another['token'])
    assert client.post(BASE+'/student/connections/confirm',headers=ah,json={'request_id':preview,'confirm':True}).status_code==409
    assert client.post(BASE+'/student/connections/unlink',headers=ah,json={'student':student_id,'confirm':True}).status_code==403
    with local_access.db() as con:con.execute('UPDATE pair_codes SET expires=?',(time.time()-1,))
    assert client.post(BASE+'/student/connections/confirm',headers=sh,json={'request_id':preview,'confirm':True}).status_code==409


def test_recovery_is_single_use_and_revokes_all_old_sessions(family):
    client,guardian,_,student=family
    gh=headers('guardian',guardian['token'])
    regenerated=client.post(BASE+'/guardian/recovery-codes',headers=gh,json={'password':PASSWORD})
    assert regenerated.status_code==200
    code=regenerated.json()['recovery_codes'][0]
    with local_access.db() as con:
        assert con.execute('SELECT code FROM recovery_codes WHERE user=?',(guardian['user']['id'],)).fetchone()[0]!=code
    assert client.post(BASE+'/guardian/recover',headers=headers('guardian'),json={'username':'guardian','code':code,'password':'changed-pass-123'}).status_code==200
    assert client.get('/local/me',headers=gh).status_code==401
    assert client.get('/local/me',headers=headers('student',student['token'])).status_code==200
    assert client.post(BASE+'/guardian/recover',headers=headers('guardian'),json={'username':'guardian','code':code,'password':PASSWORD}).status_code==400
    assert client.post(BASE+'/guardian/session',headers=headers('guardian'),json={'username':'guardian','password':'changed-pass-123'}).status_code==200


def test_production_registration_client_allowlist_and_version_gate(family,monkeypatch):
    client,guardian,*_=family
    monkeypatch.setenv('SULLIVAN_PRODUCTION','1')
    monkeypatch.setenv('SULLIVAN_PUBLIC_URL','https://sullivan.example')
    monkeypatch.setenv('SULLIVAN_EXTENSION_CLIENTS',json.dumps({'guardian':CLIENT,'student':'b'*32}))
    monkeypatch.setenv('SULLIVAN_SIGNUP_INVITE','fixture-invite')
    assert client.post(BASE+'/guardian/session',headers=headers('guardian'),json={'username':'guardian','password':PASSWORD}).status_code==403
    assert client.post(BASE+'/guardian/accounts',headers=headers('guardian'),json={'username':'produser','password':PASSWORD}).status_code==403
    assert client.post(BASE+'/guardian/accounts',headers=headers('guardian'),json={'username':'produser','password':PASSWORD,'invite':'fixture-invite'}).status_code==201
    assert client.post('/local/setup',headers={'X-Local-Request':'1'},json={'username':'bad','password':PASSWORD}).status_code==403
    monkeypatch.setenv('SULLIVAN_MIN_EXTENSION_VERSION','0.4.0')
    assert client.get(BASE+'/guardian/capabilities',headers=headers('guardian')).status_code==426
    assert client.get(BASE+'/guardian/capabilities',headers=headers('guardian')|{'X-Sullivan-Version':'0.4.0'}).status_code==200


def test_family_logout_and_devices_are_owner_scoped(family):
    client,guardian,_,_=family
    data=exchange(client,'guardian',oauth(client,'guardian','guardian')).json()
    gh=headers('guardian',data['access_token'])
    listing=client.get(BASE+'/guardian/devices',headers=gh)
    assert listing.status_code==200 and listing.json()[0]['id']==data['family_id']
    other=client.post(BASE+'/guardian/register',headers=headers('guardian'),json={'username':'otherg','password':PASSWORD}).json()
    assert client.delete(BASE+'/guardian/devices/'+data['family_id'],headers=headers('guardian',other['token'])).status_code==404
    assert client.delete(BASE+'/guardian/session',headers=gh).status_code==200
    assert refresh(client,'guardian',data['refresh_token']).status_code==401
