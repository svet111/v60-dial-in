from pydantic import BaseModel, Field
from typing import Optional


class BrewCreate(BaseModel):
    bean_name: str = Field(..., min_length=1, max_length=100)
    roast_level: str = Field(..., pattern="^(light|medium|dark)$")
    coffee_g: float = Field(..., gt=5, le=60)
    water_g: float = Field(..., gt=50, le=1000)
    water_temp_c: int = Field(..., ge=80, le=100)
    pour_count: int = Field(..., ge=1, le=5)
    swirl: bool = False
    drawdown_sec: int = Field(..., ge=30, le=600)
    taste_score: int = Field(..., ge=-5, le=5)  # -5 sour, 0 balanced, +5 bitter
    notes: Optional[str] = ""


class BrewRecord(BrewCreate):
    id: int
    ratio: float
    created_at: str


class RecommendationResponse(BaseModel):
    strategy: str
    suggested_temp_c: int
    suggested_water_g: int
    suggested_ratio: float
    suggested_pour_count: int
    suggested_swirl: bool
    explanation: list[str]