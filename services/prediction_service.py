"""Championship prediction service using statistical analysis + AI."""

import datetime
import json
import logging
from typing import Optional

from services.ergast_client import ErgastClient
from services.ai_assistant import AISummarizer

logger = logging.getLogger(__name__)

PREDICTION_SYSTEM_PROMPT = """You are a Formula 1 championship prediction expert.

You will be given:
1. Current championship standings (drivers or constructors)
2. Form analysis (last 5 races performance)
3. Remaining races in the season
4. Statistical prediction based on points gaps

Your task:
- Analyze the data and predict who will win the championship
- Provide a confidence level (0.0 to 1.0)
- Explain your reasoning clearly
- Consider: current points gap, momentum, remaining races, historical patterns

Respond in valid JSON with these exact keys:
{
  "predicted_champion_id": "driver_id or constructor_id",
  "predicted_champion_name": "Name",
  "predicted_final_points": 450,
  "confidence": 0.85,
  "reasoning": "Detailed explanation of your prediction",
  "top_contenders": [
    {"id": "...", "name": "...", "predicted_points": 420, "chance_pct": 0.12}
  ]
}

RULES:
- Base predictions on data, not speculation
- Consider DNF risk for aggressive drivers
- Large points gaps (>50) with few races remaining = high confidence
- Close battles with many races = lower confidence
- Always include at least 3 top contenders
"""


