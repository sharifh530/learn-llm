"""The existing parameterized SQLite queries, executed on Turso over HTTPS.

Each context owns a remote connection/baton. Writes commit together; errors
roll back. No local replica, credentials in URLs, or automatic write retries.
"""
from contextlib import contextmanager
import sqlite3
import logging
from urllib.parse import urlsplit, urlunsplit

import httpx

from app.db import SCHEMA


class CloudStorageError(RuntimeError):
    pass


def endpoint(url):
    parts = urlsplit(url)
    if parts.scheme not in ('libsql', 'turso', 'https') or not parts.hostname or not parts.hostname.endswith('.turso.io') or parts.username or parts.password or parts.query or parts.fragment or parts.path not in ('', '/'):
        raise CloudStorageError('Use the Turso database URL supplied by the Vercel integration.')
    return urlunsplit(('https', parts.netloc, '/v2/pipeline', '', ''))


def encode(value):
    if value is None:
        return {'type': 'null'}
    if isinstance(value, int):
        return {'type': 'integer', 'value': str(value)}
    if isinstance(value, float):
        return {'type': 'float', 'value': value}
    if isinstance(value, str):
        return {'type': 'text', 'value': value}
    raise TypeError('Unsupported SQL parameter type.')


def decode(value):
    kind = value['type']
    if kind == 'null':
        return None
    if kind == 'integer':
        return int(value['value'])
    if kind == 'float':
        return float(value['value'])
    if kind == 'text':
        return value['value']
    raise CloudStorageError('Unexpected database value type.')


class Row(dict):
    def __getitem__(self, key):
        return list(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


class Cursor:
    def __init__(self, result):
        names = [column['name'] for column in result['cols']]
        self.rows = [Row(zip(names, map(decode, row))) for row in result['rows']]
        self.rowcount = result['affected_row_count']
        self.lastrowid = int(result['last_insert_rowid']) if result.get('last_insert_rowid') else None

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows

    def __iter__(self):
        return iter(self.fetchall())


class Connection:
    def __init__(self, database):
        self.url, self.token = database.url, database.token
        self.client = httpx.Client(timeout=10, transport=database.transport)
        self.baton, self.transaction, self.initial = None, False, True

    def pipeline(self, requests):
        try:
            response = self.client.post(self.url, headers={'Authorization': 'Bearer ' + self.token},
                json={'baton': self.baton, 'requests': requests})
            response.raise_for_status()
            data = response.json()
            self.baton = data.get('baton')
            # The connection's assigned server must remain within Turso.
            if data.get('base_url'):
                self.url = endpoint(data['base_url'])
            results = []
            for item in data['results']:
                if item['type'] == 'error':
                    code = item['error'].get('code', '')
                    logging.warning('Tiny Chat Lab database error code: %s', code)
                    if code.startswith('SQLITE_CONSTRAINT'):
                        raise sqlite3.IntegrityError('A conflicting record already exists.')
                    raise CloudStorageError('Cloud storage could not complete this action. Retry the same action to recover it.')
                results.append(item['response'].get('result'))
            return results
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise CloudStorageError('Cloud storage is unavailable. Your input is preserved; retry the same action.') from None

    def execute(self, sql, args=()):
        operation = sql.strip().split()[0].upper()
        requests = []
        if self.initial:
            requests.append({'type': 'execute', 'stmt': {'sql': 'PRAGMA foreign_keys = ON'}})
            self.initial = False
        if operation in ('INSERT', 'UPDATE', 'DELETE', 'REPLACE') and not self.transaction:
            # A pipeline continues after SQL errors. Confirm BEGIN succeeds
            # before sending a write, otherwise it could run in autocommit.
            requests.append({'type': 'execute', 'stmt': {'sql': 'BEGIN IMMEDIATE'}})
            self.pipeline(requests)
            requests = []
            self.transaction = True
        if operation == 'BEGIN':
            self.transaction = True
        requests.append({'type': 'execute', 'stmt': {'sql': sql, 'args': list(map(encode, args)), 'want_rows': True}})
        return Cursor(self.pipeline(requests)[-1])

    def close(self, success):
        try:
            if self.baton:
                requests = []
                if self.transaction:
                    requests.append({'type': 'execute', 'stmt': {'sql': 'COMMIT' if success else 'ROLLBACK'}})
                requests.append({'type': 'close'})
                self.pipeline(requests)
        finally:
            self.client.close()


class CloudDatabase:
    remote = True

    def __init__(self, url, token, transport=None):
        self.url, self.token, self.transport = endpoint(url), token, transport
        if not token:
            raise CloudStorageError('Connect a Turso database to this Vercel project first.')
        # Expand only. Repeated cold starts can safely finish partial setup.
        with self.connection() as connection:
            for statement in SCHEMA.split(';'):
                if statement.strip():
                    connection.execute(statement)
            connection.execute('CREATE TABLE IF NOT EXISTS cloud_settings (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)')
            connection.execute('CREATE TABLE IF NOT EXISTS generation_workers (id TEXT PRIMARY KEY REFERENCES generations(id), started_at REAL NOT NULL)')

    @contextmanager
    def connection(self):
        connection = Connection(self)
        try:
            yield connection
        except BaseException:
            try:
                connection.close(False)
            except Exception:
                pass  # Preserve the original error; a dropped stream rolls back.
            raise
        else:
            connection.close(True)
