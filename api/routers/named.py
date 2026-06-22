from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from datetime import datetime, timezone

from api.database import get_db
from api.models import User, Chart, AccessCode
from api.config import settings

router = APIRouter(tags=["named"])

FRONTEND = "https://astrowyze.netlify.app"


@router.get("/u/{name}")
async def named_profile(name: str, db: AsyncSession = Depends(get_db)):
    # Find user by name (case-insensitive)
    result = await db.execute(
        select(User).where(func.lower(User.name) == name.lower())
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"No profile found for '{name}'")

    # Get their most recent chart
    chart_result = await db.execute(
        select(Chart)
        .where(Chart.user_id == user.id)
        .order_by(Chart.created_at.desc())
        .limit(1)
    )
    chart = chart_result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail=f"No chart found for '{name}'")

    # Find a valid demo/trusted code linked to this chart
    now = datetime.now(timezone.utc)
    code_result = await db.execute(
        select(AccessCode).where(
            AccessCode.chart_id == chart.id,
            or_(AccessCode.expires_at.is_(None), AccessCode.expires_at > now),
        ).limit(1)
    )
    access = code_result.scalar_one_or_none()

    url = f"{FRONTEND}/profile/{chart.id}"
    if access:
        url += f"?demo={access.code}"

    return RedirectResponse(url=url, status_code=302)
