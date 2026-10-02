"""Hosted-mode UI acceptance against isolated fake HTTPS storage/provider."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
from uuid import uuid4

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def run():
    output = ROOT/'data/browser-checks'/uuid4().hex
    output.mkdir(parents=True)
    qa = ROOT/'data/qa'
    qa.mkdir(parents=True,exist_ok=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0))
        port = listener.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    with (output/'server.log').open('w') as log:
        server = subprocess.Popen([sys.executable,'-m','uvicorn','tests.cloud_browser_fixture:create_cloud_app',
            '--factory','--host','127.0.0.1','--port',str(port)],cwd=ROOT,
            env={**os.environ,'TINY_CHAT_DATABASE':str(output/'cloud.db')},stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(80):
                try:
                    with urlopen(base+'/health',timeout=1):
                        break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Cloud fixture did not start.')
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                context = browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='reduce')
                page = context.new_page()
                errors, external = [], []
                page.on('pageerror',lambda error:errors.append(str(error)))
                def guard(route):
                    if route.request.url.startswith(base):
                        route.continue_()
                    else:
                        external.append(route.request.url)
                        route.abort()
                context.route('**/*',guard)
                page.goto(base+'/settings')
                expect(page.locator('#provider-auth option')).to_have_count(1)
                page.locator('#provider-key').fill('fake-cloud-browser-key')
                page.locator('#provider-model').fill('fake-model')
                page.locator('#save-provider').click()
                expect(page.locator('#key-state')).to_have_text('Key saved · hidden')
                expect(page.locator('#provider-key')).to_have_value('')
                page.reload()
                expect(page.locator('#key-state')).to_have_text('Key saved · hidden')
                assert 'fake-cloud-browser-key' not in context.request.get(base+'/api/provider/status').text()
                assert page.evaluate("!JSON.stringify({...localStorage,...sessionStorage}).includes('fake-cloud-browser-key')")
                page.locator('#test-provider').click()
                expect(page.locator('#provider-test-status')).to_contain_text('TEST FAKE')
                page.goto(base+'/chat')
                expect(page.locator('#chat-send')).to_be_enabled()
                page.locator('#chat-input').fill('My favorite fruit is mango')
                page.locator('#chat-send').click()
                expect(page.locator('#chat-status')).to_contain_text('Demo reply received')
                page.locator('#chat-input').fill('What was my favorite fruit?')
                page.locator('#chat-send').click()
                expect(page.locator('#chat-status')).to_contain_text('Demo reply received')
                expect(page.locator('#chat-messages')).to_contain_text('mango')
                page.reload()
                expect(page.locator('#chat-messages')).to_contain_text('mango')
                page.locator('#chat-mode').select_option('google_cloud')
                expect(page.locator('#chat-send')).to_be_enabled()
                page.locator('#chat-input').fill('slow cloud fake')
                page.locator('#chat-send').click()
                expect(page.locator('#chat-messages')).to_contain_text('TEST FAKE: first chunk')
                page.locator('#chat-stop').click()
                expect(page.locator('#chat-status')).to_contain_text('Stopped')
                page.goto(base+'/settings')
                page.locator('#remove-provider-key').click()
                expect(page.locator('#key-state')).to_have_text('No key saved')
                for width in (390,768,1440):
                    page.set_viewport_size({'width':width,'height':1100})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=str(qa/'cloud-settings-test.png'),full_page=True)
                assert not errors and not external,(errors,external)
                report={'mode':'isolated cloud harness; fake provider; no external network',
                        'checks':['encrypted Settings persistence','instance-safe demo stream','follow-up memory','reload','fake Google test','cross-request Stop','secret-free responses/storage','responsive settings'],
                        'errors':errors,'external_requests':external}
                (qa/'cloud-browser-report.json').write_text(json.dumps(report,indent=2))
                browser.close()
                print(json.dumps(report))
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__=='__main__':
    run()
