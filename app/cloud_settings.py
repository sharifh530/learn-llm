"""Encrypted Settings persistence for the private single-learner cloud lab."""
import base64
from dataclasses import asdict
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken

from app.config import AISettings
from app.models import ProviderSettings
from app.settings_store import SettingsStore, SettingsStoreError


class CloudSettingsStore(SettingsStore):
    def __init__(self, database):
        self.database = database
        # The integration's bearer token stays outside the database. Rotating
        # it requires re-entering the Google key; never fall back to plaintext.
        self.cipher = Fernet(base64.urlsafe_b64encode(hashlib.sha256(
            ('tiny-chat-settings-v1:' + database.token).encode()).digest()))

    def candidate(self, current, body):
        if body.auth_mode != 'express_key':
            raise SettingsStoreError('Use a Google Cloud express key for the hosted lab. Local ADC is available in the Windows app.')
        return super().candidate(current, body)

    def load(self, connection=None):
        if connection is not None:
            row = connection.execute('SELECT value FROM cloud_settings WHERE id=1').fetchone()
        else:
            with self.database.connection() as own:
                row = own.execute('SELECT value FROM cloud_settings WHERE id=1').fetchone()
        if not row:
            return AISettings()
        try:
            data = json.loads(row['value'])
            if data.pop('version') != 1:
                raise ValueError('version')
            protected = data.pop('protected_key')
            data['api_key'] = self.cipher.decrypt(protected.encode()).decode() if protected else ''
            body = ProviderSettings.model_validate(data)
            return AISettings(**body.model_dump())
        except (ValueError, TypeError, KeyError, InvalidToken):
            raise SettingsStoreError('Saved connection could not be opened. Re-enter your key in Settings; learning data is preserved.') from None

    def save(self, settings, connection=None):
        data = asdict(settings)
        key = data.pop('api_key')
        data.pop('provider')
        data.update(version=1, protected_key=self.cipher.encrypt(key.encode()).decode() if key else '')
        sql = 'INSERT INTO cloud_settings(id,value) VALUES(1,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value'
        if connection is not None:
            connection.execute(sql, (json.dumps(data),))
        else:
            with self.database.connection() as own:
                own.execute(sql, (json.dumps(data),))
