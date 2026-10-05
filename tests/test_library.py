"""M5 evidence boundaries, retrieval limits, and shared paid-request policy."""
import json
from pathlib import Path
import shutil
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import AISettings
from app.content import ContentError, ContentStore
from app.main import create_app
from app.models import LibrarySearch
from app.providers import ModelReply
from app.library import chunks, LibraryService


class EvidenceProvider:
    def __init__(self):
        self.calls=[]
        self.corrupt=None
        self.finish='STOP'

    def generate(self,instruction,message,input_limit,output_limit,on_call):
        data=json.loads(message)
        self.calls.append((instruction,data,input_limit,output_limit))
        on_call();on_call()
        evidence=[{'source_id':note['source_id'],'quote':note['text']} for note in data['notes'][:2]]
        reply={'insufficient':False,'evidence':evidence}
        if self.corrupt:
            reply=self.corrupt(reply)
        return ModelReply(json.dumps(reply),30,20,50,self.finish)


@pytest.fixture
def lab(tmp_path):
    provider=EvidenceProvider()
    app=create_app(tmp_path/'test.db',ai_settings=AISettings(enabled=True,api_key='fake-secret-m5',model='fake-model'),provider=provider)
    with TestClient(app) as client:
        yield client,app,provider


def question(message='Which drinks contain mango?',mode='demo',**extra):
    return {'message':message,'mode':mode,'request_id':str(uuid4()),**extra}


def test_retrieval_quotes_provenance_and_zero_paid_side_effects(lab):
    client,app,fake=lab
    catalog=client.get('/api/library').json()
    ids={chunk['source_id'] for note in catalog['notes'] for chunk in note['chunks']}
    assert len(ids)==9 and len(catalog['notes'])==4
    search=client.post('/api/library/search',json={'message':'Which drinks contain mango?'}).json()
    assert search['query_terms']==['drink','mango']
    assert search['total_matches']==3 and len(search['chunks'])==3
    assert all(chunk['score']==2 and chunk['matched']==['drink','mango'] for chunk in search['chunks'])
    # The negative statement matches too: expose the baseline honestly.
    assert 'no mango' in search['chunks'][-1]['text']
    response=client.post('/api/library/answers',json=question())
    data=response.json()
    assert data['mode']=='demo' and data['provider_calls']==0
    assert {item['source_id'] for item in data['evidence']}<=ids
    assert all(item['quote']==item['text'] for item in data['evidence'])
    assert not fake.calls and app.state.ai.usage()['attempts']==0
    assert client.get('/api/progress').json()['xp']==0
    assert client.get('/api/chats').json()==[]
    assert response.headers['cache-control']=='no-store'


def test_missing_evidence_filter_synonyms_and_empty_query(lab):
    client,_,fake=lab
    for mode in ('demo','google_cloud'):
        for message in ('Who owns the caf\u00e9?','Quantum zebras','the cafe','Fruit smoothie'):
            data=client.post('/api/library/answers',json=question(message,mode)).json()
            assert data['insufficient'] and not data['evidence'] and data['provider_calls']==0
    filtered=client.post('/api/library/search',json={'message':'Saturday','note_id':'N01'}).json()
    assert not filtered['chunks']
    all_notes=client.post('/api/library/search',json={'message':'When does the cafe close on Saturday?'}).json()
    assert all_notes['chunks'][0]['note_id']=='N02'
    assert all_notes['chunks'][0]['score']==2
    assert not fake.calls


def test_chunk_preview_preserves_words_and_paragraphs_without_saving(lab):
    client,_,fake=lab
    text=' '.join(f'word{i}' for i in range(25))+'\n\nSeparate paragraph.'
    data=client.post('/api/library/chunks',json={'text':text,'words':10}).json()
    assert [item['word_count'] for item in data['chunks']]==[10,10,5,2]
    assert ' '.join(item['text'] for item in data['chunks'])==' '.join(text.split())
    assert len({item['source_id'] for item in data['chunks']})==4
    assert data['saved'] is False and not fake.calls
    assert text not in client.get('/api/library').text


def test_checked_google_context_usage_caching_and_restart(lab):
    client,app,fake=lab
    request=question(mode='google_cloud')
    response=client.post('/api/library/answers',json=request).json()
    assert response['mode']=='google_cloud' and len(response['evidence'])==2
    assert response['usage']['total_tokens']==50 and not response['truncated']
    instruction,data,input_limit,output_limit=fake.calls[0]
    assert 'untrusted data' in instruction and len(data['notes'])==3
    assert set(data)=={'question','library_fingerprint','notes'}
    assert 'fake-secret-m5' not in json.dumps(data) and 'tutor' not in data
    assert (input_limit,output_limit)==(12000,2048)
    assert client.post('/api/library/answers',json=request).json()['cached']
    assert len(fake.calls)==1
    other=create_app(app.state.database.path,ai_settings=app.state.ai.settings,provider=fake)
    with TestClient(other) as second:
        assert second.post('/api/library/answers',json=request).json()['cached']
        assert second.get('/api/provider/status').json()['usage']['attempts']==1
    assert len(fake.calls)==1
    assert client.post('/api/library/answers',json={**request,'message':'mango price'}).status_code==409


