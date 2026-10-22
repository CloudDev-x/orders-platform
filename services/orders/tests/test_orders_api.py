import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # Run the app's lifespan so the engine and session factory exist, as they do in production
    async with app.router.lifespan_context(app):
        async with app.state.engine.begin() as connection:
            await connection.execute(text("TRUNCATE TABLE orders"))
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


async def test_create_then_fetch_order(client: AsyncClient) -> None:
    created = await client.post("/orders", json={"customer_id": "cust-1", "total_amount": "10.50"})
    assert created.status_code == 201
    order = created.json()
    assert order["status"] == "pending"

    fetched = await client.get(f"/orders/{order['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["customer_id"] == "cust-1"


async def test_missing_order_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/orders/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_rejects_non_positive_amount(client: AsyncClient) -> None:
    response = await client.post("/orders", json={"customer_id": "cust-1", "total_amount": "-5"})
    assert response.status_code == 422


async def test_readyz_reports_ready_when_database_is_up(client: AsyncClient) -> None:
    response = await client.get("/readyz")
    assert response.status_code == 200
