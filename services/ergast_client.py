"""Async client for the Ergast F1 Developer API."""

import asyncio
import httpx

from config import ERGAST_BASE_URL, ERGAST_TIMEOUT


class ErgastClient:
    """Fetches Formula 1 race data from the Ergast API."""

    def __init__(self) -> None:
        self.base_url = ERGAST_BASE_URL
        self.timeout = ERGAST_TIMEOUT
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create a persistent HTTP client (reuses connections)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def _get(self, url: str, retries: int = 5) -> dict:
        """Perform an async GET request to the Ergast API with retry on 429."""
        client = await self._get_client()
        last_response = None
        for attempt in range(retries):
            response = await client.get(f"{self.base_url}/{url}")
            last_response = response
            if response.status_code == 429:
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s, 16s, 32s
                await asyncio.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        # All retries exhausted
        assert last_response is not None
        last_response.raise_for_status()
        return {}  # unreachable but satisfies type checker

    async def close(self) -> None:
        """Close the persistent HTTP client if it exists."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

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
                "circuit_id": r.get("Circuit", {}).get("circuitId", ""),
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
                "constructor_id": s.get("Constructor", {}).get("constructorId", ""),
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
            constructor = result_entry.get("Constructor", {})
            results.append({
                "round": int(race.get("round", 0)),
                "race_name": race.get("raceName", ""),
                "circuit": race.get("Circuit", {}).get("circuitName", ""),
                "circuit_id": race.get("Circuit", {}).get("circuitId", ""),
                "date": race.get("date", ""),
                "position": result_entry.get("position", ""),
                "grid": int(result_entry.get("grid", 0)),
                "points": float(result_entry.get("points", 0)),
                "status": result_entry.get("status", ""),
                "constructor": constructor.get("name", ""),
                "constructor_id": constructor.get("constructorId", ""),
            })

        return results

    async def get_circuit_info(self, circuit_id: str) -> dict | None:
        """Fetch info and recent race results for a circuit."""
        data = await self._get(f"circuits/{circuit_id}.json")
        try:
            circuit = data["MRData"]["CircuitTable"]["Circuits"][0]
        except (KeyError, IndexError):
            return None

        return {
            "circuit_id": circuit.get("circuitId", ""),
            "name": circuit.get("circuitName", ""),
            "location": circuit.get("Location", {}).get("locality", ""),
            "country": circuit.get("Location", {}).get("country", ""),
            "latitude": circuit.get("Location", {}).get("lat", ""),
            "longitude": circuit.get("Location", {}).get("long", ""),
            "url": circuit.get("url", ""),
        }

    async def get_season_races(self, year: int) -> list[dict]:
        """Fetch all race results for a given season (full results, not just schedule)."""
        data = await self._get(f"{year}.json")
        try:
            races = data["MRData"]["RaceTable"]["Races"]
        except (KeyError, IndexError):
            return []

        return races

    async def get_driver_all_results(self, driver_ref: str) -> list[dict]:
        """Fetch ALL race results for a driver across their entire career.

        Uses pagination since Ergast limits to 30 results per page by default.
        We use limit=100 and paginate through all results.
        """
        all_results = []
        offset = 0
        limit = 100

        while True:
            data = await self._get(
                f"drivers/{driver_ref}/results.json?limit={limit}&offset={offset}"
            )
            try:
                races = data["MRData"]["RaceTable"]["Races"]
                total = int(data["MRData"].get("total", 0))
            except (KeyError, IndexError):
                break

            for race in races:
                result_entry = race.get("Results", [{}])[0]
                if not result_entry:
                    continue
                constructor = result_entry.get("Constructor", {})
                all_results.append({
                    "season": int(race.get("season", 0)),
                    "round": int(race.get("round", 0)),
                    "race_name": race.get("raceName", ""),
                    "circuit": race.get("Circuit", {}).get("circuitName", ""),
                    "circuit_id": race.get("Circuit", {}).get("circuitId", ""),
                    "date": race.get("date", ""),
                    "position": result_entry.get("position", ""),
                    "grid": int(result_entry.get("grid", 0)),
                    "points": float(result_entry.get("points", 0)),
                    "status": result_entry.get("status", ""),
                    "constructor": constructor.get("name", ""),
                    "constructor_id": constructor.get("constructorId", ""),
                })

            offset += limit
            if offset >= total:
                break

        return all_results

    async def get_constructor_all_results(self, constructor_ref: str) -> list[dict]:
        """Fetch ALL race results for a constructor across their entire history.

        Uses pagination (API caps at 100 per page).
        Returns one entry per driver per race (so 2 entries per race for 2-car teams).
        """
        all_results = []
        offset = 0
        limit = 100

        while True:
            data = await self._get(
                f"constructors/{constructor_ref}/results.json?limit={limit}&offset={offset}"
            )
            try:
                races = data["MRData"]["RaceTable"]["Races"]
                total = int(data["MRData"].get("total", 0))
            except (KeyError, IndexError):
                break

            for race in races:
                # Each race can have multiple Results entries (one per driver)
                for result_entry in race.get("Results", []):
                    driver = result_entry.get("Driver", {})
                    constructor = result_entry.get("Constructor", {})
                    all_results.append({
                        "season": int(race.get("season", 0)),
                        "round": int(race.get("round", 0)),
                        "race_name": race.get("raceName", ""),
                        "circuit": race.get("Circuit", {}).get("circuitName", ""),
                        "circuit_id": race.get("Circuit", {}).get("circuitId", ""),
                        "date": race.get("date", ""),
                        "position": result_entry.get("position", ""),
                        "grid": int(result_entry.get("grid", 0)),
                        "points": float(result_entry.get("points", 0)),
                        "status": result_entry.get("status", ""),
                        "driver": driver.get("driverId", ""),
                        "constructor": constructor.get("name", ""),
                        "constructor_id": constructor.get("constructorId", ""),
                    })

            offset += limit
            if offset >= total:
                break

        return all_results

    async def get_constructor_info(self, constructor_ref: str) -> dict:
        """Fetch basic info for a constructor."""
        data = await self._get(f"constructors/{constructor_ref}.json")
        try:
            constructor = data["MRData"]["ConstructorTable"]["Constructors"][0]
        except (KeyError, IndexError):
            raise ValueError(f"Constructor '{constructor_ref}' not found")

        return {
            "constructor_id": constructor.get("constructorId", ""),
            "name": constructor.get("name", ""),
            "nationality": constructor.get("nationality", ""),
            "url": constructor.get("url", ""),
        }

    async def get_all_constructors(self) -> list[dict]:
        """Fetch ALL F1 constructors for search/autocomplete.

        Cached on first call to avoid repeated API hits.
        API caps at 100 per page, so we paginate accordingly.
        """
        all_constructors: list[dict] = []
        offset = 0
        limit = 100

        while True:
            data = await self._get(f"constructors.json?limit={limit}&offset={offset}")
            try:
                constructors = data["MRData"]["ConstructorTable"]["Constructors"]
                total = int(data["MRData"].get("total", 0))
            except (KeyError, IndexError):
                break

            if not constructors:
                break

            for c in constructors:
                all_constructors.append({
                    "constructor_id": c.get("constructorId", ""),
                    "name": c.get("name", ""),
                    "nationality": c.get("nationality", ""),
                    "url": c.get("url", ""),
                })

            offset += limit
            if offset >= total or len(constructors) < limit:
                break

        return all_constructors

    async def get_all_drivers(self) -> list[dict]:
        """Fetch ALL F1 drivers (879+) for search/autocomplete.

        Cached on first call to avoid repeated API hits.
        API caps at 100 per page, so we paginate accordingly.
        """
        all_drivers: list[dict] = []
        offset = 0
        limit = 100  # API maximum

        while True:
            data = await self._get(f"drivers.json?limit={limit}&offset={offset}")
            try:
                drivers = data["MRData"]["DriverTable"]["Drivers"]
                total = int(data["MRData"].get("total", 0))
            except (KeyError, IndexError):
                break

            if not drivers:
                break

            for driver in drivers:
                all_drivers.append({
                    "driver_id": driver.get("driverId", ""),
                    "code": driver.get("code", ""),
                    "given_name": driver.get("givenName", ""),
                    "family_name": driver.get("familyName", ""),
                    "full_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                    "date_of_birth": driver.get("dateOfBirth", ""),
                    "nationality": driver.get("nationality", ""),
                    "permanent_number": driver.get("permanentNumber", ""),
                })

            offset += limit
            if offset >= total or len(drivers) < limit:
                break

        return all_drivers

    async def get_circuit_recent_results(self, circuit_id: str, limit: int = 5) -> list[dict]:
        """Fetch up to `limit` most recent race results at a circuit.

        Uses season-by-season approach since the Ergast total count
        counts individual driver results, not unique races.
        """
        import datetime
        current_year = datetime.datetime.now().year

        results = []
        # Check seasons from most recent backwards
        for year in range(current_year, 1950, -1):
            if len(results) >= limit:
                break
            try:
                data = await self._get(f"{year}/circuits/{circuit_id}/results.json")
                races = data["MRData"]["RaceTable"]["Races"]
            except (KeyError, IndexError):
                continue

            for race in races:
                if len(results) >= limit:
                    break
                result_entry = race.get("Results", [{}])[0]
                if not result_entry:
                    continue
                driver = result_entry.get("Driver", {})
                constructor = result_entry.get("Constructor", {})
                results.append({
                    "season": race.get("season", ""),
                    "round": int(race.get("round", 0)),
                    "race_name": race.get("raceName", ""),
                    "date": race.get("date", ""),
                    "position": result_entry.get("position", ""),
                    "driver_name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                    "driver_id": driver.get("driverId", ""),
                    "constructor": constructor.get("name", ""),
                    "grid": int(result_entry.get("grid", 0)),
                    "points": float(result_entry.get("points", 0)),
                    "status": result_entry.get("status", ""),
                })

        # Results are already most-recent-first (we iterate years backwards)
        return results[:limit]

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
            "circuit_id": race_table.get("Circuit", {}).get("circuitId", ""),
            "location": race_table.get("Circuit", {}).get("Location", {}),
            "date": race_table.get("date", "Unknown"),
            "time": race_table.get("time", ""),
            "results": parsed_results,
        }
