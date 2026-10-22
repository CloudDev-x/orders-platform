import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order
from app.repositories.orders import OrderRepository
from app.schemas import OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    # One session per request, closed when the response is sent
    async with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderRead)
async def create_order(payload: OrderCreate, session: SessionDep) -> Order:
    order = Order(customer_id=payload.customer_id, total_amount=payload.total_amount)
    return await OrderRepository(session).add(order)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(order_id: uuid.UUID, session: SessionDep) -> Order:
    order = await OrderRepository(session).get(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
    return order
