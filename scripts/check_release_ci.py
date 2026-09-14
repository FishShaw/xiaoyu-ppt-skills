"""Reject stale successful CI when a newer main run is pending or failed."""
import json, os, subprocess

def validate(runs, sha):
    matches = [r for r in runs if r['head_sha'] == sha and r['head_branch'] == 'main'
               and r['event'] in ('push', 'schedule', 'workflow_dispatch')]
    if not matches:
        raise ValueError('No main CI for this exact commit')
    latest = max(matches, key=lambda r: r['id'])
    if latest['status'] != 'completed' or latest['conclusion'] != 'success':
        raise ValueError('Latest main CI must complete successfully')

def main():
    sha = os.environ['SHA']; repo = os.environ['REPO']
    raw = subprocess.check_output(['gh', 'api',
        f'repos/{repo}/actions/workflows/ci.yml/runs?head_sha={sha}&per_page=100'], text=True)
    validate(json.loads(raw)['workflow_runs'], sha)

if __name__ == '__main__':
    main()
