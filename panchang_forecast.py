"""
Financial Panchang Forecaster
------------------------------
Pulls Panchang data for the next two days (Mumbai coordinates, Amsterdam
timezone) from vedicpanchanga.com, and pushes a short, one-line-per-item
notification to ntfy.sh covering: Tithi (with Amavasya/Purnima flagged),
Nakshatra, Bhadra Kaal, Rahu Kalam and Gulika Kalam.

All times shown are already in Amsterdam local time (the API returns them
that way when timezone=Europe/Amsterdam is passed). Only the clock time is
shown (e.g. "18:02"); a date is only added onto the end time when a window
crosses over into the next calendar day (e.g. "18:02 -> 10 Jul 04:46").
"""

import json
import sys
from datetime import date, datetime, timedelta

import requests

URL = "https://vedicpanchanga.com/api/get-panchang"

LATITUDE = 19.0760
LONGITUDE = 72.8777
TIMEZONE = "Europe/Amsterdam"

# How many days ahead to forecast, and how far out to start.
# DAY_OFFSETS = (1, 2) -> "tomorrow" and "the day after tomorrow"
# Change to (0, 1) if you want "today" and "tomorrow" instead.
DAY_OFFSETS = (1, 2)

NTFY_BASE = "https://ntfy.sh"
NTFY_TOPIC_FILE = "ntfy_topic.txt"

OUTPUT_JSON_FILE = "panchang_output.json"


def load_ntfy_topic() -> str:
    try:
        with open(NTFY_TOPIC_FILE, "r", encoding="utf-8") as f:
            topic = f.read().strip()
    except FileNotFoundError:
        print(f"ERROR: {NTFY_TOPIC_FILE} not found. Create it with your ntfy.sh topic name.")
        sys.exit(1)

    if not topic or topic.lower().startswith("your-"):
        print("ERROR: ntfy_topic.txt is empty or still a placeholder. Put your real topic in it.")
        sys.exit(1)

    return topic


def fetch_panchang(target_date: date) -> dict:
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "date": target_date.isoformat(),
        "timezone": TIMEZONE,
    }
    print(f"Requesting Panchang for {target_date.isoformat()} ...")
    print(params)
    response = requests.get(URL, params=params, timeout=60)
    print("Status Code:", response.status_code)
    response.raise_for_status()
    return response.json()


def is_amavasya(tithi_name: str) -> bool:
    return "amavasya" in tithi_name.lower()


def is_purnima(tithi_name: str) -> bool:
    return "purnima" in tithi_name.lower()


def fmt_range(start_iso: str, end_iso: str):
    """Format a start/end pair as 'HH:MM -> HH:MM', only adding a date onto
    the end time if it falls on a different calendar day than the start.
    Returns None if either timestamp is missing."""
    if not start_iso or not end_iso:
        return None
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    start_str = start.strftime("%H:%M")
    if start.date() == end.date():
        end_str = end.strftime("%H:%M")
    else:
        end_str = end.strftime("%d %b %H:%M")
    return f"{start_str} -> {end_str}"


def build_day_summary(data: dict) -> str:
    raw_date = data.get("date", "unknown")
    try:
        header_date = datetime.fromisoformat(raw_date).strftime("%d %b %Y")
    except ValueError:
        header_date = raw_date

    panchang = data.get("panchang", {})
    inauspicious = data.get("inauspicious_timings", {})

    lines = [f"— {header_date} —"]

    # Tithi (covers Amavasya / Purnima flagging directly on the line)
    tithi_entries = panchang.get("tithi_sequence") or [panchang.get("tithi", {})]
    for t in tithi_entries:
        name = t.get("name", "")
        rng = fmt_range(t.get("starts_at"), t.get("ends_at"))
        if not name or not rng:
            continue
        marker = ""
        if is_amavasya(name):
            marker = "\U0001F311 "
        elif is_purnima(name):
            marker = "\U0001F315 "
        lines.append(f"{marker}Tithi: {name} {rng}")

    # Nakshatra
    nakshatra_entries = panchang.get("nakshatra_sequence") or [panchang.get("nakshatra", {})]
    for n in nakshatra_entries:
        name = n.get("name", "")
        rng = fmt_range(n.get("starts_at"), n.get("ends_at"))
        if not name or not rng:
            continue
        lines.append(f"Nakshatra: {name} {rng}")

    # Bhadra Kaal (can be zero, one, or more windows in a day)
    for b in inauspicious.get("bhadra", []):
        rng = fmt_range(b.get("start"), b.get("end"))
        if rng:
            lines.append(f"Bhadra Kaal: {rng}")

    # Rahu Kalam
    rahu = inauspicious.get("rahu_kalam") or {}
    rng = fmt_range(rahu.get("start"), rahu.get("end"))
    if rng:
        lines.append(f"Rahu Kalam: {rng}")

    # Gulika Kalam
    gulika = inauspicious.get("gulika_kalam") or {}
    rng = fmt_range(gulika.get("start"), gulika.get("end"))
    if rng:
        lines.append(f"Gulika Kalam: {rng}")

    return "\n".join(lines)


def send_ntfy(topic: str, title: str, message: str) -> None:
    print(f"Sending ntfy notification to topic '{topic}' ...")
    resp = requests.post(
        f"{NTFY_BASE}/{topic}",
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": "default",
            "Tags": "crystal_ball,moneybag",
        },
        timeout=30,
    )
    print("ntfy Status Code:", resp.status_code)
    resp.raise_for_status()


def main():
    topic = load_ntfy_topic()

    all_data = {}
    summaries = []

    for offset in DAY_OFFSETS:
        target_date = date.today() + timedelta(days=offset)
        try:
            data = fetch_panchang(target_date)
        except requests.RequestException as exc:
            print(f"ERROR fetching Panchang for {target_date.isoformat()}: {exc}")
            summaries.append(f"— {target_date.strftime('%d %b %Y')} —\nError fetching data")
            continue

        all_data[target_date.isoformat()] = data
        summaries.append(build_day_summary(data))

    # Save the raw combined JSON as an artifact for the workflow to upload.
    with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved raw data as {OUTPUT_JSON_FILE}")

    full_message = "\n\n".join(summaries)
    print("\n========== NOTIFICATION BODY ==========\n")
    print(full_message)
    print(f"\nMessage length: {len(full_message.encode('utf-8'))} bytes")

    first_date = (date.today() + timedelta(days=DAY_OFFSETS[0])).strftime("%d %b")
    last_date = (date.today() + timedelta(days=DAY_OFFSETS[-1])).strftime("%d %b")
    title = f"Panchang Forecast: {first_date} - {last_date}"

    send_ntfy(topic, title, full_message)
    print("\nDone.")


if __name__ == "__main__":
    main()
