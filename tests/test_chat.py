import json
import threading
import time
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from google import genai

from app.config import AISettings
from app.main import create_app
from app.providers import AIError, GoogleProvider, ModelReply


class StreamFake:
    def __init__(self):
        self.calls=[]
        self.hold=threading.Event()
        self.entered=threading.Event()
        self.error=None
        self.finish='STOP'

    def stream(self,instruction,messages,input_limit,output_limit,on_call,cancelled):
        self.calls.append((instruction,messages,input_limit,output_limit))
        on_call();on_call()
        yield ModelReply('FAKE visible chunk. ')
        self.entered.set()
        while not self.hold.wait(.01):
            if cancelled():
                return
        if self.error:
            raise self.error
        yield ModelReply('Earlier user: '+messages[0]['text'])
        yield ModelReply('',20,10,30,self.finish)


@pytest.fixture
def fixture(tmp_path):
    provider=StreamFake()
    app=create_app(tmp_path/'chat.db',ai_settings=AISettings(enabled=True,api_key='test-secret',model='test-model'),provider=provider)
    with TestClient(app) as client:
        yield client,app,provider
    provider.hold.set()


def create(client,mode='google_cloud',persona='guide'):
    response=client.post('/api/chats',json={'mode':mode,'persona':persona})
    assert response.status_code==200
    return response.json()['id']


def start(client,chat,message='My fruit is mango',identity=None):
    response=client.post(f'/api/chats/{chat}/messages',json={'message':message,'request_id':identity or str(uuid4())})
    assert response.status_code==200,response.text
    return response.json()['id']


def wait(client,identity):
    for _ in range(300):
        value=client.get(f'/api/generations/{identity}').json()
        if value['status']!='running':
            return value
        time.sleep(.01)
    raise AssertionError('Generation did not finish')


def test_context_persona_idempotency_and_restart(fixture):
    client,app,fake=fixture
    chat=create(client,persona='coach');identity=str(uuid4())
    start(client,chat,identity=identity)
    assert fake.entered.wait(3)
    assert start(client,chat,identity=identity)==identity
    assert len(fake.calls)==1
    assert client.post(f'/api/chats/{chat}/messages',json={'message':'other','request_id':identity}).status_code==409
    assert client.post('/api/ai/messages',json={'message':'busy','request_id':str(uuid4())}).status_code==429
    fake.hold.set();assert wait(client,identity)['status']=='complete'
    second=start(client,chat,'What was my fruit?');wait(client,second)
    instruction,context,*limits=fake.calls[-1]
    assert 'Python examples' in instruction and limits==[12000,2048]
    assert [item['role'] for item in context]==['user','assistant','user']
    assert context[0]['text']=='My fruit is mango'
    restarted=create_app(app.state.database.path,ai_settings=app.state.ai.settings,provider=fake)
    with TestClient(restarted) as other:
        saved=other.get(f'/api/chats/{chat}').json()
        assert len(saved['turns'])==2 and saved['persona']=='coach'
        assert other.post(f'/api/chats/{chat}/messages',json={'message':'What was my fruit?','request_id':second}).json()['id']==second
    assert len(fake.calls)==2 and app.state.ai.usage()['attempts']==2
    assert app.state.progress.summary()['xp']==0


def test_stop_fences_late_text_and_partial_selection(fixture):
    client,app,fake=fixture
    chat=create(client);identity=start(client,chat);assert fake.entered.wait(3)
    stopped=client.post(f'/api/generations/{identity}/cancel',json={}).json()
    assert stopped['status']=='stopped' and stopped['text']=='FAKE visible chunk. '
    fake.hold.set();time.sleep(.08)
    assert client.get(f'/api/generations/{identity}').json()['text']==stopped['text']
    turn=client.get(f'/api/chats/{chat}').json()['turns'][0]
    assert turn['selected_id'] is None
    assert client.post(f'/api/chats/{chat}/messages',json={'message':'follow up','request_id':str(uuid4())}).status_code==409
    path=f'/api/chats/{chat}/turns/{turn["id"]}/select'
    assert client.post(path,json={'generation_id':identity}).status_code==409
    assert client.post(path,json={'generation_id':identity,'include_partial':True}).status_code==200
    follow=start(client,chat,'follow up');wait(client,follow)
    assert fake.calls[-1][1][1]['text']==stopped['text']


