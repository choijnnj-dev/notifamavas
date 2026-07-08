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

def get_panchang_for_time(dt):
    """Fetches high-precision state at a specific time."""
    time_data = Time(
        hour=dt.hour, minute=dt.minute, 
        day=dt.day, month=dt.month, year=dt.year, 
        offset="+05:30", geolocation=location
    )
    return {
        "tithi": str(Calculate.LunarDay(time_data)),
        "nakshatra": str(Calculate.MoonConstellation(time_data)),
        "karana": str(Calculate.Karana(time_data))
    }

def generate_report():
    report = ["=== 2-DAY DETAILED PANCHANG FORECAST ==="]
    
    # Loop for today and tomorrow
    for i in range(2):
        target_dt = datetime.now(IN_TZ) + timedelta(days=i)
        data = get_panchang_for_time(target_dt)
        
        day_label = "Today" if i == 0 else "Tomorrow"
        report.append(f"\n--- {day_label} ({target_dt.strftime('%d-%b')}) ---")
        report.append(f"• Tithi: {data['tithi']}")
        report.append(f"• Nakshatra: {data['nakshatra']}")
        
        # Risk & Phase Logic
        if "Vishti" in data['karana']:
            report.append("• ALERT: Bhadra Kaal ACTIVE (High Friction)")
        
        special_phases = ["Amavasya", "Purnima", "Ekadashi"]
        for phase in special_phases:
            if phase in data['tithi']:
                report.append(f"• Special Phase: {phase} Active")

    return "\n".join(report)

if __name__ == "__main__":
    message = generate_report()
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode('utf-8'),
        headers={"Title": "Accurate 2-Day Panchang", "Priority": "high"}
    )
