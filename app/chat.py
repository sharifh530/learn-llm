"""Saved turns, selected reply variants, bounded context, and durable streaming."""
import hashlib
import json
import re
import threading
import time
from uuid import uuid4

from app.demo import reply
from app.providers import AIError, ModelReply

PERSONAS = {
    'guide': ('Curious guide', 'Explain with a tiny everyday example and one check question.'),
    'coach': ('Python coach', 'Use short Python examples when useful. Explain each step.'),
    'concise': ('Pocket explainer', 'Prefer three concise sentences unless the user requests another format.'),
}
BASE = ('You are Tiny Chat Lab, a friendly chatbot for a basic Python learner. '
        'Use the supplied conversation when relevant; omitted history is unavailable. '
        'Admit uncertainty. Do not claim to execute code, access other chats, or train yourself. '
        'Persona controls style, not factual correctness or permissions. ')


class ChatService:
    def __init__(self, database, ai):
        self.database, self.ai = database, ai
        self.jobs, self.lock = {}, threading.Lock()
        with database.connection() as connection:
            connection.execute("UPDATE generations SET status='interrupted',error='Server restarted; partial reply saved.',error_code='interrupted' WHERE status='running'")

    def list(self, mode, archived=False):
        with self.database.connection() as connection:
            return [dict(row) for row in connection.execute('SELECT * FROM chats WHERE mode=? AND archived=? ORDER BY updated_at DESC', (mode, int(archived)))]

    def create(self, body):
        identity, now = str(uuid4()), time.time()
        with self.database.connection() as connection:
            if connection.execute('SELECT COUNT(*) FROM chats').fetchone()[0] >= 200:
                raise AIError('storage_limit', 'The local chat limit (200) is reached.', 409)
            connection.execute('INSERT INTO chats(id,title,mode,persona,created_at,updated_at) VALUES(?,?,?,?,?,?)',
                               (identity, 'New experiment', body.mode, body.persona, now, now))
        return self.get(identity)

    def require(self, connection, chat_id):
        row = connection.execute('SELECT * FROM chats WHERE id=?', (chat_id,)).fetchone()
        if not row:
            raise AIError('missing', 'That saved chat was not found.', 404)
        return dict(row)

    def get(self, chat_id):
        with self.database.connection() as connection:
            chat = self.require(connection, chat_id)
            turns = [dict(row) for row in connection.execute('SELECT * FROM chat_turns WHERE chat_id=? ORDER BY created_at,id', (chat_id,))]
            for turn in turns:
                turn['variants'] = [dict(row) for row in connection.execute('SELECT * FROM generations WHERE turn_id=? ORDER BY created_at,id', (turn['id'],))]
                for variant in turn['variants']:
                    variant['context'] = json.loads(variant.pop('context_json'))
                    variant.pop('payload_hash')
        return {**chat, 'turns': turns}

    def generation(self, identity):
        with self.database.connection() as connection:
            row = connection.execute('SELECT g.*,t.chat_id FROM generations g JOIN chat_turns t ON t.id=g.turn_id WHERE g.id=?', (identity,)).fetchone()
            if not row:
                raise AIError('missing', 'That reply was not found.', 404)
            result = dict(row)
        result['context'] = json.loads(result.pop('context_json'))
        result.pop('payload_hash')
        return result

    def writable(self, connection, chat_id):
        chat = self.require(connection, chat_id)
        if chat['archived']:
            raise AIError('archived', 'Restore this chat before changing it.', 409)
        if connection.execute("SELECT COUNT(*) FROM generations g JOIN chat_turns t ON t.id=g.turn_id WHERE t.chat_id=? AND g.status='running'", (chat_id,)).fetchone()[0]:
            raise AIError('busy', 'This chat already has a running reply. Stop or wait first.', 409)
        return chat

    def update(self, chat_id, body):
        with self.lock, self.database.connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            self.writable(connection, chat_id)
            connection.execute('UPDATE chats SET title=?,persona=?,updated_at=? WHERE id=?', (body.title,body.persona,time.time(),chat_id))
        return self.get(chat_id)

    def archive(self, chat_id, archived):
        with self.lock, self.database.connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            self.require(connection, chat_id)
            if archived:
                self.writable(connection, chat_id)
            connection.execute('UPDATE chats SET archived=?,updated_at=? WHERE id=?', (int(archived),time.time(),chat_id))
        return self.get(chat_id)

    def context(self, chat_id, message='', before=None):
        chat = self.get(chat_id)
        instruction = BASE + PERSONAS[chat['persona']][1]
        eligible = []
        for turn in chat['turns']:
            if turn['id']==before:
                break
            selected = next((item for item in turn['variants'] if item['id']==turn['selected_id']), None)
            if selected:
                eligible.append((turn, selected))
        # A byte count is a conservative selection heuristic, NOT a tokenizer.
        # The provider performs an actual count before any live generation.
        size = len((instruction+message).encode('utf-8')) + 64
        chosen = []
        for turn, selected in reversed(eligible):
            cost = len((turn['user_text']+selected['text']).encode('utf-8')) + 64
            if len(chosen)>=10 or size+cost>12000:
                break
            chosen.insert(0, (turn, selected)); size += cost
        messages = []
        for turn, selected in chosen:
            messages.extend([{'role':'user','text':turn['user_text']}, {'role':'assistant','text':selected['text']}])
        if message:
            messages.append({'role':'user','text':message})
        return {'instruction':instruction,'messages':messages,'included_turn_ids':[turn['id'] for turn,_ in chosen],
                'omitted_turns':len(eligible)-len(chosen),'selection_bytes':size,
                'selection_label':'UTF-8 byte heuristic, not an actual token count',
                'input_token_limit':12000,'output_token_limit':2048,'persona':chat['persona']}

    def start(self, chat_id, body, retry_turn=None):
        identity = body.request_id
        payload = {'chat_id':chat_id,'message':getattr(body,'message',None),'retry_turn':retry_turn}
        digest = hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
        # Lock makes context construction and turn creation atomic for this single-process app.
        with self.lock:
            with self.database.connection() as connection:
                previous = connection.execute('SELECT * FROM generations WHERE id=?', (identity,)).fetchone()
                if previous:
                    if previous['payload_hash']!=digest:
                        raise AIError('conflict','That request ID belongs to another chat operation.',409)
                    return self.generation(identity)
                chat = self.writable(connection, chat_id)
                turns = connection.execute('SELECT * FROM chat_turns WHERE chat_id=? ORDER BY created_at,id', (chat_id,)).fetchall()
                if retry_turn:
                    if not turns or turns[-1]['id']!=retry_turn:
                        raise AIError('branch','Only the latest turn can be retried. Start a new chat for a different branch.',409)
                    turn_id, message = retry_turn, turns[-1]['user_text']
                    count = connection.execute('SELECT COUNT(*) FROM generations WHERE turn_id=?', (turn_id,)).fetchone()[0]
                    if count>=5:
                        raise AIError('variants','This turn has five attempts. Start a new chat.',409)
                else:
                    if len(turns)>=100:
                        raise AIError('storage_limit','This chat has 100 turns. Start a new experiment.',409)
                    if turns and not turns[-1]['selected_id']:
                        raise AIError('unresolved','Retry the latest reply or explicitly use its partial text before continuing.',409)
                    turn_id, message = str(uuid4()), body.message
            context = self.context(chat_id, message, retry_turn)
            if chat['mode']=='google_cloud' and (problem:=self.ai.settings.problem()):
                raise AIError('configuration',problem)
            with self.database.connection() as connection:
                connection.execute('BEGIN IMMEDIATE')
                self.writable(connection,chat_id)
                if chat['mode']=='google_cloud':
                    prior = self.ai.reserve(connection,identity,digest,'saved_chat')
                    if prior:
                        raise AIError('conflict','That request ID was already used by another AI operation.',409)
                elif connection.execute('SELECT 1 FROM ai_requests WHERE request_id=?',(identity,)).fetchone():
                    raise AIError('conflict','That request ID was already used.',409)
                if not retry_turn:
                    connection.execute('INSERT INTO chat_turns(id,chat_id,user_text,created_at) VALUES(?,?,?,?)',(turn_id,chat_id,message,time.time()))
                    if not turns and chat['title']=='New experiment':
                        connection.execute('UPDATE chats SET title=? WHERE id=?',(message[:60],chat_id))
                connection.execute('INSERT INTO generations(id,turn_id,payload_hash,context_json,status,created_at) VALUES(?,?,?,?,?,?)',
                                   (identity,turn_id,digest,json.dumps(context),'running',time.time()))
                connection.execute('UPDATE chats SET updated_at=? WHERE id=?',(time.time(),chat_id))
            stop = threading.Event()
            self.jobs[identity] = stop
            threading.Thread(target=self.run,args=(identity,chat['mode'],context,stop),daemon=True,name='chat-generation').start()
        return self.generation(identity)

    def demo_stream(self, context, stop):
        messages = context['messages']
        question = messages[-1]['text']
        previous = [item['text'] for item in messages[:-1] if item['role']=='user']
        if re.search(r'(earlier|remember|favorite|favourite)',question,re.I) and previous:
            text = 'Demo memory rule: your earlier message was “'+previous[-1]+'”. This is a Python lookup, not a model.'
        else:
            text = reply(question)
        text = 'Demo · '+PERSONAS[context['persona']][0]+': '+text
        for offset in range(0,len(text),14):
            if stop.wait(.045):
                return
            yield ModelReply(text[offset:offset+14])
        yield ModelReply('',0,0,0,'STOP')

    def run(self, identity, mode, context, stop):
        text, usage, reason, error = '', (None,None,None), None, None
        started = time.monotonic()
        def cancelled():
            if time.monotonic()-started>90:
                raise AIError('timeout','Reply exceeded this app’s 90-second limit. Partial text saved.',504)
            return stop.is_set()
        def on_call():
            with self.database.connection() as connection:
                connection.execute('UPDATE ai_requests SET provider_calls=provider_calls+1 WHERE request_id=?',(identity,))
        stream = None
        try:
            stream = self.demo_stream(context,stop) if mode=='demo' else self.ai.provider.stream(
                     context['instruction'],context['messages'],12000,2048,on_call,cancelled)
            for chunk in stream:
                if cancelled():
                    break
                if chunk.total_tokens is not None or chunk.input_tokens is not None or chunk.output_tokens is not None:
                    usage = (chunk.input_tokens,chunk.output_tokens,chunk.total_tokens)
                if chunk.finish_reason:
                    reason = chunk.finish_reason
                combined = text + chunk.text
                text = combined[:16000]
                if len(combined)>16000:
                    raise AIError('output_limit','Reply reached the app’s text limit. Partial text saved.',413)
                with self.database.connection() as connection:
                    connection.execute("UPDATE generations SET text=?,input_tokens=?,output_tokens=?,total_tokens=?,finish_reason=? WHERE id=? AND status='running'",(text,*usage,reason,identity))
            if not stop.is_set() and not text.strip():
                raise AIError('empty','No usable reply was returned. Your question is saved.',422,usage)
        except Exception as failure:
            error = failure if isinstance(failure,AIError) else AIError('unavailable','This reply failed. Your question and partial text are saved.')
            if error.usage:
                usage = error.usage
        finally:
            if stream is not None and hasattr(stream,'close'):
                try:
                    stream.close()
                except Exception:
                    pass
            status = 'stopped' if stop.is_set() else ('blocked' if error and error.code=='blocked' else 'failed' if error else 'truncated' if reason=='MAX_TOKENS' else 'complete')
            with self.database.connection() as connection:
                # Stop is committed immediately; late chunks cannot change it.
                if status=='blocked':
                    text = ''
                connection.execute("UPDATE generations SET status=?,text=?,error=?,error_code=?,input_tokens=?,output_tokens=?,total_tokens=?,finish_reason=? WHERE id=? AND status='running'",
                    (status,text,str(error) if error else None,error.code if error else None,*usage,reason,identity))
                generation = connection.execute('SELECT * FROM generations WHERE id=?',(identity,)).fetchone()
                if generation['status']=='complete':
                    connection.execute('UPDATE chat_turns SET selected_id=? WHERE id=? AND selected_id IS NULL',(identity,generation['turn_id']))
                connection.execute('UPDATE ai_requests SET status=?,error_code=?,input_tokens=?,output_tokens=?,total_tokens=? WHERE request_id=?',
                    ('succeeded' if generation['status']=='complete' else generation['status'],error.code if error else None,*usage,identity))
            if mode=='google_cloud' and status=='complete':
                self.ai.connected = True
            with self.lock:
                self.jobs.pop(identity,None)

    def cancel(self, identity):
        with self.lock:
            with self.database.connection() as connection:
                connection.execute('BEGIN IMMEDIATE')
                row = connection.execute('SELECT * FROM generations WHERE id=?',(identity,)).fetchone()
                if not row:
                    raise AIError('missing','That reply was not found.',404)
                if row['status']=='running':
                    if event:=self.jobs.get(identity):
                        event.set()
                    connection.execute("UPDATE generations SET status='stopped',error='Stopped. Partial text saved; usage may be unknown.',error_code='stopped' WHERE id=?",(identity,))
        return self.generation(identity)

    def select(self, chat_id, turn_id, body):
        with self.lock, self.database.connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            self.writable(connection,chat_id)
            latest = connection.execute('SELECT id FROM chat_turns WHERE chat_id=? ORDER BY created_at DESC,id DESC LIMIT 1',(chat_id,)).fetchone()
            row = connection.execute('SELECT * FROM generations WHERE id=? AND turn_id=?',(body.generation_id,turn_id)).fetchone()
            if not latest or latest['id']!=turn_id or not row:
                raise AIError('branch','Only replies to the latest turn can be selected.',409)
            allowed = row['status']=='complete' or (body.include_partial and row['status'] in ('stopped','failed','interrupted','truncated') and row['text'].strip())
            if not allowed:
                raise AIError('partial','Select a complete reply, or explicitly include a saved partial reply.',409)
            connection.execute('UPDATE chat_turns SET selected_id=? WHERE id=?',(row['id'],turn_id))
        return self.get(chat_id)

    def events(self, identity):
        self.generation(identity)
        previous = None
        while True:
            current = self.generation(identity)
            value = json.dumps(current)
            if value!=previous:
                # Full snapshots make reconnects lossless, with no delta offset ambiguity.
                event = 'snapshot' if current['status']=='running' else 'done'
                yield f'event: {event}\ndata: {value}\n\n'
                previous = value
            if current['status']!='running':
                break
            time.sleep(.12)
