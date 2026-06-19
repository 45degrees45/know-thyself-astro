from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.routers import charts, reports, chat, questions, payments, demo, admin

app = FastAPI(title="AstroWise API", version="1.0.0")

_origins = [o.strip() for o in settings.frontend_url.split(",") if o.strip()]
for _extra in ["http://localhost:3000", "https://astrowyze.netlify.app", "https://astrowyze-staging.netlify.app"]:
    if _extra not in _origins:
        _origins.append(_extra)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(charts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(demo.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
