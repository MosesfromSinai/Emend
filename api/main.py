"""Emend API. Docker/compose run `uvicorn api.main:app`."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.errors import error_response, register_error_handlers
from api.routers import applications, artifacts, health, jd, resumes


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

    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):
        length = request.headers.get("content-length")
        if (
            length is not None
            and length.isdigit()
            and int(length) > settings.max_body_bytes
        ):
            return error_response(
                413,
                "payload_too_large",
                f"Request body exceeds {settings.max_body_bytes} bytes",
            )
        return await call_next(request)

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
    return app


app = create_app()
