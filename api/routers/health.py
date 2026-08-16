import logging

from fastapi import APIRouter
from sqlalchemy import text

from api import db as db_module
from api.errors import error_response
from api.schemas import HealthOut

logger = logging.getLogger("emend.health")

router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health():
    # A healthcheck that can't reach the database is exactly the deploy
    # Railway's healthcheckPath exists to catch -- returning "ok"
    # unconditionally would let a broken deploy (dead DB connection,
    # exhausted pool) take live traffic and only fail on a real request.
    # Connects directly via the engine (not the request-scoped
    # Depends(get_db) session) so a connection failure surfaces here,
    # inside this function's own try/except, rather than during dependency
    # resolution before the route body even runs.
    try:
        with db_module.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        logger.exception("health check: database unreachable")
        return error_response(503, "db_unreachable", "Database is unreachable")
    return HealthOut(status="ok")
