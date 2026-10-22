import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, status
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

NOTIFICATION_LOG: list[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("notifications service starting")
    yield
    logger.info("notifications service shutting down")


app = FastAPI(title="Notifications Service", lifespan=lifespan)


class OrderEvent(BaseModel):
    order_id: str
    customer_id: str
    total_amount: str
    status: str
    event_type: str


@app.get("/healthz", status_code=status.HTTP_200_OK)
async def healthz():
    return {"status": "healthy"}


@app.get("/readyz", status_code=status.HTTP_200_OK)
async def readyz():
    return {"status": "ready"}


@app.post("/notify", status_code=status.HTTP_202_ACCEPTED)
async def notify(event: OrderEvent):
    record = {
        "order_id": event.order_id,
        "customer_id": event.customer_id,
        "event_type": event.event_type,
        "total_amount": event.total_amount,
        "status": event.status,
        "notified_at": datetime.utcnow().isoformat() + "Z",
        "channel": "email",
    }
    NOTIFICATION_LOG.append(record)
    logger.info("notification sent: order=%s customer=%s event=%s", event.order_id, event.customer_id, event.event_type)
    return {"message": "notification accepted", "record": record}


@app.get("/notifications", status_code=status.HTTP_200_OK)
async def list_notifications():
    return NOTIFICATION_LOG
