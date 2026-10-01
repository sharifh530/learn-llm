"""M3 browser acceptance with an isolated database and an explicit fake provider."""
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
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    environment={**os.environ,'TINY_CHAT_DATABASE':str(output/'m3.db')}
    with (output/'server.log').open('w') as log:
        server=subprocess.Popen([sys.executable,'-m','uvicorn','tests.browser_fixture:create_app','--factory','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT)
        try:
            for _ in range(80):
                try:
                    with urlopen(base+'/health',timeout=1):
                        break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('M3 test server did not start')
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch()
                context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
                page=context.new_page();errors=[];external=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                def guard(route):
                    if route.request.url.startswith(base):
                        route.continue_()
                    else:
                        external.append(route.request.url);route.abort()
                context.route('**/*',guard)
                page.goto(base+'/chat')
                expect(page.locator('#chat-send')).to_be_enabled()
                page.locator('#chat-mode').select_option('google_cloud')
                expect(page.locator('#chat-send')).to_be_enabled()
                page.locator('#chat-title').fill('Mango memory experiment')
                page.locator('#chat-persona').select_option('coach')
                page.locator('#save-chat-settings').click()
                expect(page.locator('#chat-status')).to_contain_text('persona saved')
                def send(text):
                    page.locator('#chat-input').fill(text);page.locator('#chat-send').click()
                def complete():
                    expect(page.locator('#chat-status')).to_contain_text('Google reply received')
                def saved():
                    identity=page.locator('#saved-chats').input_value()
                    return context.request.get(base+f'/api/chats/{identity}').json()
                def attempts():
                    return context.request.get(base+'/api/provider/status').json()['usage']['attempts']
                send('My favorite fruit is mango.');complete()
                assert saved()['title']=='Mango memory experiment'
                send('What was my fruit earlier?');complete()
                page.locator('.variant-actions').last.get_by_role('button',name='Inspect sent context').click()
                expect(page.locator('#context-messages')).to_contain_text('My favorite fruit is mango.')
                expect(page.locator('#context-messages')).to_contain_text('Python examples')
                assert [item['role'] for item in saved()['turns'][-1]['variants'][-1]['context']['messages']]==['user','assistant','user']
                original=saved()['turns'][-1]['selected_id']
                page.get_by_role('button',name='Try another reply · new Google attempt').click();complete()
                assert saved()['turns'][-1]['selected_id']==original
                page.get_by_role('button',name='Use this reply',exact=True).click()
                expect(page.locator('#chat-status')).to_contain_text('selection saved')
                assert saved()['turns'][-1]['selected_id']!=original
                page.reload();expect(page.locator('#chat-send')).to_be_enabled()
                expect(page.locator('#chat-messages')).to_contain_text('mango')
                expect(page.locator('#chat-persona')).to_have_value('coach')
                send('slow stop experiment')
                expect(page.locator('.chat-message.user').last).to_contain_text('slow stop experiment')
                expect(page.locator('.chat-message').last.locator('p')).to_contain_text('first chunk')
                page.locator('#chat-stop').click()
                expect(page.locator('#chat-status')).to_contain_text('Stopped')
                stopped=saved()['turns'][-1]['variants'][-1]
                assert stopped['status']=='stopped' and stopped['text'] and saved()['turns'][-1]['selected_id'] is None
                count=attempts();page.reload();expect(page.locator('#chat-send')).to_be_enabled()
                assert attempts()==count
                page.get_by_role('button',name='Use partial reply').click()
                expect(page.locator('#chat-status')).to_contain_text('selection saved')
                send('Is that partial answer enough?');complete()
                assert saved()['turns'][-1]['variants'][-1]['context']['messages'][-2]['text']==stopped['text']
                send('slow refresh experiment')
                expect(page.locator('.chat-message.user').last).to_contain_text('slow refresh experiment')
                expect(page.locator('.chat-message').last.locator('p')).to_contain_text('first chunk')
                count=attempts();page.reload();complete()
                assert attempts()==count
                send('simulate error')
                expect(page.locator('#chat-status')).to_contain_text('simulated failure')
                expect(page.locator('#chat-input')).to_have_value('simulate error')
                assert saved()['turns'][-1]['variants'][-1]['status']=='failed'
                # Explicit retry is a new attempt, preserving the earlier failed variant.
                page.get_by_role('button',name='Try another reply · new Google attempt').click()
                expect(page.locator('#chat-status')).to_contain_text('simulated failure')
                expect(page.locator('.variant-state')).to_have_count(8)
                assert attempts()==8
                identity=saved()['id']
                page.locator('#archive-chat').click()
                expect(page.locator('#chat-status')).to_contain_text('Chat moved')
                page.locator('#show-archived').check()
                expect(page.locator('#chat-messages')).to_contain_text('mango')
                page.locator('#archive-chat').click()
                expect(page.locator('#chat-status')).to_contain_text('Chat moved')
                assert not context.request.get(base+f'/api/chats/{identity}').json()['archived']
                # Safely rendering an unbroken draft in the inspector, at narrow widths.
                page.locator('#chat-input').fill('<script>not executable</script>'+('🙂'*950))
                page.locator('#context-inspector>summary').click() if not page.locator('#context-inspector').get_attribute('open') else None
                page.locator('#preview-context').click()
                expect(page.locator('#context-caption')).to_contain_text('Preview for the current draft')
                assert page.evaluate('window.injected === undefined')
                for width in (360,390,640,1440):
                    page.set_viewport_size({'width':width,'height':1000 if width==1440 else 850})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),f'overflow at {width}'
                    page.screenshot(path=str(output/f'chat-{width}.png'),full_page=True)
                page.set_viewport_size({'width':1440,'height':1000})
                page.locator('#chat-mode').select_option('demo')
                expect(page.locator('#chat-send')).to_be_enabled()
                send('My favorite fruit is mango.')
                expect(page.locator('#chat-status')).to_contain_text('Demo reply received')
                send('What was my favorite fruit earlier?')
                expect(page.locator('#chat-status')).to_contain_text('Demo reply received')
                page.locator('#context-inspector>summary').click() if page.locator('#context-inspector').get_attribute('open') is not None else None
                page.evaluate('() => {document.activeElement.blur(); window.scrollTo(0,0);}')
                page.screenshot(path=str(output/'chat-preview.png'))
                assert context.request.get(base+'/api/progress').json()['xp']==0
                assert not errors and not external,(errors,external)
                report={'status':'passed','provider':'FAKE; no live Google','checks':['saved persona and messages','follow-up context roles','explicit alternate selection','stop and partial selection','refresh reconnect without new attempt','explicit retry and failure draft','archive and restore','safe long Unicode context','responsive widths 360/390/640/1440','no AI XP'],'attempts':attempts(),'javascript_errors':errors,'external_requests':external}
                (output/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));print(f'Screenshots: {output}')
                browser.close()
        finally:
            server.terminate();server.wait(timeout=10)


if __name__=='__main__':
    run()
