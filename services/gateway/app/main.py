import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, Response

from app.api.orders import router as orders_router
from app.config import get_settings
from app.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("gateway")

REQUEST_ID_HEADER = "X-Request-ID"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # One shared client per process: connection pooling, one timeout policy for all calls to orders
    async with httpx.AsyncClient(
        base_url=settings.orders_base_url,
        timeout=settings.http_timeout_seconds,
    ) as orders_http:
        app.state.orders_http = orders_http
        yield


app = FastAPI(title="gateway", lifespan=lifespan)
app.include_router(orders_router)


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    # The gateway is the edge: it always generates the ID, never trusts a client-supplied one.
    request_id = str(uuid.uuid4())
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
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    # Deliberately does not check orders. If it did, an orders outage would take the gateway out of
    # rotation too, and every route would fail for the same reason.
    return {"status": "ready"}
