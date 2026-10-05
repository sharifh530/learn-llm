"""Provider fakes verify policy; SDK MockTransport verifies serialization, never live access."""
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Event
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from google import genai
from google.genai import errors, types

from app.config import AISettings
from app.main import create_app
from app.providers import AIError, GoogleProvider, ModelReply, provider_error


class FakeProvider:
    def __init__(self):
        self.calls = []
        self.error = None

    def generate(self, instruction, message, input_limit, output_limit, on_call):
        self.calls.append((instruction, message, input_limit, output_limit))
        on_call()
        if self.error:
            raise self.error
        on_call()
        return ModelReply('TEST FAKE: a short explanation, not a live Google reply.', 20, 10, 30)


@pytest.fixture
def live_fixture(tmp_path):
    provider = FakeProvider()
    settings = AISettings(enabled=True, api_key='fake-secret-never-display', model='test-model')
    app = create_app(tmp_path / 'test.db', ai_settings=settings, provider=provider)
    with TestClient(app) as client:
        yield client, app, provider


def body(message='Explain tokens', **extra):
    return {'message': message, 'request_id': str(uuid4()), **extra}


def test_disabled_no_calls_and_secret_free_status(tmp_path):
    provider = FakeProvider()
    app = create_app(tmp_path / 'test.db', ai_settings=AISettings(api_key='fake-secret'), provider=provider)
    with TestClient(app) as client:
        assert client.post('/api/ai/messages', json=body()).status_code == 503
        assert not provider.calls
        state = client.get('/api/provider/status')
        assert not state.json()['configured'] and not state.json()['connected']
        for path in ('/settings', '/chat', '/lessons/L07', '/api/provider/status'):
            assert 'fake-secret' not in client.get(path).text
        assert 'fake-secret' not in repr(app.state.ai.settings)


def test_tutor_context_separation_mode_and_stale_version(live_fixture):
    client, app, fake = live_fixture
    version = client.get('/api/lessons/L07').json()['version']
    hint = body(lesson_id='L07', version=version, mode='hint')
    assert client.post('/api/tutor/messages', json=hint).status_code == 200
    instruction, message, input_limit, output_limit = fake.calls[-1]
    assert 'Mode: hint' in instruction and 'Prompt Kitchen' in message
    assert 'reference_solution' not in message and 'correct_choice_id' not in message and 'quiz' not in message
    assert (input_limit, output_limit) == (6000, 1024)
    solution = body(lesson_id='L07', version=version, mode='solution')
    assert client.post('/api/tutor/messages', json=solution).status_code == 200
    assert 'reference_solution' in fake.calls[-1][1]
    assert client.post('/api/ai/messages', json=body('chat-only-marker')).status_code == 200
    assert fake.calls[-1][1] == 'chat-only-marker' and 'Prompt Kitchen' not in fake.calls[-1][0]
    assert client.post('/api/tutor/messages', json=body(lesson_id='L07', version=99)).status_code == 409
    assert len(fake.calls) == 3
    assert client.post('/api/tutor/messages', json=body(lesson_id='L19', version=1)).status_code == 404
    assert app.state.progress.summary()['xp'] == 0


def test_idempotency_usage_and_restart(live_fixture):
    client, app, fake = live_fixture
    request = body()
    response = client.post('/api/ai/messages', json=request).json()
    assert response['mode'] == 'google_cloud' and response['usage']['total_tokens'] == 30
    assert client.post('/api/ai/messages', json=request).json()['cached']
    assert len(fake.calls) == 1
    assert client.post('/api/ai/messages', json={**request, 'message': 'changed'}).status_code == 409
    assert client.post('/api/provider/test', json={'request_id': str(uuid4())}).status_code == 200
    assert fake.calls[-1][-1] == 128
    state = client.get('/api/provider/status').json()
    assert state['configured'] and state['connected']
    assert state['usage']['attempts'] == 2 and state['usage']['provider_calls'] == 4
    assert state['usage']['reported_total_tokens'] == 60 and state['usage']['cost'] is None
    restarted = create_app(app.state.database.path, ai_settings=app.state.ai.settings, provider=fake)
    with TestClient(restarted) as other:
        assert other.post('/api/ai/messages', json=request).json()['cached']
        assert other.get('/api/provider/status').json()['usage']['attempts'] == 2