@pytest.mark.parametrize('corrupt',[
    lambda result:{**result,'evidence':[{'source_id':'invented','quote':'fiction'}]},
    lambda result:{**result,'evidence':[{'source_id':result['evidence'][0]['source_id'],'quote':'Mango Cloud costs 40 coins.'}]},
    lambda result:{**result,'evidence':[{'source_id':'N02-v1-p1-1','quote':"On weekdays, Pip's caf\u00e9 opens at 09:00 and closes at 17:00."}]},
    lambda result:{**result,'evidence':[result['evidence'][0],result['evidence'][0]]},
    lambda result:{**result,'reply':'Untrusted free-form claim'},
    lambda result:{**result,'insufficient':True},
    lambda result:[],
])
def test_invalid_model_evidence_is_withheld_and_consumes_attempt(lab,corrupt):
    client,app,fake=lab
    fake.corrupt=corrupt
    request=question(mode='google_cloud')
    response=client.post('/api/library/answers',json=request)
    assert response.status_code==422 and response.json()['code']=='evidence'
    assert 'fake-secret-m5' not in response.text and '40 coins' not in response.text
    assert app.state.ai.usage()['reported_total_tokens']==50
    assert app.state.ai.usage()['provider_calls']==2
    assert client.post('/api/library/answers',json=request).status_code==409
    assert len(fake.calls)==1
    with app.state.database.connection() as connection:
        row=connection.execute('SELECT status,response FROM ai_requests WHERE request_id=?',(request['request_id'],)).fetchone()
        assert row['status']=='failed' and row['response'] is None


def test_insufficient_and_truncated_google_response(lab):
    client,app,fake=lab
    fake.corrupt=lambda result:{'insufficient':True,'evidence':[]}
    reply=client.post('/api/library/answers',json=question('Who invented mango drinks?',mode='google_cloud')).json()
    assert reply['insufficient'] and not reply['evidence']
    assert reply['mode']=='google_cloud' and reply['usage']['total_tokens']==50
    fake.corrupt=None;fake.finish='MAX_TOKENS'
    assert client.post('/api/library/answers',json=question(mode='google_cloud')).status_code==422
    assert app.state.ai.usage()['reported_total_tokens']==100


def test_library_validation_origin_and_disabled_ai(tmp_path):
    app=create_app(tmp_path/'disabled.db',ai_settings=AISettings())
    with TestClient(app) as client:
        assert client.get('/library').status_code==200
        for body in ({'message':''},{'message':'mango','extra':'ignored?'},{'message':'x'*4001},{'message':'mango','note_id':'N99'}):
            assert client.post('/api/library/search',json=body).status_code==422
        for body in ({'text':'a','words':True},{'text':'a','words':9},{'text':'a','words':81},{'text':' '*5,'words':30}):
            assert client.post('/api/library/chunks',json=body).status_code==422
        assert client.post('/api/library/answers',json=question(mode='google_cloud')).status_code==503
        assert client.post('/api/library/answers',json=question()).status_code==200
        assert client.post('/api/library/answers',json=question(),headers={'Origin':'https://foreign.example'}).status_code==403


def test_library_reload_is_atomic_and_attempt_context_is_revision_bound(lab,tmp_path):
    client,app,fake=lab
    request=question(mode='google_cloud')
    assert client.post('/api/library/answers',json=request).status_code==200
    # Same paid attempt must not be reinterpreted after a content change.
    app.state.content.library['notes'][0]['text']+='\n\nNew mango drink.'
    app.state.content.library['notes'][0]['version']+=1
    assert client.post('/api/library/answers',json=request).status_code==409
    assert len(fake.calls)==1
    root=Path(__file__).resolve().parents[1]
    shutil.copytree(root/'content',tmp_path/'content')
    store=ContentStore(tmp_path/'content')
    original=store.library
    path=tmp_path/'content/library.json'
    data=json.loads(path.read_text(encoding='utf-8'))
    data['notes'][1]['id']=data['notes'][0]['id']
    path.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(ContentError):store.reload()
    assert store.library is original


def test_google_library_uses_global_quota(lab):
    client,app,fake=lab
    for _ in range(8):assert client.post('/api/library/answers',json=question(mode='google_cloud')).status_code==200
    response=client.post('/api/library/answers',json=question(mode='google_cloud'))
    assert response.status_code==429 and response.json()['code']=='limit'
    assert client.post('/api/provider/test',json={'request_id':str(uuid4())}).status_code==429
    assert len(fake.calls)==8
