import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order


class OrderRepository:
    """All SQL for orders lives here. Routers never touch the session directly."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, order: Order) -> Order:
        self._session.add(order)
        await self._session.commit()
        await self._session.refresh(order)
        return order

    async def get(self, order_id: uuid.UUID) -> Order | None:
        return await self._session.get(Order, order_id)
