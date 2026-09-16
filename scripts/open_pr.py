"""Create a PR only after the exact pushed branch commit has successful push CI."""
import argparse,json,subprocess
def run(*args):return subprocess.check_output(args,text=True).strip()
def validate_run(runs,branch,sha):
    matching=[r for r in runs if r['headBranch']==branch and r['headSha']==sha]
    if not matching or matching[0]['status']!='completed' or matching[0]['conclusion']!='success':
        raise ValueError('Latest push CI for this exact branch commit has not succeeded')
def main():
    p=argparse.ArgumentParser();p.add_argument('--title',required=True);p.add_argument('--body-file',required=True);args=p.parse_args()
    branch=run('git','branch','--show-current')
    if not branch or branch=='main':raise SystemExit('Use a feature branch')
    if run('git','status','--porcelain'):raise SystemExit('Commit or preserve local changes before opening PR')
    sha=run('git','rev-parse','HEAD')
    remote=run('git','ls-remote','--heads','origin','refs/heads/'+branch).split()
    if not remote or remote[0]!=sha:raise SystemExit('Push the exact local commit first')
    runs=json.loads(run('gh','run','list','--workflow','ci.yml','--event','push','--commit',sha,'--limit','20','--json','headBranch,headSha,status,conclusion'))
    validate_run(runs,branch,sha)
    existing=json.loads(run('gh','pr','list','--base','main','--head',branch,'--state','open','--json','url'))
    if existing:print(existing[0]['url']);return
    print(run('gh','pr','create','--base','main','--head',branch,'--title',args.title,'--body-file',args.body_file))
if __name__=='__main__':main()
