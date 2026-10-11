"""Exercise the shared server locally, or perform read-only production checks."""
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

base = sys.argv[1].rstrip('/')
readonly = '--readonly' in sys.argv


def request(path, payload=None, content_type='application/json'):
    data = None if payload is None else (json.dumps(payload).encode() if isinstance(payload, dict) else payload)
    req = urllib.request.Request(base + path, data=data, headers={'Content-Type': content_type})
    with urllib.request.urlopen(req, timeout=45) as response:
        assert response.status == 200
        return response.read()


pages = ['/', '/demos/fraud/', '/demos/logs/', '/demos/password/', '/demos/phishing/']
for path in pages:
    for attempt in range(45):
        try:
            html = request(path)
            assert b'<html' in html.lower(), path
            if path not in ('/', '/demos/fraud/'):
                assert b'data-prefix="' + path.rstrip('/').encode() + b'"' in html, path
            print('Page available:', path, flush=True)
            break
        except (urllib.error.URLError, TimeoutError):
            if attempt == 44:
                raise
            time.sleep(2)

assert request('/_stcore/health').strip() == b'ok'
assert request('/demos/fraud/_stcore/health').strip() == b'ok'
assert json.loads(request('/demos/password/health'))
assert json.loads(request('/demos/phishing/api/health'))['services']['database'] == 'connected'
assert json.loads(request('/demos/logs/api/stats')) is not None
schema = json.loads(request('/demos/password/openapi.json'))
assert schema['servers'][0]['url'] == '/demos/password', schema.get('servers')
print('All five backends and password API routing passed.', flush=True)

if not readonly:
    password = json.loads(request('/demos/password/analyze', {'password': 'Demo-only-Password!42', 'check_breach': False}))
    assert 'entropy_bits' in password and 'score' in password
    generated = json.loads(request('/demos/password/generate', {'length': 20}))
    assert len(generated['password']) == 20
    analysis = json.loads(request('/demos/phishing/api/analyze-text', {'content': 'Urgent: verify your account and update payment now.'}))
    assert analysis['success'] and analysis['data']['threat_score'] > 0
    boundary = 'free-hosting-test-boundary'
    text = '\n'.join(f'Jan 10 12:00:0{i} server sshd[123]: Failed password for invalid user test from 192.0.2.1 port 12345 ssh2' for i in range(6))
    upload = (f'--{boundary}\r\nContent-Disposition: form-data; name="logfile"; filename="hosting-test.log"\r\nContent-Type: text/plain\r\n\r\n{text}\r\n--{boundary}--\r\n').encode()
    parsed = json.loads(request('/demos/logs/api/upload', upload, 'multipart/form-data; boundary=' + boundary))
    assert parsed['status'] == 'ok' and parsed['events_parsed'] == 6, parsed
    assert json.loads(request('/demos/logs/api/stats'))
    print('Password analysis/generation, phishing analysis and log upload/data flow passed.', flush=True)
