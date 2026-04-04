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
