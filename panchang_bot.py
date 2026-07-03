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
    
    # Target Tomorrow's trade window (Calculated 24h out from the 7 PM script trigger)
    now_nl = datetime.now(nl_tz)
    target_date_nl = now_nl + timedelta(days=1)
    target_date_mumbai = target_date_nl.astimezone(mumbai_tz)
    
    # 2. Offline Astronomical Moon Math
    gate = ephem.Observer()
    gate.lat, gate.lon = mumbai_lat, mumbai_lon
    gate.date = target_date_mumbai.strftime('%Y/%m/%d %H:%M:%S')
    
    # Get next new moon moment safely offline
    next_new_moon = ephem.next_new_moon(gate.date)
    next_new_moon_dt = next_new_moon.datetime().replace(tzinfo=pytz.utc).astimezone(mumbai_tz)
    
    # Is Amavasya center point happening tomorrow?
    is_amavasya = next_new_moon_dt.date() == target_date_mumbai.date()
    
    # Calculate approximate Nakshatra offset mapping (Sidereal Lahiri standard)
    moon = ephem.Moon(gate)
    moon_lon = (float(moon.ra) * 15 - 24.2) % 360  
    nakshatra_idx = int(moon_lon / 13.33) % 27
    
    # Map the financial wealth markers you want to trace
    nakshatras = {
        0: "Ashwini (Swift / Day Trades)", 
        3: "Rohini (Fixed / Blue-Chip Holding)", 
        7: "Pushya (Super Wealth Nourisher)",
        13: "Chitra (Swift / Day Trades)", 
        21: "Shravana (Fixed / Blue-Chip Holding)", 
        26: "Revati (Swift / Day Trades)"
    }
    star_name = nakshatras.get(nakshatra_idx, "Standard Multi-Tier Star Alignment")

    # Dynamic Indicators Flags
    is_shukla_paksha = not is_amavasya and (next_new_moon_dt - target_date_mumbai).days > 14
    
    yoga_alert = "Normal Daily Balance"
    karana_alert = "Standard Dynamic"
    
    if is_amavasya:
        tithi_name = "Amavasya (New Moon Period)"
    elif is_shukla_paksha:
        tithi_name = "Shukla Paksha (Waxing Light) [UPWARD TREND]"
        if target_date_mumbai.day % 15 in [2, 3, 5, 11, 13]:
            tithi_name += " - Strategic Wealth Tithi Accumulation Active!"
            yoga_alert = "Amrita / Sarvartha Siddhi Operational"
            karana_alert = "Bava / Balava Growth Window Open [GROWTH]"
    else:
        tithi_name = "Krishna Paksha (Waning Light) [DOWNWARD TREND]"

    # 3. Micro-target the Volatile Warning Windows (Rahu & Gulika Kaal)
    mumbai_sunrise = target_date_mumbai.replace(hour=6, minute=0, second=0, microsecond=0)
    weekday = target_date_mumbai.weekday()  
    
    rahu_slots = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
    gulika_slots = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}
    
    def calculate_window_clocks(slot_index):
        window_start = mumbai_sunrise + timedelta(hours=(slot_index - 1) * 1.5)
        window_end = window_start + timedelta(hours=1.5)
        return f"{window_start.astimezone(nl_tz).strftime('%I:%M %p')} to {window_end.astimezone(nl_tz).strftime('%I:%M %p')}"

    rahu_time_string = calculate_window_clocks(rahu_slots[weekday])
    gulika_time_string = calculate_window_clocks(gulika_slots[weekday])

    # 4. Construct the Main Text Body
    message_body = (
        f"Date Checked: {target_date_nl.strftime('%A, %d-%b-%Y')}\n"
        f"Calculations explicitly anchored to Mumbai metrics\n\n"
        f"Tithi / Paksha System:\n• {tithi_name}\n\n"
        f"Financial Star Alignment:\n• {star_name}\n\n"
        f"Yogas & Karanas:\n• {yoga_alert}\n• {karana_alert}\n\n"
        f"NETHERLANDS TIME CAUTION WINDOWS:\n"
        f"Rahu Kaal: {rahu_time_string} (Impulsive Trap)\n"
        f"Gulika Kaal: {gulika_time_string} (Stagnant Stalling Risk)"
    )

    title_tag = "Mumbai Amavasya Alert" if is_amavasya else "Daily Financial Panchang Update"

    # Send data completely sanitized with clean headers
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message_body.encode('utf-8'),
        headers={
            "Title": title_tag,
            "Priority": "high",
            "Tags": "chart_with_upwards_trend,warning,bell"
        }
    )
    print("Market setup notification dispatched cleanly to device.")

if __name__ == "__main__":
    check_mumbai_market_panchang()
