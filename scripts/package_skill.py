"""Build a deterministic, allowlisted .skill ZIP; no private project assets."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'skills/xiaoyu-ppt'
def build(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    output=destination/'xiaoyu-ppt.skill'
    if output.exists():raise FileExistsError(output)
    files=sorted(p for p in SRC.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.md','.py','.yaml'})
    manifest={}
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:
            if p.is_symlink():raise ValueError('Symlink in source')
            name='xiaoyu-ppt/'+p.relative_to(SRC).as_posix();raw=p.read_bytes();entry=zipfile.ZipInfo(name,(2020,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o100644<<16
            z.writestr(entry,raw);manifest[name]=hashlib.sha256(raw).hexdigest()
    version=re.search(r'version: "([\d.]+)"',(SRC/'SKILL.md').read_text()).group(1)
    (destination/'manifest.json').write_text(json.dumps({'version':version,'files':manifest,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()},indent=2)+'\n')
    return output
if __name__=='__main__':print(build(sys.argv[1] if len(sys.argv)>1 else ROOT/'dist'))
