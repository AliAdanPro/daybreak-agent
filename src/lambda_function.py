"""DayBreak — an always-on morning brief agent.

Runs unattended on a schedule (Amazon EventBridge Scheduler), gathers the
morning's raw material (local weather + news headlines), asks Amazon Bedrock
(Nova Micro) to write a short personal brief, and emails it via Amazon SNS.

No third-party API keys required: weather comes from Open-Meteo (free, no key)
and headlines from public RSS feeds. Uses only the Python standard library
plus boto3, which is preinstalled in the AWS Lambda runtime.
"""

import json
import logging
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- Configuration (all overridable via Lambda environment variables) ---
CITY_NAME = os.environ.get("CITY_NAME", "Islamabad")
CITY_LAT = os.environ.get("CITY_LAT", "33.6844")
CITY_LON = os.environ.get("CITY_LON", "73.0479")
# Pakistan Standard Time is UTC+5 all year (no daylight saving).
UTC_OFFSET_HOURS = float(os.environ.get("UTC_OFFSET_HOURS", "5"))
TZ_LABEL = os.environ.get("TZ_LABEL", "PKT")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.amazon.nova-micro-v1:0")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
HEADLINE_FEEDS = os.environ.get(
    "HEADLINE_FEEDS",
    "https://feeds.bbci.co.uk/news/world/rss.xml,"
    "https://feeds.arstechnica.com/arstechnica/index",
)
MAX_HEADLINES_PER_FEED = int(os.environ.get("MAX_HEADLINES_PER_FEED", "5"))

ATOM_NS = "{http://www.w3.org/2005/Atom}"

# WMO weather interpretation codes used by Open-Meteo.
WMO_WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "light snowfall",
    73: "moderate snowfall",
    75: "heavy snowfall",
    77: "snow grains",
    80: "light rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "light snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with light hail",
    99: "thunderstorm with heavy hail",
}


