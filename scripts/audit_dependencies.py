"""Fail closed on new high/critical advisories; exact, expiring exceptions only."""
import datetime,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def evaluate(report,exceptions,today):
    failures=[];accepted=[]
    known={}
    for ex in exceptions:
        expiry=datetime.date.fromisoformat(ex['expires'])
        approved=datetime.date.fromisoformat(ex['approved'])
        if not approved<=today<=expiry or (expiry-approved).days>31:failures.append('Expired or invalid exception: '+ex['url'])
        else:known[(ex['package'],ex['url'])]=ex
    vulnerabilities=report.get('vulnerabilities')
    if not isinstance(vulnerabilities,dict):raise ValueError('Malformed npm audit report')
    def leaves(name,seen):
        if name in seen:raise ValueError('Cyclic advisory graph')
        v=vulnerabilities[name];out=[]
        for via in v['via']:
            if isinstance(via,str):out.extend(leaves(via,seen|{name}))
            else:out.append((name,via))
        return out
    lock=json.loads((ROOT/'package-lock.json').read_text())
    for name,v in vulnerabilities.items():
        if v['severity'] not in ('high','critical'):continue
        items=leaves(name,set())
        if not items:failures.append('Unexplained vulnerable package: '+name)
        for package,advisory in items:
            key=(package,advisory['url']);ex=known.get(key);node=lock['packages'].get('node_modules/'+package,{})
            if ex and node.get('dev') is True and node.get('version')==ex['version'] and ex.get('scope')=='synthetic-fixtures-only':accepted.append(key)
            else:failures.append('Unapproved advisory: '+package+' '+advisory['url'])
    return {'passed':not failures,'failures':sorted(set(failures)),'accepted':sorted(set(accepted))}
def main():
    r=subprocess.run(['npm','audit','--json'],cwd=ROOT,capture_output=True,text=True,timeout=90)
    if r.returncode not in (0,1):raise RuntimeError(r.stderr)
    report=json.loads(r.stdout)
    if 'error' in report:raise RuntimeError(str(report['error']))
    exceptions=json.loads((ROOT/'.github/security-exceptions.json').read_text())
    result=evaluate(report,exceptions,datetime.date.today())
    print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
if __name__=='__main__':main()