def test_alternative_requires_explicit_selection_and_cannot_change_old_turn(fixture):
    client,app,fake=fixture;fake.hold.set();chat=create(client)
    first=start(client,chat);wait(client,first)
    turn=client.get(f'/api/chats/{chat}').json()['turns'][0]
    retry_path=f'/api/chats/{chat}/turns/{turn["id"]}/retry'
    body={'request_id':str(uuid4())};alternate=client.post(retry_path,json=body).json()['id'];wait(client,alternate)
    assert client.post(retry_path,json=body).json()['id']==alternate
    assert client.get(f'/api/chats/{chat}').json()['turns'][0]['selected_id']==first
    assert client.post(f'/api/chats/{chat}/turns/{turn["id"]}/select',json={'generation_id':alternate}).status_code==200
    follow=start(client,chat,'next');wait(client,follow)
    assert client.post(retry_path,json={'request_id':str(uuid4())}).status_code==409


@pytest.mark.parametrize('kind',['failure','blocked','truncated','empty','oversized'])
def test_terminal_states_and_usage(fixture,kind):
    client,app,fake=fixture;fake.hold.set();chat=create(client)
    if kind in ('failure','blocked'):
        fake.error=AIError('blocked' if kind=='blocked' else 'test','Safe failure',usage=(20,2,22))
    elif kind=='truncated':
        fake.finish='MAX_TOKENS'
    elif kind=='oversized':
        def oversized(*args):
            yield ModelReply('x'*17000)
        fake.stream=oversized
    else:
        def empty(*args):
            yield ModelReply('',20,0,20,'STOP')
        fake.stream=empty
    value=wait(client,start(client,chat))
    assert value['status']=={'failure':'failed','blocked':'blocked','truncated':'truncated','empty':'failed','oversized':'failed'}[kind]
    if kind=='blocked':
        assert value['text']==''
    if kind=='oversized':
        assert len(value['text'])==16000
    assert value['total_tokens']=={'failure':22,'blocked':22,'truncated':30,'empty':20,'oversized':None}[kind]
    assert client.get(f'/api/chats/{chat}').json()['turns'][0]['selected_id'] is None


def test_demo_no_ai_ledger_archive_restore_and_isolation(fixture):
    client,app,fake=fixture;chat=create(client,'demo')
    wait(client,start(client,chat));value=wait(client,start(client,chat,'What was my favorite fruit earlier?'))
    assert 'mango' in value['text'] and not fake.calls and app.state.ai.usage()['attempts']==0
    other=create(client,'demo')
    assert client.post(f'/api/chats/{other}/context',json={'message':'next'}).json()['messages']==[{'role':'user','text':'next'}]
    assert client.post(f'/api/chats/{chat}/archive',json={}).json()['archived']==1
    assert len(client.get('/api/chats?mode=demo').json())==1
    assert client.post(f'/api/chats/{chat}/messages',json={'message':'no','request_id':str(uuid4())}).status_code==409
    assert client.post(f'/api/chats/{chat}/restore',json={}).status_code==200


