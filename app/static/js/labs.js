import {api, node, readTab, writeTab} from './common.js';

const $ = selector => document.querySelector(selector);
const key = 'tiny-chat-observatory-v1';
const names = ['similarity', 'attention', 'training'];
const fmt = number => number.toFixed(4);
let currentWeight = 1, history = [], step = 0, busy = false;
const revisions = {similarity: 0, attention: 0, training: 0};
const timers = {};
const controls = [...document.querySelectorAll('.lab-controls input, .lab-controls select')];
const finite = (n, min, max) => typeof n === 'number' && Number.isFinite(n) && n >= min && n <= max;

function save() {
  writeTab(key, JSON.stringify({controls: Object.fromEntries(controls.map(c => [c.id, c.type === 'checkbox' ? c.checked : c.value])), weight: currentWeight}));
}
function outputs() {
  document.querySelectorAll('[data-value]').forEach(output => {
    output.textContent = output.dataset.value === 'model-weight' ? fmt(currentWeight) : document.getElementById(output.dataset.value).value;
  });
}
try {
  const saved = JSON.parse(readTab(key, '{}'));
  for (const control of controls) {
    const value = saved.controls?.[control.id];
    if (control.type === 'checkbox' && typeof value === 'boolean') control.checked = value;
    else if (control.type === 'range' && typeof value === 'string' && finite(Number(value), Number(control.min), Number(control.max))) control.value = value;
    else if (control.tagName === 'SELECT' && [...control.options].some(o => o.value === value)) control.value = value;
  }
  currentWeight = finite(saved.weight, 0, 6) ? saved.weight : Number($('#model-weight').value);
  $('#model-weight').value = currentWeight;
} catch { /* Corrupt optional storage starts with the authored defaults. */ }
outputs();

function selectLab(name, focus = false) {
  if (!names.includes(name)) name = 'similarity';
  for (const id of names) {
    const button = $(`#lab-tab-${id}`), active = id === name;
    button.setAttribute('aria-selected', String(active));
    button.tabIndex = active ? 0 : -1;
    $(`#lab-${id}`).hidden = !active;
  }
  const url = new URL(location.href);
  url.searchParams.set('experiment', name);
  window.history.replaceState(null, '', url);
  if (focus) $(`#lab-tab-${name}`).focus();
}
document.querySelectorAll('[data-lab]').forEach(button => {
  button.addEventListener('click', () => selectLab(button.dataset.lab));
  button.addEventListener('keydown', event => {
    let index = names.indexOf(button.dataset.lab);
    if (event.key === 'ArrowRight') index = (index + 1) % names.length;
    else if (event.key === 'ArrowLeft') index = (index + 2) % names.length;
    else if (event.key === 'Home') index = 0;
    else if (event.key === 'End') index = names.length - 1;
    else return;
    event.preventDefault(); selectLab(names[index], true);
  });
});
selectLab(new URL(location.href).searchParams.get('experiment'));

