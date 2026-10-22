import asyncio
import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.orders import router as orders_router
from app.config import get_settings
from app.db import create_engine, make_session_factory
from app.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("orders")

REQUEST_ID_HEADER = "X-Request-ID"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_engine(settings)
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(title="orders", lifespan=lifespan)
app.include_router(orders_router)


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    # Orders is internal-only: it accepts the ID the gateway sent, and only makes one if missing.
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code}",
        extra={"request_id": request_id},
    )
    return response


@app.get("/healthz")
def healthz() -> dict[str, str]:
    # Liveness: the process is up. Never checks the database.
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> Response:
    # Readiness: can this pod do real work? Bounded so a hung database fails the probe.
    try:
        async with asyncio.timeout(2):
            async with app.state.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
    except Exception:
        logger.exception("readiness check failed", extra={"check": "database"})
        return JSONResponse(
            {"status": "unavailable", "check": "database"}, status_code=503
        )
    return JSONResponse({"status": "ready"})
