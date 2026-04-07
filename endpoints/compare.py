"""Driver head-to-head comparison endpoint."""

import datetime
import logging

from fastapi import APIRouter, HTTPException, Query

from services.ergast_client import ErgastClient

router = APIRouter(prefix="/api/compare", tags=["compare"])

ergast_client = ErgastClient()
logger = logging.getLogger(__name__)

# In-memory cache for the full driver list (fetched once from API)
_cached_drivers: list[dict] | None = None


@router.get("/drivers/search")
async def search_drivers(q: str = Query(..., min_length=1, max_length=100)) -> list[dict]:
    """Search F1 drivers by name.

    Query param:
        q — search query (matched against full name, given name, family name, or code)

    Returns up to 20 matching drivers. Results are cached after first API fetch.
    """
    global _cached_drivers

    # Fetch and cache all drivers on first call
    if _cached_drivers is None:
        try:
            _cached_drivers = await ergast_client.get_all_drivers()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch driver list: {e}") from e

    query = q.lower()
    results = []
    for driver in _cached_drivers:
        full_name = driver["full_name"].lower()
        given = driver["given_name"].lower()
        family = driver["family_name"].lower()
        code = driver.get("code", "").lower()
        driver_id = driver["driver_id"].lower()

        # Exact match on any field gets priority
        if query in full_name or query in given or query in family or query in code or query in driver_id:
            results.append(driver)
            if len(results) >= 20:
                break

    return results


@router.get("/drivers")
async def compare_drivers(a: str, b: str) -> dict:
    """Compare two drivers side-by-side.

    Query params:
        a — first driver's Ergast driver ID (e.g. 'hamilton')
        b — second driver's Ergast driver ID (e.g. 'max_verstappen')

    Returns career stats for both drivers plus their head-to-head
    record in races where they both competed.
    """
    # Fetch both drivers' info
    try:
        driver_a_info = await ergast_client.get_driver_info(a)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Driver '{a}' not found: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ergast API error fetching driver '{a}': {e}") from e

    try:
        driver_b_info = await ergast_client.get_driver_info(b)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Driver '{b}' not found: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ergast API error fetching driver '{b}': {e}") from e

    # Fetch ALL career results for both drivers (paginated, efficient)
    try:
        a_all_results = await ergast_client.get_driver_all_results(a)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch career results for '{a}': {e}") from e

    try:
        b_all_results = await ergast_client.get_driver_all_results(b)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch career results for '{b}': {e}") from e

    # Build career stats
    driver_a_career = _compute_career_stats(a_all_results)
    driver_b_career = _compute_career_stats(b_all_results)

    # Fetch championship counts (only for seasons they competed)
    a_seasons = set(r["season"] for r in a_all_results)
    b_seasons = set(r["season"] for r in b_all_results)
    driver_a_career["championships"] = await _count_championships(a, a_seasons)
    driver_b_career["championships"] = await _count_championships(b, b_seasons)

    # Build constructor history
    driver_a_career["teams"] = _compute_constructor_history(a_all_results)
    driver_b_career["teams"] = _compute_constructor_history(b_all_results)

    # Compute head-to-head record
    h2h = _compute_head_to_head(a_all_results, b_all_results)

    return {
        "driver_a": {
            "info": driver_a_info,
            "career": driver_a_career,
        },
        "driver_b": {
            "info": driver_b_info,
            "career": driver_b_career,
        },
        "head_to_head": h2h,
    }


def _compute_career_stats(results: list[dict]) -> dict:
    """Aggregate career statistics from a list of race results."""
    total_races = len(results)
    total_wins = 0
    total_podiums = 0
    total_poles = 0
    total_points = 0.0
    best_finish = None
    worst_finish = None
    dnfs = 0
    seasons_competed: set[int] = set()

    for r in results:
        pos_str = str(r.get("position", ""))
        grid = r.get("grid", 0)
        points = float(r.get("points", 0))
        status = r.get("status", "")
        season = r.get("season", 0)

        seasons_competed.add(season)
        total_points += points

        if pos_str.isdigit():
            pos = int(pos_str)
            if best_finish is None or pos < best_finish:
                best_finish = pos
            if worst_finish is None or pos > worst_finish:
                worst_finish = pos

            if pos == 1:
                total_wins += 1
            if pos <= 3:
                total_podiums += 1

        if status and status != "Finished" and not pos_str.isdigit():
            dnfs += 1

        if isinstance(grid, int) and grid == 1:
            total_poles += 1

    return {
        "races": total_races,
        "wins": total_wins,
        "podiums": total_podiums,
        "poles": total_poles,
        "points": total_points,
        "championships": 0,  # filled in separately
        "best_finish": best_finish,
        "worst_finish": worst_finish,
        "dnfs": dnfs,
        "seasons_competed": sorted(seasons_competed),
    }


