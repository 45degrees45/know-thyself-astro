import csv
import io
import secrets as _secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from api.database import get_db
from api.models import User, Chart, AccessCode, QuestionBank, TrustedEmailWhitelist
from api.config import settings
from api.schemas import TrustedCodeGenerateRequest, WhitelistAddRequest, DemoCodeCreateRequest

router = APIRouter(tags=["admin"])

DEFAULT_QUESTIONS = [
    # know_thyself
    ("know_thyself", "What is my core life purpose according to my chart?"),
    ("know_thyself", "What are my biggest natural strengths?"),
    ("know_thyself", "What shadow traits should I work on?"),
    ("know_thyself", "What makes me unique compared to others?"),
    ("know_thyself", "What drives me at the deepest level?"),
    ("know_thyself", "How do others perceive me vs who I really am?"),
    # trending
    ("trending", "What does my chart say about 2026?"),
    ("trending", "What is my biggest opportunity right now?"),
    ("trending", "What should I focus on in the next 6 months?"),
    ("trending", "What karmic lesson am I working through currently?"),
    # spiritual
    ("spiritual", "What is my spiritual path according to my chart?"),
    ("spiritual", "What past life karma am I carrying into this life?"),
    ("spiritual", "Why do I feel deeply drawn to certain practices or places?"),
    ("spiritual", "What is my relationship with the divine?"),
    ("spiritual", "What does my Ketu placement say about my soul's history?"),
    # career
    ("career", "What career domains suit me best?"),
    ("career", "When is my peak career period in this dasha?"),
    ("career", "What are my natural professional strengths?"),
    ("career", "Am I in the right field for my chart?"),
    ("career", "What holds me back from professional success?"),
    # relationship
    ("relationship", "What kind of partner am I in a relationship?"),
    ("relationship", "What do I need most from a partner to feel loved?"),
    ("relationship", "What does my 7th house say about my marriage?"),
    ("relationship", "Why do certain relationship patterns keep repeating?"),
    ("relationship", "When is a promising window for committed partnership?"),
    # last_question
    ("last_question", "What is the one thing my chart most wants me to know?"),
    ("last_question", "If I could ask my chart one question, what would the answer be?"),
]


def _auth(secret: str):
    if secret != settings.demo_secret:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/admin/seed-questions")
async def seed_questions(secret: str, db: AsyncSession = Depends(get_db)):
    _auth(secret)
    existing = await db.execute(select(QuestionBank))
    if existing.scalars().all():
        return {"ok": True, "message": "Already seeded — no changes made"}

    for tab, question in DEFAULT_QUESTIONS:
        db.add(QuestionBank(tab=tab, question=question, active=True))
    await db.commit()
    return {"ok": True, "seeded": len(DEFAULT_QUESTIONS)}


@router.get("/admin/export")
async def export_csv(secret: str, db: AsyncSession = Depends(get_db)):
    _auth(secret)

    users_result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = {u.id: u for u in users_result.scalars().all()}

    charts_result = await db.execute(select(Chart).order_by(Chart.created_at.desc()))
    charts = charts_result.scalars().all()

    codes_result = await db.execute(select(AccessCode))
    codes_by_chart: dict[str, list[AccessCode]] = {}
    for code in codes_result.scalars().all():
        if code.chart_id:
            codes_by_chart.setdefault(code.chart_id, []).append(code)

    now = datetime.now(timezone.utc)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "chart_id", "name", "email", "birth_date", "birth_time",
        "birth_place", "paid", "demo_active", "demo_expires",
        "chart_created_at",
    ])

    for chart in charts:
        user = users.get(chart.user_id)
        chart_codes = codes_by_chart.get(chart.id, [])
        active_code = next((c for c in chart_codes if c.expires_at and c.expires_at > now), None)

        writer.writerow([
            chart.id,
            user.name if user else "",
            user.email if user else "",
            chart.birth_date,
            chart.birth_time,
            chart.birth_place,
            "Yes" if (user and user.paid) else "No",
            "Yes" if active_code else "No",
            active_code.expires_at.strftime("%Y-%m-%d %H:%M UTC") if active_code else "",
            chart.created_at.strftime("%Y-%m-%d %H:%M UTC"),
        ])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=astrowise_users.csv"},
    )


@router.post("/admin/demo-codes/create")
async def create_demo_code(req: DemoCodeCreateRequest, db: AsyncSession = Depends(get_db)):
    if req.secret != settings.demo_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    chart_result = await db.execute(select(Chart).where(Chart.id == req.chart_id))
    if not chart_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Chart not found")
    code = "DEMO-" + _secrets.token_urlsafe(6).upper()
    db.add(AccessCode(code=code, chart_id=req.chart_id, note=req.note))
    await db.commit()
    return {"code": code, "chart_id": req.chart_id}


@router.post("/admin/trusted-codes/generate")
async def generate_trusted_codes(req: TrustedCodeGenerateRequest, db: AsyncSession = Depends(get_db)):
    if req.secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    codes = []
    for _ in range(req.count):
        code = "TRUST-" + _secrets.token_urlsafe(6).upper()
        db.add(AccessCode(code=code, type="trusted", note=req.note))
        codes.append({"code": code})
    await db.commit()
    return {"codes": codes}


@router.post("/admin/whitelist/add")
async def add_to_whitelist(req: WhitelistAddRequest, db: AsyncSession = Depends(get_db)):
    if req.secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    existing = await db.execute(
        select(TrustedEmailWhitelist).where(TrustedEmailWhitelist.email == req.email)
    )
    if existing.scalar_one_or_none():
        return {"ok": True, "message": "Already whitelisted"}
    db.add(TrustedEmailWhitelist(email=req.email, note=req.note))
    await db.commit()
    return {"ok": True}


@router.post("/admin/patch-name")
async def patch_user_name(secret: str, chart_id: str, name: str, db: AsyncSession = Depends(get_db)):
    if secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(select(Chart).where(Chart.id == chart_id))
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    user_result = await db.execute(select(User).where(User.id == chart.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.name = name
    await db.commit()
    return {"ok": True, "name": name}


@router.get("/admin/trusted-users")
async def list_trusted_users(secret: str, db: AsyncSession = Depends(get_db)):
    if secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    result = await db.execute(
        select(AccessCode, Chart, User)
        .join(Chart, AccessCode.chart_id == Chart.id, isouter=True)
        .join(User, Chart.user_id == User.id, isouter=True)
        .where(AccessCode.type == "trusted")
        .order_by(AccessCode.created_at.desc())
    )
    rows = []
    for code, chart, user in result.all():
        rows.append({
            "code": code.code,
            "note": code.note,
            "email": user.email if user else None,
            "name": user.name if user else None,
            "chart_id": code.chart_id,
            "redeemed": code.chart_id is not None,
            "created_at": code.created_at.isoformat(),
        })
    return rows
