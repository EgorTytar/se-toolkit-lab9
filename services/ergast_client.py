"""Async client for the Ergast F1 Developer API."""

import httpx

from config import ERGAST_BASE_URL, ERGAST_TIMEOUT


class ErgastClient:
    """Fetches Formula 1 race data from the Ergast API."""

    def __init__(self) -> None:
        self.base_url = ERGAST_BASE_URL
        self.timeout = ERGAST_TIMEOUT

    async def _get(self, url: str) -> dict:
        """Perform an async GET request to the Ergast API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{url}", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def get_latest_race(self) -> dict:
        """Fetch data for the most recent race."""
        data = await self._get("current/last/results.json")
        return self._extract_race_data(data)

    async def get_race_by_year_round(
        self, year: int, round: int
    ) -> dict:
        """Fetch data for a specific race by season year and round number."""
        data = await self._get(f"{year}/{round}/results.json")
        return self._extract_race_data(data)

    async def get_season_schedule(self, year: int) -> list[dict]:
        """Fetch the schedule for a full season (all races)."""
        data = await self._get(f"{year}.json")
        try:
            races = data["MRData"]["RaceTable"]["Races"]
        except (KeyError, IndexError):
            raise ValueError(f"No schedule data found for season {year}")

        return [
            {
                "round": int(r.get("round", 0)),
                "race_name": r.get("raceName", "Unknown"),
                "circuit": r.get("Circuit", {}).get("circuitName", "Unknown"),
                "date": r.get("date", "Unknown"),
            }
            for r in races
        ]

    async def get_driver_standings(self, year: int) -> list[dict]:
        """Fetch driver championship standings for a season."""
        data = await self._get(f"{year}/driverStandings.json")
        try:
            standings = data["MRData"]["StandingsTable"]["StandingsLists"][0]
        except (KeyError, IndexError):
            raise ValueError(f"No driver standings found for season {year}")

        return [
            {
                "position": int(s.get("position", 0)),
                "driver_id": s.get("Driver", {}).get("driverId", ""),
                "driver_code": s.get("Driver", {}).get("code", ""),
                "driver_name": f"{s.get('Driver', {}).get('givenName', '')} {s.get('Driver', {}).get('familyName', '')}".strip(),
                "nationality": s.get("Driver", {}).get("nationality", ""),
                "constructor": s.get("Constructors", [{}])[0].get("name", "Unknown"),
                "points": float(s.get("points", 0)),
                "wins": int(s.get("wins", 0)),
            }
            for s in standings.get("DriverStandings", [])
        ]

    async def get_constructor_standings(self, year: int) -> list[dict]:
        """Fetch constructor championship standings for a season."""
        data = await self._get(f"{year}/constructorStandings.json")
        try:
            standings = data["MRData"]["StandingsTable"]["StandingsLists"][0]
        except (KeyError, IndexError):
            raise ValueError(f"No constructor standings found for season {year}")

        return [
            {
                "position": int(s.get("position", 0)),
                "constructor": s.get("Constructor", {}).get("name", "Unknown"),
                "nationality": s.get("Constructor", {}).get("nationality", ""),
                "points": float(s.get("points", 0)),
                "wins": int(s.get("wins", 0)),
            }
            for s in standings.get("ConstructorStandings", [])
        ]

    async def get_driver_info(self, driver_ref: str) -> dict:
        """Fetch basic info for a driver by their Ergast driver reference."""
        data = await self._get(f"drivers/{driver_ref}.json")
        try:
            driver = data["MRData"]["DriverTable"]["Drivers"][0]
        except (KeyError, IndexError):
            raise ValueError(f"Driver '{driver_ref}' not found")

        return {
            "driver_id": driver.get("driverId", ""),
            "code": driver.get("code", ""),
            "given_name": driver.get("givenName", ""),
            "family_name": driver.get("familyName", ""),
            "full_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
            "date_of_birth": driver.get("dateOfBirth", ""),
            "nationality": driver.get("nationality", ""),
            "permanent_number": driver.get("permanentNumber", ""),
            "url": driver.get("url", ""),
        }

    async def get_driver_season_results(self, driver_ref: str, year: int) -> list[dict]:
        """Fetch all race results for a driver in a given season."""
        data = await self._get(f"{year}/drivers/{driver_ref}/results.json")
        try:
            races = data["MRData"]["RaceTable"]["Races"]
        except (KeyError, IndexError):
            return []

        results = []
        for race in races:
            result_entry = race.get("Results", [{}])[0]
            if not result_entry:
                continue
            results.append({
                "round": int(race.get("round", 0)),
                "race_name": race.get("raceName", ""),
                "circuit": race.get("Circuit", {}).get("circuitName", ""),
                "date": race.get("date", ""),
                "position": result_entry.get("position", ""),
                "grid": int(result_entry.get("grid", 0)),
                "points": float(result_entry.get("points", 0)),
                "status": result_entry.get("status", ""),
            })

        return results

    @staticmethod
    def _extract_race_data(data: dict) -> dict:
        """Extract and structure race information from the raw API response."""
        try:
            race_table = data["MRData"]["RaceTable"]["Races"][0]
        except (KeyError, IndexError):
            raise ValueError("No race data found in API response")

        results = race_table.get("Results", [])
        parsed_results = []

        for entry in results:
            driver = entry.get("Driver", {})
            constructor = entry.get("Constructor", {})
            parsed_results.append(
                {
                    "position": int(entry.get("position", 0)),
                    "driver_id": driver.get("driverId", ""),
                    "driver_number": driver.get("permanentNumber", "N/A"),
                    "driver_code": driver.get("code", "N/A"),
                    "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                    "constructor": constructor.get("name", "Unknown"),
                    "grid": int(entry.get("grid", 0)),
                    "laps": int(entry.get("laps", 0)),
                    "status": entry.get("status", "Unknown"),
                    "time": entry.get("Time", {}).get("time", ""),
                    "points": float(entry.get("points", 0)),
                }
            )

        return {
            "season": race_table.get("season", "Unknown"),
            "round": int(race_table.get("round", 0)),
            "race_name": race_table.get("raceName", "Unknown"),
            "circuit": race_table.get("Circuit", {}).get("circuitName", "Unknown"),
            "location": race_table.get("Circuit", {}).get("Location", {}),
            "date": race_table.get("date", "Unknown"),
            "time": race_table.get("time", ""),
            "results": parsed_results,
        }
