"""Publish hosting files only, then verify or restore the original Dockerfile."""
import json
import os
import pathlib
import sys
import time
import urllib.request
from huggingface_hub import HfApi, CommitOperationAdd

root = pathlib.Path(sys.argv[1])
repo = 'vikrant892/nasa-space-challenge'
sources = json.loads((root / '_hosting/sources.json').read_text())
original = sources['nasa-space-challenge']['revision']
api = HfApi(token=os.environ['HF_TOKEN'])
assert api.whoami()['name'].lower() == 'vikrant892', 'Hosting identity does not match the intended owner'
assert api.repo_info(repo, repo_type='space').sha == original, 'Space changed since preparation; not overwriting it'
with urllib.request.urlopen(f'https://huggingface.co/spaces/{repo}/resolve/{original}/Dockerfile', timeout=30) as response:
    original_dockerfile = response.read()
operations = [CommitOperationAdd(path_in_repo=p.relative_to(root).as_posix(), path_or_fileobj=p)
              for p in sorted(root.rglob('*')) if p.is_file()]
operations.append(CommitOperationAdd(path_in_repo='_hosting/backups/Dockerfile.before', path_or_fileobj=original_dockerfile))
commit = api.create_commit(repo, repo_type='space', operations=operations,
                          parent_commit=original, commit_message='Host four demos within the existing free server slot')
print('Hosting-only commit:', commit.oid, flush=True)
base = 'https://vikrant892-nasa-space-challenge.hf.space'
try:
    for attempt in range(180):
        runtime = api.get_space_runtime(repo)
        info = api.repo_info(repo, repo_type='space')
        assert info.sha == commit.oid, 'Space changed during deployment; refusing an automatic rollback'
        raw = runtime.raw
        stage = getattr(runtime.stage, 'value', runtime.stage)
        if attempt % 6 == 0: print('Runtime:', stage, flush=True)
        if stage == 'RUNNING' and raw.get('sha') == commit.oid:
            import subprocess
            subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name('verify.py')), base, '--readonly'], check=True)
            print('All five demos verified at', base, flush=True)
            break
        if stage in ('BUILD_ERROR', 'RUNTIME_ERROR', 'CONFIG_ERROR', 'PAUSED'):
            raise RuntimeError('Shared server did not start: ' + stage)
        time.sleep(5)
    else: raise TimeoutError('Deployment did not become ready within 15 minutes')
except Exception:
    if api.repo_info(repo, repo_type='space').sha == commit.oid:
        restored = api.create_commit(repo, repo_type='space', parent_commit=commit.oid,
                                    operations=[CommitOperationAdd(path_in_repo='Dockerfile', path_or_fileobj=original_dockerfile)],
                                    commit_message='Restore the original NASA hosting recipe after failed verification')
        print('Original Dockerfile restored:', restored.oid, flush=True)
    raise
