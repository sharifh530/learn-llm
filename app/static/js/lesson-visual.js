/* Authored visual traces only. No eval, Python execution, provider call, or XP. */
import {node} from './common.js';

const host = document.querySelector('[data-visual-story]');
if (host) {
  const lesson = JSON.parse(document.querySelector('#lesson-data').textContent);
  const story = lesson.visual;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const play = host.querySelector('#story-play');
  const next = host.querySelector('#story-next');
  const back = host.querySelector('#story-back');
  const pace = host.querySelector('#story-pace');
  const diagram = host.querySelector('#story-diagram');
  const rail = host.querySelector('#story-rail');
  const source = host.querySelector('#example-code');
  const status = host.querySelector('#story-status');
  const panel = document.querySelector('#panel-learn');
  const motionOK = () => !reduced.matches && !document.documentElement.classList.contains('motion-off');
  let index = 0, timer = null, playing = false;
  const lines = [];
  source.replaceChildren();
  // Keep source text byte-for-byte identical for Copy code, including its newline.
  lesson.python_example.code.split('\n').forEach((text, offset, all) => {
    const line = node('span','story-code-line',text);
    line.dataset.line = String(offset + 1);
    line.setAttribute('aria-label',`Line ${offset + 1}: ${text}`);
    source.append(line); lines.push(line);
    if (offset < all.length - 1) source.append(document.createTextNode('\n'));
  });
  const sceneButtons = story.frames.map((frame, offset) => {
    const button = node('button','story-scene-button');
    button.type = 'button'; button.setAttribute('aria-label',`Scene ${offset + 1}: ${frame.title}`);
    button.append(node('span','scene-number',String(offset + 1)),node('span','scene-name',frame.title));
    button.addEventListener('click',() => {stop();render(offset,true);});
    rail.append(button); return button;
  });
  function stop() {
    clearTimeout(timer); timer=null; playing=false;
    play.textContent='Play story';play.setAttribute('aria-pressed','false');
  }
  function showFocusedLine() {
    if (panel.hidden) return;
    // Resizing can wrap earlier lines and move the selected line out of view.
    const pre=source.closest('pre');
    const first=lines[story.frames[index].lines[0]-1];
    pre.scrollTop=Math.max(0,pre.scrollTop+first.getBoundingClientRect().top-pre.getBoundingClientRect().top-45);
  }
  function render(offset, animate=false) {
    index=offset;host.dataset.scene=String(index);
    const frame=story.frames[index];
    host.querySelector('#story-position').textContent=`Scene ${index+1} of ${story.frames.length}`;
    host.querySelector('#story-scene-title').textContent=frame.title;
    host.querySelector('#story-explain').textContent=frame.explain;
    host.querySelector('#story-console').textContent=frame.console||'Nothing printed yet.';
    host.querySelector('#story-line-label').textContent=`Follow Python ${frame.lines.length===1?'line':'lines'} ${frame.lines.join(', ')}. Highlighted lines explain this scene.`;
    lines.forEach((line,offset) => line.classList.toggle('is-focused',frame.lines.includes(offset+1)));
    // Move only the code pane, never the lesson or keyboard focus.
    showFocusedLine();
    diagram.dataset.layout=frame.layout;diagram.replaceChildren();
    frame.items.forEach((item,itemIndex) => {
      const tile=node('div','visual-tile');tile.dataset.tone=item.tone;
      tile.append(node('span','visual-label',item.label),node('strong','',item.value),node('small','',item.detail));
      if (frame.layout==='bars') {
        const meter=node('div','visual-meter');meter.setAttribute('aria-hidden','true');
        const bar=node('span');bar.style.transform=`scaleX(${item.amount/100})`;meter.append(bar);tile.append(meter);
        if (animate && motionOK()) bar.animate([{transform:'scaleX(0)'},{transform:`scaleX(${item.amount/100})`}],{duration:650,easing:'cubic-bezier(.2,.7,.3,1)'});
      }
      diagram.append(tile);
      if (animate && motionOK()) tile.animate([{opacity:.35,transform:frame.layout==='tokens'?'translateX(-14px)':'translateY(10px)'},{opacity:1,transform:'translate(0,0)'}],{duration:380,delay:itemIndex*55,easing:'ease-out'});
    });
    sceneButtons.forEach((button,offset) => {
      button.setAttribute('aria-current',offset===index?'step':'false');
      button.dataset.seen=String(offset<index);
    });
    back.disabled=index===0;next.disabled=index===story.frames.length-1;
    status.textContent=index===story.frames.length-1?'Story complete. Compare the console with expected output, then check your hunch.':`${frame.title}. ${playing?'Playing; Pause story stops here.':'Use Next scene, or choose any scene above.'}`;
  }
  function schedule() {
    clearTimeout(timer);
    timer=setTimeout(() => {
      if (!playing || !motionOK() || document.hidden || panel.hidden) {stop();return;}
      render(index+1,true);
      if (index===story.frames.length-1) stop();else schedule();
    },Number(pace.value));
  }
  play.addEventListener('click',() => {
    if (playing) {stop();status.textContent='Paused. This scene stays visible.';return;}
    if (!motionOK()) return;
    if (index===story.frames.length-1) render(0);
    playing=true;play.textContent='Pause story';play.setAttribute('aria-pressed','true');
    status.textContent='Playing the authored story. Pause whenever you want to inspect a scene.';schedule();
  });
  next.addEventListener('click',() => {stop();if(index<story.frames.length-1)render(index+1,true);});
  back.addEventListener('click',() => {stop();if(index>0)render(index-1,true);});
  host.querySelector('#story-reset').addEventListener('click',() => {stop();render(0,true);});
  pace.addEventListener('change',() => {if(playing)schedule();});
  function preferences() {
    if (!motionOK()) stop();
    play.disabled=!motionOK();
    play.title=motionOK()?'Play through the scenes; pause at any time.':'Motion is off. All scenes remain available through Next, Back, and scene buttons.';
  }
  new MutationObserver(preferences).observe(document.documentElement,{attributes:true,attributeFilter:['class']});
  new MutationObserver(() => {if(panel.hidden)stop();}).observe(panel,{attributes:true,attributeFilter:['hidden']});
  new ResizeObserver(showFocusedLine).observe(source.closest('pre'));
  reduced.addEventListener('change',preferences);
  document.addEventListener('visibilitychange',() => {if(document.hidden)stop();});
  window.addEventListener('pagehide',stop);
  story.challenge.choices.forEach((choice) => {
    const button=node('button','story-choice',choice.text);button.type='button';button.setAttribute('aria-pressed','false');
    button.addEventListener('click',() => {
      host.querySelectorAll('.story-choice').forEach(other => {other.setAttribute('aria-pressed',String(other===button));other.removeAttribute('data-verdict');});
      button.dataset.verdict=choice.correct?'correct':'retry';
      const feedback=host.querySelector('#story-feedback');feedback.textContent=(choice.correct?'You spotted it. ':'Try another angle. ')+choice.feedback;
      feedback.dataset.verdict=choice.correct?'correct':'retry';
      if(motionOK())feedback.animate([{opacity:.4,transform:'translateY(5px)'},{opacity:1,transform:'translateY(0)'}],{duration:280});
    });
    host.querySelector('#story-choices').append(button);
  });
  host.querySelector('[data-story-controls]').hidden=false;rail.hidden=false;
  host.querySelector('.story-challenge').hidden=false;
  render(0);preferences();
}
