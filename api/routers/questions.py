from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.database import get_db
from api.models import QuestionBank, WeeklyQuestion

router = APIRouter(tags=["questions"])


# NOTE: Fixed-path routes MUST come before the {tab} parameterised route.
# FastAPI matches in registration order — /questions/last would be captured
# by {tab}="last" if registered after the parameterised route.

@router.get("/questions/last")
async def get_last_question(db: AsyncSession = Depends(get_db)):
    week = date.today().strftime("%Y-W%V")
    result = await db.execute(
        select(WeeklyQuestion).where(
            WeeklyQuestion.week_of == week,
            WeeklyQuestion.active == True,
        )
    )
    q = result.scalar_one_or_none()
    return {"question": q.question if q else "What are you most afraid to become?"}


@router.get("/questions/{tab}")
async def get_questions(tab: str, lagna: str = None, db: AsyncSession = Depends(get_db)):
    q = select(QuestionBank).where(
        QuestionBank.tab == tab,
        QuestionBank.active == True,
    )
    if lagna:
        q = q.where(
            (QuestionBank.lagna_filter == lagna) | (QuestionBank.lagna_filter == None)
        )
    result = await db.execute(q.order_by(QuestionBank.click_count.desc()).limit(12))
    rows = result.scalars().all()
    return [{"id": r.id, "question": r.question, "clicks": r.click_count} for r in rows]


@router.post("/questions/{question_id}/click")
async def record_click(question_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(QuestionBank).where(QuestionBank.id == question_id))
    q = result.scalar_one_or_none()
    if q:
        q.click_count += 1
        await db.commit()
    return {"ok": True}
