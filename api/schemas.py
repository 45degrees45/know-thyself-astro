from pydantic import BaseModel, EmailStr
from typing import Any


class ChartRequest(BaseModel):
    name: str
    birth_date: str   # YYYY-MM-DD
    birth_time: str   # HH:MM (24h)
    birth_place: str
    email: EmailStr


class ChartSummary(BaseModel):
    chart_id: str
    lagna: str
    lagna_deg: float
    current_dasha: str
    yogas: list[str]
    animal: str
    animal_desc: str


class ChatRequest(BaseModel):
    chart_id: str
    tab: str
    message: str


class PaymentOrderRequest(BaseModel):
    chart_id: str


class PaymentVerifyRequest(BaseModel):
    chart_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