def http_get(url, timeout=10):
    request = urllib.request.Request(url, headers={"User-Agent": "DayBreakAgent/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def get_weather():
    """Fetch today's forecast for the configured city from Open-Meteo (no API key)."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={CITY_LAT}&longitude={CITY_LON}"
        "&current=temperature_2m"
        "&daily=temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max,weather_code,wind_speed_10m_max"
        "&timezone=auto&forecast_days=1"
    )
    data = json.loads(http_get(url))
    daily = data["daily"]
    code = daily["weather_code"][0]
    return {
        "city": CITY_NAME,
        "temperature_now_c": data.get("current", {}).get("temperature_2m"),
        "high_c": daily["temperature_2m_max"][0],
        "low_c": daily["temperature_2m_min"][0],
        "rain_chance_pct": daily["precipitation_probability_max"][0],
        "max_wind_kmh": daily["wind_speed_10m_max"][0],
        "conditions": WMO_WEATHER_CODES.get(code, f"weather code {code}"),
    }


def get_headlines():
    """Fetch top headlines from the configured public RSS/Atom feeds."""
    headlines = []
    for feed_url in [u.strip() for u in HEADLINE_FEEDS.split(",") if u.strip()]:
        try:
            root = ET.fromstring(http_get(feed_url))
            source = (
                root.findtext("channel/title")
                or root.findtext(f"{ATOM_NS}title")
                or urlparse(feed_url).netloc
            ).strip()
            items = root.findall(".//item") or root.findall(f".//{ATOM_NS}entry")
            for item in items[:MAX_HEADLINES_PER_FEED]:
                title = item.findtext("title") or item.findtext(f"{ATOM_NS}title")
                if title:
                    headlines.append({"source": source, "title": title.strip()})
        except Exception:
            logger.exception("Could not fetch feed %s", feed_url)
    return headlines


def write_brief_with_ai(weather, headlines, now_local):
    """Ask Amazon Bedrock (Nova Micro) to turn the raw material into a friendly brief."""
    material = {
        "date": now_local.strftime("%A, %d %B %Y"),
        "local_time": now_local.strftime("%H:%M") + f" {TZ_LABEL}",
        "weather": weather,
        "headlines": headlines,
    }
    prompt = (
        "You are DayBreak, a personal morning brief assistant. Using ONLY the JSON "
        "material below, write a warm, concise morning brief as PLAIN TEXT email "
        "body (no markdown symbols, no subject line). Structure:\n"
        "1. A one-line friendly greeting mentioning the day and date.\n"
        "2. WEATHER: 2-3 sentences on today's weather with practical advice "
        "(e.g. umbrella, heat, wind).\n"
        "3. HEADLINES: the news as short bullet lines starting with '- ', keeping "
        "each headline's meaning, grouped by source. Do not invent news.\n"
        "4. A single upbeat closing line to start the day well.\n"
        "Keep the whole brief under 250 words. If a section's data is missing, "
        "skip that section silently.\n\n"
        f"MATERIAL:\n{json.dumps(material, ensure_ascii=False)}"
    )
    client = boto3.client("bedrock-runtime")
    response = client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 700, "temperature": 0.4},
    )
    return response["output"]["message"]["content"][0]["text"].strip()


def fallback_brief(weather, headlines, now_local):
    """Assemble a plain brief from raw data so the agent still reports even if the AI call fails."""
    lines = [f"Good morning! Here is your brief for {now_local.strftime('%A, %d %B %Y')}."]
    if weather:
        lines.append(
            f"\nWEATHER in {weather['city']}: {weather['conditions']}, "
            f"high {weather['high_c']}C / low {weather['low_c']}C, "
            f"rain chance {weather['rain_chance_pct']}%, "
            f"wind up to {weather['max_wind_kmh']} km/h."
        )
    if headlines:
        lines.append("\nHEADLINES:")
        lines.extend(f"- [{h['source']}] {h['title']}" for h in headlines)
    lines.append("\nHave a great day!")
    return "\n".join(lines)


def send_email(subject, body):
    boto3.client("sns").publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=body)


def describe_trigger(event):
    """Honestly describe how this run was started.

    The EventBridge schedule's target input injects context attributes
    (schedule ARN + scheduled time), so a scheduler-fired run identifies
    itself; anything else is reported as a manual test.
    """
    if isinstance(event, dict) and event.get("source") == "aws.scheduler":
        schedule = event.get("schedule_arn", "").split("/")[-1] or "unknown"
        return (
            "ran unattended on AWS Lambda, fired by Amazon EventBridge Scheduler "
            f"(schedule '{schedule}', scheduled for {event.get('scheduled_time', '?')} UTC). "
            "Nobody pressed a button."
        )
    return "ran on AWS Lambda (manual test run)."


def lambda_handler(event, context):
    if not SNS_TOPIC_ARN:
        raise RuntimeError("SNS_TOPIC_ARN environment variable is not set")

    now_local = datetime.now(timezone.utc).astimezone(
        timezone(timedelta(hours=UTC_OFFSET_HOURS))
    )
    problems = []

    weather = None
    try:
        weather = get_weather()
    except Exception as exc:
        problems.append(f"weather: {exc}")
        logger.exception("Weather fetch failed")

    headlines = get_headlines()
    if not headlines:
        problems.append("headlines: no feeds could be fetched")

    ai_used = True
    try:
        body = write_brief_with_ai(weather, headlines, now_local)
    except Exception as exc:
        ai_used = False
        problems.append(f"bedrock: {exc}")
        logger.exception("Bedrock call failed, using fallback brief")
        body = fallback_brief(weather, headlines, now_local)

    body += (
        f"\n\n--\nDayBreak, {now_local.strftime('%H:%M')} {TZ_LABEL}: "
        + describe_trigger(event)
    )
    # SNS subjects must be plain ASCII, max 100 chars.
    subject = f"Your Morning Brief - {now_local.strftime('%a, %d %b %Y')}"
    send_email(subject, body)

    result = {
        "ok": True,
        "ai_used": ai_used,
        "weather_ok": weather is not None,
        "headline_count": len(headlines),
        "problems": problems,
    }
    logger.info(json.dumps(result))
    return result

if __name__ == "__main__":
    # Allow running directly via Docker / CLI for demonstration
    lambda_handler({"source": "manual-cli"}, None)
