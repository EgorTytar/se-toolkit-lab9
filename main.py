"""FastAPI application for the F1 Race Results Summarizer."""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import AIResponse, ErrorResponse, RaceSummaryResponse
from services.ai_assistant import AISummarizer
from services.ergast_client import ErgastClient
from services.data_parser import format_race_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="F1 Race Results Summarizer",
    description="AI-powered Formula 1 race summaries using real Ergast API data",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ergast_client = ErgastClient()
ai_summarizer = AISummarizer()


@app.get("/")
async def root() -> dict:
    """Root endpoint — points to API docs."""
    return {
        "service": "F1 Race Results Summarizer",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "latest_race": "/api/races/latest",
            "specific_race": "/api/races/{year}/{round}",
        },
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "ai_available": ai_summarizer.is_available,
    }


@app.get(
    "/api/races/latest",
    response_model=RaceSummaryResponse,
    responses={500: {"model": ErrorResponse}},
)
async def get_latest_race_summary(user_query: str = "") -> RaceSummaryResponse:
    """Summarize the most recent Formula 1 race.

    Fetches results from the Ergast API and generates an AI-powered summary.
    Optionally pass a `user_query` to ask a specific question.
    """
    try:
        race_data = await ergast_client.get_latest_race()
    except Exception as e:
        logger.error("Failed to fetch latest race: %s", e)
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    return await _build_response(race_data, user_query)


@app.get(
    "/api/races/{year}/{round}",
    response_model=RaceSummaryResponse,
    responses={500: {"model": ErrorResponse}},
)
async def get_race_summary(
    year: int, round: int, user_query: str = ""
) -> RaceSummaryResponse:
    """Summarize a specific Formula 1 race by year and round number.

    Example: `/api/races/2024/1` for the first race of 2024.
    """
    if year < 1950 or year > 2030:
        raise HTTPException(status_code=400, detail="Year must be between 1950 and 2030")
    if round < 1 or round > 30:
        raise HTTPException(status_code=400, detail="Round must be between 1 and 30")

    try:
        race_data = await ergast_client.get_race_by_year_round(year, round)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to fetch race %s/%s: %s", year, round, e)
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    return await _build_response(race_data, user_query)


async def _build_response(race_data: dict, user_query: str) -> RaceSummaryResponse:
    """Shared logic: format race data and generate AI summary."""
    race_text = format_race_data(race_data)
    ai_result = await ai_summarizer.summarize(race_text, user_query)

    return RaceSummaryResponse(
        race_name=race_data["race_name"],
        circuit=race_data["circuit"],
        date=race_data["date"],
        season=race_data["season"],
        round=race_data["round"],
        ai_response=AIResponse(**ai_result),
    )
