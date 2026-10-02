"""Cloud protocol harness: separate instances share SQLite only via HTTPS JSON.

The harness checks transport and lifecycle, not live Turso/Google availability.
"""
from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3
import threading
import time
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.cloud_db import CloudDatabase, CloudStorageError, encode, decode
from app.cloud_settings import CloudSettingsStore
from app.main import create_app
from app.providers import ModelReply
from app.vercel import HostedLab


class SQLServer:
    def __init__(self, path):
        self.path, self.connections = path, {}
        self.lock = threading.Lock()
        self.fail_begin = False

    def request(self, request):
        assert request.url.scheme=='https' and request.url.path=='/v2/pipeline'
        assert request.headers['authorization']=='Bearer fake-database-token'
        data = json.loads(request.content)
        with self.lock:
            baton = data.get('baton') or uuid4().hex
            connection = self.connections.setdefault(baton, sqlite3.connect(self.path, isolation_level=None, check_same_thread=False, timeout=3))
        results = []
        for item in data['requests']:
            if item['type']=='close':
                connection.close()
                with self.lock:
                    del self.connections[baton]
                baton = None
                results.append({'type':'ok','response':{'type':'close'}})
                continue
            try:
                statement = item['stmt']
                if statement['sql'].strip().upper().startswith('PRAGMA USER_VERSION'):
                    raise sqlite3.OperationalError('native Turso does not parse user_version')
                if self.fail_begin and statement['sql'].startswith('BEGIN'):
                    raise sqlite3.OperationalError('busy')
                cursor = connection.execute(statement['sql'],tuple(decode(value) for value in statement.get('args',[])))
                result = {'cols':[{'name':item[0]} for item in cursor.description or []],
                          'rows':[[encode(value) for value in row] for row in cursor.fetchall()],
                          'affected_row_count':max(cursor.rowcount,0),'last_insert_rowid':str(cursor.lastrowid or 0)}
                results.append({'type':'ok','response':{'type':'execute','result':result}})
            except sqlite3.Error as error:
                results.append({'type':'error','error':{'code':'SQLITE_CONSTRAINT' if isinstance(error,sqlite3.IntegrityError) else 'SQLITE_ERROR','message':str(error)}})
        if baton is not None and not connection.in_transaction:
            connection.close()
            with self.lock:
                del self.connections[baton]
            baton = None
        return httpx.Response(200,json={'baton':baton,'base_url':None,'results':results})


class Provider:
    def __init__(self):
        self.calls = []
        self.entered, self.hold = threading.Event(), threading.Event()

    def generate(self,*args):
        self.calls.append(args)
        args[-1]()
        return ModelReply('FAKE cloud reply',12,5,17)

    def stream(self,instruction,messages,input_limit,output_limit,on_call,cancelled):
        self.calls.append(messages)
        on_call()
        yield ModelReply('FAKE first chunk. ')
        self.entered.set()
        while not self.hold.wait(.01):
            if cancelled():
                return
        yield ModelReply('Mango remembered.')
        yield ModelReply('',12,5,17,'STOP')


@pytest.fixture
def cloud(tmp_path):
    server = SQLServer(tmp_path/'remote.db')
    database = CloudDatabase('libsql://test.turso.io','fake-database-token',httpx.MockTransport(server.request))
    store, provider = CloudSettingsStore(database), Provider()
    def client():
        return TestClient(create_app(database=database,settings_store=store,hosted=True,provider=provider,
            allowed_hosts=['testserver','*.vercel.app']))
    yield client, database, store, provider, server
    provider.hold.set()


def save(client,key='fake-google-secret'):
    return client.post('/api/provider/settings',json={'enabled':True,'api_key':key,'model':'fake-model','auth_mode':'express_key'})


