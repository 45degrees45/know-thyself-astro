import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Integer, Boolean, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    google_id: Mapped[str | None] = mapped_column(String, nullable=True)
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    charts: Mapped[list["Chart"]] = relationship(back_populates="user")


class Chart(Base):
    __tablename__ = "charts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    birth_date: Mapped[str] = mapped_column(String)
    birth_time: Mapped[str] = mapped_column(String)
    birth_place: Mapped[str] = mapped_column(String)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    tz: Mapped[str] = mapped_column(String)
    chart_json: Mapped[dict] = mapped_column(JSON)
    anon_slug: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="charts")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="chart")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chart_id: Mapped[str] = mapped_column(ForeignKey("charts.id"), index=True)
    tab: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    chart: Mapped["Chart"] = relationship(back_populates="messages")


class QuestionBank(Base):
    __tablename__ = "question_bank"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tab: Mapped[str] = mapped_column(String, index=True)
    question: Mapped[str] = mapped_column(Text)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    lagna_filter: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class WeeklyQuestion(Base):
    __tablename__ = "weekly_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text)
    week_of: Mapped[str] = mapped_column(String, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
