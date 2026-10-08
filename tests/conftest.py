import pytest
import requests


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('DDNS_API_PASSWORD', raising=False)
    def forbidden(*args, **kwargs):
        pytest.fail('Real network requests are forbidden in tests')
    monkeypatch.setattr(requests.sessions.Session, 'request', forbidden)