def test_progress_chats_and_encrypted_settings_survive_instances(cloud):
    factory, db, store, provider, server = cloud
    with factory() as first:
        for path in ('/','/lessons/L01','/workshop','/observatory','/chat','/settings'):
            assert first.get(path).status_code==200
        assert save(first).status_code==200
        assert 'fake-google-secret' not in first.get('/api/provider/status').text
        assert first.post('/api/lessons/L01/acknowledgments',json={'kind':'reading','version':1}).status_code==200
        chat = first.post('/api/chats',json={'mode':'demo'}).json()['id']
        identity = str(uuid4())
        body = {'message':'My favorite fruit is mango','request_id':identity}
        assert first.post(f'/api/chats/{chat}/messages',json=body).json()['status']=='running'
    with factory() as second:
        assert second.get('/api/progress').json()['xp']>0
        assert second.get('/api/provider/status').json()['key_saved']
        assert second.get(f'/api/generations/{identity}').json()['status']=='running'
        assert 'event: done' in second.get(f'/api/generations/{identity}/events').text
        assert second.get(f'/api/generations/{identity}').json()['status']=='complete'
        assert second.post(f'/api/chats/{chat}/messages',json=body).json()['id']==identity
        assert save(second,'').status_code==200
        assert store.load().api_key=='fake-google-secret'
        assert 'local ADC' not in second.get('/settings').text
    with db.connection() as connection:
        stored = connection.execute('SELECT value FROM cloud_settings').fetchone()['value']
    assert 'fake-google-secret' not in stored
    assert provider.calls==[]
    assert server.connections=={}


def test_one_worker_across_instances_stop_and_reservation(cloud):
    factory, db, store, provider, server = cloud
    first, second = factory(), factory()
    assert save(first).status_code==200
    chat = first.post('/api/chats',json={'mode':'google_cloud'}).json()['id']
    identity = str(uuid4())
    body = {'message':'My fruit is mango','request_id':identity}
    assert first.post(f'/api/chats/{chat}/messages',json=body).status_code==200
    with ThreadPoolExecutor(2) as workers:
        stream = workers.submit(lambda:first.get(f'/api/generations/{identity}/events'))
        assert provider.entered.wait(3)
        watching = workers.submit(lambda:second.get(f'/api/generations/{identity}/events'))
        assert second.get(f'/api/generations/{identity}').json()['status']=='running'
        assert save(second,'different').status_code==409
        assert second.post(f'/api/chats/{chat}/messages',json=body).json()['id']==identity
        stopped = second.post(f'/api/generations/{identity}/cancel',json={}).json()
        assert stopped['status']=='stopped' and stopped['text']=='FAKE first chunk. '
        provider.hold.set()
        assert 'event: done' in stream.result(5).text
        assert 'event: done' in watching.result(5).text
    assert len(provider.calls)==1
    assert second.get('/api/provider/status').json()['usage']['attempts']==1
    assert second.get(f'/api/chats/{chat}').json()['turns'][0]['selected_id'] is None
    assert first.get(f'/api/generations/{identity}').json()['text']==stopped['text']
    first.close(); second.close()


def test_disconnect_preserves_partial_without_selecting_it(cloud):
    factory, db, store, provider, server = cloud
    from app.ai import AIService
    from app.chat import ChatService
    from app.content import ContentStore
    from app.config import CONTENT_DIR
    from app.models import ChatCreate, AIMessage
    ai = AIService(store.load(),db,ContentStore(CONTENT_DIR),provider)
    ai.settings_store = store
    chats = ChatService(db,ai)
    identity = str(uuid4())
    chat = chats.create(ChatCreate(mode='demo'))
    chats.start(chat['id'],AIMessage(message='tokens',request_id=identity))
    events = chats.events(identity)
    assert 'snapshot' in next(events)
    events.close()
    generation = chats.generation(identity)
    assert generation['status']=='interrupted' and generation['text']
    assert chats.get(chat['id'])['turns'][0]['selected_id'] is None


