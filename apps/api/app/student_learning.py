"""Student-only learning preferences and media metadata; raw media is never accepted."""
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app import local_access as accounts


def authorize(request: Request):
    from app.extension_access import current
    user = current(request)
    if user is None:
        raise HTTPException(401, '학생 확장에서 다시 로그인해 주세요.')
    if user['role'] != 'student':
        raise HTTPException(403, '학생만 사용할 수 있습니다.')


router = APIRouter(prefix='/extension/v1/student', dependencies=[Depends(authorize)])


@router.get('/lectures/{ident}')
def lecture(ident: str, request: Request):
    result = accounts.lecture(ident, request)
    result['settings'] = json.loads(accounts.require(request, 'student')['settings'])
    with accounts.db() as con:
        row = con.execute('SELECT identity FROM lecture_media WHERE lecture=?', (ident,)).fetchone()
        result['media_identity'] = json.loads(row[0]) if row else None
    return result


class Preferences(BaseModel):
    model_config = {'extra': 'forbid'}
    speech_rate: float = Field(ge=.75, le=1.25)
    speech_volume: float = Field(ge=0, le=1)
    auto_description: bool
    reader_mode: bool
    focus_voice: bool


@router.put('/preferences')
def preferences(payload: Preferences, request: Request):
    user = accounts.require(request, 'student')
    with accounts.db() as con:
        settings = json.loads(user['settings'])
        settings.update(payload.model_dump())
        if settings['reader_mode']:
            settings['focus_voice'] = False
        con.execute('UPDATE users SET settings=? WHERE id=?', (json.dumps(settings), user['id']))
    return {'settings': settings}
