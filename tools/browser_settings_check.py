"""Settings acceptance: isolated DB, encrypted fake key, explicit FAKE provider."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
from uuid import uuid4
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
KEY = 'test-only-settings-key-not-a-real-credential'


def run():
    output = ROOT / 'data/browser-checks' / uuid4().hex
    output.mkdir(parents=True)
    qa = ROOT / 'data/qa'
    qa.mkdir(parents=True, exist_ok=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0)); port = listener.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    env = {**os.environ, 'TINY_CHAT_DATABASE': str(output / 'settings.db')}
    with (output / 'server.log').open('w') as log:
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'tests.browser_fixture:create_settings_app', '--factory', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(80):
                try:
                    with urlopen(base + '/health', timeout=1): break
                except OSError: time.sleep(.1)
            else: raise RuntimeError('Settings test server did not start')
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                context = browser.new_context(viewport={'width': 1440, 'height': 1100}, reduced_motion='reduce')
                page = context.new_page(); errors = []; external = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                def guard(route):
                    if route.request.url.startswith(base): route.continue_()
                    else: external.append(route.request.url); route.abort()
                context.route('**/*', guard)
                def state(): return context.request.get(base + '/api/provider/status').json()
                page.goto(base + '/settings')
                expect(page.locator('#provider-key')).to_have_attribute('type', 'password')
                expect(page.locator('#remove-provider-key')).to_be_disabled()
                page.locator('#provider-key').fill(KEY)
                page.locator('#provider-model').fill('test-only-model')
                # A local failure preserves input for an intentional retry, never draft storage.
                context.route('**/api/provider/settings', lambda route: route.fulfill(status=503, content_type='application/json', body='{"detail":"Local save unavailable; retry."}'))
                page.locator('#save-provider').click()
                expect(page.locator('#provider-save-status')).to_contain_text('retry')
                expect(page.locator('#provider-key')).to_have_value(KEY)
                context.unroute('**/api/provider/settings')
                page.locator('#save-provider').click()
                expect(page.locator('#provider-save-status')).to_contain_text('No restart needed')
                expect(page.locator('#provider-key')).to_have_value('')
                expect(page.locator('#key-state')).to_have_text('Key saved · hidden')
                assert state()['configured'] and not state()['connected']
                assert state()['usage']['attempts'] == 0
                assert KEY not in json.dumps(state())
                assert KEY not in (output / 'ai-settings.json').read_text()
                assert KEY not in page.evaluate('JSON.stringify({...localStorage}) + JSON.stringify({...sessionStorage})')
                page.reload()
                expect(page.locator('#provider-key')).to_have_value('')
                expect(page.locator('#key-state')).to_contain_text('Key saved')
                # Blank keeps key; model-only update immediately resets verified status.
                page.locator('#save-provider').click()
                expect(page.locator('#provider-save-status')).to_contain_text('No restart needed')
                assert state()['key_saved']
                page.locator('#test-provider').click()
                expect(page.locator('#provider-test-status')).to_contain_text('TEST FAKE')
                assert state()['connected'] and state()['usage']['attempts'] == 1
                page.goto(base + '/chat')
                page.locator('#chat-mode').select_option('google_cloud')
                page.locator('#chat-input').fill('Verify newly saved settings')
                page.locator('#chat-send').click()
                expect(page.locator('#chat-status')).to_contain_text('Google reply received')
                page.goto(base + '/settings')
                page.locator('#provider-auth').select_option('adc')
                expect(page.locator('#adc-fields')).to_be_visible()
                expect(page.locator('#express-fields')).to_be_hidden()
                page.locator('#provider-auth').select_option('express_key')
                page.locator('#provider-enabled').uncheck()
                page.locator('#save-provider').click()
                expect(page.locator('#provider-state')).to_contain_text('AI is disabled')
                assert state()['key_saved']
                page.locator('#provider-enabled').check()
                page.locator('#save-provider').click()
                expect(page.locator('#provider-state')).to_contain_text('Configured')
                expect(page.locator('#provider-key')).to_have_value('')
                assert not state()['connected']
                for width in (360,390,768,1280,1440):
                    page.set_viewport_size({'width': width, 'height': 1000})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), width
                    if width == 390: page.screenshot(path=str(qa / 'settings-mobile.png'), full_page=True)
                page.set_viewport_size({'width': 1440, 'height': 1400})
                page.locator('.page-heading h1').click()
                page.evaluate('scrollTo(0,0)')
                page.screenshot(path=str(qa / 'settings-connection.png'))
                page.locator('#provider-auth').focus(); page.keyboard.press('Tab')
                expect(page.locator('#provider-key')).to_be_focused()
                page.locator('#remove-provider-key').click()
                expect(page.locator('#provider-save-status')).to_contain_text('Key removed')
                expect(page.locator('#remove-provider-key')).to_be_disabled()
                assert not state()['key_saved'] and not state()['configured']
                assert state()['usage']['attempts'] == 2
                page.reload()
                expect(page.locator('#key-state')).to_have_text('No key saved')
                assert not json.loads((output / 'ai-settings.json').read_text())['protected_key']
                assert context.request.get(base + '/api/progress').json()['xp'] == 0
                assert not errors, errors
                assert not external, external
                report = {'status':'passed', 'profile':'isolated test data; FAKE provider, no Google calls', 'checks':['password input', 'failed save recovery', 'encrypted disk persistence', 'no key in responses/drafts', 'blank key retention', 'refresh', 'hot connection test and chat', 'enable/disable', 'ADC field switching', 'remove key', 'keyboard and mobile layouts'], 'widths':[360,390,768,1280,1440], 'javascript_errors':errors, 'external_requests':external}
                (qa / 'settings-browser-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
                print(json.dumps(report, indent=2)); browser.close()
        finally:
            server.terminate(); server.wait(timeout=10)


if __name__ == '__main__': run()
