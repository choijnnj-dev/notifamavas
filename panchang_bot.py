import requests
import pytz
from datetime import datetime, timedelta
from vedastro import *

# Configuration
NTFY_TOPIC = "mumama"
IN_TZ = pytz.timezone('Asia/Kolkata')
LOC_LAT, LOC_LON = 19.0760, 72.8777
location = GeoLocation("Mumbai", LOC_LON, LOC_LAT)
Calculate.SetAPIKey('FreeAPIUser')

def get_day_data(target_dt):
    """Calculates all required Vedic data for a specific day."""
    time_data = Time(
        hour=12, minute=0, # Mid-day calculation for stable daily markers
        day=target_dt.day, month=target_dt.month, year=target_dt.year, 
        offset="+05:30", geolocation=location
    )
    
    # Accurate Vedic markers
    tithi = str(Calculate.LunarDay(time_data))
    nakshatra = str(Calculate.MoonConstellation(time_data))
    karana = str(Calculate.Karana(time_data))
    
    # Rahu Kaal (Logic based on day of the week)
    # Mapping: Mon=0 ... Sun=6
    weekday = target_dt.weekday()
    # Rahu Kaal standard start/end offsets from sunrise (approx 06:00)
    rahu_table = {0: (7.5, 9.0), 1: (15.0, 16.5), 2: (12.0, 13.5), 
                  3: (13.5, 15.0), 4: (10.5, 12.0), 5: (9.0, 10.5), 6: (16.5, 18.0)}
    start_h, end_h = rahu_table[weekday]
    rahu_start = (target_dt.replace(hour=6, minute=0) + timedelta(hours=start_h)).strftime('%I:%M %p')
    rahu_end = (target_dt.replace(hour=6, minute=0) + timedelta(hours=end_h)).strftime('%I:%M %p')

    return {
        "tithi": tithi,
        "nakshatra": nakshatra,
        "is_bhadra": "Vishti" in karana,
        "rahu": f"{rahu_start} - {rahu_end}"
    }

def generate_report():
    report = [f"=== 2-DAY DETAILED PANCHANG FORECAST ==="]
    
    for i in range(2):
        target_dt = datetime.now(IN_TZ) + timedelta(days=i)
        data = get_day_data(target_dt)
        
        day_label = "Today" if i == 0 else "Tomorrow"
        report.append(f"\n--- {day_label} ({target_dt.strftime('%d-%b-%Y')}) ---")
        report.append(f"• Tithi: {data['tithi']}")
        report.append(f"• Nakshatra: {data['nakshatra']}")
        report.append(f"• Rahu Kaal: {data['rahu']}")
        
        if data['is_bhadra']:
            report.append("• ALERT: Bhadra Kaal ACTIVE (High Friction)")
            
        for phase in ["Amavasya", "Purnima", "Ekadashi"]:
            if phase in data['tithi']:
                report.append(f"• Special Phase: {phase} Active")

    return "\n".join(report)

if __name__ == "__main__":
    message = generate_report()
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode('utf-8'),
        headers={"Title": "Panchang Update", "Priority": "high"}
    )
