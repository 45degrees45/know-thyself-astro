"""Cofounder matching router — POST /api/cofounder-match."""
import asyncio
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from astro_engine.geo import geocode
from astro_engine.calc import calculate_chart
from astro_engine.match import match_cofounders

router = APIRouter(tags=["match"])


class PersonInput(BaseModel):
    name: str
    date: str                    # YYYY-MM-DD or DD-MM-YYYY
    time: str = "12:00"          # HH:MM; ignored when time_accuracy=="unknown"
    time_accuracy: Literal["exact", "approximate", "unknown"] = "exact"
    place: str


class MatchRequest(BaseModel):
    person_a: PersonInput
    person_b: PersonInput


@router.post("/cofounder-match")
async def cofounder_match(req: MatchRequest):
    time_a = "12:00" if req.person_a.time_accuracy == "unknown" else req.person_a.time
    time_b = "12:00" if req.person_b.time_accuracy == "unknown" else req.person_b.time

    try:
        geo_a, geo_b = await asyncio.gather(
            asyncio.to_thread(geocode, req.person_a.place),
            asyncio.to_thread(geocode, req.person_b.place),
        )
        chart_a, chart_b = await asyncio.gather(
            asyncio.to_thread(
                calculate_chart,
                req.person_a.date, time_a,
                geo_a["lat"], geo_a["lon"], geo_a["timezone"],
            ),
            asyncio.to_thread(
                calculate_chart,
                req.person_b.date, time_b,
                geo_b["lat"], geo_b["lon"], geo_b["timezone"],
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    birth_dt_a = datetime.fromisoformat(chart_a["birth_utc"]).replace(tzinfo=None)
    birth_dt_b = datetime.fromisoformat(chart_b["birth_utc"]).replace(tzinfo=None)

    return await asyncio.to_thread(
        match_cofounders,
        chart_a, chart_b,
        req.person_a.name, req.person_b.name,
        birth_dt_a, birth_dt_b,
        req.person_a.time_accuracy, req.person_b.time_accuracy,
    )
