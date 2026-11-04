"""Local accounts and assignment authorization. No provider configuration is read here."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from uuid import uuid4
from typing import Literal
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, SecretStr
from app.runtime import BUILD, INSTANCE
from app import login_voice

router = APIRouter(prefix='/local')
COOKIE = 'sullivan_local_session'

def enabled():
    return os.getenv('SULLIVAN_ROLE_AUTH', '1') != '0'

@contextmanager
def db():
    default=Path(__file__).resolve().parents[3]/'data/private/accounts.sqlite'
    path = Path(os.getenv('SULLIVAN_ACCOUNTS_DB', str(default))).resolve()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    con.executescript('''
    CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT UNIQUE, name TEXT, role TEXT, guardian TEXT, salt TEXT, password TEXT, onboarded INTEGER DEFAULT 0, settings TEXT DEFAULT '{}');
    CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, user TEXT REFERENCES users(id), expires REAL);
    CREATE TABLE IF NOT EXISTS owners(session TEXT PRIMARY KEY, guardian TEXT);
    CREATE TABLE IF NOT EXISTS lectures(id TEXT PRIMARY KEY, guardian TEXT, title TEXT, subject TEXT, snapshot TEXT, playback TEXT, ready INTEGER DEFAULT 0, media_key TEXT, chat_allowed INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS assignments(lecture TEXT REFERENCES lectures(id) ON DELETE CASCADE, student TEXT REFERENCES users(id), position INTEGER, PRIMARY KEY(lecture, student));
    CREATE TABLE IF NOT EXISTS progress(lecture TEXT REFERENCES lectures(id) ON DELETE CASCADE, student TEXT REFERENCES users(id), payload TEXT, PRIMARY KEY(lecture, student));
    CREATE TABLE IF NOT EXISTS failures(identity TEXT PRIMARY KEY, count INTEGER, until REAL);
    ''')
    os.chmod(path, 0o600)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()

def public(user):
    return {k:user[k] for k in ('id','username','name','role','guardian','onboarded')} | {'settings':json.loads(user['settings'])}

def current(request):
    token = request.cookies.get(COOKIE, '')
    if not token: return None
    with db() as c:
        return c.execute('SELECT u.* FROM users u JOIN sessions s ON s.user=u.id WHERE s.token=? AND s.expires>?', (hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone()

def require(request, role=None):
    user = current(request)
    if user is None: raise HTTPException(401, '먼저 로그인해 주세요.')
    if role and user['role'] != role: raise HTTPException(403, '이 기능은 보호자만 사용할 수 있습니다.')
    return user

def own(c, user, lecture):
    row=c.execute('SELECT * FROM lectures WHERE id=?',(lecture,)).fetchone()
    if not row: raise HTTPException(404,'강의를 찾을 수 없습니다.')
    if user['role']=='guardian':
        allowed=row['guardian']==user['id']
    else:
        allowed=row['ready'] and c.execute('SELECT 1 FROM assignments WHERE lecture=? AND student=?',(lecture,user['id'])).fetchone()
    if not allowed: raise HTTPException(403,'배정된 준비 완료 강의만 열 수 있습니다.')
    return row

def attach_owner(request, session):
    if enabled():
        u=require(request,'guardian')
        with db() as c:c.execute('INSERT INTO owners VALUES (?,?)',(session,u['id']))

async def guard(request, call_next):
    if not enabled(): return await call_next(request)
    path=request.url.path
    try:
        if request.method not in ('GET','HEAD','OPTIONS') and (path.startswith('/v1/') or path.startswith('/local/')):
            origin=request.headers.get('origin')
            if origin and origin != str(request.base_url).rstrip('/'):
                raise HTTPException(403,'다른 출처의 요청은 허용하지 않습니다.')
            if request.headers.get('x-local-request')!='1':raise HTTPException(403,'요청 확인 헤더가 필요합니다.')
        if path.startswith('/v1/'):
            u=require(request,'guardian')
            parts=path.split('/')
            if len(parts)>3 and parts[2]=='lectures':
                with db() as c:
                    owner=c.execute('SELECT guardian FROM owners WHERE session=?',(parts[3],)).fetchone()
                    if not owner or owner[0]!=u['id']:raise HTTPException(403,'다른 계정의 분석 세션입니다.')
        response=await call_next(request)
        if path.startswith(('/local/','/v1/')) or path=='/' or Path(path).suffix in ('.html','.js','.css','.json'):response.headers['Cache-Control']='no-store'
        return response
    except HTTPException as e:
        return JSONResponse({'detail':e.detail},status_code=e.status_code,headers={'Cache-Control':'no-store'})

class Credentials(BaseModel):
    username:str=Field(min_length=3,max_length=60,pattern=r'^[a-zA-Z0-9_.-]+$')
    password:str=Field(min_length=8,max_length=128)
    name:str=Field(default='보호자',min_length=1,max_length=80)
    role:Literal['student','guardian'] | None=None

def create_user(c,p,role,guardian=None):
    salt=secrets.token_hex(16);ident=uuid4().hex
    try:c.execute('INSERT INTO users(id,username,name,role,guardian,salt,password) VALUES(?,?,?,?,?,?,?)',(ident,p.username,p.name,role,guardian,salt,password_hash(p.password,salt)))
    except sqlite3.IntegrityError:raise HTTPException(409,'다른 로그인 이름을 사용해 주세요.')
    return ident

def login_response(c,ident):
    token=secrets.token_urlsafe(32)
    c.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
    c.execute('INSERT INTO sessions VALUES(?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),ident,time.time()+28800))
    response=JSONResponse(public(c.execute('SELECT * FROM users WHERE id=?',(ident,)).fetchone()))
    # The local launcher binds loopback HTTP. SameSite, origin checks and a custom header protect mutations.
    response.set_cookie(COOKIE,token,httponly=True,samesite='strict',max_age=28800)
    return response

@router.get('/status')
def status(request:Request):
    native=login_voice.available(request)
    with db() as c:return {'needs_setup':not bool(c.execute("SELECT 1 FROM users WHERE role='guardian'").fetchone()),'build':BUILD,'instance':INSTANCE,'sample_assignment':'server-catalog-v1','system_login_voice':native,'system_login_voice_profile':login_voice.profile() if native else None}

class LoginVoiceRequest(BaseModel):
    model_config={'extra':'forbid'}
    action:Literal['start','stop']
    ident:str=Field(min_length=8,max_length=64,pattern=r'^[a-zA-Z0-9-]+$')

@router.post('/login-voice')
def initial_login_voice(p:LoginVoiceRequest,request:Request):
    if not login_voice.available(request):raise HTTPException(503,'이 실행에서는 로컬 시작 음성을 사용할 수 없습니다.')
    if p.action=='stop':
        login_voice.stop(p.ident)
        return {'completed':False,'cancelled':True}
    if current(request) is not None:raise HTTPException(409,'로그인된 화면에서는 시작 안내를 실행하지 않습니다.')
    return login_voice.speak(p.ident)

@router.post('/setup')
def setup(p:Credentials):
    with db() as c:
        c.execute('BEGIN IMMEDIATE')
        if c.execute("SELECT 1 FROM users WHERE role='guardian'").fetchone():raise HTTPException(403,'초기 보호자 설정은 이미 완료됐습니다.')
        return login_response(c,create_user(c,p,'guardian'))

@router.post('/login')
def login(p:Credentials,request:Request):
    identity=hashlib.sha256(f'{request.client.host if request.client else "local"}:{p.username}'.encode()).hexdigest()
    denied=False
    with db() as c:
        f=c.execute('SELECT * FROM failures WHERE identity=?',(identity,)).fetchone()
        if f and f['count']>=5 and f['until']>time.time():raise HTTPException(429,'로그인 시도가 많습니다. 10분 뒤 다시 시도해 주세요.')
        u=c.execute('SELECT * FROM users WHERE username=?',(p.username,)).fetchone()
        salt=u['salt'] if u else '00'*16
        valid=hmac.compare_digest(password_hash(p.password,salt),u['password'] if u else '0'*128)
        if not u or not valid:
            count=f['count']+1 if f and f['until']>time.time() else 1
            c.execute('INSERT OR REPLACE INTO failures VALUES(?,?,?)',(identity,count,time.time()+600));denied=True
        else:
            if p.role and p.role!=u['role']:raise HTTPException(403,'선택한 로그인 유형과 계정이 다릅니다. 학생 로그인 또는 보호자 로그인을 다시 선택해 주세요.')
            c.execute('DELETE FROM failures WHERE identity=?',(identity,))
            response=login_response(c,u['id'])
    if denied:raise HTTPException(401,'로그인 이름 또는 비밀번호를 확인해 주세요.')
    return response

@router.post('/logout')
def logout(request:Request):
    with db() as c:c.execute('DELETE FROM sessions WHERE token=?',(hashlib.sha256(request.cookies.get(COOKIE,'').encode()).hexdigest(),))
    response=JSONResponse({'ok':True});response.delete_cookie(COOKIE);return response

@router.get('/me')
def me(request:Request):return public(require(request))

@router.post('/students')
def student_create(p:Credentials,request:Request):
    u=require(request,'guardian')
    with db() as c:return {'id':create_user(c,p,'student',u['id'])}

@router.get('/students')
def students(request:Request):
    u=require(request,'guardian')
    with db() as c:return [public(r) for r in c.execute('SELECT * FROM users WHERE guardian=? ORDER BY name',(u['id'],))]

class Settings(BaseModel):
    auto_description:bool=True
    problem_mode:bool=True
    speech_rate:float=Field(default=.95,ge=.75,le=1.25)
    speech_volume:float=Field(default=.9,ge=0,le=1)
    reader_mode:bool=False
    focus_voice:bool=False
    reset_onboarding:bool=False

@router.put('/students/{ident}/settings')
def settings(ident:str,p:Settings,request:Request):
    u=require(request,'guardian')
    with db() as c:
        if not c.execute('SELECT 1 FROM users WHERE id=? AND guardian=?',(ident,u['id'])).fetchone():raise HTTPException(403,'연결된 학생이 아닙니다.')
        c.execute('UPDATE users SET settings=?,onboarded=CASE WHEN ? THEN 0 ELSE onboarded END WHERE id=?',(p.model_dump_json(exclude={'reset_onboarding'}),p.reset_onboarding,ident))
    return {'ok':True}

@router.post('/onboarding')
def onboarding(request:Request):
    u=require(request,'student')
    with db() as c:c.execute('UPDATE users SET onboarded=1 WHERE id=?',(u['id'],))
    return {'ok':True}

class Publish(BaseModel):
    title:str=Field(min_length=1,max_length=160)
    subject:str=Field(default='일반',max_length=80)
    students:list[str]=Field(min_length=1,max_length=50)
    snapshot:dict | None=None
    session_id:str | None=None
    sample_id:str | None=None
    playback:dict=Field(default_factory=dict)
    store_local_media:bool=False
    ready:bool=False
    chat_consent:bool=False
    access_code:SecretStr | None=None

@router.post('/lectures')
def publish(p:Publish,request:Request):
    from app.main import agent
    from app.models import LectureSnapshot
    from app.adapters.video_link import normalize_video_link
    u=require(request,'guardian')
    if p.chat_consent:
        from app.core.demo_gate import check_access_code, DemoGateError
        try:check_access_code(p.access_code.get_secret_value() if p.access_code else None)
        except DemoGateError as e:raise HTTPException(e.status_code,e.message) from None
    with db() as c:
        if len(set(p.students))!=len(p.students):raise HTTPException(400,'같은 학생을 여러 번 배정할 수 없습니다.')
        for student in p.students:
            if not c.execute('SELECT 1 FROM users WHERE id=? AND guardian=?',(student,u['id'])).fetchone():raise HTTPException(403,'연결된 학생만 배정할 수 있습니다.')
        if p.sample_id not in (None,'science','history'):raise HTTPException(400,'샘플을 확인해 주세요.')
        if p.sample_id:
            from app.sample_catalog import prepared_sample
            _,snap=prepared_sample(p.sample_id)
        else:
            owner=c.execute('SELECT guardian FROM owners WHERE session=?',(p.session_id,)).fetchone()
            if not owner or owner[0]!=u['id']:raise HTTPException(403,'본인의 분석 세션만 사용할 수 있습니다.')
            snap=agent.snapshot(p.session_id)
            if snap.active_mode=='waiting':raise HTTPException(400,'분석 또는 학습자료 준비를 먼저 완료해 주세요.')
        # Only server-checked metadata is published; provider keys and access codes are never persisted.
        playback={'kind':'none'}
        kind=p.playback.get('kind')
        if kind in ('youtube','direct'):
            link=normalize_video_link(str(p.playback.get('normalized_url','')))
            if link.playback_kind not in ('youtube','direct'):raise HTTPException(400,'재생 가능한 영상 주소가 필요합니다.')
            playback={'kind':link.playback_kind,'normalized_url':link.normalized_url,'playback_url':link.playback_url}
        elif p.store_local_media:
            playback={'kind':'local','name':str(p.playback.get('name','강의 영상'))[:160]}
        from app.core.lecture_agent import redact_sensitive_text
        def redact_tree(value):
            if isinstance(value,str): return redact_sensitive_text(value)
            if isinstance(value,list): return [redact_tree(v) for v in value]
            if isinstance(value,dict): return {k:redact_tree(v) for k,v in value.items()}
            return value
        snap=LectureSnapshot.model_validate(redact_tree(snap.model_dump(mode='json')))
        if p.ready and p.store_local_media:raise HTTPException(400,'파일 강의는 브라우저 암호화 저장을 마친 뒤 준비 완료로 제공해 주세요.')
        if p.ready and snap.active_mode=='waiting':raise HTTPException(400,'학습자료 준비를 먼저 완료해 주세요.')
        ident=uuid4().hex
        key=secrets.token_hex(32) if p.store_local_media else None
        c.execute('INSERT INTO lectures VALUES(?,?,?,?,?,?,?,?,?)',(ident,u['id'],p.title,p.subject,snap.model_dump_json(),json.dumps(playback),int(p.ready),key,int(p.chat_consent)))
        for student in p.students:
            position=c.execute('SELECT COALESCE(MAX(position),0)+1 FROM assignments WHERE student=?',(student,)).fetchone()[0]
            c.execute('INSERT INTO assignments VALUES(?,?,?)',(ident,student,position))
    return {'id':ident,'media_key':key,'ready':p.ready}

class SampleAssignment(BaseModel):
    students:list[str]=Field(min_length=1,max_length=50)

@router.post('/samples/{sample_id}/assign')
def assign_sample(sample_id:str,p:SampleAssignment,request:Request):
    require(request,'guardian')
    from app.sample_catalog import catalog
    spec=catalog().get(sample_id)
    if spec is None:raise HTTPException(404,'지원하는 샘플을 선택해 주세요.')
    result=publish(Publish(title=spec['title'],subject=spec['subject'],students=p.students,sample_id=sample_id,ready=True,playback={'kind':'youtube','normalized_url':spec['videoUrl']}),request)
    return {**result,'title':spec['title'],'students':p.students,'build':BUILD}

@router.put('/lectures/{ident}/ready')
def ready(ident:str,request:Request):
    u=require(request,'guardian')
    with db() as c:
        row=own(c,u,ident)
        if json.loads(row['snapshot']).get('active_mode')=='waiting':raise HTTPException(400,'학습자료 준비를 먼저 완료해 주세요.')
        c.execute('UPDATE lectures SET ready=1 WHERE id=?',(ident,))
    return {'ok':True}

@router.get('/lectures')
def lectures(request:Request):
    u=require(request)
    with db() as c:
        if u['role']=='guardian':rows=c.execute('SELECT l.id,l.title,l.subject,l.ready,l.playback,NULL AS position FROM lectures l WHERE guardian=? ORDER BY rowid DESC',(u['id'],)).fetchall()
        else:rows=c.execute('SELECT l.id,l.title,l.subject,l.ready,a.position FROM lectures l JOIN assignments a ON l.id=a.lecture WHERE a.student=? AND l.ready=1 ORDER BY a.position,l.rowid',(u['id'],)).fetchall()
        assignments={}
        if u['role']=='guardian':
            for a in c.execute('SELECT a.lecture,a.student FROM assignments a JOIN lectures l ON l.id=a.lecture WHERE l.guardian=? ORDER BY a.rowid',(u['id'],)):
                assignments.setdefault(a['lecture'],[]).append(a['student'])
        result=[]
        for r in rows:
            row={k:r[k] for k in ('id','title','subject','ready','position')}
            if u['role']=='guardian':
                row['students']=assignments.get(r['id'],[])
                row['playback_kind']=json.loads(r['playback']).get('kind','none')
            result.append(row)
        return result

@router.get('/lectures/{ident}')
def lecture(ident:str,request:Request):
    u=require(request)
    from app.models import LectureSnapshot
    with db() as c:
        r=own(c,u,ident)
        snapshot=json.loads(r['snapshot'])
        snapshot['session']['title']=r['title'];snapshot['session']['subject']=r['subject']
        settings=json.loads(u['settings'])
        # A student's stronger problem protection can only narrow the prepared result.
        if u['role']=='student' and settings.get('problem_mode',True):
            snapshot['session']['problem_mode']=True
            for gap in snapshot['visual_gaps']:
                if gap['kind']=='answer':gap.update(action='HOLD',safe_to_speak=False,public_description='',source_text=None)
            if any(g['kind']=='answer' for g in snapshot['visual_gaps']):
                snapshot['study_guide']={};snapshot['passage']=None;snapshot['review']={};snapshot['concept_index']=[]
        blocked=[g for g in snapshot['visual_gaps'] if not g['safe_to_speak'] or g['confidence']<.72]
        forbidden=[str(value) for g in blocked for value in (g.get('public_description'),g.get('source_text')) if value]
        def contains_blocked(value):return any(text in json.dumps(value,ensure_ascii=False) for text in forbidden)
        if contains_blocked(snapshot.get('study_guide')):snapshot['study_guide']={}
        if contains_blocked(snapshot.get('passage')):snapshot['passage']=None
        for key,items in snapshot.get('review',{}).items():
            if isinstance(items,list):snapshot['review'][key]=[item for item in items if not contains_blocked(item)]
        snapshot['concept_index']=[item for item in snapshot.get('concept_index',[]) if not contains_blocked(item)]
        for gap in snapshot['visual_gaps']:
            if not gap['safe_to_speak'] or gap['confidence']<.72:gap.update(safe_to_speak=False,public_description='',source_text=None,action='HOLD')
        snapshot['safe_description_count']=sum(g['safe_to_speak'] and g['action'] in ('INTERRUPT','DESCRIBE_AT_BREAK') for g in snapshot['visual_gaps'])
        snapshot['held_count']=sum(g['action']=='HOLD' for g in snapshot['visual_gaps'])
        p=c.execute('SELECT payload FROM progress WHERE lecture=? AND student=?',(ident,u['id'])).fetchone()
        return {'id':r['id'],'title':r['title'],'subject':r['subject'],'snapshot':LectureSnapshot.model_validate(snapshot).model_dump(mode='json'),'playback':json.loads(r['playback']),'media_key':r['media_key'],'progress':json.loads(p[0]) if p else {}}

class Edit(BaseModel):
    title:str=Field(min_length=1,max_length=160)
    subject:str=Field(min_length=1,max_length=80)
    students:list[str]=Field(min_length=1,max_length=50)

@router.put('/lectures/{ident}')
def edit(ident:str,p:Edit,request:Request):
    u=require(request,'guardian')
    with db() as c:
        own(c,u,ident)
        for student in p.students:
            if not c.execute('SELECT 1 FROM users WHERE id=? AND guardian=?',(student,u['id'])).fetchone():raise HTTPException(403,'연결된 학생만 배정할 수 있습니다.')
        c.execute('UPDATE lectures SET title=?,subject=? WHERE id=?',(p.title,p.subject,ident))
        previous={r['student']:r['position'] for r in c.execute('SELECT * FROM assignments WHERE lecture=?',(ident,))}
        c.execute('DELETE FROM assignments WHERE lecture=?',(ident,))
        for student in p.students:c.execute('INSERT INTO assignments VALUES(?,?,?)',(ident,student,previous.get(student,999)))
    return {'ok':True}

class Order(BaseModel):
    student:str
    lectures:list[str]=Field(max_length=500)

@router.put('/order')
def order(p:Order,request:Request):
    u=require(request,'guardian')
    with db() as c:
        if not c.execute('SELECT 1 FROM users WHERE id=? AND guardian=?',(p.student,u['id'])).fetchone():raise HTTPException(403,'연결된 학생이 아닙니다.')
        existing={r[0] for r in c.execute('SELECT lecture FROM assignments WHERE student=?',(p.student,))}
        if len(set(p.lectures))!=len(p.lectures) or set(p.lectures)!=existing:raise HTTPException(400,'배정된 강의 전체 순서를 보내 주세요.')
        for i,ident in enumerate(p.lectures):c.execute('UPDATE assignments SET position=? WHERE lecture=? AND student=?',(i+1,ident,p.student))
    return {'ok':True}

@router.delete('/lectures/{ident}')
def delete(ident:str,request:Request):
    u=require(request,'guardian')
    with db() as c:own(c,u,ident);c.execute('DELETE FROM lectures WHERE id=?',(ident,))
    return {'ok':True}

class Progress(BaseModel):
    position_ms:int=Field(default=0,ge=0,le=86400000)
    bookmarks:list[dict]=Field(default_factory=list,max_length=100)
    underlined:list[str]=Field(default_factory=list,max_length=100)
    note:str=Field(default='',max_length=6000)

@router.put('/lectures/{ident}/progress')
def progress(ident:str,p:Progress,request:Request):
    u=require(request,'student')
    payload=p.model_dump_json()
    if len(payload)>64000:raise HTTPException(413,'학습 기록이 너무 큽니다.')
    with db() as c:
        own(c,u,ident)
        c.execute('INSERT OR REPLACE INTO progress VALUES(?,?,?)',(ident,u['id'],payload))
    return {'ok':True}


@router.post('/lectures/{ident}/agent-turn')
async def student_chat(ident:str,request:Request):
    import asyncio
    from app.models import AgentTurnInput, LectureSnapshot
    from app.adapters.gemini_agent import run_agent_turn, AgentTurnError, AgentUnavailableError
    from app.core.demo_gate import limiter, client_ip, analysis_timeout_seconds, server_gemini_key, DemoGateError
    u=require(request,'student')
    with db() as c:
        row=own(c,u,ident)
        if not row['chat_allowed']:raise HTTPException(403,'보호자가 Gemini 학습 대화를 허용하지 않았습니다. 로컬 보조 모드를 사용합니다.')
    if not server_gemini_key():raise HTTPException(503,'지금은 로컬 보조 모드로 답합니다.')
    payload=AgentTurnInput.model_validate(await request.json())
    snapshot=LectureSnapshot.model_validate(lecture(ident,request)['snapshot'])
    try:
        await asyncio.to_thread(limiter.consume,client_ip(request))
        return await asyncio.wait_for(run_agent_turn(snapshot,message=payload.message,current_time_ms=payload.current_time_ms),timeout=analysis_timeout_seconds())
    except DemoGateError as e:raise HTTPException(e.status_code,e.message) from None
    except asyncio.TimeoutError:raise HTTPException(504,'응답 시간이 초과되었습니다. 다시 질문하거나 로컬 보조 모드를 사용하세요.') from None
    except (AgentTurnError,AgentUnavailableError) as e:raise HTTPException(502,str(e)) from None


@router.get('/students/{ident}/order')
def student_order(ident:str,request:Request):
    u=require(request,'guardian')
    with db() as c:
        if not c.execute('SELECT 1 FROM users WHERE id=? AND guardian=?',(ident,u['id'])).fetchone():raise HTTPException(403,'연결된 학생이 아닙니다.')
        return [r[0] for r in c.execute('SELECT lecture FROM assignments WHERE student=? ORDER BY position,rowid',(ident,))]


class PersonalSpeechPreferences(BaseModel):
    model_config = {"extra": "forbid"}
    focus_voice: bool
    reader_mode: bool

@router.put('/preferences')
def personal_preferences(p:PersonalSpeechPreferences,request:Request):
    u=require(request,'student')
    with db() as c:
        prefs=json.loads(u['settings'])
        prefs.update(p.model_dump())
        if prefs['reader_mode']:prefs['focus_voice']=False
        c.execute('UPDATE users SET settings=? WHERE id=?',(json.dumps(prefs),u['id']))
    return {'settings':prefs}
