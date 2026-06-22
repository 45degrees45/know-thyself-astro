import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from api.database import get_db
from api.models import AccessCode, Chart
from api.schemas import DemoGenerateRequest, DemoRedeemRequest
from api.config import settings

router = APIRouter(tags=["demo"])

WINDOW_MINUTES = 1


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


@router.get("/demo/lookup/{code}")
async def lookup_code(code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccessCode).where(AccessCode.code == code))
    access = result.scalar_one_or_none()
    if not access:
        return {"ok": False, "error": "not_found"}
    return {
        "ok": True,
        "type": access.type,
        "chart_id": access.chart_id,
        "pre_linked": access.chart_id is not None,
    }


@router.post("/demo/redeem")
async def redeem_code(req: DemoRedeemRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccessCode).where(AccessCode.code == req.code))
    access = result.scalar_one_or_none()

    if not access:
        raise HTTPException(status_code=404, detail="Code not found")

    # Resolve chart_id: prefer request value, fall back to pre-linked
    chart_id = req.chart_id or access.chart_id
    if not chart_id:
        raise HTTPException(status_code=400, detail="chart_id required for this code")
    if access.chart_id and access.chart_id != chart_id:
        raise HTTPException(status_code=409, detail="Code already used for a different chart")

    chart_result = await db.execute(select(Chart).where(Chart.id == chart_id))
    if not chart_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chart not found")

    access.chart_id = chart_id
    access.expires_at = None  # permanent for all code types
    await db.commit()
    return {"ok": True, "expires_at": None}


@router.get("/demo/status/{chart_id}")
async def demo_status(chart_id: str, db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(AccessCode).where(
            AccessCode.chart_id == chart_id,
            or_(AccessCode.expires_at.is_(None), AccessCode.expires_at > now),
        )
    )
    active = result.scalar_one_or_none()
    if active:
        return {"active": True, "expires_at": None, "remaining_seconds": None}
    return {"active": False}
