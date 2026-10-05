import {api,aiCall,node,readTab,writeTab} from './common.js';
const form=document.querySelector('#library-form'), question=document.querySelector('#library-question');
const mode=document.querySelector('#library-mode'), note=document.querySelector('#library-note');
const status=document.querySelector('#library-status'), search=document.querySelector('#library-search'), answer=document.querySelector('#library-answer');
const panel=document.querySelector('#library-answer-panel'), inspector=document.querySelector('#retrieval-inspector');
const draftKey='tiny-chat-library-question';
question.value=readTab(draftKey);
question.addEventListener('input',()=>{writeTab(draftKey,question.value);panel.hidden=true;});
const controls=[question,mode,note,search,answer,...document.querySelectorAll('[data-library-question]')];
function busy(value){controls.forEach(control=>control.disabled=value);form.setAttribute('aria-busy',String(value));}
function modeHelp(){
  const google=mode.value==='google_cloud';
  answer.textContent=google?'Ask Google ↗':'Show evidence';
  document.querySelector('#library-mode-help').textContent=google?'Explicitly sends your question and up to three café chunks to Google. Calls may incur charges. Exact quotes and source IDs are checked before display.':'Python keyword search and exact quotes. Zero Google calls; this is a retrieval rehearsal.';
  panel.hidden=true;
}
mode.addEventListener('change',modeHelp);note.addEventListener('change',()=>{panel.hidden=true;document.querySelector('#retrieval-results').replaceChildren();});
function sourceLink(chunk){
  const link=node('a','',`${chunk.title} · ${chunk.source_id}`);link.href=`#source-${chunk.source_id}`;
  link.addEventListener('click',()=>{const target=document.getElementById(`source-${chunk.source_id}`);if(target){target.closest('details').open=true;target.focus({preventScroll:true});}});
  return link;
}
function trace(data){
  document.querySelector('#retrieval-terms').textContent=`Search words: ${data.query_terms.join(', ')||'(none after common words are removed)'} · ${data.total_matches} positive matches; showing ${data.chunks.length}.`;
  const target=document.querySelector('#retrieval-results');target.replaceChildren();
  data.chunks.forEach(chunk=>{const article=node('article','retrieved-clue');article.append(sourceLink(chunk),node('p','',chunk.text),node('p','small muted',`Score ${chunk.score} · matched: ${chunk.matched.join(', ')}`));target.append(article);});
  if(!data.chunks.length)target.append(node('p','muted','No matching clues. Try a different question or a broader note selection.'));
}
async function ask(preview){
  if(!form.reportValidity())return;
  const body={message:question.value.trim(),note_id:note.value};writeTab(draftKey,question.value);
  busy(true);panel.hidden=true;status.dataset.error='false';status.textContent=preview?'Looking through the café notes…':(mode.value==='demo'?'Finding matching quotes…':'Asking Google to select evidence…');
  try{
    const result=preview?await api('/api/library/search',body):await aiCall('/api/library/answers',{...body,mode:mode.value});
    trace(preview?result:result.retrieval);
    if(preview){inspector.open=true;status.textContent='Clues found using Python. No Google request was made.';}
    else{
      const target=document.querySelector('#library-evidence');target.replaceChildren();
      document.querySelector('#evidence-heading').textContent=result.insufficient?'A useful “I don’t know.”':(result.mode==='demo'?'Matching clues, not an AI answer':'Google-selected evidence');
      document.querySelector('#library-reply').textContent=result.insufficient||result.mode==='demo'?result.reply:'These exact passages were selected from the retrieved notes. Read their conditions and decide whether they answer your question.';
      result.evidence.forEach(chunk=>{const item=node('figure','evidence-quote');item.append(node('blockquote','',chunk.quote),sourceLink(chunk));target.append(item);});
      document.querySelector('#library-usage').textContent=result.mode==='google_cloud'?`${result.cached?'Recovered saved response · ':''}${result.usage.total_tokens??'Unknown'} reported tokens · Cost unknown. Checked quotes are not a guarantee of relevance or truth.`:'Zero Google calls · No model training · No XP awarded here.';
      panel.hidden=false;status.textContent=result.insufficient?'The library cannot support an answer from this search.':(result.mode==='demo'?'Offline evidence ready. Check the notes before trusting the match.':'Source IDs and exact quotes passed the check.');
    }
  }catch(error){status.dataset.error='true';status.textContent=error.message;}
  finally{busy(false);}
}
search.addEventListener('click',()=>ask(true));form.addEventListener('submit',event=>{event.preventDefault();ask(false);});
document.querySelectorAll('[data-library-question]').forEach(button=>button.addEventListener('click',()=>{question.value=button.dataset.libraryQuestion;writeTab(draftKey,question.value);question.focus();panel.hidden=true;}));
const chunkForm=document.querySelector('#chunk-form'),size=document.querySelector('#chunk-size'),chunkStatus=document.querySelector('#chunk-status');
size.addEventListener('input',()=>document.querySelector('#chunk-size-value').value=size.value);
chunkForm.addEventListener('submit',async event=>{
  event.preventDefault();const button=chunkForm.querySelector('button');button.disabled=true;chunkStatus.dataset.error='false';chunkStatus.textContent='Splitting at paragraph boundaries, then at the word limit…';
  try{
    const result=await api('/api/library/chunks',{text:document.querySelector('#chunk-text').value,words:Number(size.value)});
    const target=document.querySelector('#chunk-results');target.replaceChildren();
    result.chunks.forEach(chunk=>{const item=node('article','source-chunk');item.append(node('code','',`${chunk.source_id} · ${chunk.word_count} words`),node('p','',chunk.text));target.append(item);});
    chunkStatus.textContent=`${result.chunks.length} practice pieces. Word limits can cut a sentence; notice what context each piece loses. Nothing was saved.`;
  }catch(error){chunkStatus.dataset.error='true';chunkStatus.textContent=error.message;}
  finally{button.disabled=false;}
});
