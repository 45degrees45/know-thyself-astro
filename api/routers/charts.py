"""
Charts router — POST /api/chart, GET /api/chart/{id}, GET /api/chart/{id}/reading.
"""
import asyncio
import logging
import secrets as _secrets

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload

from api.database import get_db, AsyncSessionLocal
from api.models import User, Chart, AccessCode, TrustedEmailWhitelist
from api.schemas import ChartRequest, ChartSummary
from api.services.astro_service import AstroService

router = APIRouter(tags=["charts"])
_astro = AstroService()


async def _save_profile_html(chart_id: str, chart_json: dict, name: str) -> None:
    """Background task: generate profile HTML and persist it."""
    try:
        html = await asyncio.to_thread(_astro.generate_profile_html, chart_json, name)
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Chart).where(Chart.id == chart_id))
            chart = result.scalar_one_or_none()
            if chart:
                chart.profile_html = html
                await db.commit()
    except Exception:
        logging.exception("Profile HTML generation failed for chart_id=%s", chart_id)


@router.post("/chart", response_model=ChartSummary, status_code=201)
async def create_chart(
    req: ChartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate a Vedic birth chart, persist it, and return a summary.

    Upserts the User by email. Auto-grants trusted access if email is whitelisted.
    Triggers async profile HTML generation after response is sent.
    """
    # Upsert user by email — safe against concurrent duplicate inserts
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email=req.email, name=req.name)
        db.add(user)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            result = await db.execute(select(User).where(User.email == req.email))
            user = result.scalar_one()
    else:
        user.name = req.name

    # Calculate chart — runs in thread to avoid blocking the event loop
    try:
        chart_json = await asyncio.to_thread(
            _astro.calculate, req.birth_date, req.birth_time, req.birth_place
        )
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

    # Check email whitelist for auto-trusted grant
    wl_result = await db.execute(
        select(TrustedEmailWhitelist).where(TrustedEmailWhitelist.email == req.email)
    )
    trusted = wl_result.scalar_one_or_none() is not None

    await db.commit()
    await db.refresh(chart)

    # Auto-create permanent trusted AccessCode for whitelisted users
    if trusted:
        code = "TRUST-" + _secrets.token_urlsafe(6).upper()
        db.add(AccessCode(code=code, chart_id=chart.id, type="trusted", expires_at=None))
        await db.commit()

    # Generate profile HTML after response is sent
    background_tasks.add_task(_save_profile_html, chart.id, chart_json, req.name)

    summary = _astro.build_summary(chart_json)
    return {
        "chart_id": chart.id,
        "name": req.name,
        **summary,
        "paid": user.paid,
        "trusted": trusted,
        "profile_html_ready": False,
    }


@router.get("/chart/{chart_id}/reading", response_class=HTMLResponse)
async def get_reading(chart_id: str, db: AsyncSession = Depends(get_db)):
    """Return the generated full natal profile HTML."""
    result = await db.execute(select(Chart).where(Chart.id == chart_id))
    chart = result.scalar_one_or_none()
    if not chart or not chart.profile_html:
        raise HTTPException(status_code=404, detail="Reading not ready yet")
    return HTMLResponse(content=chart.profile_html)


@router.get("/chart/{chart_id}", response_model=ChartSummary)
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

    # Check if a permanent trusted code exists for this chart
    trusted_result = await db.execute(
        select(AccessCode).where(
            AccessCode.chart_id == chart_id,
            AccessCode.type == "trusted",
            AccessCode.expires_at.is_(None),
        )
    )
    trusted = trusted_result.scalar_one_or_none() is not None

    summary = _astro.build_summary(chart.chart_json)
    return {
        "chart_id": chart.id,
        "name": chart.user.name or "",
        **summary,
        "paid": chart.user.paid,
        "trusted": trusted,
        "profile_html_ready": chart.profile_html is not None,
    }