async def _count_championships(driver_id: str, seasons: set[int]) -> int:
    """Count how many championships a driver won across their competed seasons."""
    championships = 0
    for year in seasons:
        try:
            standings = await ergast_client.get_driver_standings(year)
            champ = next(
                (s for s in standings if s["driver_id"] == driver_id and s["position"] == 1),
                None,
            )
            if champ:
                championships += 1
        except Exception:
            pass
    return championships


def _compute_constructor_history(results: list[dict]) -> list[dict]:
    """Compute the constructor history for a driver.

    Returns a list of teams the driver has raced for, with:
    - constructor name & ID
    - years driven
    - total races, wins, podiums, points with that team
    """
    teams: dict[str, dict] = {}

    for r in results:
        constructor_id = r.get("constructor_id", "unknown")
        constructor_name = r.get("constructor", "Unknown")
        season = r.get("season", 0)
        pos_str = str(r.get("position", ""))
        points = float(r.get("points", 0))

        if constructor_id not in teams:
            teams[constructor_id] = {
                "constructor_id": constructor_id,
                "constructor_name": constructor_name,
                "years": set(),
                "races": 0,
                "wins": 0,
                "podiums": 0,
                "points": 0.0,
            }

        team = teams[constructor_id]
        team["years"].add(season)
        team["races"] += 1
        team["points"] += points

        if pos_str.isdigit():
            pos = int(pos_str)
            if pos == 1:
                team["wins"] += 1
            if pos <= 3:
                team["podiums"] += 1

    # Convert to sorted list (most races first)
    return sorted(
        [
            {
                "constructor_id": t["constructor_id"],
                "constructor_name": t["constructor_name"],
                "years": sorted(t["years"]),
                "races": t["races"],
                "wins": t["wins"],
                "podiums": t["podiums"],
                "points": t["points"],
            }
            for t in teams.values()
        ],
        key=lambda t: t["races"],
        reverse=True,
    )


def _compute_head_to_head(
    a_results: list[dict], b_results: list[dict]
) -> dict:
    """Compute H2H by matching races from shared seasons by round number."""
    # Index results by (season, round)
    a_by_race: dict[tuple[int, int], dict] = {}
    for r in a_results:
        key = (r["season"], r["round"])
        a_by_race[key] = r

    b_by_race: dict[tuple[int, int], dict] = {}
    for r in b_results:
        key = (r["season"], r["round"])
        b_by_race[key] = r

    # Find shared races
    shared_race_keys = sorted(set(a_by_race.keys()) & set(b_by_race.keys()))

    a_wins = 0
    b_wins = 0
    draws = 0
    race_details: list[dict] = []

    for (season, rnd) in shared_race_keys:
        a_r = a_by_race[(season, rnd)]
        b_r = b_by_race[(season, rnd)]

        a_pos = str(a_r.get("position", ""))
        b_pos = str(b_r.get("position", ""))
        a_status = a_r.get("status", "")
        b_status = b_r.get("status", "")

        winner = _determine_race_winner(a_pos, b_pos, a_status, b_status)
        if winner == "a":
            a_wins += 1
        elif winner == "b":
            b_wins += 1
        else:
            draws += 1

        race_details.append({
            "season": season,
            "round": rnd,
            "race_name": a_r.get("race_name", ""),
            "date": a_r.get("date", ""),
            "driver_a": {
                "position": a_pos,
                "points": float(a_r.get("points", 0)),
                "status": a_status,
            },
            "driver_b": {
                "position": b_pos,
                "points": float(b_r.get("points", 0)),
                "status": b_status,
            },
            "winner": winner,
        })

    # Shared seasons
    a_seasons = set(r["season"] for r in a_results)
    b_seasons = set(r["season"] for r in b_results)
    shared_seasons = sorted(a_seasons & b_seasons)

    return {
        "shared_seasons": shared_seasons,
        "shared_races": len(shared_race_keys),
        "driver_a_wins": a_wins,
        "driver_b_wins": b_wins,
        "draws": draws,
        "race_details": race_details,
    }


def _determine_race_winner(a_pos: str, b_pos: str, a_status: str, b_status: str) -> str:
    """Determine who won the head-to-head in a single race.

    Returns 'a', 'b', or 'draw'.
    """
    a_classified = a_pos.isdigit()
    b_classified = b_pos.isdigit()

    if a_classified and b_classified:
        a_int = int(a_pos)
        b_int = int(b_pos)
        if a_int < b_int:
            return "a"
        elif b_int < a_int:
            return "b"
        else:
            return "draw"
    elif a_classified and not b_classified:
        return "a"
    elif b_classified and not a_classified:
        return "b"
    else:
        return "draw"