def test_failures_are_redacted_not_retried(live_fixture):
    client, app, fake = live_fixture
    fake.error = RuntimeError('contains fake-secret-never-display and a sensitive URL')
    request = body()
    response = client.post('/api/ai/messages', json=request)
    assert response.status_code == 503
    assert 'fake-secret' not in response.text
    assert client.post('/api/ai/messages', json=request).status_code == 409
    assert len(fake.calls) == 1
    usage = app.state.ai.usage()
    assert usage['unknown_usage_attempts'] == 1 and usage['provider_calls'] == 1
    assert client.post('/api/ai/messages', json=body('x' * 4001)).status_code == 422
    assert client.post('/api/ai/messages', json=body(' ')).status_code == 422
    assert client.post('/api/ai/messages', json=body(system_instruction='override')).status_code == 422


def test_minute_and_day_limits(live_fixture):
    client, app, fake = live_fixture
    for _ in range(8):
        assert client.post('/api/ai/messages', json=body()).status_code == 200
    assert client.post('/api/ai/messages', json=body()).status_code == 429
    import time
    with app.state.database.connection() as connection:
        connection.execute('UPDATE ai_requests SET created_at=?', (int(time.time() // 86400) * 86400,))
        for _ in range(42):
            connection.execute("INSERT INTO ai_requests(request_id,payload_hash,purpose,status,created_at) VALUES(?,?,'chat','failed',?)", (str(uuid4()), 'test', int(time.time() // 86400) * 86400))
    assert client.post('/api/ai/messages', json=body()).status_code == 429
    assert len(fake.calls) == 8


def test_concurrent_calls_admit_one(live_fixture):
    client, app, fake = live_fixture
    entered, release = Event(), Event()
    original = fake.generate
    def slow(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)
    fake.generate = slow
    request = body()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(client.post, '/api/ai/messages', json=request)
        try:
            assert entered.wait(3)
            retry = client.post('/api/ai/messages', json=request)
            assert retry.status_code == 409 and retry.json()['code'] == 'in_progress'
            assert client.post('/api/ai/messages', json=body()).status_code == 429
        finally:
            release.set()
        assert first.result().status_code == 200
    assert len(fake.calls) == 1
    assert client.post('/api/ai/messages', json=request).json()['cached']


@pytest.mark.parametrize('code,expected', [(400,'model'), (401,'access'), (403,'access'), (404,'model'), (429,'quota'), (500,'unavailable')])
def test_provider_error_mapping(code, expected):
    public = provider_error(errors.APIError(code, {'message': 'fake-secret'}))
    assert public.code == expected and 'fake-secret' not in str(public)


@pytest.mark.parametrize('scenario', ['success', 'too_large', 'empty', 'empty_usage', 'blocked', 'quota', 'timeout', 'unknown_usage', 'unblocked', 'truncated'])
def test_real_sdk_serialization_and_failure_handling(monkeypatch, scenario):
    calls, settings = [], AISettings(enabled=True, api_key='fake-cloud-key', model='test-model')
    def handle(request):
        calls.append(request)
        payload = json.loads(request.content)
        assert 'fake-cloud-key' not in request.url.query.decode()
        if request.url.path.endswith(':countTokens'):
            assert payload['systemInstruction']['parts'][0]['text'] == 'job instruction'
            return httpx.Response(200, json={'totalTokens': 7000 if scenario == 'too_large' else 12})
        assert request.url.path.endswith(':generateContent')
        assert payload['generationConfig']['maxOutputTokens'] == 1024
        if scenario == 'quota':
            return httpx.Response(429, json={'error': {'message': 'fake-cloud-key', 'code': 429}})
        if scenario == 'timeout':
            raise httpx.ReadTimeout('fake-cloud-key')
        if scenario == 'blocked':
            return httpx.Response(200, json={'promptFeedback': {'blockReason': 'SAFETY'}})
        if scenario == 'empty':
            return httpx.Response(200, json={})
        if scenario == 'empty_usage':
            return httpx.Response(200, json={'usageMetadata': {'promptTokenCount': 12, 'totalTokenCount': 12}})
        result = {'candidates': [{'content': {'role': 'model', 'parts': [{'text': 'MockTransport response'}]}, 'finishReason': 'STOP'}]}
        if scenario == 'unblocked':
            result['promptFeedback'] = {'blockReason': 'BLOCKED_REASON_UNSPECIFIED'}
        if scenario == 'truncated':
            result['candidates'][0]['finishReason'] = 'MAX_TOKENS'
        if scenario != 'unknown_usage':
            result['usageMetadata'] = {'promptTokenCount': 12, 'candidatesTokenCount': 5, 'totalTokenCount': 17}
        return httpx.Response(200, json=result)
    real_client = genai.Client
    def test_client(**arguments):
        assert arguments['vertexai'] is True and arguments['api_key'] == settings.api_key
        assert arguments['http_options'].timeout == 30000
        assert arguments['http_options'].retry_options.attempts == 1
        arguments['http_options'].client_args = {'transport': httpx.MockTransport(handle)}
        return real_client(**arguments)
    monkeypatch.setattr('app.providers.genai.Client', test_client)
    counter = []
    if scenario in ('success', 'unknown_usage', 'unblocked', 'truncated'):
        result = GoogleProvider(settings).generate('job instruction', 'question', 6000, 1024, lambda: counter.append(1))
        assert result.text == 'MockTransport response'
        assert result.total_tokens == (None if scenario == 'unknown_usage' else 17)
        if scenario == 'truncated':
            assert result.finish_reason == 'MAX_TOKENS'
    else:
        with pytest.raises(AIError) as error:
            GoogleProvider(settings).generate('job instruction', 'question', 6000, 1024, lambda: counter.append(1))
        assert error.value.code == {'too_large':'input_limit','empty':'empty','empty_usage':'empty','blocked':'blocked','quota':'quota','timeout':'timeout'}[scenario]
        if scenario == 'empty_usage':
            assert error.value.usage[-1] == 12
        assert 'fake-cloud-key' not in str(error.value)
    assert len(calls) == len(counter) == (1 if scenario == 'too_large' else 2)


def test_failed_response_usage_is_retained(live_fixture):
    client, app, fake = live_fixture
    fake.error = AIError('empty', 'No visible text.', 422, usage=(20, 0, 20))
    assert client.post('/api/ai/messages', json=body()).status_code == 422
    usage = app.state.ai.usage()
    assert usage['reported_total_tokens'] == 20 and usage['unknown_usage_attempts'] == 0


def test_adc_uses_explicit_credentials(monkeypatch):
    settings = AISettings(enabled=True, auth_mode='adc', project='test-project', location='global', model='test-model')
    credential = object()
    monkeypatch.setattr('google.auth.default', lambda **kw: (credential, None))
    def check_client(**arguments):
        assert arguments['credentials'] is credential
        assert arguments['project'] == 'test-project' and arguments['location'] == 'global'
        assert 'api_key' not in arguments
        raise ValueError('mock stops before network')
    monkeypatch.setattr('app.providers.genai.Client', check_client)
    with pytest.raises(AIError):
        GoogleProvider(settings).generate('job', 'question', 6000, 1024, lambda: None)


def test_append_only_schema_preserves_progress(tmp_path):
    from app.db import Database
    path = tmp_path / 'progress.db'
    first = Database(path)
    with first.connection() as connection:
        connection.execute("INSERT INTO xp_awards VALUES('L01-build','build',30,'original')")
        connection.execute('DROP TABLE ai_requests')
        connection.execute('PRAGMA user_version=1')
    updated = Database(path)
    with updated.connection() as connection:
        assert connection.execute('SELECT SUM(amount) FROM xp_awards').fetchone()[0] == 30
        assert connection.execute('PRAGMA user_version').fetchone()[0] == 3
        assert connection.execute('SELECT COUNT(*) FROM ai_requests').fetchone()[0] == 0
