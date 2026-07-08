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

def get_day_report(target_dt):
    """Calculates all metrics and returns a list of formatted strings."""
    time_data = Time(
        hour=12, minute=0,
        day=target_dt.day, month=target_dt.month, year=target_dt.year, 
        offset="+05:30", geolocation=location
    )
    
    tithi = str(Calculate.LunarDay(time_data))
    nakshatra = str(Calculate.MoonConstellation(time_data))
    karana = str(Calculate.Karana(time_data))
    
    # Paksha calculation: Shukla if Tithi 1-15, Krishna if 16-30
    # Vedastro Tithi string usually contains the name
    paksha = "Shukla Paksha" if any(x in tithi for x in ["Shukla", "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shasthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"]) else "Krishna Paksha"

    # Rahu Kaal (Standard Vedic Table based on weekday)
    weekday = target_dt.weekday()
    rahu_table = {0: ("07:30 AM", "09:00 AM"), 1: ("03:00 PM", "04:30 PM"), 2: ("12:00 PM", "01:30 PM"), 
                  3: ("01:30 PM", "03:00 PM"), 4: ("10:30 AM", "12:00 PM"), 5: ("09:00 AM", "10:30 AM"), 6: ("04:30 PM", "06:00 PM")}
    rahu_start, rahu_end = rahu_table[weekday]

    lines = [
        f"• Tithi: {tithi}",
        f"• Paksha: {paksha}",
        f"• Nakshatra: {nakshatra}",
        f"• Rahu Kaal: {rahu_start} to {rahu_end}"
    ]
    
    if "Vishti" in karana:
        lines.append("• ALERT: Bhadra Kaal ACTIVE (High Friction)")
    
    for phase in ["Amavasya", "Purnima", "Ekadashi"]:
        if phase in tithi:
            lines.append(f"• Special Phase: {phase} Active")
            
    return lines

def generate_report():
    report = ["=== 2-DAY DETAILED PANCHANG FORECAST ==="]
    for i in range(2):
        target_dt = datetime.now(IN_TZ) + timedelta(days=i)
        report.append(f"\n--- {target_dt.strftime('%A, %d-%b-%Y')} ---")
        report.extend(get_day_report(target_dt))
    return "\n".join(report)

if __name__ == "__main__":
    message = generate_report()
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode('utf-8'),
        headers={"Title": "Panchang Update", "Priority": "high"}
    )
