import uuid
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.clients.orders import OrdersClient
from app.schemas import OrderCreate

router = APIRouter(prefix="/orders", tags=["orders"])


def get_orders_client(request: Request) -> OrdersClient:
    return OrdersClient(request.app.state.orders_http)


OrdersDep = Annotated[OrdersClient, Depends(get_orders_client)]


def _passthrough(upstream: httpx.Response) -> Response:
    # Return orders' status and body unchanged, so a 404 or 422 from orders reaches the caller as-is
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type"),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, request: Request, client: OrdersDep) -> Response:
    try:
        upstream = await client.create_order(
            payload.model_dump(mode="json"), request.state.request_id
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "orders service timed out") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "orders service unavailable") from exc
    return _passthrough(upstream)


@router.get("/{order_id}")
async def get_order(order_id: uuid.UUID, request: Request, client: OrdersDep) -> Response:
    try:
        upstream = await client.get_order(str(order_id), request.state.request_id)
    except httpx.TimeoutException as exc:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "orders service timed out") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "orders service unavailable") from exc
    return _passthrough(upstream)
