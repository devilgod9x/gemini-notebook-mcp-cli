"""Optional bearer-token authentication for the HTTP/SSE MCP transports.

Without it, any local process that can reach the port can call tools and act
through the saved Google session. Set ``NOTEBOOKLM_MCP_AUTH_TOKEN`` to require
``Authorization: Bearer <token>`` on every request. Off by default so existing
HTTP setups keep working.
"""

import hmac
import json
import os

AUTH_TOKEN_ENV = "NOTEBOOKLM_MCP_AUTH_TOKEN"
MIN_TOKEN_LENGTH = 16


def get_auth_token() -> str | None:
    """Return the configured token, or None when auth is not enabled.

    Raises:
        ValueError: If a token is set but too short to be worth anything.
    """
    token = os.environ.get(AUTH_TOKEN_ENV, "").strip()
    if not token:
        return None
    if len(token) < MIN_TOKEN_LENGTH:
        raise ValueError(
            f"{AUTH_TOKEN_ENV} must be at least {MIN_TOKEN_LENGTH} characters "
            "(use a long random string)."
        )
    return token


class BearerTokenMiddleware:
    """Pure ASGI middleware that rejects requests without the right bearer token."""

    def __init__(self, app, token: str) -> None:
        self.app = app
        self._token = token.encode("utf-8")

    def _authorized(self, scope) -> bool:
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                scheme, _, supplied = value.partition(b" ")
                if scheme.lower() != b"bearer":
                    return False
                # Constant-time comparison so the token can't be guessed byte by byte.
                return hmac.compare_digest(supplied.strip(), self._token)
        return False

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in ("http", "websocket") or self._authorized(scope):
            await self.app(scope, receive, send)
            return

        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return

        body = json.dumps({"error": "unauthorized"}).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"www-authenticate", b"Bearer"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def build_http_middleware() -> list | None:
    """Return the Starlette middleware list for FastMCP, or None if auth is off."""
    token = get_auth_token()
    if token is None:
        return None
    from starlette.middleware import Middleware

    return [Middleware(BearerTokenMiddleware, token=token)]
