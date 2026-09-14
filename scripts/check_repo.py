"""Portable repository hygiene and skill-contract checks. No remote mutation."""
from pathlib import Path
import re, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/xiaoyu-ppt'
def check():
    errors=[]
    text=(SKILL/'SKILL.md').read_text(encoding='utf-8')
    if not re.search(r'^name: xiaoyu-ppt$',text,re.M):errors.append('Invalid skill name')
    if not re.search(r'^description: .+',text,re.M):errors.append('Missing description')
    if not re.search(r'version: "\d+\.\d+\.\d+"',text):errors.append('Missing semantic version')
    for p in SKILL.rglob('*.md'):
        for ref in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if not ref.startswith(('http:','https:','#')) and not (p.parent/ref.split('#')[0]).exists():errors.append(f'Broken link in {p.relative_to(ROOT)}: {ref}')
    # Include prospective source files before their first git add, but not generated output.
    result=subprocess.run(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT,capture_output=True,check=True)
    allowed={'.md','.py','.js','.json','.yaml','.yml','.gitignore'}
    for name in result.stdout.decode().split('\0'):
        if not name:continue
        p=ROOT/name
        if p.is_symlink():errors.append('Symlink not allowed: '+name);continue
        if p.suffix not in allowed and p.name not in {'.gitignore','CODEOWNERS'}:errors.append('Unexpected file type: '+name);continue
        data=p.read_text(encoding='utf-8')
        private_path='/'+'Users/'
        if private_path in data:errors.append('Private machine path: '+name)
        for pattern in [r'gh[pousr]_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{30,}',r'-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----']:
            if re.search(pattern,data):errors.append('Possible credential: '+name)
        if p.stat().st_size>2*1024*1024:errors.append('Unexpectedly large source: '+name)
    return errors
if __name__=='__main__':
    errors=check();print('\n'.join(errors) if errors else 'Repository and skill contract: PASS');sys.exit(bool(errors))
