"""Prepare an additive Hugging Face deployment, leaving app sources untouched."""
import pathlib
import shutil
import sys

source = pathlib.Path(__file__).parent
target = pathlib.Path(sys.argv[1])
target.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source / 'Dockerfile', target / 'Dockerfile')
hosting = target / '_hosting'
hosting.mkdir(exist_ok=True)
for filename in ('sources.json', 'download_sources.py', 'wsgi_adapter.py',
                 'asgi_adapter.py', 'prefix.js', 'nginx.conf', 'supervisord.conf'):
    shutil.copyfile(source / filename, hosting / filename)
print('Prepared hosting-only files; original application files are not included in upload operations.')
