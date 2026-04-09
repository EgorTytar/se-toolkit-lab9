"""Driver head-to-head comparison endpoint."""

import asyncio
import datetime
import logging

from fastapi import APIRouter, HTTPException, Query

from services.ergast_client import ErgastClient

router = APIRouter(prefix="/api/compare", tags=["compare"])

ergast_client = ErgastClient()
logger = logging.getLogger(__name__)

# In-memory cache for the full driver list (fetched once from API)
_cached_drivers: list[dict] | None = None
_driver_lock = asyncio.Lock()


@router.get("/drivers/search")
async def search_drivers(q: str = Query(..., min_length=1, max_length=100)) -> list[dict]:
    """Search F1 drivers by name.

    Query param:
        q — search query (matched against full name, given name, family name, or code)

    Returns up to 20 matching drivers. Results are cached after first API fetch.
    """
    global _cached_drivers

    # Fetch and cache all drivers on first call (with lock to prevent concurrent fetches)
    if _cached_drivers is None:
        async with _driver_lock:
            # Double-check after acquiring lock
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
async def compare_drivers(
    a: str,
    b: str,
) -> dict:
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

    finish_pos_sum = 0
    classified_count = 0
    grid_sum = 0
    grid_count = 0

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
            classified_count += 1
            finish_pos_sum += pos
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

        if isinstance(grid, int) and grid > 0:
            grid_sum += grid
            grid_count += 1
            if grid == 1:
                total_poles += 1

    # Derived averages
    avg_finish = round(finish_pos_sum / classified_count, 2) if classified_count > 0 else None
    avg_points = round(total_points / total_races, 2) if total_races > 0 else 0
    avg_grid = round(grid_sum / grid_count, 2) if grid_count > 0 else None
    win_pct = round((total_wins / total_races) * 100, 1) if total_races > 0 else 0
    podium_pct = round((total_podiums / total_races) * 100, 1) if total_races > 0 else 0
    dnf_pct = round((dnfs / total_races) * 100, 1) if total_races > 0 else 0

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
        "avg_finish": avg_finish,
        "avg_points": avg_points,
        "avg_grid": avg_grid,
        "win_pct": win_pct,
        "podium_pct": podium_pct,
        "dnf_pct": dnf_pct,
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
        "shared_races": len(race_details),
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


# ── Teammates ──

