"""Verify mounted browser requests, downloads and Streamlit WebSockets."""
import sys
from playwright.sync_api import sync_playwright

base = sys.argv[1].rstrip('/')
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page()
    for path, text in (('/', 'Cosmic Keys'), ('/demos/fraud/', 'Credit Card Fraud')):
        page.goto(base + path, wait_until='domcontentloaded')
        page.get_by_text(text, exact=False).first.wait_for(timeout=120000)
        assert page.locator('[data-testid="stException"]').count() == 0
        print('Streamlit browser/WebSocket app rendered:', path, flush=True)
    for path, endpoint, payload, expected in (
        ('/demos/password/', '/analyze', {'password': 'Browser-test-Password!42', 'check_breach': False}, 'score'),
        ('/demos/phishing/', '/api/analyze-text', {'content': 'Urgent: verify your account now.'}, 'success'),
        ('/demos/logs/', '/api/stats', None, None),
    ):
        page.goto(base + path, wait_until='domcontentloaded')
        result = page.evaluate('''async ([path, payload]) => {
          const response = await fetch(path, payload === null ? {} : {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
          });
          return {url: response.url, status: response.status, data: await response.json()};
        }''', [endpoint, payload])
        assert result['status'] == 200, result
        assert result['url'].startswith(base + path), result
        if expected: assert expected in result['data'], result
        if path == '/demos/phishing/':
            assert page.locator('a[download]').first.get_attribute('href').startswith('/demos/phishing/')
        print('Browser request stayed within its demo and returned data:', path, flush=True)
    browser.close()
