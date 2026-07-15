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

NEW: a "reflection" section is appended each run. It looks at TODAY's
Panchang (the day this script runs), derives a very simple, rule-of-thumb
"astro outlook" from whether Bhadra Kaal / Rahu Kalam / Gulika Kalam /
Amavasya-Purnima overlap Indian market trading hours (09:15-15:30 IST),
then compares that outlook against what actually happened on the NSE/BSE
today (Nifty 50 + Sensex % move, plus the biggest gainers/losers among a
basket of large-cap Nifty stocks). This is an informal, non-scientific
comparison intended for personal curiosity only -- NOT financial advice,
and NOT a validated predictive model. A single day tells you nothing
statistically; treat it as a fun log, not a signal.
"""

import json
import sys
from datetime import date, datetime, timedelta
from datetime import time as dtime
from zoneinfo import ZoneInfo

import requests

try:
    import yfinance as yf
except ImportError:
    yf = None

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

# ---------------------------------------------------------------------------
# Market reflection configuration
# ---------------------------------------------------------------------------

IST = ZoneInfo("Asia/Kolkata")
AMS = ZoneInfo("Europe/Amsterdam")

MARKET_OPEN_IST = dtime(9, 15)
MARKET_CLOSE_IST = dtime(15, 30)

INDEX_TICKERS = {
    "^NSEI": "Nifty 50",
    "^BSESN": "Sensex",
}

# A basket of large-cap NSE stocks used to surface "top movers" for the day.
# Feel free to trim/extend this list.
TICKER_NAMES = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "TCS",
    "HDFCBANK.NS": "HDFC Bank",
    "ICICIBANK.NS": "ICICI Bank",
    "INFY.NS": "Infosys",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "ITC.NS": "ITC",
    "SBIN.NS": "State Bank of India",
    "BHARTIARTL.NS": "Bharti Airtel",
    "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "LT.NS": "Larsen & Toubro",
    "AXISBANK.NS": "Axis Bank",
    "BAJFINANCE.NS": "Bajaj Finance",
    "ASIANPAINT.NS": "Asian Paints",
    "MARUTI.NS": "Maruti Suzuki",
    "SUNPHARMA.NS": "Sun Pharma",
    "TITAN.NS": "Titan",
    "ULTRACEMCO.NS": "UltraTech Cement",
    "WIPRO.NS": "Wipro",
    "NESTLEIND.NS": "Nestle India",
}


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


# ---------------------------------------------------------------------------
# Market reflection helpers
# ---------------------------------------------------------------------------

def market_window_in_amsterdam(d: date):
    """Indian market trading hours (09:15-15:30 IST) for date `d`,
    converted to Europe/Amsterdam, to compare against Panchang windows
    which are already expressed in Amsterdam local time."""
    start_ist = datetime.combine(d, MARKET_OPEN_IST, tzinfo=IST)
    end_ist = datetime.combine(d, MARKET_CLOSE_IST, tzinfo=IST)
    return start_ist.astimezone(AMS), end_ist.astimezone(AMS)


def parse_aware(iso_str: str) -> datetime:
    """Parse an ISO datetime string; assume Amsterdam tz if no offset given."""
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=AMS)
    return dt


def ranges_overlap(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


def collect_inauspicious_windows(data: dict, target_date: date) -> list:
    """Pull Bhadra Kaal / Rahu Kalam / Gulika Kalam windows out of today's
    Panchang, clip each one to Indian market hours, and return only the
    windows that actually fall inside trading hours (fully or partially).
    Each entry carries both its Amsterdam-local and IST clock times so the
    intraday index check below can look up the right candles."""
    inauspicious = data.get("inauspicious_timings", {})
    m_start, m_end = market_window_in_amsterdam(target_date)

    raw_windows = []
    for b in inauspicious.get("bhadra", []):
        if b.get("start") and b.get("end"):
            raw_windows.append(("Bhadra Kaal", b["start"], b["end"]))
    rahu = inauspicious.get("rahu_kalam") or {}
    if rahu.get("start") and rahu.get("end"):
        raw_windows.append(("Rahu Kalam", rahu["start"], rahu["end"]))
    gulika = inauspicious.get("gulika_kalam") or {}
    if gulika.get("start") and gulika.get("end"):
        raw_windows.append(("Gulika Kalam", gulika["start"], gulika["end"]))

    windows = []
    for label, start_iso, end_iso in raw_windows:
        try:
            w_start, w_end = parse_aware(start_iso), parse_aware(end_iso)
        except ValueError:
            continue
        if not ranges_overlap(w_start, w_end, m_start, m_end):
            continue  # this window never touches trading hours at all
        clipped_start = max(w_start, m_start)
        clipped_end = min(w_end, m_end)
        partial = (clipped_start != w_start) or (clipped_end != w_end)
        windows.append({
            "label": label,
            "full_start_ams": w_start,
            "full_end_ams": w_end,
            "clipped_start_ist": clipped_start.astimezone(IST),
            "clipped_end_ist": clipped_end.astimezone(IST),
            "partial_overlap": partial,
        })

    tithi_flag = None
    tithi_entries = data.get("panchang", {}).get("tithi_sequence") or [data.get("panchang", {}).get("tithi", {})]
    for t in tithi_entries:
        name = t.get("name", "")
        if is_amavasya(name):
            tithi_flag = "Amavasya (traditionally a caution tithi)"
        elif is_purnima(name):
            tithi_flag = "Purnima (traditionally a favorable/high-energy tithi)"

    return windows, tithi_flag


def fetch_intraday_nifty(target_date: date):
    """5-minute Nifty 50 candles for `target_date`, indexed in IST.
    Returns None if unavailable (e.g. weekend/holiday, or too old for
    Yahoo's intraday retention window)."""
    if yf is None:
        return None
    try:
        df = yf.Ticker("^NSEI").history(period="5d", interval="5m")
        if df.empty:
            return None
        df.index = df.index.tz_convert(IST)
        df = df[df.index.date == target_date]
        return df if not df.empty else None
    except Exception as exc:
        print(f"Error fetching intraday Nifty data: {exc}")
        return None


def price_at_or_before(df_ist, ts_ist):
    subset = df_ist[df_ist.index <= ts_ist]
    if subset.empty:
        # nothing at/before this timestamp (e.g. window starts right at
        # market open) -- fall back to the first available candle instead
        subset = df_ist[df_ist.index >= ts_ist]
        if subset.empty:
            return None
        return float(subset["Close"].iloc[0])
    return float(subset["Close"].iloc[-1])


def evaluate_windows(windows: list, df_ist) -> list:
    """For each window, measure the ACTUAL Nifty 50 % move during exactly
    that clipped time slot (not the whole day). This is the direct,
    time-specific check -- it does not rely on end-of-day close alone."""
    results = []
    for w in windows:
        entry = dict(w)
        if df_ist is None:
            entry["pct_move"] = None
            entry["note"] = "intraday data unavailable"
        else:
            p_start = price_at_or_before(df_ist, w["clipped_start_ist"])
            p_end = price_at_or_before(df_ist, w["clipped_end_ist"])
            if p_start is None or p_end is None or p_start == 0:
                entry["pct_move"] = None
                entry["note"] = "no candles inside this window"
            else:
                pct = round((p_end - p_start) / p_start * 100, 3)
                entry["pct_move"] = pct
                if pct <= -0.15:
                    entry["note"] = "Nifty dipped during this window"
                elif pct >= 0.15:
                    entry["note"] = "Nifty rose during this window"
                else:
                    entry["note"] = "essentially flat during this window"
        results.append(entry)
    return results


def fetch_index_performance(ticker: str, name: str) -> dict:
    if yf is None:
        return {"name": name, "error": "yfinance not installed"}
    try:
        df = yf.Ticker(ticker).history(period="5d")
        closes = df["Close"].dropna()
        if len(closes) < 2:
            return {"name": name, "error": "insufficient data (market may be closed/holiday)"}
        prev_close = float(closes.iloc[-2])
        last_close = float(closes.iloc[-1])
        pct_change = (last_close - prev_close) / prev_close * 100
        return {
            "name": name,
            "prev_close": round(prev_close, 2),
            "last_close": round(last_close, 2),
            "pct_change": round(pct_change, 2),
            "day_high": round(float(df["High"].iloc[-1]), 2),
            "day_low": round(float(df["Low"].iloc[-1]), 2),
        }
    except Exception as exc:
        return {"name": name, "error": str(exc)}


def fetch_top_movers(tickers: list) -> list:
    if yf is None:
        return []
    try:
        raw = yf.download(
            tickers=tickers, period="5d", interval="1d",
            group_by="ticker", progress=False, threads=True,
        )
    except Exception as exc:
        print(f"Error batch-downloading stock data: {exc}")
        return []

    movers = []
    for t in tickers:
        try:
            df = raw[t] if len(tickers) > 1 else raw
            closes = df["Close"].dropna()
            if len(closes) < 2:
                continue
            prev_close = float(closes.iloc[-2])
            last_close = float(closes.iloc[-1])
            pct_change = (last_close - prev_close) / prev_close * 100
            movers.append({
                "ticker": t,
                "name": TICKER_NAMES.get(t, t),
                "prev_close": round(prev_close, 2),
                "last_close": round(last_close, 2),
                "pct_change": round(pct_change, 2),
            })
        except Exception as exc:
            print(f"Skipping {t}: {exc}")
            continue
    return movers


def build_reflection(today: date) -> dict:
    """Returns {"text": <str for notification>, "data": <dict for JSON>}."""
    lines = ["===== Today's Reflection: Panchang vs Indian Markets =====",
             f"Date: {today.strftime('%d %b %Y')}", ""]
    data_out = {"date": today.isoformat()}

    # --- Actual index performance (whole-day context) ---
    index_results = {t: fetch_index_performance(t, n) for t, n in INDEX_TICKERS.items()}
    for idx in index_results.values():
        if "error" in idx:
            lines.append(f"{idx['name']}: data unavailable ({idx['error']})")
        else:
            sign = "+" if idx["pct_change"] >= 0 else ""
            lines.append(
                f"{idx['name']}: {idx['last_close']} ({sign}{idx['pct_change']}%), "
                f"day range {idx['day_low']}-{idx['day_high']}"
            )
    lines.append("")
    data_out["indices"] = index_results

    # --- Window-by-window check: what did Nifty ACTUALLY do during each
    # specific inauspicious window today, not just the whole day? ---
    windows, tithi_flag = [], None
    try:
        today_panchang = fetch_panchang(today)
        windows, tithi_flag = collect_inauspicious_windows(today_panchang, today)
    except requests.RequestException as exc:
        lines.append(f"Could not fetch today's Panchang: {exc}")

    intraday_df = fetch_intraday_nifty(today)
    evaluated = evaluate_windows(windows, intraday_df) if windows else []

    lines.append("Window-by-window check (Nifty 50, measured only during each specific slot):")
    if tithi_flag:
        lines.append(f"  Tithi today: {tithi_flag}")
    if not windows:
        lines.append("  - No Bhadra Kaal / Rahu Kalam / Gulika Kalam windows overlapped trading hours today")
    elif intraday_df is None:
        lines.append("  - Intraday Nifty data unavailable (market holiday, weekend, or data retention limit)")
    else:
        for w in evaluated:
            span = f"{w['clipped_start_ist']:%H:%M} - {w['clipped_end_ist']:%H:%M} IST"
            partial = " (partial overlap with trading hours)" if w["partial_overlap"] else ""
            if w["pct_move"] is None:
                lines.append(f"  - {w['label']} [{span}]{partial}: {w['note']}")
            else:
                sign = "+" if w["pct_move"] >= 0 else ""
                lines.append(f"  - {w['label']} [{span}]{partial}: {sign}{w['pct_move']}% -- {w['note']}")

    lines.append(
        "  (Informal, non-scientific comparison for personal curiosity only -- "
        "not financial advice, and one day proves nothing statistically.)"
    )
    data_out["tithi_flag"] = tithi_flag
    data_out["windows"] = [
        {
            "label": w["label"],
            "window_start_ist": w["clipped_start_ist"].isoformat(),
            "window_end_ist": w["clipped_end_ist"].isoformat(),
            "partial_overlap": w["partial_overlap"],
            "pct_move": w["pct_move"],
            "note": w["note"],
        }
        for w in evaluated
    ]
    lines.append("")

    # --- Top movers among major Nifty large-caps ---
    movers = fetch_top_movers(list(TICKER_NAMES.keys()))
    if movers:
        gainers = sorted(movers, key=lambda m: m["pct_change"], reverse=True)[:3]
        losers = sorted(movers, key=lambda m: m["pct_change"])[:3]

        lines.append("Top gainers:")
        for g in gainers:
            lines.append(f"  {g['name']}: {g['last_close']} (+{g['pct_change']}%)")
        lines.append("Top losers:")
        for l in losers:
            lines.append(f"  {l['name']}: {l['last_close']} ({l['pct_change']}%)")

        data_out["top_gainers"] = gainers
        data_out["top_losers"] = losers
    else:
        lines.append("Top movers data unavailable")

    return {"text": "\n".join(lines), "data": data_out}


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

    # New: reflection on today's astro outlook vs today's actual market move.
    reflection = build_reflection(date.today())
    all_data["reflection"] = reflection["data"]

    # Save the raw combined JSON as an artifact for the workflow to upload.
    with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved raw data as {OUTPUT_JSON_FILE}")

    full_message = "\n\n".join(summaries) + "\n\n" + reflection["text"]
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
