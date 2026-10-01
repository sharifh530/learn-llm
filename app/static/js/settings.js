import {api, aiCall, toast} from "./common.js";

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

const testButton = document.querySelector("#test-provider");
testButton.addEventListener("click", async () => {
  testButton.disabled = true;
  const status = document.querySelector("#provider-test-status");
  status.textContent = "Counting the prompt and asking Google for one short reply…";
  try {
    const result = await aiCall("/api/provider/test", {});
    status.textContent = `Google replied: ${result.reply} (${result.usage.total_tokens ?? 'unknown'} reported tokens)${result.truncated ? ' · Output limit reached' : ''}`;
  } catch (error) {status.textContent = error.message;}
  finally {
    testButton.disabled = false;
    try {
      const state = await api("/api/provider/status");
      document.querySelector("#provider-state").textContent = state.message;
      const usage = state.usage;
      document.querySelector("#provider-usage").textContent = `${usage.attempts} / 50 attempts · ${usage.provider_calls} model API calls attempted · ${usage.reported_total_tokens} reported tokens · ${usage.unknown_usage_attempts} attempts with unknown usage`;
    } catch { /* Test result remains visible if the local server disconnects. */ }
  }
});
