"""
Charts router — POST /api/chart and GET /api/chart/{id}.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from api.database import get_db
from api.models import User, Chart
from api.schemas import ChartRequest
from api.services.astro_service import AstroService

router = APIRouter(tags=["charts"])
_astro = AstroService()


@router.post("/chart")
async def create_chart(req: ChartRequest, db: AsyncSession = Depends(get_db)):
    """
    Calculate a Vedic birth chart, persist it, and return a summary.

    Upserts the User by email so repeat submissions from the same person
    accumulate charts under one account rather than creating duplicates.
    """
    # Upsert user by email
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email=req.email, name=req.name)
        db.add(user)
        await db.flush()  # get user.id before FK reference

    # Calculate chart — lat/lon/tz are now returned from calculate()
    try:
        chart_json = _astro.calculate(req.birth_date, req.birth_time, req.birth_place)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    chart = Chart(
        user_id=user.id,
        birth_date=req.birth_date,
        birth_time=req.birth_time,
        birth_place=req.birth_place,
        lat=chart_json["lat"],
        lon=chart_json["lon"],
        tz=chart_json["tz"],
        chart_json=chart_json,
    )
    db.add(chart)
    await db.commit()
    await db.refresh(chart)

    summary = _astro.build_summary(chart_json)
    return {"chart_id": chart.id, **summary}


@router.get("/chart/{chart_id}")
async def get_chart(chart_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve a previously calculated chart by ID.

    Uses selectinload to eagerly fetch the User (needed for `paid` status)
    because async SQLAlchemy does not support lazy loading.
    """
    result = await db.execute(
        select(Chart)
        .where(Chart.id == chart_id)
        .options(selectinload(Chart.user))
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")

    summary = _astro.build_summary(chart.chart_json)
    return {"chart_id": chart.id, **summary, "paid": chart.user.paid}
