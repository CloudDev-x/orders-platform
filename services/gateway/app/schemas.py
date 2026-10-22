from decimal import Decimal

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    """Validated at the edge, so bad input never reaches the orders service."""

    customer_id: str = Field(min_length=1, max_length=64)
    total_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
