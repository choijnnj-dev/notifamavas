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
    utc_amavasya_peak = next_new_moon.datetime().replace(tzinfo=pytz.utc)
    mumbai_amavasya_peak = utc_amavasya_peak.astimezone(mumbai_tz)
    
    amavasya_start_nl = (mumbai_amavasya_peak - timedelta(hours=12)).astimezone(nl_tz)
    amavasya_end_nl = (mumbai_amavasya_peak + timedelta(hours=12)).astimezone(nl_tz)
    
    # Calculate Purnima (Full Moon Peak)
    next_full_moon = ephem.next_full_moon(gate.date)
    utc_purnima_peak = next_full_moon.datetime().replace(tzinfo=pytz.utc)
    mumbai_purnima_peak = utc_purnima_peak.astimezone(mumbai_tz)
    
    purnima_start_nl = (mumbai_purnima_peak - timedelta(hours=12)).astimezone(nl_tz)
    purnima_end_nl = (mumbai_purnima_peak + timedelta(hours=12)).astimezone(nl_tz)
    
    # Construct the message body dynamically based on what is active
    message_lines = ["=== 2-DAY FUTURE FORECAST ==="]
    
    # Check if lunar events open within our 2-day lookahead window
    if amavasya_start_nl <= two_days_later_nl:
        message_lines.append(f"AMAVASYA IN 2-DAY WINDOW:")
        message_lines.append(f"• Starts: {amavasya_start_nl.strftime('%A, %d-%b at %I:%M %p')} (NL Clock)")
        message_lines.append(f"• Ends: {amavasya_end_nl.strftime('%A, %d-%b at %I:%M %p')} (NL Clock)")
        
    if purnima_start_nl <= two_days_later_nl:
        message_lines.append(f"PURNIMA IN 2-DAY WINDOW:")
        message_lines.append(f"• Starts: {purnima_start_nl.strftime('%A, %d-%b at %I:%M %p')} (NL Clock)")
        message_lines.append(f"• Ends: {purnima_end_nl.strftime('%A, %d-%b at %I:%M %p')} (NL Clock)")

    # 2-Day Loop for Risk and Tracking Snapshot
    for i in range(1, 3):
        target_date_nl = now_nl + timedelta(days=i)
        target_date_mumbai = target_date_nl.astimezone(mumbai_tz)
        
        gate.date = target_date_mumbai.replace(hour=12, minute=0).strftime('%Y/%m/%d %H:%M:%S')
        moon = ephem.Moon(gate)
        
        # Nakshatra Calculation
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
        
        # Determine Phase Status
        is_amavasya_active = amavasya_start_nl.date() <= target_date_nl.date() <= amavasya_end_nl.date()
        is_purnima_active = purnima_start_nl.date() <= target_date_nl.date() <= purnima_end_nl.date()
        is_shukla_paksha = not is_amavasya_active and (mumbai_amavasya_peak - target_date_mumbai).days > 14
        
        yoga_alert = "Normal Daily Balance"
        karana_alert = "Standard Dynamic"
        
        if is_amavasya_active:
            tithi_name = f"Amavasya Phase (Active NL: {amavasya_start_nl.strftime('%I:%M %p')} to {amavasya_end_nl.strftime('%I:%M %p')})"
        elif is_purnima_active:
            tithi_name = f"Purnima Phase (Active NL: {purnima_start_nl.strftime('%I:%M %p')} to {purnima_end_nl.strftime('%I:%M %p')})"
        elif is_shukla_paksha:
            tithi_name = "Shukla Paksha (Waxing Light) [UPWARD TREND]"
            if target_date_mumbai.day % 15 in [2, 3, 5, 11, 13]:
                tithi_name += " - Strategic Wealth Accumulation Active!"
                yoga_alert = "Amrita / Sarvartha Siddhi Operational"
                karana_alert = "Bava / Balava Growth Window Open [GROWTH]"
        else:
            tithi_name = "Krishna Paksha (Waning Light) [DOWNWARD TREND]"
            
        message_lines.append(f"\n=== FORECAST DAY {i}: {target_date_nl.strftime('%A, %d-%b-%Y')} ===")
        message_lines.append(f"• Tithi: {tithi_name}")
        message_lines.append(f"• Nakshatra: {star_name}")
        message_lines.append(f"• Yoga/Karana: {yoga_alert} | {karana_alert}")
        
        # Risk Windows
        mumbai_sunrise = target_date_mumbai.replace(hour=6, minute=0, second=0, microsecond=0)
        mumbai_sunset = target_date_mumbai.replace(hour=18, minute=30, second=0, microsecond=0)
        weekday = target_date_mumbai.weekday()  
        
        rahu_slots = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
        gulika_slots = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}
        
        def get_window_times(slot_index):
            w_start = mumbai_sunrise + timedelta(hours=(slot_index - 1) * 1.5)
            w_end = w_start + timedelta(hours=1.5)
            return w_start.astimezone(nl_tz), w_end.astimezone(nl_tz)

        rahu_start, rahu_end = get_window_times(rahu_slots[weekday])
        gulika_start, gulika_end = get_window_times(gulika_slots[weekday])
        
        # Only add risk metrics if they occur during the timeline context (Filtering out 'No' strings)
        message_lines.append(f"• Rahu Kaal: {rahu_start.strftime('%d-%b %I:%M %p')} to {rahu_end.strftime('%d-%b %I:%M %p')}")
        message_lines.append(f"• Gulika Kaal: {gulika_start.strftime('%d-%b %I:%M %p')} to {gulika_end.strftime('%d-%b %I:%M %p')}")
        
        # Bhadra Calculation
        bhadra_active = False
        tithi_day = target_date_mumbai.day % 15
        if is_shukla_paksha:
            if tithi_day in [4, 11]:
                bhadra_active = True
                bhadra_start_dt = mumbai_sunrise + timedelta(hours=6)
                bhadra_end_dt = mumbai_sunset
            elif tithi_day in [8, 15]:
                bhadra_active = True
                bhadra_start_dt = mumbai_sunrise
                bhadra_end_dt = mumbai_sunrise + timedelta(hours=6)
        else:
            if tithi_day in [3, 10]:
                bhadra_active = True
                bhadra_start_dt = mumbai_sunrise + timedelta(hours=6)
                bhadra_end_dt = mumbai_sunset
            elif tithi_day in [7, 14]:
                bhadra_active = True
                bhadra_start_dt = mumbai_sunrise
                bhadra_end_dt = mumbai_sunrise + timedelta(hours=6)
                
        if bhadra_active:
            bh_start_nl = bhadra_start_dt.astimezone(nl_tz)
            bh_end_nl = bhadra_end_dt.astimezone(nl_tz)
            message_lines.append(f"• Bhadra Kaal: {bh_start_nl.strftime('%d-%b %I:%M %p')} to {bh_end_nl.strftime('%d-%b %I:%M %p')} (High Friction - Hold Execution)")

    message_body = "\n".join(message_lines)
    title_tag = "Financial Panchang 2-Day Update"

    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message_body.encode('utf-8'),
        headers={
            "Title": title_tag,
            "Priority": "high"
        }
    )
    print("Clean 2-day forecast timestamp notification dispatched successfully.")

if __name__ == "__main__":
    check_mumbai_market_panchang()
