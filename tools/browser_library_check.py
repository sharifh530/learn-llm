"""M5 UI acceptance with isolated storage, a fake provider, and blocked egress."""
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

ROOT=Path(__file__).resolve().parents[1]


def run():
    output=ROOT/'data/browser-checks'/uuid4().hex
    output.mkdir(parents=True)
    qa=ROOT/'data/qa';qa.mkdir(parents=True,exist_ok=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    with (output/'server.log').open('w') as log:
        server=subprocess.Popen([sys.executable,'-m','uvicorn','tests.library_browser_fixture:create_library_app','--factory','--host','127.0.0.1','--port',str(port)],cwd=ROOT,
            env={**os.environ,'TINY_CHAT_DATABASE':str(output/'library.db')},stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(80):
                try:
                    with urlopen(base+'/health',timeout=1):break
                except OSError:time.sleep(.1)
            else:raise RuntimeError('M5 fixture failed to start.')
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch()
                context=browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='reduce')
                page=context.new_page();errors=[];external=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                def guard(route):
                    if route.request.url.startswith(base):route.continue_()
                    else:external.append(route.request.url);route.abort()
                context.route('**/*',guard)
                page.goto(base+'/workshop')
                page.get_by_role('link',name='Open the library').click()
                expect(page.locator('#library-question')).to_be_visible()
                page.get_by_role('button',name='A mango mystery').click()
                page.locator('#library-search').click()
                expect(page.locator('#library-status')).to_contain_text('No Google request')
                expect(page.locator('#retrieval-terms')).to_contain_text('drink, mango')
                expect(page.locator('#retrieval-results .retrieved-clue')).to_have_count(3)
                page.locator('#library-answer').click()
                expect(page.locator('#library-answer-panel')).to_contain_text('Matching clues, not an AI answer')
                expect(page.locator('#library-evidence figure')).to_have_count(3)
                expect(page.locator('#library-usage')).to_contain_text('Zero Google calls')
                assert context.request.get(base+'/api/provider/status').json()['usage']['attempts']==0
                page.get_by_role('button',name='A missing clue').click()
                page.locator('#library-answer').click()
                expect(page.locator('#library-reply')).to_contain_text('No matching clues')
                expect(page.locator('#library-evidence figure')).to_have_count(0)
                page.locator('#library-note').select_option('N01')
                page.get_by_role('button',name='Saturday plans').click()
                page.locator('#library-search').click()
                expect(page.locator('#retrieval-results')).to_contain_text('No matching clues')
                page.locator('#library-note').select_option('')
                page.locator('#library-search').click()
                expect(page.locator('#retrieval-results')).to_contain_text('14:00')
                page.locator('#library-mode').select_option('google_cloud')
                page.get_by_role('button',name='A mango mystery').click()
                page.locator('#library-answer').click()
                expect(page.locator('#evidence-heading')).to_have_text('Google-selected evidence')
                expect(page.locator('#library-evidence figure')).to_have_count(2)
                expect(page.locator('#library-usage')).to_contain_text('50 reported tokens')
                page.locator('#library-evidence a').first.click()
                expect(page.locator('#source-N01-v1-p1-1')).to_be_focused()
                assert page.locator('#note-N01').get_attribute('open') is not None
                # Lose a completed HTTP response, then recover the same paid ID.
                def lose_response(route):
                    route.fetch();route.abort()
                page.route('**/api/library/answers',lose_response)
                page.locator('#library-question').fill('mango price')
                page.locator('#library-answer').click()
                expect(page.locator('#library-status')).to_contain_text('could not be reached')
                assert context.request.get(base+'/api/provider/status').json()['usage']['attempts']==2
                page.unroute('**/api/library/answers',lose_response)
                page.reload()
                expect(page.locator('#library-question')).to_have_value('mango price')
                page.locator('#library-mode').select_option('google_cloud')
                page.locator('#library-answer').click()
                expect(page.locator('#library-usage')).to_contain_text('Recovered saved response')
                assert context.request.get(base+'/api/provider/status').json()['usage']['attempts']==2
                page.locator('#library-question').fill('mango forged')
                page.locator('#library-answer').click()
                expect(page.locator('#library-status')).to_contain_text('answer was withheld')
                expect(page.locator('#library-question')).to_have_value('mango forged')
                expect(page.locator('#library-answer-panel')).to_be_hidden()
                assert 'forged secret claim' not in page.locator('body').inner_text()
                page.locator('#chunk-size').fill('10')
                page.locator('#chunk-form button').click()
                expect(page.locator('#chunk-status')).to_contain_text('Nothing was saved')
                expect(page.locator('#chunk-results article')).to_have_count(4)
                page.locator('#chunk-text').fill('<img src=x onerror=alert(1)> harmless text')
                page.locator('#chunk-form button').click()
                expect(page.locator('#chunk-results')).to_contain_text('<img')
                assert page.locator('#chunk-results img').count()==0
                page.locator('#library-mode').select_option('demo')
                page.goto(base+'/library')
                page.get_by_role('button',name='A mango mystery').click()
                page.locator('#library-answer').click()
                expect(page.locator('#library-evidence figure')).to_have_count(3)
                for width in (360,390,768,1024,1440):
                    page.set_viewport_size({'width':width,'height':1100})
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),width
                    if width in (390,1440):
                        page.screenshot(path=str(qa/f'library-{width}.png'),full_page=True)
                page.evaluate("document.body.style.zoom='2'")
                if not page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'):
                    print(page.evaluate("Array.from(document.querySelectorAll('body *')).filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,15).map(e=>({tag:e.tagName,cls:e.className,id:e.id,right:e.getBoundingClientRect().right}))"))
                    page.screenshot(path=str(qa/'library-zoom-check.png'),full_page=True)
                    raise AssertionError('CSS zoom overflow')
                page.evaluate("document.body.style.zoom='1'")
                page.locator('#library-question').focus()
                page.keyboard.press('Tab')
                expect(page.get_by_role('button',name='A mango mystery')).to_be_focused()
                assert page.evaluate('document.getAnimations().length')==0
                assert not errors,errors
                assert not external,external
                progress=context.request.get(base+'/api/progress').json()
                assert progress['xp']==0 and progress['journal_count']==0
                report={'status':'passed','provider':'FAKE; no real Google calls',
                    'checks':['offline clues','negative mango match exposed','missing evidence','note filtering','checked fake Google selection','source focus','lost-response recovery without extra attempt','invalid quote withheld','draft preservation','chunk preview','escaped text','keyboard order','reduced motion','200% zoom'],
                    'widths':[360,390,768,1024,1440],'javascript_errors':errors,'external_requests':external,'learner_data':'isolated fixture'}
                (qa/'library-browser-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
                print(json.dumps(report))
                browser.close()
        finally:
            server.terminate();server.wait(timeout=10)


if __name__=='__main__':run()
