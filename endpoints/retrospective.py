"""Season retrospective endpoint: AI summary of entire F1 season."""

import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User
from dependencies import get_current_user
from services.ai_assistant import AISummarizer
from services.ergast_client import ErgastClient
from services.cache_service import get_cached_response, cache_response, CACHE_TTL_RETROSPECTIVE

router = APIRouter(prefix="/api/seasons", tags=["retrospective"])

ai_summarizer = AISummarizer()
ergast_client = ErgastClient()
logger = logging.getLogger(__name__)


@router.get("/{year}/retrospective")
async def get_season_retrospective(
    year: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an AI retrospective for a full F1 season.

    Fetches all races, driver standings, and constructor standings
    for the specified year, then asks the AI to write a comprehensive
    season narrative. Results are cached for faster subsequent requests.
    """
    # Validate year range
    current_year = datetime.datetime.now().year
    if year < 1950 or year > current_year + 1:
        raise HTTPException(
            status_code=400,
            detail=f"Year must be between 1950 and {current_year + 1}",
        )

    # Check cache first
    cache_key = f"retro_{year}"
    cached = await get_cached_response(db, cache_key)
    if cached:
        logger.info(f"Returning cached retrospective for {year}")
        return cached

    # Fetch season data in parallel
    try:
        import asyncio
        schedule_task = asyncio.create_task(ergast_client.get_season_schedule(year))
        driver_standings_task = asyncio.create_task(
            ergast_client.get_driver_standings(year)
        )
        constructor_standings_task = asyncio.create_task(
            ergast_client.get_constructor_standings(year)
        )

        schedule = await schedule_task
        driver_standings = await driver_standings_task
        constructor_standings = await constructor_standings_task
    except Exception as e:
        logger.warning(f"Failed to fetch season {year} data: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch data for season {year}",
        )

    if not schedule:
        raise HTTPException(
            status_code=404,
            detail=f"No schedule data found for {year}",
        )

    # Check if season is completed (needed for labels below)
    is_ongoing = any(
        r.get("date") > datetime.datetime.now().strftime("%Y-%m-%d")
        for r in schedule
    )
    season_status = "ONGOING" if is_ongoing else "COMPLETED"
    standings_label = "Current" if is_ongoing else "Final"

    # Build season context for AI
    context_parts = []

    # Season overview
    context_parts.append(f"**{year} F1 Season Overview ({season_status})**")
    context_parts.append(f"Total races: {len(schedule)}")
    context_parts.append(f"Races completed: {sum(1 for r in schedule if r.get('date') <= datetime.datetime.now().strftime('%Y-%m-%d'))}")

    # Championship standings
    leader = None
    if driver_standings:
        leader = driver_standings[0]
        context_parts.append(
            f"\n**{standings_label} Drivers' Standings Leader:** {leader['driver_name']} "
            f"({leader['constructor']}) — {leader['points']} pts, {leader['wins']} wins"
        )
        if len(driver_standings) >= 2:
            runner_up = driver_standings[1]
            margin = leader['points'] - runner_up['points']
            context_parts.append(
                f"Margin to 2nd place ({runner_up['driver_name']}): {margin} pts"
            )

    constructors_leader = None
    if constructor_standings:
        constructors_leader = constructor_standings[0]
        context_parts.append(
            f"\n**{standings_label} Constructors' Standings Leader:** {constructors_leader['constructor']} "
            f"— {constructors_leader['points']} pts, {constructors_leader['wins']} wins"
        )

    # Race-by-race summary (just round numbers and names for brevity)
    race_list = ", ".join(f"R{r['round']}: {r['race_name']}" for r in schedule)
    context_parts.append(f"\n**Race Calendar ({len(schedule)} rounds):**")
    context_parts.append(race_list)

    # Top drivers detail (just top 5 for brevity)
    if driver_standings:
        context_parts.append(f"\n**Top 5 Drivers {standings_label} Standings:**")
        for i, d in enumerate(driver_standings[:5]):
            context_parts.append(
                f"{i+1}. {d['driver_name']} ({d['constructor']}) — {d['points']} pts, {d['wins']} wins"
            )

    # Top teams detail
    if constructor_standings:
        context_parts.append(f"\n**Constructors' {standings_label} Standings:**")
        for i, c in enumerate(constructor_standings):
            context_parts.append(
                f"{i+1}. {c['constructor']} — {c['points']} pts, {c['wins']} wins"
            )

    context_text = "\n".join(context_parts)

    # Add explicit warnings about missing data
    context_text += f"\n\n**⚠️ DATA LIMITATIONS:**\n"
    context_text += f"- Individual race results are NOT provided — only the race calendar\n"
    context_text += f"- Do NOT describe specific races, lap times, or race incidents\n"
    context_text += f"- Only drivers/teams listed in the standings above exist in this dataset\n"
    context_text += f"- Do NOT mention any driver, team, or points not explicitly listed above\n"
    context_text += f"- This is a factual standings summary, not a narrative race-by-race recap\n"

    # Generate AI retrospective
    system_prompt = (
        f"You are an F1 data analyst. Write a factual summary of the {year} F1 season based "
        f"STRICTLY on the data provided below. This season is {season_status}.\n\n"
        f"CRITICAL RULES:\n"
        f"1. ONLY use data explicitly provided in the context below\n"
        f"2. NEVER invent race results, driver positions, points, or team names\n"
        f"3. If the season is ongoing, describe current standings — do NOT predict outcomes\n"
        f"4. If the season is complete, summarize final standings\n"
        f"5. If you lack specific race-by-race data, do NOT describe individual races\n"
        f"6. Do NOT mention teams, drivers, or points not listed in the data\n"
        f"7. Use markdown formatting\n"
        f"8. Keep it concise (~200-400 words)\n\n"
        f"STRUCTURE:\n"
        f"- Current standings overview (drivers and constructors)\n"
        f"- Key observations from the data provided\n"
        f"- Note on season status (ongoing vs complete)\n\n"
        f"{'⚠️ IMPORTANT: This season is still in progress. Only describe what has happened so far. '
         f'Do not use past tense for the championship — use present tense. Do not declare a winner.' if is_ongoing else ''}\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": (
            f"Write the {year} F1 season retrospective using this data:\n\n{context_text}"
        )},
    ]

    try:
        logger.info(f"Generating AI retrospective for {year}...")
        response = await ai_summarizer.chat_response(messages)
        logger.info(f"AI response received for {year} ({len(response)} chars)")
        result = {
            "year": year,
            "total_races": len(schedule),
            "races_completed": sum(
                1 for r in schedule if r.get("date") <= datetime.datetime.now().strftime("%Y-%m-%d")
            ),
            "is_ongoing": is_ongoing,
            "champion": leader if driver_standings else None,
            "constructors_champion": constructors_leader if constructor_standings else None,
            "retrospective": response,
        }

        # Cache the response
        try:
            await cache_response(db, cache_key, result, CACHE_TTL_RETROSPECTIVE)
        except Exception as cache_err:
            logger.warning(f"Cache write failed for {year}: {cache_err}")
            # Continue anyway - caching is optional

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI retrospective failed for {year}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI retrospective: {str(e)}",
        )
