from vedastro import *
from datetime import datetime, timedelta
import pytz
import requests

# Configuration
NTFY_TOPIC = "mumama"
LOC_LAT, LOC_LON = 19.0760, 72.8777
location = GeoLocation("Mumbai", LOC_LON, LOC_LAT)
NL_TZ = pytz.timezone('Europe/Amsterdam')
IN_TZ = pytz.timezone('Asia/Kolkata')

# Initialize API
Calculate.SetAPIKey('FreeAPIUser')

def get_data_for_time(dt):
    """Fetches high-precision state at a specific time."""
    time_data = Time(
        hour=dt.hour, minute=dt.minute, 
        day=dt.day, month=dt.month, year=dt.year, 
        offset="+05:30", geolocation=location
    )
    
    # Get current state
    tithi = str(Calculate.LunarDay(time_data))
    nakshatra = str(Calculate.MoonConstellation(time_data))
    karana = str(Calculate.Karana(time_data))
    
    # Get transition timestamps
    next_tithi_change = Calculate.NextLunarDayChange(time_data)
    next_nak_change = Calculate.NextConstellationChange(time_data)
    
    return {
        "tithi": tithi,
        "nakshatra": nakshatra,
        "karana": karana,
        "next_tithi_change": next_tithi_change,
        "next_nak_change": next_nak_change
    }

def generate_report():
    report = ["=== 2-DAY DETAILED PANCHANG FORECAST ==="]
    
    # Loop for today and tomorrow
    for i in range(2):
        target_dt = datetime.now(IN_TZ) + timedelta(days=i)
        data = get_data_for_time(target_dt)
        
        day_label = "Today" if i == 0 else "Tomorrow"
        report.append(f"\n--- {day_label} ({target_dt.strftime('%d-%b')}) ---")
        report.append(f"• Tithi: {data['tithi']} (Changes: {data['next_tithi_change']})")
        report.append(f"• Nakshatra: {data['nakshatra']} (Changes: {data['next_nak_change']})")
        
        if "Vishti" in data['karana']:
            report.append("• ALERT: Bhadra Kaal ACTIVE (High Friction)")
            
        if any(x in data['tithi'] for x in ["Amavasya", "Purnima", "Ekadashi"]):
            report.append(f"• Special Phase: {data['tithi']} Active")

    return "\n".join(report)

if __name__ == "__main__":
    message = generate_report()
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode('utf-8'),
        headers={"Title": "Accurate 2-Day Panchang", "Priority": "high"}
    )
