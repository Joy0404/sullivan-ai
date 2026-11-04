import threading
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from app import login_voice
from app.main import app

HEAD={'X-Local-Request':'1'}

@pytest.fixture
def native(monkeypatch):
    monkeypatch.setenv('SULLIVAN_ROLE_AUTH','1')
    monkeypatch.setenv('SULLIVAN_SYSTEM_LOGIN_VOICE','1')
    monkeypatch.setattr(login_voice,'PLATFORM','darwin')
    monkeypatch.setattr(login_voice,'korean_voice',lambda:'Yuna')
    monkeypatch.setattr(login_voice,'SAY',SimpleNamespace(is_file=lambda:True))
    with login_voice._lock:
        login_voice._recent.clear();login_voice._active=None
    return TestClient(app,base_url='http://127.0.0.1',client=('127.0.0.1',50001),headers=HEAD)

class Process:
    def __init__(self):self.code=None;self.stopped=False;self.started=threading.Event();self.release=threading.Event()
    def poll(self):return self.code
    def wait(self,timeout):
        self.started.set();assert self.release.wait(timeout)
        self.code=-15 if self.stopped else 0;return self.code
    def terminate(self):self.stopped=True;self.release.set()
    def kill(self):self.terminate()

def test_requires_explicit_local_native_mode(native,monkeypatch):
    assert native.get('/local/status').json()['system_login_voice']
    monkeypatch.setenv('SULLIVAN_SYSTEM_LOGIN_VOICE','0')
    assert not native.get('/local/status').json()['system_login_voice']
    assert native.post('/local/login-voice',json={'action':'start','ident':'test-start-1'}).status_code==503

def test_remote_hosts_and_cloud_cannot_speak(native,monkeypatch):
    request=lambda host,client:SimpleNamespace(url=SimpleNamespace(hostname=host),client=SimpleNamespace(host=client))
    assert not login_voice.available(request('127.0.0.1','203.0.113.10'))
    assert not login_voice.available(request('attacker.test','127.0.0.1'))
    monkeypatch.setenv('RENDER','true')
    assert not login_voice.available(request('127.0.0.1','127.0.0.1'))

def test_only_fixed_phrase_and_owned_process(native,monkeypatch):
    calls=[];process=Process();process.release.set()
    def spawn(args,**kwargs):calls.append((args,kwargs));return process
    monkeypatch.setattr(login_voice.subprocess,'Popen',spawn)
    payload={'action':'start','ident':'test-start-2'}
    assert native.post('/local/login-voice',json=payload).json()['completed']
    assert native.post('/local/login-voice',json=payload).json()['completed']
    assert len(calls)==1
    assert calls[0][0]==['/usr/bin/say','-v','Yuna','-r','166','[[volm 0.9]]학생 로그인']
    assert native.get('/local/status').json()['system_login_voice_profile']=={'name':'Yuna','lang':'ko-KR','rate':.95,'volume':.9,'pitch':1}
    assert not calls[0][1].get('shell')
    assert native.post('/local/login-voice',json={**payload,'text':'arbitrary text'}).status_code==422

def test_cancel_before_delayed_start(native,monkeypatch):
    monkeypatch.setattr(login_voice.subprocess,'Popen',lambda *a,**k:pytest.fail('Cancelled startup revived'))
    payload={'ident':'test-early-stop'}
    assert native.post('/local/login-voice',json={**payload,'action':'stop'}).json()['cancelled']
    assert native.post('/local/login-voice',json={**payload,'action':'start'}).json()['cancelled']

def test_cancel_in_flight_stops_only_its_process(native,monkeypatch):
    process=Process();monkeypatch.setattr(login_voice.subprocess,'Popen',lambda *a,**k:process)
    result=[];worker=threading.Thread(target=lambda:result.append(login_voice.speak('test-running')))
    worker.start();assert process.started.wait(2)
    login_voice.stop('different-notice');assert not process.stopped
    login_voice.stop('test-running');worker.join(2)
    assert result==[{'completed':False,'cancelled':True}]
    assert login_voice._active is None

def test_csrf_and_logged_in_greeting_are_blocked(native):
    no_header=TestClient(app,base_url='http://127.0.0.1',client=('127.0.0.1',50002))
    payload={'action':'start','ident':'test-csrf'}
    assert no_header.post('/local/login-voice',json=payload).status_code==403
    assert native.post('/local/login-voice',json=payload,headers={'Origin':'https://attacker.test'}).status_code==403
    assert native.post('/local/setup',json={'username':'guardian','password':'fixture-pass-123'}).status_code==200
    assert native.post('/local/login-voice',json=payload).status_code==409
    assert native.post('/local/login-voice',json={**payload,'action':'stop'}).status_code==200
