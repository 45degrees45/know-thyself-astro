import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from api.models import Base, User, Chart

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s

def test_create_user_and_chart(db):
    user = User(email="test@x.com", name="Test")
    db.add(user)
    db.flush()
    chart = Chart(
        user_id=user.id,
        birth_date="1985-03-07",
        birth_time="07:15",
        birth_place="Kangazha, Kerala",
        lat=9.75, lon=76.78, tz="Asia/Kolkata",
        chart_json={"lagna": "Pisces", "lagna_deg": 0.9},
    )
    db.add(chart)
    db.commit()
    assert chart.id is not None
    assert chart.user_id == user.id
