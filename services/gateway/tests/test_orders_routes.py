import asyncio
import json
import uuid
from collections.abc import Callable

import httpx
from httpx import ASGITransport, AsyncClient

from app.main import app

Handler = Callable[[httpx.Request], httpx.Response]


async def call(handler: Handler, method: str, url: str, **kwargs: object) -> httpx.Response:
    async with app.router.lifespan_context(app):
        app.state.orders_http = httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url="http://orders"
        )
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await client.request(method, url, **kwargs)  # type: ignore[arg-type]


def test_create_order_forwards_body_and_request_id() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["request_id"] = request.headers.get("x-request-id")
        return httpx.Response(201, json={"id": "abc"})

    payload = {"customer_id": "cust_1", "total_amount": "25.00"}
    resp = asyncio.run(call(handler, "POST", "/orders", json=payload))

    assert resp.status_code == 201
    assert resp.json() == {"id": "abc"}
    assert seen["body"] == payload
    assert seen["request_id"] == resp.headers["x-request-id"]


def test_create_order_rejects_invalid_payload_without_calling_upstream() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(201, json={})

    resp = asyncio.run(
        call(handler, "POST", "/orders", json={"customer_id": "", "total_amount": "-1"})
    )

    assert resp.status_code == 422
    assert calls == []


def test_get_order_passes_through_found() -> None:
    order_id = uuid.uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/orders/{order_id}"
        return httpx.Response(200, json={"id": str(order_id)})

    resp = asyncio.run(call(handler, "GET", f"/orders/{order_id}"))

    assert resp.status_code == 200
    assert resp.json() == {"id": str(order_id)}


def test_get_order_passes_through_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "order not found"})

    resp = asyncio.run(call(handler, "GET", f"/orders/{uuid.uuid4()}"))

    assert resp.status_code == 404
    assert resp.json() == {"detail": "order not found"}


def test_upstream_timeout_maps_to_504() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    resp = asyncio.run(call(handler, "GET", f"/orders/{uuid.uuid4()}"))

    assert resp.status_code == 504
    assert resp.json() == {"detail": "orders service timed out"}


def test_upstream_unreachable_maps_to_502() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    resp = asyncio.run(
        call(handler, "POST", "/orders", json={"customer_id": "cust_1", "total_amount": "5.00"})
    )

    assert resp.status_code == 502
    assert resp.json() == {"detail": "orders service unavailable"}
