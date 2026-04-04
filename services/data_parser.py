"""Formats structured race data into AI prompt-ready text."""


def format_race_data(race_data: dict) -> str:
    """Convert parsed race data into the input format expected by the AI prompt.

    Produces a clean, readable string like:

        Race: Bahrain Grand Prix
        Circuit: Bahrain International Circuit
        Date: 2024-03-02

        Results:
        1. Max Verstappen (Red Bull) - 25 points
        2. ...
    """
    lines = [
        f"Race: {race_data['race_name']}",
        f"Circuit: {race_data['circuit']}",
        f"Date: {race_data['date']}",
        "",
        "Results:",
    ]

    results = race_data.get("results", [])
    if not results:
        lines.append("No results available for this race.")
        return "\n".join(lines)

    for entry in results:
        pos = entry["position"]
        name = entry["driver_name"]
        constructor = entry["constructor"]
        points = entry["points"]
        status = entry.get("status", "")

        # Build the result line
        line = f"{pos}. {name} ({constructor}) - {points} points"

        # Append status if not a normal finish
        if status and status != "Finished":
            line += f" [{status}]"

        lines.append(line)

    return "\n".join(lines)
