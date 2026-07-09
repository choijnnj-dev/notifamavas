"""
Financial Panchang Forecaster
------------------------------
Pulls Panchang data for the next two days (Mumbai coordinates, Amsterdam
timezone) from vedicpanchanga.com, extracts every timing that matters for a
financial/trading-oriented read (tithi, paksha, nakshatra, yoga, karana,
Bhadra Kaal, Rahu Kalam, Yamaganda, Gulika Kalam, Dur Muhurtam, Amavasya /
Purnima flags, plus the standard auspicious windows), and pushes a fully
timestamped summary to an ntfy.sh topic.

Every single timestamp in the output notification is explicit ISO-8601,
already expressed in Europe/Amsterdam local time (the API returns it that
way when you pass timezone=Europe/Amsterdam).
"""

import json
import sys
from datetime import date, timedelta

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


def window_line(label: str, window: dict) -> str | None:
    """Return a formatted line for a single start/end window, or None if it
    doesn't occur / wasn't returned for this day (so callers can omit it
    entirely instead of printing a placeholder)."""
    if not window or not window.get("start"):
        return None
    return f"  {label}: {window.get('start', 'n/a')}  ->  {window.get('end', 'n/a')}"


def window_list_lines(label: str, windows: list) -> list:
    """Return formatted lines for a list of windows (e.g. Bhadra, Varjyam).
    Returns an empty list if there are no occurrences that day, so the
    section can be skipped entirely rather than showing 'none today'."""
    if not windows:
        return []
    lines = [f"  {label}:"]
    for w in windows:
        extra = ""
        if "nakshatra" in w:
            extra = f" [{w['nakshatra']}]"
        elif "tithi" in w:
            extra = f" [{w['tithi']}]"
        elif "karana" in w:
            extra = f" [{w['karana']}]"
        lines.append(f"    - {w.get('start', 'n/a')}  ->  {w.get('end', 'n/a')}{extra}")
    return lines