class PredictionService:
    """Generates championship predictions using stats + AI."""

    def __init__(self) -> None:
        self.ergast = ErgastClient()
        self.ai = AISummarizer()

    async def predict_driver_champion(self, year: int) -> dict:
        """Generate driver championship prediction for a season."""
        current_year = datetime.datetime.now().year
        if year < 1950 or year > current_year:
            return self._error_response(year, "drivers")

        # Fetch current standings
        try:
            standings = await self.ergast.get_driver_standings(year)
        except (ValueError, Exception) as e:
            logger.warning(f"Could not fetch driver standings for {year}: {e}")
            return self._error_response(year, "drivers")

        if not standings:
            return self._error_response(year, "drivers")

        # Get remaining/completed races
        try:
            schedule = await self.ergast.get_season_schedule(year)
        except Exception as e:
            logger.warning(f"Could not fetch schedule for {year}: {e}")
            schedule = []

        # Determine how many races have been completed
        races_completed = self._count_completed_races(schedule, year)
        races_remaining = len(schedule) - races_completed

        # Calculate form for top drivers
        top_drivers = standings[:5]  # Top 5 in championship
        form_analysis = {}
        for driver in top_drivers:
            driver_id = driver["driver_id"]
            form = await self._calculate_driver_form(driver_id, year, races_completed)
            form_analysis[driver_id] = form

        # Statistical prediction based on points pace
        statistical_prediction = self._predict_driver_points(
            standings, schedule, races_completed, races_remaining
        )

        # Build prediction prompt
        prediction_data = {
            "season": year,
            "current_standings": standings[:5],
            "form_analysis": form_analysis,
            "races_completed": races_completed,
            "races_remaining": races_remaining,
            "statistical_prediction": statistical_prediction,
        }

        # AI prediction
        ai_result = await self._get_ai_prediction(prediction_data, "drivers")

        # Merge statistical and AI predictions
        result = {
            "season": year,
            "type": "drivers",
            "races_completed": races_completed,
            "races_remaining": races_remaining,
            "predicted_champion": {
                "driver_id": ai_result.get("predicted_champion_id", standings[0]["driver_id"]),
                "name": ai_result.get("predicted_champion_name", standings[0]["driver_name"]),
                "current_points": standings[0]["points"],
                "predicted_final_points": ai_result.get("predicted_final_points", int(statistical_prediction.get(standings[0]["driver_id"], {}).get("predicted_final", standings[0]["points"]))),
                "confidence": ai_result.get("confidence", 0.5),
            },
            "top_contenders": ai_result.get("top_contenders", self._build_fallback_contenders(standings[:5], statistical_prediction)),
            "form_analysis": form_analysis,
            "ai_reasoning": ai_result.get("reasoning", "Statistical prediction based on current points pace and remaining races."),
        }

        await self.ergast.close()
        return result

    async def predict_constructor_champion(self, year: int) -> dict:
        """Generate constructor championship prediction for a season."""
        current_year = datetime.datetime.now().year
        if year < 1950 or year > current_year:
            return self._error_response(year, "constructors")

        # Fetch current standings
        try:
            standings = await self.ergast.get_constructor_standings(year)
        except (ValueError, Exception) as e:
            logger.warning(f"Could not fetch constructor standings for {year}: {e}")
            return self._error_response(year, "constructors")

        if not standings:
            return self._error_response(year, "constructors")

        # Get remaining/completed races
        try:
            schedule = await self.ergast.get_season_schedule(year)
        except Exception as e:
            logger.warning(f"Could not fetch schedule for {year}: {e}")
            schedule = []

        races_completed = self._count_completed_races(schedule, year)
        races_remaining = len(schedule) - races_completed

        # Calculate form for top constructors
        top_constructors = standings[:5]
        form_analysis = {}
        for constructor in top_constructors:
            constructor_id = constructor["constructor_id"]
            form = await self._calculate_constructor_form(constructor_id, year, races_completed)
            form_analysis[constructor_id] = form

        # Statistical prediction
        statistical_prediction = self._predict_constructor_points(
            standings, schedule, races_completed, races_remaining
        )

        # Build prediction prompt
        prediction_data = {
            "season": year,
            "current_standings": standings[:5],
            "form_analysis": form_analysis,
            "races_completed": races_completed,
            "races_remaining": races_remaining,
            "statistical_prediction": statistical_prediction,
        }

        # AI prediction
        ai_result = await self._get_ai_prediction(prediction_data, "constructors")

        # Merge statistical and AI predictions
        result = {
            "season": year,
            "type": "constructors",
            "races_completed": races_completed,
            "races_remaining": races_remaining,
            "predicted_champion": {
                "constructor_id": ai_result.get("predicted_champion_id", standings[0]["constructor_id"]),
                "name": ai_result.get("predicted_champion_name", standings[0]["constructor"]),
                "current_points": standings[0]["points"],
                "predicted_final_points": ai_result.get("predicted_final_points", int(statistical_prediction.get(standings[0]["constructor_id"], {}).get("predicted_final", standings[0]["points"]))),
                "confidence": ai_result.get("confidence", 0.5),
            },
            "top_contenders": ai_result.get("top_contenders", self._build_fallback_constructor_contenders(standings[:5], statistical_prediction)),
            "form_analysis": form_analysis,
            "ai_reasoning": ai_result.get("reasoning", "Statistical prediction based on current points pace and remaining races."),
        }

        await self.ergast.close()
        return result

    # ── Form Analysis ───────────────────────────────────────────────────

    async def _calculate_driver_form(self, driver_ref: str, year: int, races_completed: int, last_n: int = 5) -> dict:
        """Calculate a driver's form over their last N races."""
        try:
            season_results = await self.ergast.get_driver_season_results(driver_ref, year)
        except Exception:
            return self._empty_form()

        if not season_results:
            return self._empty_form()

        # Take the last N completed races
        recent = [r for r in season_results if r.get("position") != ""][ -last_n:]

        if not recent:
            return self._empty_form()

        total_points = sum(float(r.get("points", 0)) for r in recent)
        avg_points = total_points / len(recent)
        wins = sum(1 for r in recent if r.get("position") == "1")
        podiums = sum(1 for r in recent if r.get("position") in ["1", "2", "3"])
        dnfs = sum(1 for r in recent if "Retired" in r.get("status", "") or "DNF" in r.get("status", "").upper() or r.get("position") == "")

        return {
            "races_analyzed": len(recent),
            "avg_points": round(avg_points, 1),
            "total_points": total_points,
            "wins": wins,
            "podiums": podiums,
            "dnfs": dnfs,
            "win_pct": round(wins / len(recent) * 100, 1),
            "podium_pct": round(podiums / len(recent) * 100, 1),
            "dnf_pct": round(dnfs / len(recent) * 100, 1),
        }

    async def _calculate_constructor_form(self, constructor_ref: str, year: int, races_completed: int, last_n: int = 5) -> dict:
        """Calculate a constructor's form over their last N races."""
        try:
            season_results = await self.ergast.get_constructor_all_results(constructor_ref)
        except Exception:
            return self._empty_form()

        # Filter to this year and take most recent
        year_results = [r for r in season_results if r.get("season") == year]

        if not year_results:
            return self._empty_form()

        # Group by race (round) and sum constructor points
        race_points = {}
        for r in year_results:
            round_num = r.get("round", 0)
            pts = float(r.get("points", 0))
            if round_num not in race_points:
                race_points[round_num] = 0
            race_points[round_num] += pts

        # Sort by round and take last N
        sorted_rounds = sorted(race_points.keys())
        recent_rounds = sorted_rounds[-last_n:]

        if not recent_rounds:
            return self._empty_form()

        recent_points = [race_points[r] for r in recent_rounds]
        total_points = sum(recent_points)
        avg_points = total_points / len(recent_points)

        return {
            "races_analyzed": len(recent_rounds),
            "avg_points_per_race": round(avg_points, 1),
            "total_points_recent": round(total_points, 1),
        }

    # ── Statistical Prediction ──────────────────────────────────────────

    def _predict_driver_points(
        self, standings: list[dict], schedule: list[dict], completed: int, remaining: int
    ) -> dict:
        """Predict final points for each driver based on current pace."""
        predictions = {}

        for driver in standings:
            current_points = driver["points"]
            if completed > 0:
                pace = current_points / completed
                predicted_additional = pace * remaining
                predicted_final = current_points + predicted_additional
            else:
                predicted_final = current_points

            predictions[driver["driver_id"]] = {
                "current_points": current_points,
                "predicted_final": round(predicted_final, 1),
                "pace_per_race": round(current_points / completed, 1) if completed > 0 else 0,
            }

        return predictions

    def _predict_constructor_points(
        self, standings: list[dict], schedule: list[dict], completed: int, remaining: int
    ) -> dict:
        """Predict final points for each constructor based on current pace."""
        predictions = {}

        for constructor in standings:
            current_points = constructor["points"]
            if completed > 0:
                pace = current_points / completed
                predicted_additional = pace * remaining
                predicted_final = current_points + predicted_additional
            else:
                predicted_final = current_points

            predictions[constructor["constructor_id"]] = {
                "current_points": current_points,
                "predicted_final": round(predicted_final, 1),
                "pace_per_race": round(current_points / completed, 1) if completed > 0 else 0,
            }

        return predictions

    # ── AI Prediction ───────────────────────────────────────────────────

    async def _get_ai_prediction(self, data: dict, pred_type: str) -> dict:
        """Get AI prediction or return empty dict for fallback."""
        if not self.ai.is_available:
            logger.info("AI unavailable, using statistical prediction only")
            return {}

        prompt = f"""
Formula 1 {pred_type} Championship Prediction — Season {data['season']}

CURRENT STANDINGS (Top 5):
{json.dumps(data['current_standings'], indent=2)}

FORM ANALYSIS (Last 5 Races):
{json.dumps(data['form_analysis'], indent=2)}

STATISTICAL PREDICTION (Based on points pace):
{json.dumps(data['statistical_prediction'], indent=2)}

RACES COMPLETED: {data['races_completed']}
RACES REMAINING: {data['races_remaining']}

Please provide your prediction following the JSON format specified in the system prompt.
"""

        try:
            result = await self.ai.chat_response([
                {"role": "system", "content": PREDICTION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ])

            # Try to parse JSON from the response
            result = result.strip()
            if result.startswith("```"):
                # Remove code blocks if present
                lines = result.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith("```json") or line.startswith("```"):
                        in_json = not in_json if line.startswith("```") else True
                        continue
                    json_lines.append(line)
                result = "\n".join(json_lines)

            # Find JSON object in response
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
        except Exception as e:
            logger.warning(f"AI prediction failed: {e}")

        return {}

    # ── Helpers ─────────────────────────────────────────────────────────

    def _count_completed_races(self, schedule: list[dict], year: int) -> int:
        """Count how many races in the season have been completed."""
        if not schedule:
            return 0

        now = datetime.datetime.now()
        completed = 0

        for race in schedule:
            race_date = race.get("date", "")
            if not race_date:
                continue
            try:
                race_dt = datetime.datetime.strptime(race_date, "%Y-%m-%d")
                if race_dt < now:
                    completed += 1
            except ValueError:
                continue

        return completed

    def _empty_form(self) -> dict:
        """Return empty form data when no data is available."""
        return {
            "races_analyzed": 0,
            "avg_points": 0,
            "total_points": 0,
            "wins": 0,
            "podiums": 0,
            "dnfs": 0,
            "win_pct": 0,
            "podium_pct": 0,
            "dnf_pct": 0,
        }

    def _build_fallback_contenders(self, standings: list[dict], predictions: dict) -> list[dict]:
        """Build contenders list from statistical prediction when AI fails."""
        contenders = []
        for driver in standings:
            driver_id = driver["driver_id"]
            pred = predictions.get(driver_id, {})
            contenders.append({
                "id": driver_id,
                "name": driver["driver_name"],
                "predicted_points": pred.get("predicted_final", driver["points"]),
            })
        return contenders

    def _build_fallback_constructor_contenders(self, standings: list[dict], predictions: dict) -> list[dict]:
        """Build constructor contenders list when AI fails."""
        contenders = []
        for constructor in standings:
            constructor_id = constructor["constructor_id"]
            pred = predictions.get(constructor_id, {})
            contenders.append({
                "id": constructor_id,
                "name": constructor["constructor"],
                "predicted_points": pred.get("predicted_final", constructor["points"]),
            })
        return contenders

    def _error_response(self, year: int, pred_type: str) -> dict:
        """Return an error response when prediction cannot be generated."""
        return {
            "season": year,
            "type": pred_type,
            "error": f"No prediction available for {pred_type} championship in {year}. The season may not have started or data is unavailable.",
            "races_completed": 0,
            "races_remaining": 0,
            "predicted_champion": None,
            "top_contenders": [],
            "form_analysis": {},
            "ai_reasoning": "",
        }
