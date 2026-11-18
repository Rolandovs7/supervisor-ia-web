"""In-memory stand-in for the Supabase client (no network in tests)."""

from collections import defaultdict
from types import SimpleNamespace

import pytest

from app.services import database


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, rows):
        self._rows = list(rows)

    def eq(self, column, value):
        self._rows = [r for r in self._rows if r.get(column) == value]
        return self

    def execute(self):
        return _Response(self._rows)


class _UpdateQuery:
    def __init__(self, rows, values):
        self._rows = rows
        self._values = values

    def eq(self, column, value):
        self._rows = [r for r in self._rows if r.get(column) == value]
        return self

    def execute(self):
        for row in self._rows:
            row.update(self._values)
        return _Response(self._rows)


class _Table:
    def __init__(self, store, name):
        self.store = store
        self.name = name

    def insert(self, row):
        saved = {**row, "id": f"{self.name}-{len(self.store[self.name]) + 1}"}
        self.store[self.name].append(saved)
        return _Query([saved])

    def select(self, *columns):
        return _Query(self.store[self.name])

    def update(self, values):
        return _UpdateQuery(self.store[self.name], values)


class FakeAuth:
    """Minimal Supabase Auth stand-in with stable tokens for tests."""

    def __init__(self):
        self.users = {}
        self.tokens = {}

    def issue_token(self, email):
        user = self.users.setdefault(
            email, SimpleNamespace(id=f"user-{email}", email=email)
        )
        token = f"token-{user.id}"
        self.tokens[token] = user
        return token

    def sign_up(self, credentials):
        email = credentials["email"]
        if email in self.users:
            raise ValueError("User already registered")
        return SimpleNamespace(user=self.users.setdefault(
            email, SimpleNamespace(id=f"user-{email}", email=email)
        ), session=None)

    def sign_in_with_password(self, credentials):
        user = self.users.get(credentials["email"])
        if user is None:
            raise ValueError("Invalid login credentials")
        token = self.issue_token(credentials["email"])
        return SimpleNamespace(
            user=user, session=SimpleNamespace(access_token=token)
        )

    def get_user(self, token):
        user = self.tokens.get(token)
        if user is None:
            raise ValueError("Invalid JWT")
        return SimpleNamespace(user=user)


class FakeSupabase:
    def __init__(self):
        self.store = defaultdict(list)
        self.auth = FakeAuth()

    def table(self, name):
        return _Table(self.store, name)


@pytest.fixture
def fake_supabase(monkeypatch):
    client = FakeSupabase()
    monkeypatch.setattr(database, "_client", client)
    return client


@pytest.fixture
def auth_headers(fake_supabase):
    token = fake_supabase.auth.issue_token("supervisor@example.com")
    return {"Authorization": f"Bearer {token}"}
