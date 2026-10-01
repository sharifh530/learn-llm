"""Responsive and motion proof on an isolated app, without learner data or Google."""
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
    run_dir = (ROOT / 'data/design-checks' / uuid4().hex).resolve()
    assert run_dir.is_relative_to(ROOT.resolve())
    run_dir.mkdir(parents=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    base = f'http://127.0.0.1:{port}'
    environment = {**os.environ, 'TINY_CHAT_DATABASE': str(run_dir / 'design.db'), 'AI_ENABLED':'false'}
    with (run_dir / 'server.log').open('w') as log:
        server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:create_app', '--factory', '--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(80):
                try:
                    with urlopen(base+'/health',timeout=1):
                        break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Design test server did not start')
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                context = browser.new_context(viewport={'width':1440,'height':1000})
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
                def goto(path):
                    assert page.goto(base+path).status==200
                    page.evaluate('document.fonts.ready')
                    page.wait_for_function("() => document.querySelector('#motion-toggle').title.length > 0")
                goto('/')
                assert page.evaluate("document.fonts.check('600 16px \"DM Sans\"') && document.fonts.check('700 32px Bricolage')")
                assert page.evaluate("getComputedStyle(document.querySelector('.hero-pip')).animationName")=='pip-float'
                page.locator('#motion-toggle').click()
                expect(page.locator('#motion-toggle')).to_have_attribute('aria-pressed','false')
                assert page.evaluate('document.getAnimations().length')==0
                page.reload()
                expect(page.locator('#motion-toggle')).to_have_attribute('aria-pressed','false')
                page.locator('#motion-toggle').click()
                expect(page.locator('#motion-toggle')).to_have_attribute('aria-pressed','true')
                page.emulate_media(reduced_motion='reduce')
                expect(page.locator('#motion-toggle')).to_be_disabled()
                expect(page.locator('#motion-toggle')).to_have_attribute('aria-pressed','false')
                assert page.evaluate('document.getAnimations().length')==0
                page.emulate_media(reduced_motion='no-preference')
                goto('/lessons/L01')
                page.evaluate("document.addEventListener('lab:xp', () => {window.celebrationParticles=document.querySelectorAll('.xp-particle').length}, {once:true})")
                page.locator('[data-ack=reading]').click()
                page.wait_for_function('() => window.celebrationParticles !== undefined')
                assert page.evaluate('window.celebrationParticles')==10
                expect(page.locator('.header-progress')).to_contain_text('10')
                expect(page.locator('.xp-particle')).to_have_count(0)
                page.emulate_media(reduced_motion='reduce')
                goto('/lessons/L02')
                page.evaluate("document.addEventListener('lab:xp', () => {window.celebrationParticles=document.querySelectorAll('.xp-particle').length}, {once:true})")
                page.locator('[data-ack=reading]').click()
                page.wait_for_function('() => window.celebrationParticles !== undefined')
                assert page.evaluate('window.celebrationParticles')==0

                for width in (360,390,640,1024,1440):
                    page.set_viewport_size({'width':width,'height':1000 if width>=1024 else 850})
                    for name,path in [('home','/'),('lesson','/lessons/L07'),('game','/lessons/L07?step=play'),('workshop','/workshop'),('chat','/chat'),('settings','/settings')]:
                        goto(path)
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),f'{width} {path}: horizontal overflow'
                        assert page.evaluate("[...document.querySelectorAll('img')].every(image=>image.complete && image.naturalWidth>0)"),f'{path}: missing image'
                        if width in (390,1440):
                            page.screenshot(path=str(run_dir / f'{name}-{width}.png'),full_page=True)
                        if width==1440 and name=='lesson':
                            page.screenshot(path=str(run_dir / 'lesson-preview.png'))
                    goto('/lessons/L07')
                    if width<761:
                        expect(page.locator('.lesson-contents')).not_to_have_attribute('open','')
                        page.locator('.lesson-contents>summary').click()
                        expect(page.locator('.lesson-contents nav')).to_be_visible()
                        page.locator('.lesson-contents>summary').click()
                    page.locator('[data-open-tutor]').click()
                    expect(page.locator('#tutor-dialog')).to_be_visible()
                    assert page.evaluate("document.querySelector('#tutor-dialog').scrollWidth <= document.querySelector('#tutor-dialog').clientWidth + 1")
                    page.keyboard.press('Escape')
                    expect(page.locator('[data-open-tutor]')).to_be_focused()

                # Reflow equivalent of a 1280px laptop at 200% browser zoom.
                page.set_viewport_size({'width':640,'height':450})
                goto('/lessons/L07?step=play')
                expect(page.locator('[data-activity=game] .choice-list')).to_be_visible()
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                page.screenshot(path=str(run_dir / 'reflow-200-percent.png'))
                assert not errors and not external,(errors,external)
                report={'status':'passed','viewport_widths':[360,390,640,1024,1440],
                        'checks':['self-hosted fonts','all illustrations loaded','motion toggle persists','system reduced motion disables animations','XP celebration completes and respects reduced motion','mobile lesson contents','keyboard dialog focus','all pages without horizontal overflow','200% equivalent reflow'],
                        'external_requests':external,'javascript_errors':errors,'database':'isolated; learner progress untouched'}
                (run_dir/'report.json').write_text(json.dumps(report,indent=2))
                print(json.dumps(report,indent=2))
                print(f'Screenshots: {run_dir}')
                browser.close()
        finally:
            server.terminate();server.wait(timeout=10)


if __name__=='__main__':
    run()
