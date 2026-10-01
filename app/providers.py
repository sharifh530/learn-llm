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

    def client_arguments(self):
        arguments = {'vertexai': True, 'http_options': types.HttpOptions(api_version='v1', timeout=30000,
                     retry_options=types.HttpRetryOptions(attempts=1))}
        if self.settings.auth_mode == 'express_key':
            arguments['api_key'] = self.settings.api_key
        else:
            import google.auth
            credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
            arguments.update(credentials=credentials, project=self.settings.project, location=self.settings.location)
        return arguments

    def generate(self, instruction, message, input_limit, output_limit, on_call):
        try:
            with genai.Client(**self.client_arguments()) as client:
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

    def stream(self, instruction, messages, input_limit, output_limit, on_call, cancelled):
        """Yield normalized visible text, then a final usage/finish event."""
        try:
            contents = [types.Content(role='model' if item['role']=='assistant' else 'user',
                        parts=[types.Part.from_text(text=item['text'])]) for item in messages]
            with genai.Client(**self.client_arguments()) as client:
                if cancelled():
                    return
                on_call()
                counted = client.models.count_tokens(model=self.settings.model, contents=contents,
                           config=types.CountTokensConfig(system_instruction=instruction))
                if counted.total_tokens is None:
                    raise AIError('count', 'Google returned no input token count. No generation was sent.')
                if counted.total_tokens > input_limit:
                    raise AIError('input_limit', 'Conversation context exceeds the input token limit. Start a shorter chat.', 413)
                if cancelled():
                    return
                on_call()
                stream = client.models.generate_content_stream(model=self.settings.model, contents=contents,
                         config=types.GenerateContentConfig(system_instruction=instruction, max_output_tokens=output_limit,
                                response_modalities=['TEXT'], candidate_count=1))
                usage, reason, visible = (None, None, None), None, False
                try:
                    for chunk in stream:
                        if cancelled():
                            return
                        metadata = chunk.usage_metadata
                        if metadata:
                            usage = (metadata.prompt_token_count, metadata.candidates_token_count, metadata.total_token_count)
                        block = chunk.prompt_feedback and chunk.prompt_feedback.block_reason
                        candidates = chunk.candidates or []
                        reasons = {str(candidate.finish_reason).split('.')[-1] for candidate in candidates if candidate.finish_reason}
                        if (block and str(block).split('.')[-1]!='BLOCKED_REASON_UNSPECIFIED') or reasons.intersection({'SAFETY','PROHIBITED_CONTENT','RECITATION','BLOCKLIST','SPII'}):
                            raise AIError('blocked', 'Google blocked this response. Try a different question.', 422, usage)
                        if reasons:
                            reason = str(candidates[0].finish_reason).split('.')[-1]
                        # Exclude thought and non-text parts; never expose private reasoning.
                        parts = candidates[0].content.parts if candidates and candidates[0].content else []
                        text = ''.join(part.text for part in (parts or []) if part.text and not part.thought)
                        if text:
                            visible = True
                            yield ModelReply(text)
                    if not visible:
                        raise AIError('empty', 'Google returned an empty reply. Your question is saved.', 422, usage)
                    if reason not in ('STOP','MAX_TOKENS'):
                        raise AIError('incomplete', 'Google stream ended without a normal completion marker. Partial text saved.', 503, usage)
                    yield ModelReply('', *usage, finish_reason=reason)
                finally:
                    stream.close()
        except AIError:
            raise
        except Exception as error:
            raise provider_error(error) from None
