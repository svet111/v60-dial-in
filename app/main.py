from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import BrewCreate, BrewRecord, RecommendationResponse
from app.optimizer import recommend_next_brew
from app.database import init_db, insert_brew, list_brews, list_bean_names


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="V60 Pre-Ground Brew Dial-In Optimizer", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")

@app.get("/api/beans", response_model=list[str])
def get_beans():
    return list_bean_names()

@app.post("/api/brews", response_model=BrewRecord)
def create_brew(brew: BrewCreate):
    return insert_brew(brew)


@app.get("/api/brews", response_model=list[BrewRecord])
def get_brews(bean_name: str | None = Query(default=None)):
    return list_brews(bean_name)


@app.get("/api/recommend", response_model=RecommendationResponse)
def get_recommendation(bean_name: str | None = Query(default=None)):
    brews = list_brews(bean_name)
    return recommend_next_brew(brews)