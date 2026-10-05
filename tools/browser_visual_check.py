"""Exercise every authored visual trace and motion lifecycle in a disposable app."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
from uuid import uuid4
from playwright.sync_api import expect, sync_playwright

ROOT=Path(__file__).resolve().parents[1]


def run():
    output=ROOT/'data/browser-checks'/uuid4().hex;output.mkdir(parents=True)
    shutil.copytree(ROOT/'content',output/'content')
    qa=ROOT/'data/qa';qa.mkdir(parents=True,exist_ok=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    with (output/'server.log').open('w',encoding='utf-8') as log:
        server=subprocess.Popen([sys.executable,'-m','uvicorn','tests.visual_browser_fixture:create_app','--factory','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env={**os.environ,'TINY_CHAT_DATABASE':str(output/'visual.db')},stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(80):
                try:
                    with urlopen(base+'/health',timeout=1):break
                except OSError:time.sleep(.1)
            else:raise RuntimeError('Visual fixture failed to start.')
            with sync_playwright() as pw:
                browser=pw.chromium.launch()
                context=browser.new_context(viewport={'width':1440,'height':1100},reduced_motion='reduce')
                page=context.new_page();errors=[];external=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else (external.append(route.request.url),route.abort()))
                total=0
                for number in range(1,19):
                    identity=f'L{number:02}'
                    lesson=json.loads((ROOT/'content/lessons'/f'{identity}.json').read_text(encoding='utf-8'))
                    frames=lesson['visual']['frames']
                    page.goto(base+f'/lessons/{identity}')
                    expect(page.locator('[data-story-controls]')).to_be_visible()
                    expect(page.locator('#story-play')).to_be_disabled()
                    assert page.locator('#example-code').text_content()==lesson['python_example']['code']
                    for index,frame in enumerate(frames):
                        if index:page.locator('#story-next').click()
                        expect(page.locator('#story-scene-title')).to_have_text(frame['title'])
                        expect(page.locator('#story-diagram .visual-tile')).to_have_count(len(frame['items']))
                        assert page.locator('#story-console').text_content()==(frame['console'] or 'Nothing printed yet.')
                        focused=page.locator('.story-code-line.is-focused').evaluate_all('(els)=>els.map(e=>Number(e.dataset.line))')
                        assert focused==sorted(frame['lines']),(identity,index,focused)
                        assert page.locator('.story-code-line.is-focused').first.evaluate('(el)=>{const a=el.getBoundingClientRect(),b=el.closest("pre").getBoundingClientRect();return a.top>=b.top-1 && a.top<b.bottom}'),(identity,index,'focused source offscreen')
                        total+=1
                    expect(page.locator('#story-next')).to_be_disabled()
                    assert page.locator('#story-console').text_content()==lesson['python_example']['expected_output']
                    wrong=next(i for i,c in enumerate(lesson['visual']['challenge']['choices']) if not c['correct'])
                    right=1-wrong
                    page.locator('.story-choice').nth(wrong).click()
                    expect(page.locator('#story-feedback')).to_contain_text('Try another angle.')
                    page.locator('.story-choice').nth(right).click()
                    expect(page.locator('#story-feedback')).to_contain_text('You spotted it.')
                    page.locator('#story-reset').click()
                    expect(page.locator('[data-visual-story]')).to_have_attribute('data-scene','0')
                    page.locator('#story-next').click();page.locator('#story-back').click()
                    expect(page.locator('#story-back')).to_be_disabled()
                    for width in (360,390,768,1024,1440):
                        page.set_viewport_size({'width':width,'height':1100})
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(identity,width)
                        for index in range(len(frames)):
                            page.locator('#story-rail button').nth(index).click()
                            assert page.locator('.story-code-line.is-focused').first.evaluate('(el)=>{const a=el.getBoundingClientRect(),b=el.closest("pre").getBoundingClientRect();return a.top>=b.top-1 && a.top<b.bottom}'),(identity,width,index,'focused source offscreen')
                    assert page.evaluate('document.getAnimations().length')==0
                for identity in ('L01','L05','L14','L15','L18'):
                    page.goto(base+f'/lessons/{identity}')
                    page.locator('#story-rail button').last.click()
                    page.locator('[data-visual-story]').screenshot(path=str(qa/f'visual-{identity}-1440.png'))
                    page.set_viewport_size({'width':390,'height':1100})
                    page.wait_for_function('()=>{const el=document.querySelector(".story-code-line.is-focused"),a=el.getBoundingClientRect(),b=el.closest("pre").getBoundingClientRect();return a.top>=b.top-1 && a.top<b.bottom}')
                    page.locator('[data-visual-story]').screenshot(path=str(qa/f'visual-{identity}-390.png'))
                    page.set_viewport_size({'width':1440,'height':1100})
                page.evaluate("document.body.style.zoom='2'")
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'200% zoom'
                page.evaluate("document.body.style.zoom='1'")
                # Playback is explicit, pausable, bounded, and stopped by hidden panels.
                page.emulate_media(reduced_motion='no-preference')
                page.goto(base+'/lessons/L05')
                expect(page.locator('#story-play')).to_be_enabled()
                page.locator('#story-pace').select_option('2500')
                page.locator('#story-play').click()
                expect(page.locator('[data-visual-story]')).to_have_attribute('data-scene','1',timeout=5000)
                page.locator('#story-play').click()
                expect(page.locator('#story-play')).to_have_text('Play story')
                current=page.locator('[data-visual-story]').get_attribute('data-scene')
                page.wait_for_timeout(2800)
                assert page.locator('[data-visual-story]').get_attribute('data-scene')==current
                page.locator('#story-play').click();page.locator('#tab-play').click()
                expect(page.locator('#story-play')).to_have_text('Play story')
                page.locator('#tab-learn').click()
                page.locator('#story-play').click()
                page.get_by_role('button',name='Page motion',exact=True).click()
                expect(page.locator('#story-play')).to_be_disabled()
                expect(page.locator('#story-play')).to_have_text('Play story')
                page.wait_for_timeout(100)
                assert page.evaluate('document.getAnimations().length')==0
                # Numeric bars interpolate only when motion is enabled.
                page.get_by_role('button',name='Page motion',exact=True).click()
                page.locator('#story-reset').click();page.locator('#story-next').click();page.locator('#story-next').click()
                assert page.evaluate('document.getAnimations().length')>0
                # Playback reaches its last scene once and stops rather than looping.
                page.locator('#story-play').click()
                expect(page.locator('[data-visual-story]')).to_have_attribute('data-scene','3',timeout=5000)
                expect(page.locator('#story-play')).to_have_text('Play story')
                page.emulate_media(reduced_motion='reduce')
                page.locator('#story-back').click()
                assert page.evaluate('document.getAnimations().length')==0
                # A hostile-looking authored value renders as text, not HTML.
                path=output/'content/lessons/L01.json';changed=json.loads(path.read_text(encoding='utf-8'))
                changed['visual']['frames'][1]['items'][0]['value']='<img src=x onerror=alert(1)>'
                path.write_text(json.dumps(changed),encoding='utf-8')
                assert context.request.post(base+'/api/content/reload',data={}).status==200
                page.goto(base+'/lessons/L01');page.locator('#story-next').click()
                expect(page.locator('#story-diagram')).to_contain_text('<img src=x')
                assert page.locator('#story-diagram img').count()==0
                assert not errors,errors
                assert not external,external
                progress=context.request.get(base+'/api/progress').json()
                assert progress['xp']==0 and progress['journal_count']==0
                assert context.request.get(base+'/api/provider/status').json()['usage']['attempts']==0
                report=dict(status='passed',lessons=18,scenes=total,widths=[360,390,768,1024,1440],checks=['matching code and outputs','all scene navigation','hunch feedback','copy source unchanged','play and pause','tab hides stop playback','manual and system reduced motion','bar interpolation','200% CSS zoom','safe text','zero XP or AI requests'],errors=errors,external_requests=external)
                (qa/'visual-browser-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
                print(json.dumps(report));browser.close()
        finally:
            server.terminate();server.wait(timeout=10)


if __name__=='__main__':run()
