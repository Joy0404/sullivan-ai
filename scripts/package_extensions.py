"""Package only generated extension files. Produces local artifacts, never publishes a store item."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile
from urllib.parse import urlsplit

from build_extensions import build,ROOT,VERSION


def package(server='http://127.0.0.1:8770',output=None,release=False):
    parsed=urlsplit(server)
    if release and (parsed.scheme!='https' or parsed.hostname in ('localhost','127.0.0.1','::1')):
        raise ValueError('스토어 제출용 묶음은 실제 HTTPS 서버 출처가 필요합니다.')
    output=Path(output) if output else ROOT/f'dist/releases/{VERSION}'
    output.mkdir(parents=True,exist_ok=True)
    artifacts=[]
    with tempfile.TemporaryDirectory(prefix='sullivan-package-') as temp:
        built=build(server,Path(temp)/'extensions')
        for role in ('student','guardian'):
            path=output/f'sullivan-{role}-{VERSION}.zip'
            with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                for file in sorted((built/role).rglob('*')):
                    if file.is_file():archive.write(file,file.relative_to(built/role).as_posix())
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            artifacts.append({'role':role,'file':path.name,'sha256':digest,'bytes':path.stat().st_size})
    report={'version':VERSION,'server':server,'package_mode':'store-submission' if release else 'local-development',
        'published':False,'artifacts':artifacts,'remaining':['Register two store item IDs and configure server clients','Verify actual target sites and assistive technology','Set public privacy/support URLs and reviewer access before submitting']}
    (output/'release-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server',default='http://127.0.0.1:8770');parser.add_argument('--output');parser.add_argument('--release',action='store_true')
    args=parser.parse_args();print(json.dumps(package(args.server,args.output,args.release),ensure_ascii=False,indent=2))
