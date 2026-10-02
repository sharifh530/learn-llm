import json
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import AISettings
from app.main import create_app
from app.models import ProviderSettings
from app.settings_store import SettingsStore, SettingsStoreError
from tests.test_ai import FakeProvider

SECRET = 'test-only-cloud-key-not-a-real-credential'


def body(**changes):
    return {'enabled': True, 'auth_mode': 'express_key', 'api_key': SECRET, 'model': 'test-text-model', **changes}


def test_windows_encrypted_persistence_and_ignore_environment(tmp_path, monkeypatch):
    monkeypatch.setenv('GOOGLE_CLOUD_API_KEY', 'ignored-environment-key')
    monkeypatch.setenv('AI_ENABLED', 'true')
    store = SettingsStore(tmp_path / 'ai-settings.json')
    assert not store.load().enabled
    settings = store.candidate(AISettings(), ProviderSettings(**body()))
    store.save(settings)
    raw = store.path.read_text(encoding='utf-8')
    assert SECRET not in raw and 'api_key' not in json.loads(raw)
    assert json.loads(raw)['protected_key']
    assert AISettings.load(store.path) == settings
    assert SECRET not in repr(settings)
    assert SECRET not in repr(ProviderSettings(**body()))


def test_save_hot_update_reload_keep_replace_and_remove(tmp_path):
    database = tmp_path / 'progress.db'
    fake = FakeProvider()
    app = create_app(database, provider=fake)
    with TestClient(app) as client:
        initial = client.get('/api/progress').json()
        saved = client.post('/api/provider/settings', json=body())
        assert saved.status_code == 200
        state = saved.json()
        assert state['configured'] and state['key_saved'] and not state['connected']
        assert fake.calls == []
        assert app.state.ai.settings.api_key == SECRET
        # Keeping the key is explicit via a blank field, without returning it.
        assert client.post('/api/provider/settings', json=body(api_key='', model='another-model')).status_code == 200
        assert app.state.ai.settings.api_key == SECRET
        request = {'request_id': str(uuid4())}
        assert client.post('/api/provider/test', json=request).status_code == 200
        assert client.get('/api/provider/status').json()['connected']
        assert client.post('/api/provider/settings', json=body(api_key='replacement-test-key')).status_code == 200
        assert app.state.ai.settings.api_key == 'replacement-test-key'
        assert not app.state.ai.connected
        for path in ('/settings', '/api/provider/status', '/chat'):
            text = client.get(path).text
            assert SECRET not in text and 'replacement-test-key' not in text and '.env' not in text
        assert client.get('/api/progress').json() == initial
    restarted = create_app(database)
    assert restarted.state.ai.settings.api_key == 'replacement-test-key'
    assert restarted.state.ai.provider.settings == restarted.state.ai.settings
    with TestClient(restarted) as client:
        assert client.post('/api/provider/key/remove', json={}).status_code == 200
        assert not client.get('/api/provider/status').json()['key_saved']
        assert client.post('/api/provider/test', json={'request_id': str(uuid4())}).status_code == 503
        assert client.get('/api/progress').json() == initial
    assert not create_app(database).state.ai.settings.api_key
    assert not create_app(database).state.ai.settings.enabled
    assert not json.loads((tmp_path / 'ai-settings.json').read_text())['protected_key']


@pytest.mark.parametrize('changes,code', [
    ({'api_key': ''}, 400), ({'model': ''}, 400),
    ({'auth_mode': 'adc', 'project': '', 'location': 'global'}, 400),
    ({'api_key': 'bad\nkey'}, 422), ({'auth_mode': 'studio'}, 422),
    ({'enabled': 'true'}, 422), ({'model': '../../secret'}, 422),
    ({'extra': 'not-allowed'}, 422),
])
def test_invalid_settings_do_not_save_or_call(tmp_path, changes, code):
    fake = FakeProvider()
    with TestClient(create_app(tmp_path / 'progress.db', provider=fake)) as client:
        response = client.post('/api/provider/settings', json=body(**changes))
        assert response.status_code == code
        assert SECRET not in response.text
        assert not (tmp_path / 'ai-settings.json').exists()
        assert not fake.calls


