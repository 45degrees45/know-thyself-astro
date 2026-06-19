import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from api.database import get_db, AsyncSessionLocal
from api.models import Chart, ChatMessage, AccessCode
from api.schemas import ChatRequest
from api.services.llm_adapter import LLMAdapter
from api.config import settings

router = APIRouter(tags=["chat"])
FREE_DAILY_LIMIT = 9999  # all users get unlimited access

CHAT_SYSTEM = """You are AstroWise — a wise, warm Vedic astrology guide.
The user's birth chart context is given below. Answer ONLY from what the chart shows.
Be specific to their placements — never generic.
Avoid fortune-teller certainty. Use "this chart suggests" and "you may notice".
Give complete, satisfying answers — never cut off mid-thought. 300–500 words is ideal.
When classical references are provided, cite them naturally (e.g. "As Parashara notes…").

{chart_context}

{book_passages}"""


def _build_chart_context(chart_json: dict) -> str:
    if not isinstance(chart_json, dict):
        chart_json = {}
    yogas = chart_json.get('yogas') or []
    return (
        f"Lagna: {chart_json.get('lagna', 'unknown')} {chart_json.get('lagna_deg', '')}° | "
        f"Dasha: {chart_json.get('current_dasha', 'unknown')} | "
        f"Yogas: {', '.join(yogas)} | "
        f"Animal: {chart_json.get('animal', 'unknown')} | "
        f"Moon Nakshatra: {chart_json.get('moon_nakshatra', 'unknown')}"
    )


@router.post("/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chart).where(Chart.id == req.chart_id).options(selectinload(Chart.user))
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    if not chart.user:
        raise HTTPException(status_code=500, detail="Chart has no associated user")

    is_trusted = False
    if not chart.user.paid:
        now = datetime.now(timezone.utc)
        code_result = await db.execute(
            select(AccessCode).where(
                AccessCode.chart_id == req.chart_id,
                or_(
                    and_(AccessCode.type == "demo", AccessCode.expires_at > now),
                    and_(AccessCode.type == "trusted", AccessCode.expires_at.is_(None)),
                ),
            )
        )
        access = code_result.scalar_one_or_none()
        is_trusted = access is not None and access.type == "trusted"
        has_access = access is not None

        if not has_access:
            since = now - timedelta(days=1)
            count_result = await db.execute(
                select(func.count()).where(
                    ChatMessage.chart_id == req.chart_id,
                    ChatMessage.role == "user",
                    ChatMessage.created_at >= since,
                )
            )
            if count_result.scalar() >= FREE_DAILY_LIMIT:
                raise HTTPException(
                    status_code=403,
                    detail="Daily free limit reached. Unlock full access for ₹50.",
                )

    # Save user message
    db.add(ChatMessage(chart_id=req.chart_id, tab=req.tab, role="user", content=req.message))
    await db.commit()

    from api.services.report_service import _make_adapter
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "astro_engine"))
        from book_rag import search_books, format_for_prompt
        rag_query = f"{chart.chart_json.get('lagna','')} lagna {chart.chart_json.get('moon_nakshatra','')} {req.message}"
        passages = search_books(rag_query, k=3)
        book_passages = format_for_prompt(passages) if passages else ""
    except Exception:
        book_passages = ""

    adapter = _make_adapter()
    chart_context = _build_chart_context(chart.chart_json)
    system = CHAT_SYSTEM.format(chart_context=chart_context, book_passages=book_passages)
    if is_trusted:
        system += (
            "\n\nThis user has access to their own natal chart only. "
            "If they reference another person's birth details (date, time, place) "
            "in the context of compatibility or relationship matching, you may provide "
            "a brief synastry analysis only. Do not provide a full standalone natal "
            "reading for any other person."
        )
    chart_id = req.chart_id
    tab = req.tab

    async def event_stream():
        full_response = []
        try:
            async for chunk in adapter.stream(req.message, system):
                full_response.append(chunk)
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            return
        # Save assistant reply in a new session (the request DB session is closed)
        try:
            async with AsyncSessionLocal() as save_db:
                save_db.add(ChatMessage(
                    chart_id=chart_id,
                    tab=tab,
                    role="assistant",
                    content="".join(full_response),
                ))
                await save_db.commit()
        except Exception:
            logging.exception("Failed to save assistant reply for chart_id=%s", chart_id)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
