"""Local smoke test for DayBreak's data-gathering logic.

Verifies the weather fetch, headline parsing, and the fallback brief WITHOUT
touching AWS (no Bedrock, no SNS). Run from the repo root:

    python scripts/local_test.py
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import lambda_function as agent  # noqa: E402


def main():
    now_local = datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=agent.UTC_OFFSET_HOURS))
    )

    print("=== 1. Weather (Open-Meteo) ===")
    weather = agent.get_weather()
    print(weather)
    assert weather["high_c"] is not None, "weather returned no high temperature"

    print("\n=== 2. Headlines (RSS) ===")
    headlines = agent.get_headlines()
    for h in headlines:
        print(f"- [{h['source']}] {h['title']}")
    assert headlines, "no headlines fetched"

    print("\n=== 3. Fallback brief (what ships if Bedrock ever fails) ===")
    print(agent.fallback_brief(weather, headlines, now_local))

    print("\nALL LOCAL CHECKS PASSED")


if __name__ == "__main__":
    main()