def test_settings_origin_adc_and_failed_write(tmp_path, monkeypatch):
    app = create_app(tmp_path / 'progress.db')
    with TestClient(app) as client:
        assert client.post('/api/provider/settings', json=body(), headers={'Origin': 'https://elsewhere.example'}).status_code == 403
        assert client.post('/api/provider/key/remove', json={}, headers={'Sec-Fetch-Site': 'cross-site'}).status_code == 403
        assert client.post('/api/provider/settings', json=body(auth_mode='adc', api_key='', project='project-id', location='global')).status_code == 200
        assert app.state.ai.settings.auth_mode == 'adc' and not app.state.ai.settings.api_key
        previous = app.state.ai.settings
        raw = (tmp_path / 'ai-settings.json').read_bytes()
        def fail(*args):
            raise SettingsStoreError('Could not save; previous connection unchanged.')
        monkeypatch.setattr(SettingsStore, 'save', fail)
        assert client.post('/api/provider/settings', json=body()).status_code == 400
        assert app.state.ai.settings is previous
        assert (tmp_path / 'ai-settings.json').read_bytes() == raw


def test_corrupt_config_still_opens_offline_and_can_be_replaced(tmp_path):
    path = tmp_path / 'ai-settings.json'
    path.write_text('{bad')
    app = create_app(tmp_path / 'progress.db')
    with TestClient(app) as client:
        assert client.get('/settings').status_code == 200
        assert client.get('/api/provider/status').json()['settings_notice']
        assert not app.state.ai.settings.enabled
        assert client.post('/api/provider/settings', json=body()).status_code == 200
        assert not client.get('/api/provider/status').json()['settings_notice']


def test_active_tutor_or_chat_rejects_settings_change(tmp_path):
    app = create_app(tmp_path / 'progress.db')
    with TestClient(app) as client:
        app.state.ai.active_requests = 1
        assert client.post('/api/provider/settings', json=body()).status_code == 409
        assert client.post('/api/provider/key/remove', json={}).status_code == 409
        app.state.ai.active_requests = 0
        app.state.chats.jobs['fixture-job'] = threading.Event()
        assert client.post('/api/provider/settings', json=body()).status_code == 409
        app.state.chats.jobs.clear()
        assert not (tmp_path / 'ai-settings.json').exists()


def test_atomic_replace_failure_retains_previous_encrypted_file(tmp_path, monkeypatch):
    store = SettingsStore(tmp_path / 'ai-settings.json')
    previous = store.candidate(AISettings(), ProviderSettings(**body()))
    store.save(previous)
    raw = store.path.read_bytes()
    def fail(*args):
        raise OSError('fixture disk error')
    monkeypatch.setattr(Path, 'replace', fail)
    with pytest.raises(SettingsStoreError):
        store.save(store.candidate(previous, ProviderSettings(**body(api_key='different-test-key'))))
    assert store.path.read_bytes() == raw
    assert store.load() == previous
    assert not list(tmp_path.glob('.ai-settings-*.tmp'))


def test_real_request_admission_holds_settings_until_finished(tmp_path):
    entered, release = threading.Event(), threading.Event()
    class WaitingProvider(FakeProvider):
        def generate(self, *args):
            entered.set()
            assert release.wait(5)
            return super().generate(*args)
    app = create_app(tmp_path / 'progress.db', ai_settings=AISettings(enabled=True, api_key=SECRET, model='test-model'), provider=WaitingProvider())
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=1) as workers:
        future = workers.submit(client.post, '/api/provider/test', json={'request_id': str(uuid4())})
        assert entered.wait(5)
        try:
            assert client.post('/api/provider/settings', json=body()).status_code == 409
            assert app.state.ai.settings.model == 'test-model'
        finally:
            release.set()
        assert future.result().status_code == 200
        assert app.state.ai.active_requests == 0
        assert client.post('/api/provider/settings', json=body()).status_code == 200
