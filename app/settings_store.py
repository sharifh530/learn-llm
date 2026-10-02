"""Local connection settings; Windows DPAPI protects the key at rest."""
import base64
import ctypes
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import tempfile

from app.config import AISettings
from app.models import ProviderSettings


class SettingsStoreError(ValueError):
    pass


def protect(data: bytes, decrypt=False) -> bytes:
    if os.name != 'nt':
        raise SettingsStoreError('Saving an API key requires Windows account encryption on this local app.')
    from ctypes import wintypes
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p if decrypt else wintypes.LPCWSTR,
                         ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    # User scope, with OS prompts forbidden. Never fall back to plain text.
    success = function(ctypes.byref(source), None if decrypt else 'Tiny Chat Lab API key', None, None, None, 1, ctypes.byref(output))
    if not success:
        raise SettingsStoreError('Windows could not protect or open this saved key. Save a new key using this Windows account.')
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel.LocalFree(output.data)


class SettingsStore:
    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return AISettings()
        try:
            if self.path.stat().st_size > 16000:
                raise ValueError('size')
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if data.pop('version') != 1:
                raise ValueError('version')
            encrypted = data.pop('protected_key')
            if not isinstance(encrypted, str):
                raise ValueError('key')
            body = ProviderSettings.model_validate(data)
            if body.api_key:
                raise ValueError('plain key')
            key = protect(base64.b64decode(encrypted, validate=True), decrypt=True).decode('utf-8') if encrypted else ''
            body = ProviderSettings.model_validate({**body.model_dump(), 'api_key': key})
            return AISettings(enabled=body.enabled, auth_mode=body.auth_mode, api_key=body.api_key,
                              model=body.model, project=body.project, location=body.location)
        except (OSError, ValueError, KeyError, TypeError, SettingsStoreError):
            raise SettingsStoreError('Saved connection settings could not be opened. Re-enter them in Settings; offline lessons still work.') from None

    def save(self, settings):
        data = asdict(settings)
        key = data.pop('api_key')
        data.pop('provider')
        data.update(version=1, protected_key=base64.b64encode(protect(key.encode())).decode('ascii') if key else '')
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent,
                    prefix='.ai-settings-', suffix='.tmp', delete=False) as file:
                temporary = Path(file.name)
                json.dump(data, file, indent=2)
                file.write('\n')
                file.flush()
                os.fsync(file.fileno())
            temporary.replace(self.path)
        except OSError:
            raise SettingsStoreError('Connection settings could not be saved. Your previous connection is unchanged; retry.') from None
        finally:
            if temporary and temporary.exists():
                temporary.unlink()

    def candidate(self, current, body):
        settings = replace(current, enabled=body.enabled, auth_mode=body.auth_mode,
                           api_key=body.api_key or current.api_key, model=body.model,
                           project=body.project, location=body.location)
        if settings.enabled and (problem := settings.problem()):
            raise SettingsStoreError(problem)
        return settings
