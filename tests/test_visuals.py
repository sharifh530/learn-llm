"""Visual authoring boundaries and preservation of established scoring."""
import json
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.content import ContentStore, ContentError
from app.main import create_app
from app.config import AISettings, ROOT
from tests.test_app import complete


def test_all_authored_traces_are_rendered_and_final_console_matches(tmp_path):
    client=TestClient(create_app(tmp_path/'visual.db',ai_settings=AISettings()))
    for number in range(1,19):
        identity=f'L{number:02}'
        lesson=client.get(f'/api/lessons/{identity}').json()
        assert len(lesson['visual']['frames'])>=3
        assert lesson['visual']['frames'][-1]['console']==lesson['python_example']['expected_output']
        page=client.get(f'/lessons/{identity}').text
        assert 'data-visual-story' in page and 'lesson-visual.js' in page
        assert 'This is a visual trace, not Python execution.' in page
        assert '<noscript>' in page
    assert client.get('/api/progress').json()['xp']==0


@pytest.mark.parametrize('change',['lines','layout','console','challenge','extra','amount','nan'])
def test_invalid_visual_reload_preserves_active_content(tmp_path,change):
    content=tmp_path/'content';shutil.copytree(ROOT/'content',content)
    store=ContentStore(content)
    original=store.lesson('L05')
    changed=json.loads(json.dumps(original));visual=changed['visual']
    if change=='lines':visual['frames'][0]['lines']=[999]
    if change=='layout':visual['frames'][0]['layout']='execute_code'
    if change=='console':visual['frames'][-1]['console']='invented result'
    if change=='challenge':visual['challenge']['choices'][0]['correct']=True
    if change=='extra':visual['script']='alert(1)'
    if change=='amount':visual['frames'][0]['items'][0].pop('amount')
    if change=='nan':visual['frames'][0]['items'][0]['amount']=float('nan')
    (content/'lessons/L05.json').write_text(json.dumps(changed),encoding='utf-8')
    with pytest.raises(ContentError):store.reload()
    assert store.lesson('L05')==original


def test_adding_visuals_preserves_existing_completion_and_once_only_xp(tmp_path):
    content=tmp_path/'content';shutil.copytree(ROOT/'content',content)
    path=content/'lessons/L01.json';original=json.loads(path.read_text(encoding='utf-8'))
    earlier={key:value for key,value in original.items() if key!='visual'};earlier['version']=original['version']-1
    path.write_text(json.dumps(earlier),encoding='utf-8')
    client=TestClient(create_app(tmp_path/'progress.db',content,ai_settings=AISettings()))
    complete(client)
    path.write_text(json.dumps(original),encoding='utf-8')
    assert client.post('/api/content/reload',json={}).status_code==200
    progress=client.get('/api/progress').json()
    assert progress['xp']==80
    assert progress['lessons']['L01']['completed'] and progress['lessons']['L01']['game'] and progress['lessons']['L01']['quiz']
    assert progress['lessons']['L01']['updated']
    complete(client)
    assert client.get('/api/progress').json()['xp']==80
