"""End-to-end UI + real app service using an explicitly FAKE provider, no Google calls."""
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


def run():
    run_dir = (ROOT / 'data/browser-checks' / uuid4().hex).resolve()
    assert run_dir.is_relative_to(ROOT.resolve())
    run_dir.mkdir(parents=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    environment = {**os.environ, 'TINY_CHAT_DATABASE': str(run_dir / 'ai-test.db')}
    with (run_dir / 'server.log').open('w') as log:
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'tests.browser_fixture:create_app', '--factory', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(80):
                try:
                    with urlopen(base + '/health', timeout=1):
                        break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Fake test server did not start')
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                context = browser.new_context(viewport={'width': 1280, 'height': 900}, reduced_motion='reduce')
                page = context.new_page()
                errors, external = [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                def guard(route):
                    if route.request.url.startswith(base):
                        route.continue_()
                    else:
                        external.append(route.request.url)
                        route.abort()
                context.route('**/*', guard)
                def goto(path):
                    assert page.goto(base + path).status == 200
                    assert 'test-only-fake-key' not in page.content()
                    assert page.evaluate("JSON.stringify(sessionStorage)").find('test-only-fake-key') == -1
                def usage():
                    return context.request.get(base + '/api/provider/status').json()['usage']
                goto('/settings')
                page.locator('#test-provider').click()
                expect(page.locator('#provider-test-status')).to_contain_text('TEST FAKE')
                expect(page.locator('#provider-state')).to_contain_text('Google replied')
                assert usage()['attempts'] == 1
                goto('/lessons/L07')
                page.locator('[data-open-tutor]').click()
                page.locator('#tutor-draft').fill('Explain my prompt recipe')
                page.locator('#tutor-mode').select_option('explain')
                page.locator('#tutor-send').click()
                expect(page.locator('#tutor-answer')).to_contain_text('TEST FAKE')
                expect(page.locator('#tutor-status')).to_contain_text('No XP awarded')
                page.locator('[data-close-tutor]').click()
                goto('/lessons/L08')
                page.locator('[data-open-tutor]').click()
                expect(page.locator('#tutor-draft')).to_have_value('')
                expect(page.locator('#tutor-answer')).to_have_text('')
                page.locator('#tutor-draft').fill('simulate error')
                page.locator('#tutor-send').click()
                expect(page.locator('#tutor-status')).to_contain_text('simulated failure')
                expect(page.locator('#tutor-draft')).to_have_value('simulate error')
                page.keyboard.press('Escape')
                goto('/chat')
                page.locator('#chat-mode').select_option('google_cloud')
                page.locator('#chat-input').fill('<script>window.injected=true</script>')
                page.locator('#chat-send').click()
                expect(page.locator('#chat-messages')).to_contain_text('TEST FAKE')
                assert page.evaluate('window.injected === undefined')
                page.locator('#chat-mode').select_option('demo')
                expect(page.locator('#chat-messages')).not_to_contain_text('TEST FAKE')
                page.locator('#chat-mode').select_option('google_cloud')
                page.locator('#chat-input').fill('simulate error')
                page.locator('#chat-send').click()
                expect(page.locator('#chat-status')).to_contain_text('simulated failure')
                expect(page.locator('#chat-input')).to_have_value('simulate error')

                # Lose the browser response after the server already completed.
                lost, ids = [], []
                def lose_response(route):
                    ids.append(route.request.post_data_json['request_id'])
                    response = route.fetch()
                    if not lost:
                        lost.append(True)
                        route.abort()
                    else:
                        route.fulfill(response=response)
                page.route('**/api/ai/messages', lose_response)
                page.locator('#chat-input').fill('Response recovery experiment')
                page.locator('#chat-send').click()
                expect(page.locator('#chat-status')).to_contain_text('could not be reached')
                attempts = usage()['attempts']
                page.reload()
                page.locator('#chat-mode').select_option('google_cloud')
                expect(page.locator('#chat-input')).to_have_value('Response recovery experiment')
                page.locator('#chat-send').click()
                expect(page.locator('#chat-status')).to_contain_text('Google reply received')
                assert len(ids) == 2 and ids[0] == ids[1]
                assert usage()['attempts'] == attempts
                page.unroute('**/api/ai/messages', lose_response)
                assert context.request.get(base + '/api/progress').json()['xp'] == 0

                goto('/lessons/L07')
                page.locator('[data-open-tutor]').click()
                page.locator('#tutor-draft').fill('Explain the recipe')
                page.locator('#tutor-send').click()
                expect(page.locator('#tutor-answer')).to_contain_text('TEST FAKE')
                for width in (390, 640, 1280):
                    page.set_viewport_size({'width': width, 'height': 850})
                    assert page.evaluate("document.querySelector('#tutor-dialog').scrollWidth <= document.querySelector('#tutor-dialog').clientWidth + 1")
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                    page.screenshot(path=str(run_dir / f'tutor-{width}.png'))
                page.keyboard.press('Escape')
                assert not errors and not external, (errors, external)
                report = {'status': 'passed', 'provider': 'FAKE, not live Google', 'checks': ['connection UX', 'lesson isolation', 'tutor errors preserve draft', 'chat modes separate', 'safe text rendering', 'secret absent from browser', 'lost-response retry uses same ID with no extra attempt', 'no AI XP', 'responsive tutor'], 'live_verified': False, 'browser_errors': errors, 'external_browser_requests': external}
                (run_dir / 'report.json').write_text(json.dumps(report, indent=2))
                print(json.dumps(report, indent=2))
                print(f'Screenshots and report: {run_dir}')
                browser.close()
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    run()
