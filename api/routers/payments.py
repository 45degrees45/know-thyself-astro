import asyncio
import hmac
import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.database import get_db
from api.models import Chart
from api.schemas import PaymentOrderRequest, PaymentVerifyRequest
from api.config import settings

router = APIRouter(tags=["payments"])

AMOUNT_PAISE = 5000  # ₹50


@router.post("/payments/order")
async def create_order(req: PaymentOrderRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chart).where(Chart.id == req.chart_id))
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    import razorpay
    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    order = await asyncio.to_thread(
        client.order.create,
        {"amount": AMOUNT_PAISE, "currency": "INR", "notes": {"chart_id": req.chart_id}},
    )
    return {
        "order_id": order["id"],
        "amount": AMOUNT_PAISE,
        "currency": "INR",
        "key_id": settings.razorpay_key_id,
    }


@router.post("/payments/verify")
async def verify_payment(req: PaymentVerifyRequest, db: AsyncSession = Depends(get_db)):
    expected = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{req.razorpay_order_id}|{req.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, req.razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Get chart_id from Razorpay order notes (not from client-supplied req.chart_id)
    import razorpay
    rzp_client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    rzp_order = await asyncio.to_thread(rzp_client.order.fetch, req.razorpay_order_id)
    chart_id = rzp_order.get("notes", {}).get("chart_id")
    if not chart_id:
        raise HTTPException(status_code=400, detail="Order has no chart_id in notes")

    result = await db.execute(
        select(Chart).where(Chart.id == chart_id).options(selectinload(Chart.user))
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    if not chart.user:
        raise HTTPException(status_code=500, detail="Chart has no associated user")

    if not chart.user.paid:
        chart.user.paid = True
        await db.commit()
    return {"paid": True, "chart_id": chart_id}
