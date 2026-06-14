from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import json

from api.database import get_db
from api.models import Chart
from api.services.report_service import ReportService

router = APIRouter(tags=["reports"])
_report_svc = ReportService()


@router.get("/report/{chart_id}")
async def stream_report(chart_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Chart).where(Chart.id == chart_id).options(selectinload(Chart.user))
    )
    chart = result.scalar_one_or_none()
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    if not chart.user:
        raise HTTPException(status_code=500, detail="Chart has no associated user")
    if not chart.user.paid:
        raise HTTPException(status_code=403, detail="Payment required")

    async def event_stream():
        try:
            async for chunk in _report_svc.stream_report(chart.chart_json, chart.user.name):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
