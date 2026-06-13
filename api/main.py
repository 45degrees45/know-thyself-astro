from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.routers import charts, reports, chat, questions, payments

app = FastAPI(title="AstroWise API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(charts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(payments.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
