import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app.config import get_settings
from app.logging_config import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("gateway")

REQUEST_ID_HEADER = "X-Request-ID"

app = FastAPI(title="gateway")


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
    # Liveness: the process is up and able to serve. No dependency checks here,
    # because a failing dependency should not make Kubernetes restart the pod.
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    # Readiness: should this pod receive traffic? No dependencies yet.
    # When the orders client is added, check it here and return 503 on failure.
    return {"status": "ready"}
