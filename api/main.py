"""Emend API. Docker/compose run `uvicorn api.main:app`."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.errors import ApiError, error_response, register_error_handlers
from api.routers import account, applications, artifacts, health, jd, resumes


class BodySizeLimitMiddleware:
    """Rejects any request body over `max_bytes`, streamed or not.

    A plain ASGI middleware (not `@app.middleware("http")`/BaseHTTPMiddleware)
    on purpose: BaseHTTPMiddleware forwards the body to the downstream app
    through its own background task, and overriding `receive` there raises
    the size-limit error inside that task instead of the request's own call
    stack -- it surfaces as an unhandled ExceptionGroup, not a clean 413.
    Wrapping `receive` at the raw ASGI level avoids that entirely.

    Content-Length is checked first as a fast path, but it's advisory and
    absent on a chunked-encoded request -- the real enforcement is the
    running byte count in `limited_receive`, which catches an oversized body
    regardless of what headers claim about its size.
    """

    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        content_length = headers.get(b"content-length")
        if content_length is not None and content_length.isdigit():
            if int(content_length) > self.max_bytes:
                await self._reject(scope, receive, send)
                return

        total = 0

        async def limited_receive():
            nonlocal total
            message = await receive()
            if message["type"] == "http.request":
                total += len(message.get("body", b""))
                if total > self.max_bytes:
                    raise ApiError(
                        413,
                        "payload_too_large",
                        f"Request body exceeds {self.max_bytes} bytes",
                    )
            return message

        await self.app(scope, limited_receive, send)

    async def _reject(self, scope, receive, send) -> None:
        response = error_response(
            413, "payload_too_large", f"Request body exceeds {self.max_bytes} bytes"
        )
        await response(scope, receive, send)


def create_app() -> FastAPI:
    # Interactive docs are a full, unauthenticated map of every route and
    # schema -- free reconnaissance for an attacker once real user data is
    # flowing through this API, so they're only served in local development.
    is_dev = settings.environment == "development"
    app = FastAPI(
        title="Emend API",
        version="0.1.0",
        docs_url="/docs" if is_dev else None,
        redoc_url="/redoc" if is_dev else None,
        openapi_url="/openapi.json" if is_dev else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_bytes)

    @app.middleware("http")
    async def attach_session_cookie(request: Request, call_next):
        # Runs after routing/exception handling either way, so a brand-new
        # visitor's session cookie lands even when the request that created
        # it goes on to fail (see api/sessions.py's current_session).
        response = await call_next(request)
        new_session_id = getattr(request.state, "new_session_id", None)
        if new_session_id is not None:
            response.set_cookie(
                key=settings.session_cookie_name,
                value=str(new_session_id),
                max_age=settings.session_cookie_max_age,
                httponly=True,
                secure=settings.session_cookie_secure,
                samesite=settings.session_cookie_samesite,
                path="/",
            )
        return response

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(resumes.router)
    app.include_router(applications.router)
    app.include_router(jd.router)
    app.include_router(artifacts.router)
    app.include_router(account.router)
    return app


app = create_app()
