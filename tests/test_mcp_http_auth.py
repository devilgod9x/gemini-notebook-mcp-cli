"""Optional bearer-token authentication for the HTTP/SSE MCP transports."""

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from notebooklm_tools.mcp.http_auth import (
    AUTH_TOKEN_ENV,
    BearerTokenMiddleware,
    build_http_middleware,
    get_auth_token,
)

TOKEN = "a-long-random-token-1234"


def _client(token: str = TOKEN) -> TestClient:
    app = Starlette(routes=[Route("/mcp", lambda r: PlainTextResponse("ok"))])
    app.add_middleware(BearerTokenMiddleware, token=token)
    return TestClient(app)


def test_missing_header_is_rejected():
    resp = _client().get("/mcp")
    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"


def test_wrong_token_is_rejected():
    assert _client().get("/mcp", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_wrong_scheme_is_rejected():
    assert _client().get("/mcp", headers={"Authorization": f"Basic {TOKEN}"}).status_code == 401


def test_correct_token_is_accepted():
    resp = _client().get("/mcp", headers={"Authorization": f"Bearer {TOKEN}"})
    assert resp.status_code == 200 and resp.text == "ok"


def test_scheme_is_case_insensitive():
    resp = _client().get("/mcp", headers={"Authorization": f"bearer {TOKEN}"})
    assert resp.status_code == 200


def test_auth_is_off_by_default(monkeypatch):
    monkeypatch.delenv(AUTH_TOKEN_ENV, raising=False)
    assert get_auth_token() is None
    assert build_http_middleware() is None


def test_short_token_refuses_to_start(monkeypatch):
    monkeypatch.setenv(AUTH_TOKEN_ENV, "short")
    with pytest.raises(ValueError, match="at least"):
        get_auth_token()


def test_blank_token_means_disabled(monkeypatch):
    monkeypatch.setenv(AUTH_TOKEN_ENV, "   ")
    assert get_auth_token() is None


def test_configured_token_builds_middleware(monkeypatch):
    monkeypatch.setenv(AUTH_TOKEN_ENV, TOKEN)
    middleware = build_http_middleware()
    assert middleware and middleware[0].kwargs == {"token": TOKEN}


def test_real_mcp_app_enforces_token(monkeypatch):
    """The FastMCP HTTP app built with our middleware rejects unauthenticated calls."""
    from notebooklm_tools.mcp.server import mcp

    monkeypatch.setenv(AUTH_TOKEN_ENV, TOKEN)
    app = mcp.http_app(path="/mcp", middleware=build_http_middleware())
    with TestClient(app) as client:
        assert client.post("/mcp", json={}).status_code == 401
        authed = client.post("/mcp", json={}, headers={"Authorization": f"Bearer {TOKEN}"})
        assert authed.status_code != 401
