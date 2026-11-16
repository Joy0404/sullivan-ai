"""Server-owned video analysis provenance, independent of editable source names.

No request model accepts these records. Unknown legacy data stays unknown;
imported JSON, subtitles and model-generated labels cannot certify Gemini runs.
"""
from datetime import datetime, timezone
from uuid import uuid4


def read_status(con, session_id):
    from app.models import AnalysisStatus
    row = con.execute('SELECT payload FROM analysis_records WHERE session=?', (session_id,)).fetchone()
    if row:
        try: return AnalysisStatus.model_validate_json(row['payload'])
        except ValueError: pass
    return AnalysisStatus()


def persist_status(con, session_id, status):
    con.execute('INSERT OR REPLACE INTO analysis_records VALUES(?,?)', (session_id, status.model_dump_json()))
    return status


def record_status(session_id, state, provider=None, *, con=None):
    from app import local_access
    from app.main import agent
    from app.models import AnalysisStatus
    if con is None:
        with local_access.db() as opened: return record_status(session_id, state, provider, con=opened)
    previous = read_status(con, session_id)
    status = AnalysisStatus(state=state, provider=provider,
        run_id=previous.run_id if previous.state=='analyzing' and state in ('completed','failed') or previous.state==state and previous.provider==provider and state!='analyzing' else uuid4().hex,
        recorded_at=datetime.now(timezone.utc).isoformat())
    try:
        agent.set_analysis_status(session_id, state, provider=provider)
        status = agent.snapshot(session_id).analysis_status
    except KeyError:
        pass  # Restart recovery updates the durable record without resurrecting a session.
    return persist_status(con, session_id, status)


def material_status(session_id):
    from app import local_access
    with local_access.db() as con:
        if read_status(con, session_id).state=='unknown': record_status(session_id, 'not_run', con=con)
