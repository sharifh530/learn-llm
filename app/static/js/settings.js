import {api, toast} from "./common.js";

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