def test_context_budget_keeps_whole_recent_pairs(fixture):
    client,app,fake=fixture;chat=create(client)
    with app.state.database.connection() as connection:
        for index in range(12):
            turn,generation=str(uuid4()),str(uuid4())
            connection.execute('INSERT INTO chat_turns VALUES(?,?,?,?,?)',(turn,chat,'🙂'*500,generation,index))
            connection.execute("INSERT INTO generations(id,turn_id,payload_hash,context_json,status,text,created_at) VALUES(?,?,?,'{}','complete',?,?)",(generation,turn,'x','reply '*150,index))
    context=client.post(f'/api/chats/{chat}/context',json={'message':'last'}).json()
    assert context['selection_bytes']<=12000 and context['omitted_turns']>0
    assert context['messages'][-1]=={'role':'user','text':'last'}
    assert [item['role'] for item in context['messages'][:-1]]==['user','assistant']*(len(context['messages'])//2)


def test_restart_recovers_partial_without_calling_provider(fixture):
    client,app,fake=fixture;chat=create(client)
    turn,identity=str(uuid4()),str(uuid4())
    with app.state.database.connection() as connection:
        connection.execute('INSERT INTO chat_turns VALUES(?,?,?,?,?)',(turn,chat,'saved question',None,0))
        connection.execute("INSERT INTO generations(id,turn_id,payload_hash,context_json,status,text,created_at) VALUES(?,?,?,'{}','running','saved partial',0)",(identity,turn,'x'))
    restarted=create_app(app.state.database.path,ai_settings=app.state.ai.settings,provider=fake)
    with TestClient(restarted) as other:
        value=other.get(f'/api/generations/{identity}').json()
        assert value['status']=='interrupted' and value['text']=='saved partial'
        assert 'event: done' in other.get(f'/api/generations/{identity}/events').text
    assert not fake.calls


@pytest.mark.parametrize('scenario',['normal','blocked','too_large','thought','unknown','truncated','empty','incomplete'])
def test_sdk_stream_roles_count_usage_and_thought_filter(monkeypatch,scenario):
    settings=AISettings(enabled=True,api_key='fake-key',model='test-model')
    calls=[]
    def handle(request):
        payload=json.loads(request.content);calls.append(payload)
        assert [item['role'] for item in payload['contents']]==['user','model','user']
        if request.url.path.endswith(':countTokens'):
            return httpx.Response(200,json={'totalTokens':13000 if scenario=='too_large' else 20})
        assert request.url.path.endswith(':streamGenerateContent')
        assert payload['generationConfig']['maxOutputTokens']==2048
        chunks=[{'candidates':[{'content':{'role':'model','parts':[{'text':'visible'}]}}]}]
        if scenario=='empty':
            chunks=[]
        if scenario=='thought':
            chunks.insert(0,{'candidates':[{'content':{'role':'model','parts':[{'text':'private-thought','thought':True}]}}]})
        chunks.append({'candidates':[{'finishReason':'SAFETY' if scenario=='blocked' else 'MAX_TOKENS' if scenario=='truncated' else 'STOP'}],**({} if scenario=='unknown' else {'usageMetadata':{'promptTokenCount':20,'candidatesTokenCount':3,'totalTokenCount':23}})})
        if scenario=='incomplete':
            chunks[-1]['candidates']=[{}]
        data=''.join('data: '+json.dumps(chunk)+'\n\n' for chunk in chunks)
        return httpx.Response(200,headers={'content-type':'text/event-stream'},content=data)
    real=genai.Client
    def factory(**kwargs):
        assert kwargs['vertexai'] is True
        kwargs['http_options'].client_args={'transport':httpx.MockTransport(handle)}
        return real(**kwargs)
    monkeypatch.setattr('app.providers.genai.Client',factory)
    stream=GoogleProvider(settings).stream('system',[{'role':'user','text':'mango'},{'role':'assistant','text':'noted'},{'role':'user','text':'fruit?'}],12000,2048,lambda:None,lambda:False)
    if scenario in ('blocked','too_large','empty','incomplete'):
        with pytest.raises(AIError) as error:
            list(stream)
        assert error.value.code=={'blocked':'blocked','too_large':'input_limit','empty':'empty','incomplete':'incomplete'}[scenario]
    else:
        chunks=list(stream)
        assert ''.join(item.text for item in chunks)=='visible'
        assert chunks[-1].total_tokens==(None if scenario=='unknown' else 23)
        assert chunks[-1].finish_reason==('MAX_TOKENS' if scenario=='truncated' else 'STOP')
    assert len(calls)==(1 if scenario=='too_large' else 2)
