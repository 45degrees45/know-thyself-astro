import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.database import get_db
from api.models import AccessCode, Chart
from api.schemas import DemoGenerateRequest, DemoRedeemRequest
from api.config import settings

router = APIRouter(tags=["demo"])

WINDOW_MINUTES = 10


@router.post("/demo/generate")
async def generate_codes(req: DemoGenerateRequest, db: AsyncSession = Depends(get_db)):
    if req.secret != settings.demo_secret:
        raise HTTPException(status_code=403, detail="Invalid demo secret")

    codes = []
    for _ in range(req.count):
        code = "DEMO-" + secrets.token_urlsafe(6).upper()
        db.add(AccessCode(code=code))
        codes.append(code)

    await db.commit()
    return {"codes": codes, "window_minutes": WINDOW_MINUTES}


@router.post("/demo/redeem")
async def redeem_code(req: DemoRedeemRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccessCode).where(AccessCode.code == req.code))
    access = result.scalar_one_or_none()

    if not access:
        raise HTTPException(status_code=404, detail="Code not found")
    if access.chart_id and access.chart_id != req.chart_id:
        raise HTTPException(status_code=409, detail="Code already used for a different chart")

    chart_result = await db.execute(select(Chart).where(Chart.id == req.chart_id))
    if not chart_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chart not found")

    now = datetime.now(timezone.utc)
    access.chart_id = req.chart_id

    if access.type == "trusted":
        # Permanent — no expiry
        access.expires_at = None
        await db.commit()
        return {"ok": True, "trusted": True, "expires_at": None}
    else:
        # Demo — extend 10-minute window (allows top-up)
        access.expires_at = now + timedelta(minutes=WINDOW_MINUTES)
        await db.commit()
        return {
            "ok": True,
            "trusted": False,
            "expires_at": access.expires_at.isoformat(),
            "window_minutes": WINDOW_MINUTES,
        }


@router.get("/demo/status/{chart_id}")
async def demo_status(chart_id: str, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(AccessCode).where(
            AccessCode.chart_id == chart_id,
            AccessCode.expires_at > now,
        )
    )
    active = result.scalar_one_or_none()
    if active:
        remaining = int((active.expires_at - now).total_seconds())
        return {"active": True, "expires_at": active.expires_at.isoformat(), "remaining_seconds": remaining}
    return {"active": False}
