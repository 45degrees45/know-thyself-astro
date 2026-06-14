import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from api.database import get_db, AsyncSessionLocal
from api.models import Chart, ChatMessage
from api.schemas import ChatRequest
from api.services.llm_adapter import LLMAdapter
from api.config import settings

router = APIRouter(tags=["chat"])
FREE_DAILY_LIMIT = 5

CHAT_SYSTEM = """You are AstroWise — a wise, warm Vedic astrology guide.
The user's birth chart context is given below. Answer ONLY from what the chart shows.
Be specific to their placements — never generic.
Avoid fortune-teller certainty. Use "this chart suggests" and "you may notice".
Keep answers under 200 words unless depth is truly needed.

{chart_context}"""


def _build_chart_context(chart_json: dict) -> str:
    return (
        f"Lagna: {chart_json.get('lagna', 'unknown')} {chart_json.get('lagna_deg', '')}° | "
        f"Dasha: {chart_json.get('current_dasha', 'unknown')} | "
        f"Yogas: {', '.join(chart_json.get('yogas', []))} | "
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

    if not chart.user.paid:
        since = datetime.now(timezone.utc) - timedelta(days=1)
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

    adapter = LLMAdapter(provider="anthropic", api_key=settings.anthropic_api_key)
    chart_context = _build_chart_context(chart.chart_json)
    system = CHAT_SYSTEM.format(chart_context=chart_context)
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
            pass  # Non-critical — response already sent

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
