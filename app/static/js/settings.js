import {api, aiCall, toast} from "./common.js";

const form = document.querySelector('#provider-settings');
const auth = document.querySelector('#provider-auth');
const key = document.querySelector('#provider-key');
const enabled = document.querySelector('#provider-enabled');
const saveStatus = document.querySelector('#provider-save-status');
const saveButton = document.querySelector('#save-provider');
const removeButton = document.querySelector('#remove-provider-key');
const testButton = document.querySelector('#test-provider');
let pending = false;
function fields() {
  const express = auth.value === 'express_key';
  document.querySelector('#express-fields').hidden = !express;
  document.querySelector('#adc-fields').hidden = express;
  document.querySelector('#provider-model').required = enabled.checked;
  document.querySelector('#provider-project').required = enabled.checked && !express;
  document.querySelector('#provider-location').required = enabled.checked && !express;
}
auth.addEventListener('change', fields);
enabled.addEventListener('change', fields);
fields();

function display(state) {
  document.querySelector('#provider-state').textContent = state.message;
  document.querySelector('#key-state').textContent = state.key_saved ? 'Key saved · hidden' : 'No key saved';
  key.placeholder = state.key_saved ? 'Saved key stays hidden' : 'Your Cloud express API key';
  key.closest('label').querySelector('span').textContent = state.key_saved ? 'Leave blank to keep your saved key' : 'Paste your express key here';
  removeButton.disabled = !state.key_saved;
  document.querySelector('#settings-notice').textContent = state.settings_notice;
  const usage = state.usage;
  document.querySelector('#provider-usage').textContent = `${usage.attempts} / 50 attempts · ${usage.provider_calls} model API calls attempted · ${usage.reported_total_tokens} reported tokens · ${usage.unknown_usage_attempts} attempts with unknown usage`;
}
async function changeConnection(remove = false) {
  if (pending) return;
  pending = true;
  const wasRemovable = !removeButton.disabled;
  [...form.elements].forEach(control => {control.disabled = true;});
  testButton.disabled = true;
  saveStatus.textContent = remove ? 'Removing the saved key…' : 'Saving your connection…';
  let success = false;
  try {
    const body = remove ? {} : {enabled: enabled.checked, auth_mode: auth.value, api_key: auth.value === 'express_key' ? key.value : '', model: document.querySelector('#provider-model').value, project: document.querySelector('#provider-project').value, location: document.querySelector('#provider-location').value};
    const state = await api(remove ? '/api/provider/key/remove' : '/api/provider/settings', body);
    key.value = '';
    enabled.checked = state.enabled;
    display(state);
    document.querySelector('#provider-test-status').textContent = '';
    saveStatus.textContent = remove ? 'Key removed. Google AI is disabled; your lessons and chats are preserved.' : 'Connection saved. No restart needed. Test Google connection to verify access.';
    toast(remove ? 'Saved key removed.' : 'Connection saved.');
    success = true;
  } catch (error) {saveStatus.textContent = error.message;}
  finally {
    const removable = success ? !removeButton.disabled : wasRemovable;
    [...form.elements].forEach(control => {control.disabled = false;});
    removeButton.disabled = !removable;
    testButton.disabled = false;
    pending = false; fields();
  }
}
form.addEventListener('submit', event => {event.preventDefault(); changeConnection();});
removeButton.addEventListener('click', () => changeConnection(true));
// Never put credential input into draft storage or leave it on a page exit.
window.addEventListener('pagehide', () => {key.value = '';});

document.querySelector("#reload-content").addEventListener("click", async event => {
  const button = event.currentTarget;
  const status = document.querySelector("#reload-status");
  button.disabled = true;
  status.textContent = "Validating saved lesson content…";
  try {
    const result = await api("/api/content/reload", {});
    status.textContent = `${result.authored} lessons reloaded. Refresh lesson pages to read the latest version. Your progress is preserved.`;
    toast("Validated lesson content is ready.");
  } catch (error) {status.textContent = error.message;}
  finally {button.disabled = false;}
});

testButton.addEventListener("click", async () => {
  if (pending) return;
  pending = true;
  testButton.disabled = true;
  saveButton.disabled = true;
  const wasRemovable = !removeButton.disabled;
  removeButton.disabled = true;
  const status = document.querySelector("#provider-test-status");
  status.textContent = "Counting the prompt and asking Google for one short reply…";
  try {
    const result = await aiCall("/api/provider/test", {});
    status.textContent = `Google replied: ${result.reply} (${result.usage.total_tokens ?? 'unknown'} reported tokens)${result.truncated ? ' · Output limit reached' : ''}`;
  } catch (error) {status.textContent = error.message;}
  finally {
    testButton.disabled = false;
    saveButton.disabled = false;
    removeButton.disabled = !wasRemovable;
    pending = false;
    try {
      const state = await api("/api/provider/status");
      display(state);
    } catch { /* Test result remains visible if the local server disconnects. */ }
  }
});