function meter(value, label) {
  const element = node('meter');
  element.min = 0; element.max = 1; element.value = value;
  element.setAttribute('aria-label', label);
  return element;
}
function drawSimilarity(data) {
  $('#fruit-winner').textContent = data.defined ? `${data.matches[0].emoji} ${data.matches[0].name}` : 'No direction';
  $('#fruit-summary').textContent = data.defined ? `Your vector [${data.query.join(', ')}] points most like this authored fruit.` : 'Cosine is undefined for [0, 0, 0]. No closest fruit can be chosen.';
  $('#fruit-matches').replaceChildren(...data.matches.map(item => {
    const row = node('tr');
    row.append(node('th', '', `${item.emoji} ${item.name}`), node('td', '', `[${item.vector.join(', ')}]`));
    row.firstChild.scope = 'row';
    const score = node('td', 'cosine-score');
    score.append(node('span', '', item.similarity === null ? 'Undefined' : fmt(item.similarity)));
    if (item.similarity !== null) score.append(meter(item.similarity, `${item.name} cosine ${fmt(item.similarity)}`));
    row.append(score); return row;
  }));
}
function drawAttention(data) {
  $('#attention-query-label').textContent = `${data.query_index + 1} · ${data.query}`;
  $('#attention-total').textContent = `Total = ${fmt(data.sum)}`;
  $('#attention-summary').textContent = data.causal ? 'Future positions are masked. Only the query and earlier positions can contribute.' : 'Mask off: all seven authored values can contribute.';
  $('#attention-weights').replaceChildren(...data.rows.map(item => {
    const row = node('div', `attention-row${item.masked ? ' masked' : ''}`);
    row.append(node('strong', '', `${item.index + 1} · ${item.word}`), node('span', 'small', `score ${item.score} · value ${item.value}`), meter(item.weight, `${item.word} weight ${fmt(item.weight)}`), node('b', '', item.masked ? '0 · masked' : `${(100 * item.weight).toFixed(1)}%`));
    return row;
  }));
  $('#weighted-value').textContent = `Weighted output = ${fmt(data.weighted_value)}`;
}
function drawTraining(data) {
  const state = data.after;
  currentWeight = state.weight;
  $('#model-weight').value = currentWeight;
  outputs(); save();
  $('#train-loss').textContent = fmt(state.train_loss);
  $('#check-loss').textContent = fmt(state.check_loss);
  $('#train-prediction').textContent = `x=1 → ${fmt(state.prediction)} · target 3`;
  $('#check-prediction').textContent = `x=2 → ${fmt(state.check_prediction)} · target 4`;
  if (!history.length) history.push({...data.before, step: 0});
  for (const update of data.steps) history.push({...update, step: ++step});
  history = history.slice(-13);
  $('#training-update').textContent = data.steps.length ? `${data.steps.length} update(s): weight ${fmt(data.before.weight)} → ${fmt(state.weight)}. Only the training example determined the gradient.` : `Prediction read weight ${fmt(currentWeight)}. No training update was made.`;
  const updates = history.filter(row => row.step > 0).slice(-12);
  $('#training-history').replaceChildren(...updates.map(item => {
    const row = node('tr');
    [item.step, fmt(item.weight), fmt(item.train_loss), fmt(item.check_loss)].forEach(value => row.append(node('td', '', String(value))));
    return row;
  }));
  if (!updates.length) {
    const row = node('tr'), cell = node('td', '', 'No training updates yet. Predict first.');
    cell.colSpan = 4; row.append(cell); $('#training-history').append(row);
  }
  const scale = Math.max(1, ...history.flatMap(item => [item.train_loss, item.check_loss]));
  for (const [id, field] of [['train-line', 'train_loss'], ['check-line', 'check_loss']]) {
    document.getElementById(id).setAttribute('points', history.map((item, index) => `${35 + index * 425 / Math.max(1, history.length - 1)},${150 - item[field] / scale * 125}`).join(' '));
  }
  $('#loss-scale').textContent = `0–${scale.toFixed(2)} loss`;
}
async function compute(name, operation = 'predict', count = 1) {
  const revision = ++revisions[name];
  const status = $(`#${name}-status`);
  status.textContent = 'Calculating locally…';
  const body = name === 'similarity' ? {vector: [0, 1, 2].map(i => Number($(`#feature-${i}`).value))} : name === 'attention' ? {scores: Array.from({length: 7}, (_, i) => Number($(`#score-${i}`).value)), query_index: Number($('#attention-query').value), causal: $('#causal-mask').checked, temperature: Number($('#attention-temperature').value)} : {weight: currentWeight, learning_rate: Number($('#learning-rate').value), steps: count, operation};
  try {
    const result = await api(`/api/labs/${name}`, body);
    if (revision !== revisions[name]) return;
    ({similarity: drawSimilarity, attention: drawAttention, training: drawTraining})[name](result);
    status.textContent = 'Local Python toy · no Google call or XP';
    status.classList.remove('error');
  } catch (error) {
    if (revision !== revisions[name]) return;
    status.textContent = error.message;
    status.classList.add('error');
  }
}
for (const name of names) {
  const form = $(`#${name}-form`);
  form.addEventListener('input', event => {
    if (name === 'training' && event.target.id === 'model-weight') {
      currentWeight = Number(event.target.value); history = []; step = 0;
    }
    outputs(); save();
    clearTimeout(timers[name]);
    // Invalidate an older response as soon as the input changes.
    revisions[name]++;
    timers[name] = setTimeout(() => compute(name), 150);
  });
  form.addEventListener('submit', async event => {
    event.preventDefault(); clearTimeout(timers[name]);
    if (name === 'training' && busy) return;
    if (name !== 'training') {await compute(name); return;}
    busy = true;
    const elements = [...form.elements];
    elements.forEach(control => {control.disabled = true;});
    try {await compute(name, event.submitter?.dataset.operation || 'predict', Number(event.submitter?.dataset.steps || 1));}
    finally {busy = false; elements.forEach(control => {control.disabled = false;});}
  });
  form.querySelector('[data-reset]').addEventListener('click', () => {
    clearTimeout(timers[name]); form.reset();
    if (name === 'training') {currentWeight = 1; history = []; step = 0;}
    outputs(); save(); compute(name);
  });
  compute(name);
}