def test_transaction_rollback_and_failed_begin_never_autocommits(cloud):
    _, db, _, _, server = cloud
    with pytest.raises(ValueError):
        with db.connection() as connection:
            connection.execute("INSERT INTO xp_awards VALUES('rollback','game',9,'now')")
            raise ValueError('abort')
    server.fail_begin = True
    with pytest.raises(CloudStorageError):
        with db.connection() as connection:
            connection.execute("INSERT INTO xp_awards VALUES('autocommit','game',9,'now')")
    server.fail_begin = False
    with db.connection() as connection:
        assert connection.execute('SELECT COUNT(*) FROM xp_awards').fetchone()[0]==0
    assert server.connections=={}


def test_bad_urls_and_token_rotation_fail_closed(cloud):
    factory, db, store, _, _ = cloud
    for url in ('http://test.turso.io','https://evil.example','libsql://token@test.turso.io','libsql://test.turso.io?token=secret'):
        with pytest.raises(CloudStorageError):
            CloudDatabase(url,'token')
    client = factory()
    assert save(client).status_code==200
    assert client.post('/api/journal',headers={'Origin':'https://evil.example'},json={}).status_code==403
    db.token = 'rotated'
    from app.settings_store import SettingsStoreError
    rotated = CloudSettingsStore(db)
    db.token = 'fake-database-token'
    with pytest.raises(SettingsStoreError):
        rotated.load()
    client.close()


def test_entrypoint_requires_storage_and_private_hosting(monkeypatch):
    monkeypatch.delenv('TINY_CHAT_PRIVATE_HOSTING',raising=False)
    application = FastAPI()
    application.mount('/',HostedLab())
    with TestClient(application) as client:
        result = client.get('/health')
        assert result.status_code==503 and result.json()['status']=='setup_required'
        assert client.get('/').status_code==503


def test_single_reply_quota_and_corrupt_settings_recovery(cloud):
    factory, db, store, provider, _ = cloud
    first, second = factory(), factory()
    assert save(first).status_code==200
    body = {'message':'tokens','request_id':str(uuid4())}
    assert first.post('/api/ai/messages',json=body).json()['reply']=='FAKE cloud reply'
    assert second.post('/api/ai/messages',json=body).json()['cached']
    assert len(provider.calls)==1
    with db.connection() as connection:
        connection.execute("UPDATE cloud_settings SET value='invalid'")
    assert second.get('/api/provider/status').json()['settings_notice']
    assert save(second,'').status_code==400
    assert save(second,'replacement-fake-key').status_code==200
    assert store.load().api_key=='replacement-fake-key'
    assert second.post('/api/provider/key/remove',json={}).status_code==200
    assert not store.load().enabled and not store.load().api_key
    first.close(); second.close()


def test_only_abandoned_cloud_leases_are_recovered(cloud):
    factory, db, _, _, _ = cloud
    client = factory()
    assert save(client).status_code==200
    chat = client.post('/api/chats',json={'mode':'google_cloud'}).json()['id']
    identity = str(uuid4())
    assert client.post(f'/api/chats/{chat}/messages',json={'message':'queued','request_id':identity}).status_code==200
    with db.connection() as connection:
        connection.execute('UPDATE generations SET created_at=? WHERE id=?',(time.time()-200,identity))
        connection.execute('UPDATE ai_requests SET created_at=? WHERE request_id=?',(time.time()-200,identity))
        connection.execute('INSERT INTO generation_workers VALUES(?,?)',(identity,time.time()))
    assert client.get(f'/api/generations/{identity}').json()['status']=='running'
    with db.connection() as connection:
        connection.execute('UPDATE generation_workers SET started_at=? WHERE id=?',(time.time()-200,identity))
    assert client.get(f'/api/generations/{identity}').json()['status']=='interrupted'
    with db.connection() as connection:
        assert connection.execute('SELECT status FROM ai_requests WHERE request_id=?',(identity,)).fetchone()[0]=='interrupted'
    assert 'event: done' in client.get(f'/api/generations/{identity}/events').text
    client.close()
