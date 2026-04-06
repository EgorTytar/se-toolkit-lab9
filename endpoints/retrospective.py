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
    season narrative.
    """
    # Validate year range
    current_year = datetime.datetime.now().year
    if year < 1950 or year > current_year + 1:
        raise HTTPException(
            status_code=400,
            detail=f"Year must be between 1950 and {current_year + 1}",
        )

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

    # Build season context for AI
    context_parts = []

    # Season overview
    context_parts.append(f"**{year} F1 Season Overview**")
    context_parts.append(f"Total races: {len(schedule)}")

    # Championship standings
    if driver_standings:
        champion = driver_standings[0]
        context_parts.append(
            f"\n**World Drivers' Champion:** {champion['driver_name']} "
            f"({champion['constructor']}) — {champion['points']} pts, {champion['wins']} wins"
        )
        if len(driver_standings) >= 2:
            runner_up = driver_standings[1]
            margin = champion['points'] - runner_up['points']
            context_parts.append(
                f"Margin to 2nd place ({runner_up['driver_name']}): {margin} pts"
            )

    if constructor_standings:
        top_team = constructor_standings[0]
        context_parts.append(
            f"\n**Constructors' Champion:** {top_team['constructor']} "
            f"— {top_team['points']} pts, {top_team['wins']} wins"
        )

    # Race-by-race summary
    context_parts.append(f"\n**Race Calendar & Results:**")
    for race in schedule[:]:  # All races
        race_summary = f"\nRound {race['round']}: {race['race_name']} ({race['date']})"
        race_summary += f"\n  Circuit: {race['circuit']}"
        context_parts.append(race_summary)

    # Top drivers detail
    if driver_standings:
        context_parts.append(f"\n**Top 10 Drivers Final Standings:**")
        for i, d in enumerate(driver_standings[:10]):
            context_parts.append(
                f"{i+1}. {d['driver_name']} ({d['constructor']}) — {d['points']} pts, {d['wins']} wins"
            )

    # Top teams detail
    if constructor_standings:
        context_parts.append(f"\n**Constructors' Final Standings:**")
        for i, c in enumerate(constructor_standings):
            context_parts.append(
                f"{i+1}. {c['constructor']} — {c['points']} pts, {c['wins']} wins"
            )

    context_text = "\n".join(context_parts)

    # Check if season is completed
    is_ongoing = any(
        r.get("date") > datetime.datetime.now().strftime("%Y-%m-%d")
        for r in schedule
    )

    # Generate AI retrospective
    system_prompt = (
        f"You are a veteran F1 commentator and historian. Write an engaging, "
        f"comprehensive retrospective of the {year} Formula 1 World Championship season.\n\n"
        f"STRUCTURE YOUR RESPONSE:\n"
        f"1. **Season Overview** — Who won, was it close, what defined this season?\n"
        f"2. **The Championship Battle** — Key rivalries, turning points, momentum shifts\n"
        f"3. **Standout Races** — 3-5 races that defined the season (explain why)\n"
        f"4. **Rise and Fall** — Breakthrough performances, disappointing seasons, comebacks\n"
        f"5. **Constructor Battle** — How the teams fought\n"
        f"6. **Legacy** — How this season is remembered in F1 history\n\n"
        f"WRITING STYLE:\n"
        f"- Professional, engaging, like a documentary narration\n"
        f"- Use specific data (points, margins, positions) when available\n"
        f"- Create narrative tension — who led when, how battles evolved\n"
        f"- Be accurate with the data provided — do not fabricate results\n"
        f"- Use markdown formatting for readability\n"
        f"- Keep it comprehensive but engaging (~500-800 words)\n\n"
        f"{'Note: This season may still be in progress. Frame the narrative accordingly, '
         f'focusing on what has happened so far rather than declaring it complete.' if is_ongoing else ''}\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": (
            f"Write the {year} F1 season retrospective using this data:\n\n{context_text}"
        )},
    ]

    try:
        response = await ai_summarizer.chat_response(messages)
        return {
            "year": year,
            "total_races": len(schedule),
            "races_completed": sum(
                1 for r in schedule if r.get("date") <= datetime.datetime.now().strftime("%Y-%m-%d")
            ),
            "champion": champion if driver_standings else None,
            "constructors_champion": top_team if constructor_standings else None,
            "retrospective": response,
        }
    except Exception as e:
        logger.warning(f"AI retrospective failed for {year}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate AI retrospective. Please try again.",
        )
