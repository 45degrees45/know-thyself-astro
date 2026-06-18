from pydantic import BaseModel, EmailStr, Field
from typing import Any, Literal


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
    animal_emoji: str
    paid: bool = False
    trusted: bool = False
    profile_html_ready: bool = False


class ChatRequest(BaseModel):
    chart_id: str
    tab: Literal["know_thyself", "trending", "spiritual", "career", "relationship", "last_question"]
    message: str = Field(..., max_length=2000)


class PaymentOrderRequest(BaseModel):
    chart_id: str


class PaymentVerifyRequest(BaseModel):
    chart_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class DemoGenerateRequest(BaseModel):
    secret: str
    count: int = Field(default=1, ge=1, le=50)


class DemoRedeemRequest(BaseModel):
    code: str
    chart_id: str | None = None  # optional when code is pre-linked to a chart


class DemoCodeCreateRequest(BaseModel):
    secret: str
    chart_id: str
    note: str | None = None


class TrustedCodeGenerateRequest(BaseModel):
    secret: str
    count: int = Field(default=1, ge=1, le=20)
    note: str | None = None


class WhitelistAddRequest(BaseModel):
    secret: str
    email: EmailStr
    note: str | None = None
