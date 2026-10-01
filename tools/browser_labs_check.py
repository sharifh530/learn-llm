"""Exercise M4 numeric toys in Chromium with Google disabled and a disposable DB."""
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
    output = ROOT / 'data/browser-checks' / uuid4().hex
    output.mkdir(parents=True)
    qa = ROOT / 'data/qa'
    qa.mkdir(parents=True, exist_ok=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    env = {**os.environ, 'TINY_CHAT_DATABASE': str(output / 'm4.db'), 'AI_ENABLED': 'false'}
    with (output / 'server.log').open('w') as log:
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:create_app', '--factory', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(80):
                try:
                    with urlopen(base + '/health', timeout=1):
                        break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('M4 server did not start')
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                context = browser.new_context(viewport={'width': 1440, 'height': 1100}, reduced_motion='reduce')
                page = context.new_page()
                errors, external = [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                def guard(route):
                    if route.request.url.startswith(base):
                        route.continue_()
                    else:
                        external.append(route.request.url); route.abort()
                context.route('**/*', guard)
                page.goto(base + '/lessons/L13')
                page.get_by_role('link', name='Explore the similarity toy').click()
                expect(page.locator('#fruit-winner')).to_contain_text('Apple')
                expect(page.locator('#fruit-matches')).to_contain_text('1.0000')
                def slider(identity, value, endpoint):
                    with page.expect_response(lambda r: r.url.endswith('/api/labs/' + endpoint) and r.request.method == 'POST'):
                        page.locator('#' + identity).evaluate('(el, value) => {el.value = value; el.dispatchEvent(new Event("input", {bubbles:true}));}', str(value))
                    expect(page.locator('#' + endpoint + '-status')).to_contain_text('Local Python toy')
                slider('feature-0', 0, 'similarity')
                slider('feature-1', 0, 'similarity')
                slider('feature-2', 10, 'similarity')
                expect(page.locator('#fruit-winner')).to_contain_text('Lemon')
                slider('feature-2', 0, 'similarity')
                expect(page.locator('#fruit-winner')).to_have_text('No direction')
                expect(page.locator('#fruit-matches meter')).to_have_count(0)
                page.locator('[data-reset=similarity]').click()
                expect(page.locator('#fruit-winner')).to_contain_text('Apple')
                page.locator('#feature-0').focus()
                page.keyboard.press('ArrowRight')
                expect(page.locator('[data-value=feature-0]')).to_have_text('8')
                page.locator('#lab-tab-similarity').focus()
                page.keyboard.press('ArrowRight')
                expect(page.locator('#lab-tab-attention')).to_be_focused()
                expect(page.locator('#lab-attention')).to_be_visible()
                expect(page.locator('#attention-total')).to_have_text('Total = 1.0000')
                expect(page.locator('.attention-row.masked')).to_have_count(2)
                old_output = page.locator('#weighted-value').inner_text()
                slider('score-6', 3, 'attention')
                assert page.locator('#weighted-value').inner_text() == old_output
                page.locator('#attention-query').select_option('0')
                expect(page.locator('.attention-row.masked')).to_have_count(6)
                expect(page.locator('#weighted-value')).to_have_text('Weighted output = 0.1000')
                page.locator('#causal-mask').uncheck()
                expect(page.locator('.attention-row.masked')).to_have_count(0)
                assert all(value > 0 for value in page.locator('#attention-weights meter').evaluate_all('(els) => els.map(el => el.value)'))
                slider('attention-temperature', .25, 'attention')
                page.locator('[data-reset=attention]').click()
                expect(page.locator('.attention-row.masked')).to_have_count(2)
                page.locator('#lab-tab-attention').focus()
                page.keyboard.press('End')
                expect(page.locator('#lab-tab-training')).to_be_focused()
                expect(page.locator('#lab-training')).to_be_visible()
                form = page.locator('#training-form')
                def train(name, expected):
                    form.get_by_role('button', name=name, exact=True).click()
                    expect(page.locator('[data-value=model-weight]')).to_have_text(expected)
                    expect(form.get_by_role('button', name=name, exact=True)).to_be_enabled()
                train('Predict only', '1.0000')
                train('Train one step', '2.0000')
                expect(page.locator('#train-loss')).to_have_text('1.0000')
                expect(page.locator('#check-loss')).to_have_text('0.0000')
                train('Train one step', '2.5000')
                expect(page.locator('#check-loss')).to_have_text('1.0000')
                train('Train ten steps', '2.9995')
                assert page.locator('#training-history tr').count() == 12
                stored = json.loads(page.evaluate("sessionStorage.getItem('tiny-chat-observatory-v1')"))
                assert stored['weight'] == 2.99951171875
                page.reload()
                expect(page.locator('#lab-training')).to_be_visible()
                expect(page.locator('[data-value=model-weight]')).to_have_text('2.9995')
                train('Train one step', '2.9998')
                # Full precision must survive a range control whose step is only .01.
                stored = json.loads(page.evaluate("sessionStorage.getItem('tiny-chat-observatory-v1')"))
                assert stored['weight'] == 2.999755859375
                page.locator('[data-reset=training]').click()
                expect(page.locator('[data-value=model-weight]')).to_have_text('1.0000')
                slider('learning-rate', 1, 'training')
                train('Train one step', '5.0000')
                train('Train one step', '1.0000')
                expect(page.locator('#train-loss')).to_have_text('4.0000')
                slider('model-weight', 2, 'training')
                expect(page.locator('#training-history')).to_contain_text('No training updates yet')
                # A failed local request preserves the selected weight and explains the retry.
                context.route('**/api/labs/training', lambda route: route.fulfill(status=503, content_type='application/json', body='{"detail":"Local calculation unavailable; retry."}'))
                form.get_by_role('button', name='Train one step', exact=True).click()
                expect(page.locator('#training-status')).to_contain_text('retry')
                expect(page.locator('[data-value=model-weight]')).to_have_text('2.0000')
                context.unroute('**/api/labs/training')
                page.evaluate("sessionStorage.setItem('tiny-chat-observatory-v1', '{broken')")
                page.reload()
                expect(page.locator('[data-value=model-weight]')).to_have_text('1.0000')
                expect(page.locator('#training-status')).to_contain_text('Local Python toy')
                # Controls survive a reload; training history honestly starts a new series.
                for width in (360, 390, 640, 1024, 1440):
                    page.set_viewport_size({'width': width, 'height': 850})
                    for name in ('similarity', 'attention', 'training'):
                        page.locator('#lab-tab-' + name).click()
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (width, name)
                    if width == 390:
                        page.locator('#lab-tab-similarity').click()
                        page.evaluate('scrollTo(0,0)')
                        page.screenshot(path=str(qa / 'observatory-mobile.png'), full_page=True)
                page.set_viewport_size({'width': 640, 'height': 450})
                page.locator('#lab-tab-similarity').click()
                expect(page.locator('#feature-0')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                assert page.evaluate('document.getAnimations().length') == 0
                page.set_viewport_size({'width': 1440, 'height': 1100})
                page.evaluate('scrollTo(0,0)')
                page.screenshot(path=str(qa / 'observatory-preview.png'))
                page.locator('#lab-similarity').screenshot(path=str(qa / 'observatory-experiment.png'))
                assert context.request.get(base + '/api/progress').json()['xp'] == 0
                assert context.request.get(base + '/api/provider/status').json()['usage']['attempts'] == 0
                assert not errors, errors
                assert not external, external
                report = {'status':'passed', 'checks':['similarity ranking/scaling/zero', 'causal mask and weighted output', 'keyboard tabs/sliders', 'prediction versus training', 'held-out degradation', 'learning-rate bounce', 'full-precision restore', 'failed-request recovery', 'corrupt storage', 'responsive layouts', 'reduced motion', 'zero Google calls and XP'], 'widths':[360,390,640,1024,1440], 'javascript_errors':errors, 'external_requests':external, 'profile':'isolated test database, Google disabled'}
                (qa / 'm4-browser-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
                print(json.dumps(report, indent=2))
                browser.close()
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    run()
