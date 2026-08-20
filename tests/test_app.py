import importlib
from datetime import datetime

import pytest
from requests import RequestException

app_module = importlib.import_module("page_analyzer.app")
app = app_module.app


class FakeCursor:
    def __init__(self):
        self.fetchone_result = None
        self.fetchall_result = []

    def execute(self, query, params=None):
        query_text = query.strip()
        if "SELECT id FROM urls WHERE name = %s" in query_text:
            self.fetchone_result = None
        elif "INSERT INTO urls (name) VALUES" in query_text:
            self.fetchone_result = (42,)
        elif "SELECT name FROM urls WHERE id = %s" in query_text:
            self.fetchone_result = ("https://example.com",)
        elif "SELECT id, name, created_at FROM urls WHERE id = %s" in query_text:
            self.fetchone_result = (42, "https://example.com", datetime(2024, 1, 1, 0, 0, 0))
        elif "SELECT id, status_code, h1, title, description, created_at" in query_text:
            self.fetchall_result = [
                (1, 200, "Cabecera principal", "Página de ejemplo", "Descripción de ejemplo", datetime(2024, 1, 1, 0, 0, 0))
            ]
        elif "INSERT INTO url_checks" in query_text:
            self.fetchone_result = None
        else:
            self.fetchone_result = None
            self.fetchall_result = []

    def fetchone(self):
        result = self.fetchone_result
        self.fetchone_result = None
        return result

    def fetchall(self):
        result = self.fetchall_result
        self.fetchall_result = []
        return result

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


@pytest.fixture
def client():
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    with app.test_client() as client:
        yield client


def test_invalid_url_shows_required_message(client):
    response = client.post("/urls", data={"url": "not-a-url"})

    assert response.status_code == 422
    assert b"URL no v\xc3\xa1lido" in response.data


def test_add_url_returns_success_flash(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_db_connection", lambda: FakeConnection())

    response = client.post("/urls", data={"url": "https://example.com"}, follow_redirects=True)

    assert response.status_code == 200
    assert b"La p\xc3\xa1gina se agreg\xc3\xb3 correctamente" in response.data


def test_check_url_returns_required_success_flash(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_db_connection", lambda: FakeConnection())

    class FakeResponse:
        status_code = 200
        text = "<html><head><title>P\xe1gina</title></head><body><h1>Cabecera principal</h1><meta name=\"description\" content=\"Descripci\xf3n\" /></body></html>"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(app_module.requests, "get", lambda *args, **kwargs: FakeResponse())

    response = client.post("/urls/42/checks", follow_redirects=True)

    assert response.status_code == 200
    assert b"La p\xc3\xa1gina fue verificada correctamente" in response.data


def test_check_url_returns_error_flash_on_request_exception(client, monkeypatch):
    monkeypatch.setattr(app_module, "get_db_connection", lambda: FakeConnection())

    def raise_exception(*args, **kwargs):
        raise RequestException("boom")

    monkeypatch.setattr(app_module.requests, "get", raise_exception)

    response = client.post("/urls/42/checks", follow_redirects=True)

    assert response.status_code == 200
    assert b"Ocurri\xc3\xb3 un error durante la verificaci\xc3\xb3n" in response.data
