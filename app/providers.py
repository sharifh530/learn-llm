"""Google transport: only this adapter knows how to call the SDK."""

from dataclasses import dataclass

from google import genai
from google.genai import types
import httpx


class AIError(Exception):
    def __init__(self, code, message, status=503, usage=None):
        super().__init__(message)
        self.code, self.status = code, status
        self.usage = usage


@dataclass
class ModelReply:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    finish_reason: str | None = None


def provider_error(error):
    # Never show Google's raw error, HTTP URL, headers, or credential text.
    code = getattr(error, "code", None)
    if code in (401, 403):
        return AIError("access", "Google access needs configuration. Check your auth mode and permissions.")
    if code in (400, 404):
        return AIError("model", "Check that your Google model and location support this text request and token counting.")
    if code == 429:
        return AIError("quota", "Google's quota is busy. Wait a little before retrying.", 429)
    if isinstance(error, (httpx.TimeoutException, TimeoutError)):
        return AIError("timeout", "Google took too long. Your question is preserved; retry when ready.", 504)
    return AIError("unavailable", "Google could not complete this request. Check server setup or retry later.")


class GoogleProvider:
    def __init__(self, settings):
        self.settings = settings

    def generate(self, instruction, message, input_limit, output_limit, on_call):
        try:
            options = types.HttpOptions(api_version="v1", timeout=30000,
                                        retry_options=types.HttpRetryOptions(attempts=1))
            # vertexai remains supported by the pinned SDK. It selects Cloud,
            # including express keys, rather than the Gemini Developer API.
            arguments = {"vertexai": True, "http_options": options}
            if self.settings.auth_mode == "express_key":
                arguments["api_key"] = self.settings.api_key
            else:
                # Explicit credentials prevent ambient GOOGLE_API_KEY from
                # accidentally selecting key authentication for ADC mode.
                import google.auth
                credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
                arguments.update(credentials=credentials, project=self.settings.project, location=self.settings.location)
            with genai.Client(**arguments) as client:
                on_call()
                counted = client.models.count_tokens(model=self.settings.model, contents=message,
                                                      config=types.CountTokensConfig(system_instruction=instruction))
                if counted.total_tokens is None:
                    raise AIError("count", "Google returned no input token count. No generation was sent.")
                if counted.total_tokens > input_limit:
                    raise AIError("input_limit", "That question and lesson exceed this app's token limit. Shorten your question.", 413)
                on_call()
                response = client.models.generate_content(model=self.settings.model, contents=message,
                    config=types.GenerateContentConfig(system_instruction=instruction, max_output_tokens=output_limit,
                                                       response_modalities=["TEXT"], candidate_count=1))
                block_reason = response.prompt_feedback and response.prompt_feedback.block_reason
                blocked = block_reason and str(block_reason).split(".")[-1] != "BLOCKED_REASON_UNSPECIFIED"
                candidates = response.candidates or []
                reasons = {str(candidate.finish_reason).split(".")[-1] for candidate in candidates}
                metadata = response.usage_metadata
                usage = (metadata.prompt_token_count, metadata.candidates_token_count, metadata.total_token_count) if metadata else None
                if blocked or reasons.intersection({"SAFETY", "PROHIBITED_CONTENT", "RECITATION", "BLOCKLIST", "SPII"}):
                    raise AIError("blocked", "Google returned no usable answer for this request. Try a different question.", 422, usage)
                text = response.text
                if not text or not text.strip():
                    raise AIError("empty", "Google returned an empty answer. Your question is preserved.", 422, usage)
                return ModelReply(text.strip(), metadata.prompt_token_count if metadata else None,
                                  metadata.candidates_token_count if metadata else None,
                                  metadata.total_token_count if metadata else None,
                                  str(candidates[0].finish_reason).split(".")[-1] if candidates else None)
        except AIError:
            raise
        except Exception as error:
            raise provider_error(error) from None
