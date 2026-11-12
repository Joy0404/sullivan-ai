"""Local-only SQLite backup/copy migration. Source is read-only; existing targets are never overwritten."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
TABLES=('users','lectures','assignments','progress','preparations','preparation_publications','lecture_media')


def inspect(con):
    if con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('DB 무결성 검사를 통과하지 못했습니다.')
    if con.execute('PRAGMA foreign_key_check').fetchall():raise ValueError('DB 참조 관계를 확인하세요.')
    existing={row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'users' in existing:
        dangling=con.execute("SELECT COUNT(*) FROM users s LEFT JOIN users g ON g.id=s.guardian AND g.role='guardian' WHERE s.guardian IS NOT NULL AND g.id IS NULL").fetchone()[0]
        if dangling:raise ValueError('연결된 보호자가 없는 학생 관계가 있습니다. 원본을 보존하고 관계를 확인하세요.')
    return {table:con.execute('SELECT COUNT(*) FROM '+table).fetchone()[0] for table in TABLES if table in existing}


def copy_database(source,target,migrate=False):
    source=Path(source).resolve();target=Path(target).absolute()
    if not source.is_file():raise ValueError('원본 DB 파일을 확인하세요.')
    if target.exists() or target.is_symlink():raise ValueError('대상 파일이 이미 있습니다. 새 경로를 사용하세요.')
    target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,temp=tempfile.mkstemp(prefix='.sullivan-db-',dir=target.parent);os.close(fd)
    try:
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as original,closing(sqlite3.connect(temp)) as copied:
            before=inspect(original);original.backup(copied);assert inspect(copied)==before
        if migrate:
            sys.path.insert(0,str(ROOT/'apps/api'))
            from app import local_access
            old=os.environ.get('SULLIVAN_ACCOUNTS_DB');os.environ['SULLIVAN_ACCOUNTS_DB']=temp
            try:
                with local_access.db() as copied:
                    # Never transfer browser sessions or reset/authorization grants to a new server.
                    for table in ('sessions','extension_sessions','refresh_tokens','auth_families','auth_codes','auth_requests','pair_requests','pair_codes'):
                        copied.execute('DELETE FROM '+table)
                    copied.execute("UPDATE preparations SET state='interrupted',message='서버 이전으로 중단됐습니다. 자료를 다시 선택하세요.' WHERE state IN ('queued','running')")
                    after=inspect(copied)
                    for table,count in before.items():assert after.get(table)==count,(table,count,after.get(table))
            finally:
                if old is None:os.environ.pop('SULLIVAN_ACCOUNTS_DB',None)
                else:os.environ['SULLIVAN_ACCOUNTS_DB']=old
        # Hard-link publish is atomic and refuses a concurrently-created target.
        os.chmod(temp,0o600);os.link(temp,target)
        with closing(sqlite3.connect(target)) as copied:after=inspect(copied)
        return {'result':'passed','mode':'migration' if migrate else 'backup','source_unchanged':True,'rows':after,'sessions_invalidated':migrate}
    finally:
        Path(temp).unlink(missing_ok=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['backup','migrate','check'])
    parser.add_argument('source');parser.add_argument('target',nargs='?')
    args=parser.parse_args()
    if args.action=='check':
        with sqlite3.connect(Path(args.source).resolve().as_uri()+'?mode=ro',uri=True) as con:result={'result':'passed','rows':inspect(con)}
    else:
        if not args.target:parser.error('새 대상 경로가 필요합니다.')
        result=copy_database(args.source,args.target,args.action=='migrate')
    print(json.dumps(result,ensure_ascii=False,indent=2))
