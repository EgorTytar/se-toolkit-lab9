#!/usr/bin/env python3
"""CLI demo script for the F1 Race Results Summarizer.

Usage:
    python demo.py              — Summarize the latest race
    python demo.py latest       — Same as above
    python demo.py 2024 1       — Summarize round 1 of the 2024 season
    python demo.py 2024 1 "Who won?" — With a user question
"""

import asyncio
import json
import sys

from services.ergast_client import ErgastClient
from services.data_parser import format_race_data
from services.ai_assistant import AISummarizer


def _print_banner(text: str) -> None:
    width = len(text) + 4
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def _pretty_print(data: dict) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


async def demo_latest() -> None:
    """Fetch and summarize the latest race."""
    client = ErgastClient()
    summarizer = AISummarizer()

    _print_banner("F1 Assistant — Latest Race")

    race_data = await client.get_latest_race()
    race_text = format_race_data(race_data)

    print(f"\n📍 {race_data['race_name']}")
    print(f"🏁 {race_data['circuit']}")
    print(f"📅 {race_data['date']}")
    print()

    result = await summarizer.summarize(race_text)
    _pretty_print(result)


async def demo_year_round(year: int, round_num: int, user_query: str = "") -> None:
    """Fetch and summarize a specific race."""
    client = ErgastClient()
    summarizer = AISummarizer()

    label = f"Round {round_num}"
    if user_query:
        label += f' — Question: "{user_query}"'
    _print_banner(f"F1 Assistant — {year} / {label}")

    race_data = await client.get_race_by_year_round(year, round_num)
    race_text = format_race_data(race_data)

    print(f"\n📍 {race_data['race_name']}")
    print(f"🏁 {race_data['circuit']}")
    print(f"📅 {race_data['date']}")
    print()

    result = await summarizer.summarize(race_text, user_query)
    _pretty_print(result)


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] == "latest":
        asyncio.run(demo_latest())
    elif len(args) >= 2:
        try:
            year = int(args[0])
            round_num = int(args[1])
        except ValueError:
            print("Usage: python demo.py [latest] | <year> <round> [question]")
            sys.exit(1)
        query = args[2] if len(args) > 2 else ""
        asyncio.run(demo_year_round(year, round_num, query))
    else:
        print("Usage: python demo.py [latest] | <year> <round> [question]")
        sys.exit(1)


if __name__ == "__main__":
    main()
