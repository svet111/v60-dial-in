from fastapi.testclient import TestClient
from app.main import app
from app.models import BrewRecord
from app.optimizer import recommend_next_brew
import app.database as db


def _make_brew(id: int, temp: int, ratio: float, pours: int, swirl: bool, taste: int) -> BrewRecord:
    return BrewRecord(
        id=id,
        bean_name="Test Bean",
        roast_level="medium",
        coffee_g=15.0,
        water_g=round(15.0 * ratio, 1),
        ratio=ratio,
        water_temp_c=temp,
        pour_count=pours,
        swirl=swirl,
        drawdown_sec=160,
        taste_score=taste,
        notes="",
        created_at="2026-11-18 12:00:00",
    )


def test_sour_brew_increases_extraction():
    sour_brew = _make_brew(id=1, temp=90, ratio=16.0, pours=3, swirl=False, taste=-3)
    rec = recommend_next_brew([sour_brew])

    assert rec.suggested_temp_c > 90
    assert rec.suggested_ratio >= 16.0


def test_bitter_brew_decreases_extraction():
    bitter_brew = _make_brew(id=1, temp=96, ratio=16.5, pours=3, swirl=True, taste=4)
    rec = recommend_next_brew([bitter_brew])

    assert rec.suggested_temp_c < 96
    assert rec.suggested_swirl is False


def test_ml_mode_activates_after_four_varied_brews():
    brews = [
        _make_brew(4, temp=95, ratio=16.5, pours=3, swirl=True, taste=2),
        _make_brew(3, temp=94, ratio=16.5, pours=3, swirl=True, taste=1),
        _make_brew(2, temp=90, ratio=15.5, pours=2, swirl=False, taste=-2),
        _make_brew(1, temp=88, ratio=15.0, pours=2, swirl=False, taste=-4),
    ]
    rec = recommend_next_brew(brews)

    assert rec.strategy == "Ridge Regression Optimizer"
    assert 91 <= rec.suggested_temp_c <= 94


def test_api_create_and_recommend(tmp_path, monkeypatch):
    test_db = tmp_path / "test_v60.db"
    monkeypatch.setattr(db, "DB_PATH", test_db)
    db.init_db(test_db)

    with TestClient(app) as client:
        res = client.post("/api/brews", json={
            "bean_name": "Kenya AA",
            "roast_level": "light",
            "coffee_g": 15,
            "water_g": 240,
            "water_temp_c": 91,
            "pour_count": 2,
            "swirl": False,
            "drawdown_sec": 140,
            "taste_score": -3,
            "notes": "Too sharp"
        })
        assert res.status_code == 200

        rec_res = client.get("/api/recommend", params={"bean_name": "Kenya AA"})
        assert rec_res.status_code == 200
        data = rec_res.json()
        assert data["suggested_temp_c"] == 94
        assert data["suggested_swirl"] is True