@router.get("/drivers/{driver_id}/teammates")
async def get_driver_teammates(driver_id: str) -> list[dict]:
    """Get all teammates for a driver across their career.

    Returns a list of drivers who shared a constructor with the given driver,
    including: driver info, shared seasons, shared constructor, and combined races.
    """
    # Get driver info
    try:
        driver_info = await ergast_client.get_driver_info(driver_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Driver '{driver_id}' not found: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    # Get career results to find constructors and seasons
    try:
        career = await ergast_client.get_driver_all_results(driver_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch career results: {e}") from e

    if not career:
        return []

    # Build map of (season, constructor_id) → races
    driver_teams: dict[tuple[int, str], dict] = {}
    for r in career:
        cid = r.get("constructor_id", "")
        season = r.get("season", 0)
        key = (season, cid)
        if key not in driver_teams:
            driver_teams[key] = {"constructor_id": cid, "constructor_name": r.get("constructor", ""), "races": 0}
        driver_teams[key]["races"] += 1

    # For each team, find other drivers
    # Fetch all constructors for each season the driver competed
    seasons = sorted(set(r["season"] for r in career))
    season_constructors: dict[int, list[str]] = {}
    for (season, cid) in driver_teams:
        if season not in season_constructors:
            season_constructors[season] = []
        season_constructors[season].append(cid)

    # Find teammates: other drivers in the same (season, constructor)
    teammate_map: dict[str, dict] = {}  # driver_id → info

    for (season, cid) in driver_teams:
        # Fetch all results for this constructor in this season
        # Use season + constructor endpoint
        offset = 0
        limit = 200
        while True:
            try:
                data = await ergast_client._get(
                    f"{season}/constructors/{cid}/results.json?limit={limit}&offset={offset}"
                )
                races = data["MRData"]["RaceTable"]["Races"]
            except Exception:
                break

            if not races:
                break

            for race in races:
                for entry in race.get("Results", []):
                    did = entry.get("Driver", {}).get("driverId", "")
                    if did and did != driver_id:
                        if did not in teammate_map:
                            teammate_map[did] = {
                                "driver_id": did,
                                "seasons": set(),
                                "constructors": {},
                                "total_races": 0,
                            }
                        teammate_map[did]["seasons"].add(season)
                        c_name = entry.get("Constructor", {}).get("name", cid)
                        teammate_map[did]["constructors"][cid] = c_name
                        teammate_map[did]["total_races"] += 1

            offset += limit
            total = int(data["MRData"].get("total", 0))
            if offset >= total or len(races) < limit:
                break

    # Build final result with driver info
    result = []
    for did, info in teammate_map.items():
        # Fetch basic driver info
        try:
            driver_info = await ergast_client.get_driver_info(did)
        except Exception:
            driver_info = None

        result.append({
            "driver_id": did,
            "code": driver_info.get("code", "") if driver_info else "",
            "full_name": driver_info.get("full_name", did) if driver_info else did,
            "seasons": sorted(info["seasons"]),
            "constructors": [
                {"constructor_id": cid, "constructor_name": name}
                for cid, name in sorted(info["constructors"].items())
            ],
            "total_races": info["total_races"],
        })

    # Sort by total shared seasons (most first)
    result.sort(key=lambda x: len(x["seasons"]), reverse=True)
    return result


# ── Constructor Info ──

# In-memory cache for the full constructor list
_cached_constructors: list[dict] | None = None
_constructor_lock = asyncio.Lock()


@router.get("/constructors/search")
async def search_constructors(q: str = Query(..., min_length=1, max_length=100)) -> list[dict]:
    """Search F1 constructors by name.

    Query param:
        q — search query (matched against name or nationality)

    Returns up to 20 matching constructors. Results are cached after first API fetch.
    """
    global _cached_constructors

    if _cached_constructors is None:
        async with _constructor_lock:
            if _cached_constructors is None:
                try:
                    _cached_constructors = await ergast_client.get_all_constructors()
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to fetch constructor list: {e}") from e

    query = q.lower()
    results = []
    for c in _cached_constructors:
        name = c["name"].lower()
        nationality = c["nationality"].lower()
        cid = c["constructor_id"].lower()

        if query in name or query in nationality or query in cid:
            results.append(c)
            if len(results) >= 20:
                break

    return results


@router.get("/constructors")
async def compare_constructors(a: str, b: str) -> dict:
    """Compare two constructors side-by-side.

    Query params:
        a — first constructor's Ergast ID (e.g. 'ferrari')
        b — second constructor's Ergast ID (e.g. 'mercedes')

    Returns career stats for both constructors plus their head-to-head
    record in races where they both competed.
    """
    # Fetch constructor info
    try:
        constructor_a_info = await ergast_client.get_constructor_info(a)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Constructor '{a}' not found: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ergast API error fetching constructor '{a}': {e}") from e

    try:
        constructor_b_info = await ergast_client.get_constructor_info(b)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=f"Constructor '{b}' not found: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ergast API error fetching constructor '{b}': {e}") from e

    # Fetch ALL career results for both constructors
    try:
        a_all_results = await ergast_client.get_constructor_all_results(a)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch career results for '{a}': {e}") from e

    try:
        b_all_results = await ergast_client.get_constructor_all_results(b)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch career results for '{b}': {e}") from e

    # Build career stats
    constructor_a_career = _compute_constructor_career_stats(a_all_results)
    constructor_b_career = _compute_constructor_career_stats(b_all_results)

    # Compute head-to-head record (no championship counting - too many API calls)
    h2h = _compute_constructor_h2h(a_all_results, b_all_results)

    return {
        "constructor_a": {
            "info": constructor_a_info,
            "career": constructor_a_career,
        },
        "constructor_b": {
            "info": constructor_b_info,
            "career": constructor_b_career,
        },
        "head_to_head": h2h,
    }


def _compute_constructor_career_stats(results: list[dict]) -> dict:
    """Aggregate career statistics for a constructor."""
    total_races = len(results)
    total_wins = 0
    total_podiums = 0
    total_poles = 0
    total_points = 0.0
    best_finish = None
    worst_finish = None
    dnfs = 0
    seasons_active: set[int] = set()

    finish_pos_sum = 0
    classified_count = 0
    grid_sum = 0
    grid_count = 0

    for r in results:
        pos_str = str(r.get("position", ""))
        grid = r.get("grid", 0)
        points = float(r.get("points", 0))
        status = r.get("status", "")
        season = r.get("season", 0)

        seasons_active.add(season)
        total_points += points

        if pos_str.isdigit():
            pos = int(pos_str)
            classified_count += 1
            finish_pos_sum += pos
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

        if isinstance(grid, int) and grid > 0:
            grid_sum += grid
            grid_count += 1
            if grid == 1:
                total_poles += 1

    # Averages
    avg_finish = round(finish_pos_sum / classified_count, 2) if classified_count > 0 else None
    avg_points = round(total_points / total_races, 2) if total_races > 0 else 0
    avg_grid = round(grid_sum / grid_count, 2) if grid_count > 0 else None
    win_pct = round((total_wins / total_races) * 100, 1) if total_races > 0 else 0
    podium_pct = round((total_podiums / total_races) * 100, 1) if total_races > 0 else 0
    dnf_pct = round((dnfs / total_races) * 100, 1) if total_races > 0 else 0

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
        "seasons_active": sorted(seasons_active),
        "avg_finish": avg_finish,
        "avg_points": avg_points,
        "avg_grid": avg_grid,
        "win_pct": win_pct,
        "podium_pct": podium_pct,
        "dnf_pct": dnf_pct,
    }


