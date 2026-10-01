import json
import shutil
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import labs
from app.config import AISettings
from app.content import ContentError, ContentStore
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / 'labs.db', ai_settings=AISettings())) as client:
        yield client


def test_cosine_direction_and_zero():
    apple = [7, 8, 3]
    assert labs.cosine(apple, apple) == pytest.approx(1)
    assert labs.cosine(apple, [3.5, 4, 1.5]) == pytest.approx(1)
    assert labs.cosine([1, 0], [0, 1]) == 0
    assert labs.cosine([1, 0], [-1, 0]) == -1
    assert labs.cosine(apple, [0, 0, 0]) is None
    assert labs.similarity([0, 0, 10])['matches'][0]['name'] == 'Lemon'
    assert not labs.similarity([0, 0, 0])['defined']
    assert all(item['similarity'] is None for item in labs.similarity([0, 0, 0])['matches'])


def test_attention_mask_stability_and_weighted_value():
    scores = [-3, 3, -3, 3, -3, 3, -3]
    data = labs.attention(scores, 4, True, .25)
    assert data['sum'] == pytest.approx(1)
    assert [r['weight'] for r in data['rows'][5:]] == [0, 0]
    assert all(r['weight'] >= 0 for r in data['rows'])
    assert data['weighted_value'] == pytest.approx(sum(r['weight'] * r['value'] for r in data['rows']))
    scores[5:] = [-3, 3]
    assert labs.attention(scores, 4, True, .25)['weighted_value'] == data['weighted_value']
    assert labs.attention(scores, 0, True, 1)['rows'][0]['weight'] == 1
    equal = labs.attention([0] * 7, 4, True, 1)
    assert [r['weight'] for r in equal['rows']] == pytest.approx([.2] * 5 + [0, 0])
    unmasked = labs.attention(scores, 0, False, 2)
    assert all(r['weight'] > 0 for r in unmasked['rows'])
    assert unmasked['sum'] == pytest.approx(1)
    assert max(r['weight'] for r in labs.attention(scores, 6, False, .25)['rows']) > max(r['weight'] for r in unmasked['rows'])


def test_training_inference_update_and_check_are_separate():
    prediction = labs.training(1, .25, 10, 'predict')
    assert prediction['before'] == prediction['after'] and prediction['steps'] == []
    first = labs.training(1, .25, 1, 'train')
    assert first['steps'][0]['gradient'] == -4
    assert first['after']['weight'] == 2
    assert first['after']['train_loss'] == 1 and first['after']['check_loss'] == 0
    second = labs.training(2, .25, 1, 'train')['after']
    assert second['weight'] == 2.5 and second['train_loss'] == .25 and second['check_loss'] == 1
    later = labs.training(2.5, .25, 10, 'train')['after']
    assert 2.99 < later['weight'] < 3 and later['train_loss'] < second['train_loss']
    assert later['check_loss'] > second['check_loss']
    bounce = labs.training(1, 1, 2, 'train')
    assert [r['weight'] for r in bounce['steps']] == [5, 1]
    assert [r['train_loss'] for r in bounce['steps']] == [4, 4]


@pytest.mark.parametrize('path,body', [
    ('similarity', {'vector': [1, 2]}), ('similarity', {'vector': [1, 2, 3, 4]}),
    ('similarity', {'vector': [-1, 2, 3]}), ('similarity', {'vector': [11, 2, 3]}),
    ('similarity', {'vector': ['NaN', 2, 3]}), ('similarity', {'vector': ['Infinity', 2, 3]}),
    ('similarity', {'vector': [True, 2, 3]}), ('training', {'weight': True}),
    ('similarity', {'vector': [1, 2, 3], 'code': 'print(1)'}),
    ('attention', {'scores': [0]*6, 'query_index': 4}),
    ('attention', {'scores': [0]*7, 'query_index': 7}),
    ('attention', {'scores': [0]*7, 'query_index': True}),
    ('attention', {'scores': [0]*7, 'query_index': 4, 'temperature': 0}),
    ('attention', {'scores': [0]*7, 'query_index': 4, 'causal': 'false'}),
    ('attention', {'scores': [0]*6+[4], 'query_index': 4}),
    ('training', {'weight': 7}), ('training', {'weight': 'NaN'}),
    ('training', {'learning_rate': 0}), ('training', {'learning_rate': 1.01}),
    ('training', {'steps': 11}), ('training', {'steps': True}),
    ('training', {'operation': 'execute'}), ('training', {'check_target': 3}),
])
def test_bad_toy_inputs_are_rejected(client, path, body):
    assert client.post('/api/labs/' + path, json=body).status_code == 422


@pytest.mark.parametrize('number', ['NaN', 'Infinity', '-Infinity'])
@pytest.mark.parametrize('path,template', [
    ('training', '{{"weight":{number}}}'),
    ('similarity', '{{"vector":[{number},2,3]}}'),
    ('attention', '{{"scores":[{number},0,0,0,0,0,0],"query_index":4}}'),
])
def test_raw_nonfinite_values_return_serializable_errors(client, number, path, template):
    response = client.post('/api/labs/' + path, content=template.format(number=number), headers={'Content-Type': 'application/json'})
    assert response.status_code == 422
    assert response.json()['detail'][0]['type'] == 'finite_number'
    assert 'input' not in response.json()['detail'][0]


def test_toy_routes_do_not_write_progress_chats_or_usage(client):
    db = client.app.state.database.path
    def snapshot():
        with sqlite3.connect(db) as connection:
            tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            return {table: connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall() for table in tables}
    before = snapshot()
    page = client.get('/observatory')
    assert page.status_code == 200 and 'Educational toys' in page.text
    for path, body in [('similarity', {'vector': [7, 8, 3]}), ('attention', {'scores': [0]*7, 'query_index': 4}), ('training', {'operation': 'train', 'steps': 10})]:
        response = client.post('/api/labs/' + path, json=body)
        assert response.status_code == 200 and response.headers['cache-control'] == 'no-store'
    assert snapshot() == before
    assert client.get('/api/progress').json()['xp'] == 0
    assert client.get('/api/provider/status').json()['usage']['attempts'] == 0
    assert client.get('/api/chats').json() == []
    assert client.post('/api/labs/training', json={}, headers={'Origin': 'https://elsewhere.example'}).status_code == 403


def test_unknown_registered_lab_rejected_atomically(tmp_path):
    root = Path(__file__).resolve().parents[1]
    shutil.copytree(root / 'content', tmp_path / 'content')
    content = ContentStore(tmp_path / 'content')
    old = content.lessons
    path = tmp_path / 'content/lessons/L13.json'
    lesson = json.loads(path.read_text(encoding='utf-8'))
    lesson['lab'] = 'arbitrary-script'
    path.write_text(json.dumps(lesson), encoding='utf-8')
    with pytest.raises(ContentError):
        content.reload()
    assert content.lessons is old
