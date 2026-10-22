import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    customer_id: str = Field(min_length=1, max_length=64)
    total_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: str
    total_amount: Decimal
    status: str
    created_at: datetime