async def _count_constructor_championships(constructor_id: str, seasons: set[int]) -> int:
    """Count constructor championships."""
    championships = 0
    for year in seasons:
        try:
            standings = await ergast_client.get_constructor_standings(year)
            champ = next(
                (s for s in standings if s["constructor_id"] == constructor_id and s["position"] == 1),
                None,
            )
            if champ:
                championships += 1
        except Exception:
            pass
    return championships


def _compute_constructor_h2h(
    a_results: list[dict], b_results: list[dict]
) -> dict:
    """Compute H2H between two constructors by comparing their best result in each shared race."""
    # Index by (season, round) → best result for that constructor
    a_by_race: dict[tuple[int, int], dict] = {}
    for r in a_results:
        key = (r["season"], r["round"])
        if key not in a_by_race:
            a_by_race[key] = r
        else:
            # Keep the better (lower position) result
            existing_pos = a_by_race[key].get("position", "")
            new_pos = r.get("position", "")
            if new_pos.isdigit() and (not existing_pos.isdigit() or int(new_pos) < int(existing_pos)):
                a_by_race[key] = r

    b_by_race: dict[tuple[int, int], dict] = {}
    for r in b_results:
        key = (r["season"], r["round"])
        if key not in b_by_race:
            b_by_race[key] = r
        else:
            existing_pos = b_by_race[key].get("position", "")
            new_pos = r.get("position", "")
            if new_pos.isdigit() and (not existing_pos.isdigit() or int(new_pos) < int(existing_pos)):
                b_by_race[key] = r

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
            "constructor_a": {
                "position": a_pos,
                "points": float(a_r.get("points", 0)),
                "status": a_status,
                "driver": a_r.get("driver", ""),
            },
            "constructor_b": {
                "position": b_pos,
                "points": float(b_r.get("points", 0)),
                "status": b_status,
                "driver": b_r.get("driver", ""),
            },
            "winner": winner,
        })

    a_seasons = set(r["season"] for r in a_results)
    b_seasons = set(r["season"] for r in b_results)
    shared_seasons = sorted(a_seasons & b_seasons)

    return {
        "shared_seasons": shared_seasons,
        "shared_races": len(race_details),
        "constructor_a_wins": a_wins,
        "constructor_b_wins": b_wins,
        "draws": draws,
        "race_details": race_details,
    }

