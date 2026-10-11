"""Copy complete, pinned public source snapshots without editing any app files."""
import concurrent.futures
import hashlib
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

root = pathlib.Path(sys.argv[1])
sources = json.loads(pathlib.Path(__file__).with_name('sources.json').read_text())


def download(item):
    name, spec, filename = item
    relative = pathlib.PurePosixPath(filename)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Unsafe source path')
    url = ('https://huggingface.co/spaces/' + spec['repo'] + '/resolve/'
           + spec['revision'] + '/' + urllib.parse.quote(filename, safe='/'))
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                data = response.read()
            break
        except Exception:
            if attempt == 2:
                raise RuntimeError(f'Could not copy pinned source: {name}/{filename}') from None
            time.sleep(attempt + 1)
    target = root / name / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return name, filename, hashlib.sha256(data).hexdigest()


items = [(name, spec, filename) for name, spec in sources.items() for filename in spec['files']]
checksums = {name: {} for name in sources}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    for name, filename, checksum in pool.map(download, items):
        checksums[name][filename] = checksum
root.mkdir(parents=True, exist_ok=True)
(root / 'source-checksums.json').write_text(json.dumps(checksums, indent=2))
print(f'Copied {len(items)} source files from {len(sources)} pinned snapshots.')
