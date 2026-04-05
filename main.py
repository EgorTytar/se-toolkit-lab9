"""FastAPI application for the F1 Race Results Summarizer."""

import logging
import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from models.schemas import AIResponse, ErrorResponse, RaceSummaryResponse
from services.ai_assistant import AISummarizer
from services.ergast_client import ErgastClient
from services.data_parser import format_race_data
from db.database import init_db, close_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_db_healthy = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_healthy
    try:
        await init_db()
        _db_healthy = True
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning("Database initialization failed: %s", e)
        _db_healthy = False
    yield
    await close_db()


app = FastAPI(
    title="F1 Race Results Summarizer",
    description="AI-powered Formula 1 race summaries using real Ergast API data",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend UI)
app.mount("/static", StaticFiles(directory="static"), name="static")

ergast_client = ErgastClient()
ai_summarizer = AISummarizer()


@app.get("/")
async def root() -> FileResponse:
    """Serve the frontend UI."""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "ai_available": ai_summarizer.is_available,
        "ai_model": "qwen",
        "db_healthy": _db_healthy,
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
    "/api/races/latest/results",
    responses={500: {"model": ErrorResponse}},
)
async def get_latest_race_results() -> dict:
    """Return basic results for the most recent race (no AI)."""
    try:
        race_data = await ergast_client.get_latest_race()
    except Exception as e:
        logger.error("Failed to fetch latest race: %s", e)
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    return _build_basic_results(race_data)