@router.get("/constructors/{constructor_id}")
async def get_constructor_info(constructor_id: str, year: int = 0) -> dict:
    """Get constructor info and season results.

    Similar to driver info endpoint.
    """
    import datetime
    current_year = datetime.datetime.now().year
    target_year = year if year > 0 else current_year

    try:
        info = await ergast_client.get_constructor_info(constructor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    if not info:
        raise HTTPException(status_code=404, detail=f"Constructor '{constructor_id}' not found")

    # Fetch season results for the constructor
    season_results = []
    try:
        all_results = await ergast_client.get_constructor_all_results(constructor_id)
        season_results = [r for r in all_results if r["season"] == target_year]
    except Exception:
        pass

    # Season stats
    season_stats = {}
    if season_results:
        # Count unique races (not sum of both drivers)
        unique_rounds = set(r["round"] for r in season_results)
        positions = [int(r["position"]) for r in season_results if str(r["position"]).isdigit()]
        season_stats = {
            "races": len(unique_rounds),
            "points": sum(r.get("points", 0) for r in season_results),
            "best_finish": min(positions) if positions else None,
            "wins": sum(1 for r in season_results if str(r["position"]) == "1"),
        }

    return {
        "constructor": info,
        "season": target_year,
        "results": season_results,
        "season_stats": season_stats,
    }


@router.get("/constructors/{constructor_id}/ai-summary")
async def get_constructor_ai_summary(constructor_id: str, year: int = 0) -> dict:
    """Generate an AI summary of a constructor's season performance."""
    import datetime
    from services.ai_assistant import AISummarizer

    current_year = datetime.datetime.now().year
    target_year = year if year > 0 else current_year

    try:
        info = await ergast_client.get_constructor_info(constructor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ergast API error: {e}") from e

    # Fetch season results
    season_results = []
    try:
        all_results = await ergast_client.get_constructor_all_results(constructor_id)
        season_results = [r for r in all_results if r["season"] == target_year]
    except Exception:
        pass

    if not season_results:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for {info['name']} in {target_year}",
        )

    # Build results text
    positions = [int(r["position"]) for r in season_results if str(r["position"]).isdigit()]
    wins = sum(1 for r in season_results if str(r["position"]) == "1")
    podiums = sum(1 for r in season_results if str(r["position"]).isdigit() and int(r["position"]) <= 3)
    total_points = sum(r.get("points", 0) for r in season_results)

    results_lines = []
    for r in season_results[:10]:
        results_lines.append(
            f"Round {r['round']}: {r['race_name']} — Driver: {r['driver']}, "
            f"Position: P{r['position']}, Points: {r['points']}, Grid: P{r['grid']}"
        )
    if len(season_results) > 10:
        results_lines.append(f"...and {len(season_results) - 10} more races")

    context_text = (
        f"Constructor: {info['name']}\n"
        f"Season: {target_year}\n"
        f"Races: {len(season_results)}\n"
        f"Wins: {wins}\n"
        f"Podiums: {podiums}\n"
        f"Total Points: {total_points}\n"
        f"Best Finish: P{min(positions) if positions else 'N/A'}\n"
        f"\nRace Results:\n" + "\n".join(results_lines)
    )

    summarizer = AISummarizer()
    result = await summarizer.summarize(
        context_text,
        user_query=f"Give me a detailed analysis of {info['name']}'s {target_year} F1 season performance based on the data above.",
    )

    return {
        "constructor": info["name"],
        "season": target_year,
        "ai_summary": result,
    }


# ── Constructor Comparison ──

