import {api, aiCall, node, readTab, writeTab} from './common.js';
const messages=document.querySelector('#chat-messages'), input=document.querySelector('#chat-input'), form=document.querySelector('#chat-form');
const send=document.querySelector('#chat-send'), stop=document.querySelector('#chat-stop'), status=document.querySelector('#chat-status');
const mode=document.querySelector('#chat-mode'), picker=document.querySelector('#saved-chats'), archiveFilter=document.querySelector('#show-archived');
let chat=null, running=null, busy=false, serial=0;
const narrow=matchMedia('(max-width:760px)'),library=document.querySelector('.chat-library');
const adaptLibrary=()=>{library.open=!narrow.matches;};adaptLibrary();narrow.addEventListener('change',adaptLibrary);
const draftKey=()=>`tiny-chat-saved-${chat?.id}-draft`;
const activeKey=()=>`tiny-chat-active-${mode.value}`;
function controls(value) {
  busy=value;
  [send,mode,picker,archiveFilter,document.querySelector('#clear-chat'),document.querySelector('#save-chat-settings'),document.querySelector('#archive-chat')].forEach(item=>item.disabled=value||Boolean(chat?.archived&&item===send));
  stop.hidden=!running;stop.disabled=!running;input.disabled=value||Boolean(chat?.archived);
}
function message(role,text,label) {
  const article=node('article',`chat-message ${role}`);
  article.append(node('span','message-label',label),node('p','',text));messages.append(article);return article;
}
function action(label,handler) {
  const button=node('button','variant-button',label);button.type='button';
  button.addEventListener('click',async()=>{try {await handler();} catch(error) {status.textContent=error.message;}});return button;
}
function render() {
  messages.replaceChildren();
  if (!chat.turns.length) message('assistant',mode.value==='demo'?'Hello, builder! This saved chat uses Python rules, not an LLM. Try “My favorite fruit is mango”, then “What was my favorite fruit?”':'Your selected conversation and persona will be sent to Google. Calls may incur charges. Try a small follow-up experiment.',mode.value==='demo'?'Demo bot · Python rules':'Google mode');
  chat.turns.forEach((turn,index)=>{
    message('user',turn.user_text,'You');
    turn.variants.forEach((variant,variantIndex)=>{
      const article=message('assistant',variant.text||(variant.status==='running'?'Waiting for the first chunk…':'No reply text'),mode.value==='demo'?'Demo bot · Python rules':'Google AI');article.dataset.generation=variant.id;
      article.append(node('span','variant-state',`Reply ${variantIndex+1} · ${variant.status}${turn.selected_id===variant.id?' · Used in context':''}${variant.finish_reason==='MAX_TOKENS'?' · Output limit reached':''}`));
      if (variant.error) article.append(node('span','variant-error',variant.error));
      const actions=node('div','variant-actions');actions.append(action('Inspect sent context',()=>showContext(variant.context,'Context saved with this attempt')));
      if (index===chat.turns.length-1&&!chat.archived&&!running) {
        if (turn.selected_id!==variant.id&&(variant.status==='complete'||['stopped','failed','interrupted','truncated'].includes(variant.status)&&variant.text)) actions.append(action(variant.status==='complete'?'Use this reply':'Use partial reply',async()=>{
          chat=await api(`/api/chats/${chat.id}/turns/${turn.id}/select`,{generation_id:variant.id,include_partial:variant.status!=='complete'});render();status.textContent='Context selection saved. Partial text can be incomplete or wrong.';
        }));
        if (variantIndex===turn.variants.length-1&&turn.variants.length<5) actions.append(action(mode.value==='demo'?'Try another demo reply':'Try another reply · new Google attempt',()=>attempt(`/api/chats/${chat.id}/turns/${turn.id}/retry`,{})));
      }
      article.append(actions);
    });
  });
  messages.scrollTop=messages.scrollHeight;
  document.querySelector('#chat-title').value=chat.title;document.querySelector('#chat-persona').value=chat.persona;
  document.querySelector('#chat-heading').textContent=chat.title;
  document.querySelector('#chat-subtitle').textContent=mode.value==='demo'?'Saved Python demo · zero Google calls':'Saved Google chat · selected conversation context';
  document.querySelector('#chat-mode-label').textContent=mode.value==='demo'?'Demo: no model connected':'Google mode · Calls may incur charges';
  document.querySelector('#chat-mode-help').textContent=mode.value==='demo'?'Local rules, with a small memory lookup. Persona labels illustrate style; no model is running.':'Live streams through your Python server. Stop saves partial text; it cannot guarantee that Google billing stops immediately.';
  document.querySelector('#archive-chat').textContent=chat.archived?'Restore this chat':'Archive this chat';controls(Boolean(running));
}
function showContext(context,label) {
  document.querySelector('#context-inspector').open=true;
  document.querySelector('#context-caption').textContent=`${label} · ${context.messages.length} messages · ${context.omitted_turns} earlier turns omitted · ${context.selection_bytes} selection bytes. ${context.selection_label}. Live input limit ${context.input_token_limit}; output limit ${context.output_token_limit} tokens.`;
  const target=document.querySelector('#context-messages');target.replaceChildren();
  const section=(role,text)=>{const row=node('div','context-entry');row.append(node('strong','',role),node('pre','',text));target.append(row);};
  section('System instruction',context.instruction);context.messages.forEach(item=>section(item.role,item.text));
}
async function refreshList(preferred) {
  const rows=await api(`/api/chats?mode=${mode.value}&archived=${archiveFilter.checked}`);picker.replaceChildren();
  rows.forEach(row=>{const option=node('option','',row.title);option.value=row.id;picker.append(option);});
  const chosen=rows.find(row=>row.id===preferred)||rows[0];
  if (!chosen) {
    if (archiveFilter.checked) {archiveFilter.checked=false;return refreshList(readTab(activeKey()));}
    chat=await api('/api/chats',{mode:mode.value,persona:'guide'});return refreshList(chat.id);
  }
  picker.value=chosen.id;await load(chosen.id);
}
async function load(id) {
  const token=++serial;chat=await api(`/api/chats/${id}`);writeTab(activeKey(),id);input.value=readTab(draftKey());
  running=chat.turns.flatMap(turn=>turn.variants).find(item=>item.status==='running')?.id||null;render();
  status.textContent=chat.archived?'Archived chat · Restore to continue':'Enter to send · Shift + Enter for a new line';
  if (running) await follow(running,token);
}
async function follow(id,token=serial) {
  running=id;controls(true);status.textContent='Replying… Partial text is saved. You can stop or refresh safely.';
  try {
    const response=await fetch(`/api/generations/${id}/events`);
    if (!response.ok||!response.body) throw new Error('The reply stream could not be opened. Refresh to recover the saved attempt.');
    const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='',final=null;
    while (true) {
      const {value,done}=await reader.read();buffer+=decoder.decode(value||new Uint8Array(),{stream:!done});let boundary;
      while ((boundary=buffer.indexOf('\n\n'))>=0) {
        const frame=buffer.slice(0,boundary);buffer=buffer.slice(boundary+2);
        const line=frame.split('\n').find(item=>item.startsWith('data: '));if (!line) continue;
        const generation=JSON.parse(line.slice(6));if (token!==serial) {await reader.cancel();return;}
        const paragraph=messages.querySelector(`[data-generation="${CSS.escape(id)}"] p`);
        const nearBottom=messages.scrollHeight-messages.scrollTop-messages.clientHeight<90;
        if (paragraph) paragraph.textContent=generation.text||'Waiting for the first chunk…';
        if (nearBottom) messages.scrollTop=messages.scrollHeight;if (generation.status!=='running') final=generation;
      }
      if (done) break;
    }
    if (!final) throw new Error('The stream disconnected. Refresh to recover the saved reply; do not start another attempt just to reconnect.');
    running=null;chat=await api(`/api/chats/${chat.id}`);render();const total=final.total_tokens??'unknown';
    status.textContent=final.status==='complete'?`${mode.value==='demo'?'Demo reply received · zero Google calls':'Google reply received · '+total+' reported tokens · Cost unknown'}${final.finish_reason==='MAX_TOKENS'?' · Output limit reached; reply may be incomplete':''}`:(final.error||`${final.status} · Partial text saved. Retry or choose a reply explicitly.`);
    if (final.status==='complete') {input.value='';writeTab(draftKey(),'');}
    await updatePicker();input.focus({preventScroll:true});
  } catch(error) {status.textContent=error.message;document.querySelector('#recover-stream').hidden=false;send.disabled=true;stop.disabled=false;}
}
async function updatePicker() {
  const rows=await api(`/api/chats?mode=${mode.value}&archived=${archiveFilter.checked}`);picker.replaceChildren();rows.forEach(row=>{const option=node('option','',row.title);option.value=row.id;picker.append(option);});picker.value=chat.id;
}
async function attempt(path,body) {
  if (busy) return;controls(true);status.textContent=mode.value==='demo'?'Starting a Python demo…':'Starting a Google attempt…';
  try {const generation=await aiCall(path,body);chat=await api(`/api/chats/${chat.id}`);running=generation.status==='running'?generation.id:null;render();await follow(generation.id);}
  catch(error) {status.textContent=error.message;running=null;controls(false);}
}
form.addEventListener('submit',async event=>{
  event.preventDefault();const text=input.value.trim();if (!text||busy) return;writeTab(draftKey(),input.value);
  const latest=chat.turns.at(-1),retry=latest&&!latest.selected_id&&latest.user_text===text;
  await attempt(retry?`/api/chats/${chat.id}/turns/${latest.id}/retry`:`/api/chats/${chat.id}/messages`,retry?{}:{message:text});
});
input.addEventListener('input',()=>writeTab(draftKey(),input.value));
input.addEventListener('keydown',event=>{if (event.key==='Enter'&&!event.shiftKey&&!event.isComposing) {event.preventDefault();form.requestSubmit();}});
stop.addEventListener('click',async()=>{if (!running) return;try {await api(`/api/generations/${running}/cancel`,{});} catch(error) {status.textContent=error.message;}});
document.querySelector('#recover-stream').addEventListener('click',async()=>{document.querySelector('#recover-stream').hidden=true;await load(chat.id);});
const handle=async handler=>{controls(true);try {await handler();} catch(error) {status.textContent=error.message;} finally {if (!running) controls(false);}};
mode.value=readTab('tiny-chat-saved-mode','demo');if (!['demo','google_cloud'].includes(mode.value)) mode.value='demo';
mode.addEventListener('change',()=>handle(async()=>{writeTab('tiny-chat-saved-mode',mode.value);archiveFilter.checked=false;await refreshList(readTab(activeKey()));}));
picker.addEventListener('change',()=>handle(()=>load(picker.value)));archiveFilter.addEventListener('change',()=>handle(()=>refreshList()));
document.querySelector('#clear-chat').addEventListener('click',()=>handle(async()=>{archiveFilter.checked=false;chat=await api('/api/chats',{mode:mode.value,persona:document.querySelector('#chat-persona').value});await refreshList(chat.id);}));
document.querySelector('#chat-settings').addEventListener('submit',event=>{event.preventDefault();handle(async()=>{chat=await api(`/api/chats/${chat.id}/settings`,{title:document.querySelector('#chat-title').value,persona:document.querySelector('#chat-persona').value});render();await updatePicker();status.textContent='Title and persona saved. New replies use this persona; earlier attempts keep their context snapshots.';});});
document.querySelector('#archive-chat').addEventListener('click',()=>handle(async()=>{await api(`/api/chats/${chat.id}/${chat.archived?'restore':'archive'}`,{});archiveFilter.checked=false;await refreshList();status.textContent='Chat moved. Archived chats can be restored; no conversation was deleted.';}));
document.querySelector('#preview-context').addEventListener('click',()=>handle(async()=>showContext(await api(`/api/chats/${chat.id}/context`,{message:input.value.trim()}),'Preview for the current draft')));
document.querySelectorAll('[data-chat-prompt]').forEach(button=>button.addEventListener('click',()=>{if (busy) return;input.value=button.dataset.chatPrompt;writeTab(draftKey(),input.value);form.requestSubmit();}));
controls(true);handle(()=>refreshList(readTab(activeKey())));
