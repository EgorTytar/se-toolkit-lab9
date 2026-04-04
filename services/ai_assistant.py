"""AI-powered race summarizer using an OpenAI-compatible LLM."""

import json
import logging
import os

from openai import AsyncOpenAI

from config import AI_MAX_TOKENS, AI_MODEL, AI_TEMPERATURE

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI assistant designed to power a Formula 1 assistant application.

Your responsibilities include:

1. Summarize race results in a clear and engaging way
2. Highlight key information: winner, podium finishers, notable performances
3. Explain race outcomes or events in simple terms
4. Answer user questions based ONLY on the provided data

STYLE GUIDELINES:
- Use a professional Formula 1 commentator tone
- Keep explanations beginner-friendly
- Avoid unnecessary technical jargon
- Be concise (3-5 sentences for summaries)
- Be engaging and natural (like a sports broadcast)
- DO NOT hallucinate or invent data

RULES:
1. If results are provided: Generate summary + highlights + insights
2. If no results (future race): Generate a preview of the race
3. If user asks a question: Answer clearly using ONLY given data
4. If data is limited: Still produce a useful and natural explanation
5. Never fabricate missing drivers, results, or events

ALWAYS respond in valid JSON format with these exact keys:
{
  "summary": "Short race summary (3-5 sentences)",
  "highlights": "Winner and podium finishers",
  "insights": "Optional key observations",
  "answer": "Optional direct answer to user question"
}
"""


class AISummarizer:
    """Generates race summaries using an OpenAI-compatible LLM."""

    def __init__(self) -> None:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = AI_MODEL
        self.temperature = AI_TEMPERATURE
        self.max_tokens = AI_MAX_TOKENS
        self._available = bool(api_key)

    @property
    def is_available(self) -> bool:
        """Whether the AI service can be used (API key is set)."""
        return self._available

    async def summarize(self, race_text: str, user_query: str = "") -> dict:
        """Generate a JSON race summary from formatted race data.

        Args:
            race_text: Formatted race data from data_parser.
            user_query: Optional user question to answer.

        Returns:
            dict with keys: summary, highlights, insights, answer
        """
        if not self._available:
            return self._fallback_summary(race_text)

        user_prompt = race_text
        if user_query:
            user_prompt += f"\n\nUser question: {user_query}"

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content:
                return json.loads(content)
        except Exception as e:
            logger.warning("AI summarization failed, using fallback: %s", e)

        return self._fallback_summary(race_text)

    @staticmethod
    def _fallback_summary(race_text: str) -> dict:
        """Generate a basic summary without AI when the API is unavailable."""
        # Extract key facts from the raw text for a minimal useful response
        lines = race_text.strip().split("\n")
        race_name = ""
        podium = []

        for line in lines:
            if line.startswith("Race:"):
                race_name = line.split(":", 1)[1].strip()
            elif line.startswith(("1. ", "2. ", "3. ")):
                podium.append(line)

        podium_text = "; ".join(podium[:3]) if podium else "No podium data available"
        winner = podium[0] if podium else "Unknown"

        return {
            "summary": f"Race results for the {race_name} are in. {winner} took the top spot.",
            "highlights": podium_text,
            "insights": "AI summarization unavailable — connect OPENAI_API_KEY for full summaries.",
            "answer": "",
        }