@app.get(
    "/api/seasons/{year}/schedule",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_season_schedule(year: int) -> dict:
    """Return the race schedule for a given season year.

    Example: `/api/seasons/2024/schedule`
    """
    current_year = datetime.datetime.now().year

    if year < 1950:
        raise HTTPException(status_code=404, detail="The Formula 1 World Championship was not held before 1950.")
    if year > current_year:
        raise HTTPException(status_code=404, detail=f"The {year} season schedule is not yet available.")

    try:
        schedule = await ergast_client.get_season_schedule(year)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to fetch schedule for %s: %s", year, e)
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    return {"season": year, "race_count": len(schedule), "races": schedule}


@app.get(
    "/api/standings/drivers",
    responses={500: {"model": ErrorResponse}},
)
async def get_driver_standings(year: int) -> dict:
    """Driver championship standings for a given year.

    Example: `/api/standings/drivers?year=2024`
    """
    current_year = datetime.datetime.now().year

    if year < 1950:
        return {
            "season": year,
            "type": "drivers",
            "standings": [],
            "message": "The Formula 1 World Championship was not held before 1950.",
        }

    if year > current_year:
        return {
            "season": year,
            "type": "drivers",
            "standings": [],
            "message": f"The {year} season has not started yet.",
        }

    try:
        standings = await ergast_client.get_driver_standings(year)
    except ValueError:
        return {
            "season": year,
            "type": "drivers",
            "standings": [],
            "message": "No driver standings available for this season.",
        }
    except Exception as e:
        logger.error("Failed to fetch driver standings for %s: %s", year, e)
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    return {"season": year, "type": "drivers", "standings": standings}


@app.get(
    "/api/standings/constructors",
    responses={500: {"model": ErrorResponse}},
)
async def get_constructor_standings(year: int) -> dict:
    """Constructor championship standings for a given year.

    Example: `/api/standings/constructors?year=2024`
    """
    current_year = datetime.datetime.now().year

    if year < 1950:
        return {
            "season": year,
            "type": "constructors",
            "standings": [],
            "message": "The Formula 1 World Championship was not held before 1950.",
        }

    if year > current_year:
        return {
            "season": year,
            "type": "constructors",
            "standings": [],
            "message": f"The {year} season has not started yet.",
        }

    try:
        standings = await ergast_client.get_constructor_standings(year)
    except ValueError:
        return {
            "season": year,
            "type": "constructors",
            "standings": [],
            "message": "The constructors championship was not held in this season.",
        }
    except Exception as e:
        logger.error("Failed to fetch constructor standings for %s: %s", year, e)
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    return {"season": year, "type": "constructors", "standings": standings}


@app.get(
    "/api/drivers/{driver_id}",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_driver_info(driver_id: str, year: int = 0) -> dict:
    """Get driver profile and optional season results.

    Example: `/api/drivers/hamilton?year=2024`
    """
    try:
        info = await ergast_client.get_driver_info(driver_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to fetch driver info for %s: %s", driver_id, e)
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    result = {"driver": info}

    # Optionally include season results
    if year > 0:
        try:
            results = await ergast_client.get_driver_season_results(driver_id, year)
            result["season"] = year
            result["results"] = results
            result["season_stats"] = {
                "races": len(results),
                "points": sum(r["points"] for r in results),
                "best_finish": min(
                    (int(r["position"]) for r in results if r["position"].isdigit()),
                    default=None,
                ),
            }
        except Exception as e:
            logger.warning("Could not fetch season results for %s: %s", driver_id, e)
            result["season"] = year
            result["results"] = []
            result["season_stats"] = {}

    return result


@app.get(
    "/api/races/{year}/{round}/results",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_race_results(year: int, round: int) -> dict:
    """Return basic race results without AI summary.

    If the race hasn't happened yet, returns a preview with schedule info.
    Example: `/api/races/2024/1/results`
    """
    current_year = datetime.datetime.now().year

    if year < 1950:
        raise HTTPException(status_code=400, detail="The Formula 1 World Championship was not held before 1950.")
    if year > current_year:
        raise HTTPException(status_code=400, detail=f"The {year} season has not started yet.")
    if round < 1 or round > 30:
        raise HTTPException(status_code=400, detail="Round must be between 1 and 30")

    try:
        race_data = await ergast_client.get_race_by_year_round(year, round)
    except ValueError:
        # Race entry might not exist yet (future race) — try schedule
        return await _try_schedule_preview(year, round)
    except Exception as e:
        logger.error("Failed to fetch race %s/%s: %s", year, round, e)
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    return _build_basic_results(race_data)


async def _try_schedule_preview(year: int, round: int) -> dict:
    """Try to fetch race info from the season schedule for future races."""
    try:
        schedule = await ergast_client.get_season_schedule(year)
        race_info = next((r for r in schedule if r["round"] == round), None)
        if race_info:
            return {
                "race_name": race_info["race_name"],
                "circuit": race_info["circuit"],
                "date": race_info["date"],
                "season": year,
                "round": round,
                "total_drivers": 0,
                "winner": None,
                "podium": [],
                "is_future_race": True,
            }
    except Exception as e:
        logger.warning("Could not fetch schedule for preview: %s", e)

    return {
        "race_name": f"Round {round}",
        "circuit": "Unknown",
        "date": "Unknown",
        "season": year,
        "round": round,
        "total_drivers": 0,
        "winner": None,
        "podium": [],
        "is_future_race": True,
    }


@app.get(
    "/api/races/{year}/{round}",
    response_model=RaceSummaryResponse,
    responses={500: {"model": ErrorResponse}},
)
async def get_race_summary(
    year: int, round: int, user_query: str = ""
) -> RaceSummaryResponse:
    """Summarize a specific Formula 1 race by year and round number.

    For future races (no results), generates a race preview instead.
    Example: `/api/races/2024/1` for the first race of 2024.
    """
    current_year = datetime.datetime.now().year

    if year < 1950:
        raise HTTPException(status_code=400, detail="The Formula 1 World Championship was not held before 1950.")
    if year > current_year:
        raise HTTPException(status_code=400, detail=f"The {year} season has not started yet.")
    if round < 1 or round > 30:
        raise HTTPException(status_code=400, detail="Round must be between 1 and 30")

    try:
        race_data = await ergast_client.get_race_by_year_round(year, round)
    except ValueError:
        # Future race — get info from schedule and generate a preview
        return await _build_future_race_preview(year, round, user_query)
    except Exception as e:
        logger.error("Failed to fetch race %s/%s: %s", year, round, e)
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    return await _build_response(race_data, user_query)


async def _build_future_race_preview(year: int, round: int, user_query: str) -> RaceSummaryResponse:
    """Generate a preview for a race that hasn't happened yet."""
    try:
        schedule = await ergast_client.get_season_schedule(year)
        race_info = next((r for r in schedule if r["round"] == round), None)
        if race_info:
            preview_text = (
                f"Upcoming Race: {race_info['race_name']}\n"
                f"Circuit: {race_info['circuit']}\n"
                f"Date: {race_info['date']}\n\n"
                f"This race has not taken place yet. "
                f"Check back after {race_info['date']} for results and analysis."
            )
            result = await ai_summarizer.summarize(preview_text, user_query)
            return RaceSummaryResponse(
                race_name=race_info["race_name"],
                circuit=race_info["circuit"],
                date=race_info["date"],
                season=str(year),
                round=round,
                ai_response=AIResponse(**result),
            )
    except Exception as e:
        logger.warning("Could not generate preview for %s/%s: %s", year, round, e)

    return RaceSummaryResponse(
        race_name=f"Round {round}",
        circuit="Unknown",
        date="TBD",
        season=str(year),
        round=round,
        ai_response=AIResponse(
            summary=f"Race data for round {round} of {year} is not yet available.",
            highlights="No results — this race has not taken place yet.",
            insights="Results will appear here once the race weekend is completed.",
            answer="",
        ),
    )


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


def _build_basic_results(race_data: dict) -> dict:
    """Extract basic race results without AI summary."""
    results = race_data.get("results", [])
    top3 = results[:3]
    winner = top3[0] if len(top3) > 0 else None

    return {
        "race_name": race_data["race_name"],
        "circuit": race_data["circuit"],
        "date": race_data["date"],
        "season": race_data["season"],
        "round": race_data["round"],
        "total_drivers": len(results),
        "winner": {
            "name": winner["driver_name"],
            "constructor": winner["constructor"],
            "points": winner["points"],
        }
        if winner
        else None,
        "podium": [
            {
                "position": p["position"],
                "name": p["driver_name"],
                "constructor": p["constructor"],
                "points": p["points"],
            }
            for p in top3
        ],
    }
