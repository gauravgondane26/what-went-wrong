"""CORS: fixed origins from CORS_ORIGINS, plus an optional CORS_ORIGIN_REGEX
(used by the staging API to accept Netlify branch and deploy-preview URLs)."""
from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

SITE_REGEX = r"https://(staging|deploy-preview-\d+)--www-demo\.netlify\.app"


def _app(monkeypatch, **env):
    from app import config

    for key in ("CORS_ORIGINS", "CORS_ORIGIN_REGEX"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    importlib.reload(config)
    import main

    return importlib.reload(main).app


@pytest.fixture(autouse=True)
def _restore(monkeypatch):
    yield
    monkeypatch.undo()
    from app import config

    importlib.reload(config)
    import main

    importlib.reload(main)


def _allowed(app, origin: str) -> str | None:
    with TestClient(app) as client:
        res = client.get("/api/v1/health", headers={"Origin": origin})
    assert res.status_code == 200
    return res.headers.get("access-control-allow-origin")


def test_default_allows_local_dev_only(monkeypatch):
    app = _app(monkeypatch)
    assert _allowed(app, "http://localhost:5173") == "http://localhost:5173"
    assert _allowed(app, "https://staging--www-demo.netlify.app") is None


def test_regex_allows_staging_and_previews(monkeypatch):
    app = _app(monkeypatch, CORS_ORIGINS="https://www-demo.netlify.app", CORS_ORIGIN_REGEX=SITE_REGEX)
    for origin in (
        "https://www-demo.netlify.app",
        "https://staging--www-demo.netlify.app",
        "https://deploy-preview-12--www-demo.netlify.app",
    ):
        assert _allowed(app, origin) == origin
    assert _allowed(app, "https://evil--www-demo.netlify.app") is None
    assert _allowed(app, "https://staging--other.netlify.app") is None
