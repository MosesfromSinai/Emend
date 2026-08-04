"""Emend API. Docker/compose run `uvicorn api.main:app`."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.errors import error_response, register_error_handlers
from api.routers import applications, artifacts, health, jd, resumes


def create_app() -> FastAPI:
    app = FastAPI(title="Emend API", version="0.1.0")

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

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(resumes.router)
    app.include_router(applications.router)
    app.include_router(jd.router)
    app.include_router(artifacts.router)
    return app


app = create_app()