def build_day_summary(data: dict) -> str:
    d = data.get("date", "unknown")
    loc = data.get("location", {})
    sun_moon = data.get("sun_moon", {})
    vara = data.get("vara", {})
    panchang = data.get("panchang", {})
    tithi = panchang.get("tithi", {})
    nakshatra = panchang.get("nakshatra", {})
    yoga = panchang.get("yoga", {})
    karana = panchang.get("karana", {})
    auspicious = data.get("auspicious_timings", {})
    inauspicious = data.get("inauspicious_timings", {})

    tithi_name = tithi.get("name", "")
    amavasya_flag = is_amavasya(tithi_name)
    purnima_flag = is_purnima(tithi_name)

    lines = []
    lines.append("=" * 60)
    lines.append(f"PANCHANG FORECAST — {d}")
    lines.append(
        f"Location: lat {loc.get('latitude')}, lon {loc.get('longitude')} "
        f"(Mumbai) | Timezone: {loc.get('timezone')}"
    )
    lines.append(f"Vara (weekday): {vara.get('sanskrit', 'n/a')} / {vara.get('english', 'n/a')}")
    lines.append("")

    lines.append("SUN & MOON")
    lines.append(f"  Sunrise:  {sun_moon.get('sunrise', 'n/a')}")
    lines.append(f"  Sunset:   {sun_moon.get('sunset', 'n/a')}")
    lines.append(f"  Moonrise: {sun_moon.get('moonrise', 'n/a')}")
    lines.append(f"  Moonset:  {sun_moon.get('moonset', 'n/a')}")
    lines.append(f"  Madhyahna (midday): {sun_moon.get('madhyahna', 'n/a')}")
    lines.append("")

    lines.append("TITHI / PAKSHA")
    lines.append(f"  Tithi: {tithi_name}  (Paksha: {tithi.get('paksha', 'n/a')})")
    lines.append(f"  Starts: {tithi.get('starts_at', 'n/a')}")
    lines.append(f"  Ends:   {tithi.get('ends_at', 'n/a')}")
    if amavasya_flag:
        lines.append("  *** AMAVASYA (New Moon) IS ACTIVE — key financial/no-trade watch day ***")
    if purnima_flag:
        lines.append("  *** PURNIMA (Full Moon) IS ACTIVE — key financial/no-trade watch day ***")
    lines.append("")

    lines.append("NAKSHATRA")
    lines.append(f"  {nakshatra.get('name', 'n/a')}")
    lines.append(f"  Starts: {nakshatra.get('starts_at', 'n/a')}")
    lines.append(f"  Ends:   {nakshatra.get('ends_at', 'n/a')}")
    lines.append("")

    lines.append("YOGA")
    lines.append(f"  {yoga.get('name', 'n/a')}")
    lines.append(f"  Starts: {yoga.get('starts_at', 'n/a')}")
    lines.append(f"  Ends:   {yoga.get('ends_at', 'n/a')}")
    lines.append("")

    lines.append("KARANA")
    lines.append(f"  {karana.get('name', 'n/a')}  (is_bhadra: {karana.get('is_bhadra', False)})")
    lines.append(f"  Starts: {karana.get('starts_at', 'n/a')}")
    lines.append(f"  Ends:   {karana.get('ends_at', 'n/a')}")
    lines.append("")

    lines.append("BHADRA KAAL")
    bhadra_periods = inauspicious.get("bhadra", [])
    bhadra_lines = window_list_lines("Bhadra windows", bhadra_periods)
    if bhadra_lines:
        lines.extend(bhadra_lines)
    else:
        lines.append("  No Bhadra Kaal today.")
    lines.append("")

    inaus_lines = []
    for label, key in [
        ("Rahu Kalam", "rahu_kalam"),
        ("Yamaganda", "yamaganda"),
        ("Gulika Kalam", "gulika_kalam"),
    ]:
        line = window_line(label, inauspicious.get(key))
        if line:
            inaus_lines.append(line)
    inaus_lines.extend(window_list_lines("Dur Muhurtam", inauspicious.get("dur_muhurtam", [])))
    inaus_lines.extend(window_list_lines("Varjyam", inauspicious.get("varjyam", [])))
    if inaus_lines:
        lines.append("INAUSPICIOUS KAALS")
        lines.extend(inaus_lines)
        lines.append("")

    ausp_lines = []
    for label, key in [
        ("Brahma Muhurta", "brahma_muhurta"),
        ("Abhijit Muhurta", "abhijit"),
        ("Vijay Muhurta", "vijay_muhurta"),
        ("Godhuli Muhurta", "godhuli_muhurta"),
        ("Nishita Muhurta", "nishita_muhurta"),
    ]:
        line = window_line(label, auspicious.get(key))
        if line:
            ausp_lines.append(line)
    ausp_lines.extend(window_list_lines("Amrit Kalam", auspicious.get("amrit_kalam", [])))
    ausp_lines.extend(
        window_list_lines("Sarvartha Siddhi Yoga", auspicious.get("sarvartha_siddhi_yoga", []))
    )
    ausp_lines.extend(
        window_list_lines("Amrita Siddhi Yoga", auspicious.get("amrita_siddhi_yoga", []))
    )
    if ausp_lines:
        lines.append("AUSPICIOUS TIMINGS")
        lines.extend(ausp_lines)
    lines.append("=" * 60)

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
            summaries.append(
                f"PANCHANG FORECAST — {target_date.isoformat()}\n  ERROR: could not fetch data ({exc})"
            )
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

    first_date = (date.today() + timedelta(days=DAY_OFFSETS[0])).isoformat()
    last_date = (date.today() + timedelta(days=DAY_OFFSETS[-1])).isoformat()
    title = f"Panchang Forecast: {first_date} to {last_date}"

    send_ntfy(topic, title, full_message)
    print("\nDone.")


if __name__ == "__main__":
    main()
