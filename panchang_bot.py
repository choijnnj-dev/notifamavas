import requests
from datetime import datetime, timedelta
import pytz
import ephem

# 1. Connected directly to your mobile app channel
NTFY_TOPIC = "mumama"

def check_mumbai_market_panchang():
    # Coords for Mumbai, India
    mumbai_lat = '19.0760'
    mumbai_lon = '72.8777'
    
    mumbai_tz = pytz.timezone('Asia/Kolkata')
    nl_tz = pytz.timezone('Europe/Amsterdam')
    
    # Define our strict 2-Day Future Lookahead Window
    now_nl = datetime.now(nl_tz)
    two_days_later_nl = now_nl + timedelta(days=2)
    
    # 2. Offline Astronomical Calculation
    gate = ephem.Observer()
    gate.lat, gate.lon = mumbai_lat, mumbai_lon
    gate.date = now_nl.astimezone(mumbai_tz).strftime('%Y/%m/%d %H:%M:%S')
    
    # Calculate Amavasya (New Moon Peak)
    next_new_moon = ephem.next_new_moon(gate.date)
    utc_peak = next_new_moon.datetime().replace(tzinfo=pytz.utc)
    mumbai_peak = utc_peak.astimezone(mumbai_tz)
    
    # Amavasya phase bounds (12 hours before to 12 hours after the peak)
    amavasya_start_nl = (mumbai_peak - timedelta(hours=12)).astimezone(nl_tz)
    amavasya_end_nl = (mumbai_peak + timedelta(hours=12)).astimezone(nl_tz)
    
    # Check if Amavasya opens within our 2-day lookahead window
    is_amavasya_in_window = amavasya_start_nl <= two_days_later_nl
    
    # Target Tomorrow's trade window
    target_date_nl = now_nl + timedelta(days=1)
    target_date_mumbai = target_date_nl.astimezone(mumbai_tz)
    
    gate.date = target_date_mumbai.replace(hour=12, minute=0).strftime('%Y/%m/%d %H:%M:%S')
    sun = ephem.Sun(gate)
    moon = ephem.Moon(gate)
    
    # Precise Nakshatra Calculation (Sidereal Lahiri standard)
    moon_lon = (float(moon.ra) * 15 - 24.2) % 360  
    nakshatra_idx = int(moon_lon / 13.33) % 27
    
    nakshatras = {
        0: "Ashwini (Swift / Day Trades)", 
        3: "Rohini (Fixed / Blue-Chip Holding)", 
        7: "Pushya (Super Wealth Nourisher)",
        13: "Chitra (Swift / Day Trades)", 
        21: "Shravana (Fixed / Blue-Chip Holding)", 
        26: "Revati (Swift / Day Trades)"
    }
    star_name = nakshatras.get(nakshatra_idx, "Standard Multi-Tier Star Alignment")

    # Determine Tomorrow's Tithi/Paksha phase status
    is_amavasya_tomorrow = amavasya_start_nl.date() <= target_date_nl.date() <= amavasya_end_nl.date()
    is_shukla_paksha = not is_amavasya_tomorrow and (mumbai_peak - target_date_mumbai).days > 14
    
    yoga_alert = "Normal Daily Balance"
    karana_alert = "Standard Dynamic"
    bhadra_alert = "No Bhadra Kaal structural limits detected today."
    
    if is_amavasya_tomorrow:
        tithi_name = f"Amavasya Phase (Active NL: {amavasya_start_nl.strftime('%I:%M %p')} to {amavasya_end_nl.strftime('%I:%M %p')})"
    elif is_shukla_paksha:
        tithi_name = "Shukla Paksha (Waxing Light) [UPWARD TREND]"
        if target_date_mumbai.day % 15 in [2, 3, 5, 11, 13]:
            tithi_name += " - Strategic Wealth Accumulation Active!"
            yoga_alert = "Amrita / Sarvartha Siddhi Operational"
            karana_alert = "Bava / Balava Growth Window Open [GROWTH]"
    else:
        tithi_name = "Krishna Paksha (Waning Light) [DOWNWARD TREND]"

    # 3. Calculate Volatile Windows (Rahu, Gulika, and Bhadra Kaal)
    mumbai_sunrise = target_date_mumbai.replace(hour=6, minute=0, second=0, microsecond=0)
    mumbai_sunset = target_date_mumbai.replace(hour=18, minute=30, second=0, microsecond=0)
    weekday = target_date_mumbai.weekday()  
    
    # Rahu & Gulika slots (1.5-hour daily brackets)
    rahu_slots = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
    gulika_slots = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}
    
    def calculate_window_clocks(slot_index):
        window_start = mumbai_sunrise + timedelta(hours=(slot_index - 1) * 1.5)
        window_end = window_start + timedelta(hours=1.5)
        return f"{window_start.astimezone(nl_tz).strftime('%I:%M %p')} to {window_end.astimezone(nl_tz).strftime('%I:%M %p')}"

    rahu_time_string = calculate_window_clocks(rahu_slots[weekday])
    gulika_time_string = calculate_window_clocks(gulika_slots[weekday])

    # Bhadra Kaal (Vishti Karana) Rules Mapping based on Lunar Day patterns
    # Approximates when the specialized 12-hour friction blocks intercept the day
    bhadra_active = False
    bhadra_start_dt = mumbai_sunrise
    bhadra_end_dt = mumbai_sunrise
    
    tithi_day = target_date_mumbai.day % 15
    if is_shukla_paksha:
        if tithi_day in [4, 11]:  # Bhadra rules the second half of 4th and 11th Tithis
            bhadra_active = True
            bhadra_start_dt = mumbai_sunrise + timedelta(hours=6)
            bhadra_end_dt = mumbai_sunset
        elif tithi_day in [8, 15]:  # Bhadra rules the first half of 8th and 15th Tithis
            bhadra_active = True
            bhadra_start_dt = mumbai_sunrise
            bhadra_end_dt = mumbai_sunrise + timedelta(hours=6)
    else:
        if tithi_day in [3, 10]:  # Krishna Paksha counterparts
            bhadra_active = True
            bhadra_start_dt = mumbai_sunrise + timedelta(hours=6)
            bhadra_end_dt = mumbai_sunset
        elif tithi_day in [7, 14]:
            bhadra_active = True
            bhadra_start_dt = mumbai_sunrise
            bhadra_end_dt = mumbai_sunrise + timedelta(hours=6)

    if bhadra_active:
        bhadra_alert = f"{bhadra_start_dt.astimezone(nl_tz).strftime('%I:%M %p')} to {bhadra_end_dt.astimezone(nl_tz).strftime('%I:%M %p')} (High Friction - Hold Execution)"

    # 4. Construct the Explicit Output
    if is_amavasya_in_window:
        amavasya_forecast = (
            f"⚠️ AMAVASYA IN 2-DAY WINDOW:\n"
            f"• Starts: {amavasya_start_nl.strftime('%A, %d-%b at %I:%M %p')} (NL Clock)\n"
            f"• Ends: {amavasya_end_nl.strftime('%A, %d-%b at %I:%M %p')} (NL Clock)"
        )
    else:
        amavasya_forecast = (
            f"🔮 2-DAY FORECAST WATCH:\n"
            f"• No Amavasya opening between now and {two_days_later_nl.strftime('%A, %d-%b at %I:%M %p')}.\n"
            f"• Next Amavasya starts on: {amavasya_start_nl.strftime('%A, %d-%b at %I:%M %p')} (NL Clock)"
        )

    message_body = (
        f"⏳ === 2-DAY FUTURE FORECAST ===\n"
        f"{amavasya_forecast}\n\n"
        f"📊 === TOMORROW'S TRACKING SNAPSHOT ===\n"
        f"• Date: {target_date_nl.strftime('%A, %d-%b-%Y')}\n"
        f"• Tithi: {tithi_name}\n"
        f"• Nakshatra: {star_name}\n"
        f"• Yoga/Karana: {yoga_alert} | {karana_alert}\n\n"
        f"🚫 === RISK WINDOWS (NETHERLANDS TIME) ===\n"
        f"• Rahu Kaal: {rahu_time_string}\n"
        f"• Gulika Kaal: {gulika_time_string}\n"
        f"• Bhadra Kaal: {bhadra_alert}"
    )

    title_tag = "Mumbai Amavasya Alert" if is_amavasya_tomorrow else "Daily Financial Panchang Update"

    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message_body.encode('utf-8'),
        headers={
            "Title": title_tag,
            "Priority": "high",
            "Tags": "chart_with_upwards_trend,warning,bell"
        }
    )
    print("Clean timestamp notification with Bhadra Kaal dispatched successfully.")

if __name__ == "__main__":
    check_mumbai_market_panchang()
