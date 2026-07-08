import requests
import pytz
from datetime import datetime
from vedastro import *

# Configuration
NTFY_TOPIC = "mumama"
NL_TZ = pytz.timezone('Europe/Amsterdam')
IN_TZ = pytz.timezone('Asia/Kolkata')
LOC_LAT, LOC_LON = 19.0760, 72.8777

def get_panchang_data():
    # Setup API and Location
    Calculate.SetAPIKey('FreeAPIUser')
    location = GeoLocation("Mumbai", LOC_LON, LOC_LAT)
    
    # Get current time in India for calculation
    now_in = datetime.now(IN_TZ)
    time_data = Time(
        hour=now_in.hour, minute=now_in.minute, 
        day=now_in.day, month=now_in.month, year=now_in.year, 
        offset="+05:30", geolocation=location
    )

    # Fetch Calculations
    tithi = Calculate.LunarDay(time_data)
    nakshatra = Calculate.MoonConstellation(time_data)
    karana = Calculate.Karana(time_data)
    
    # Construct Message
    lines = [f"=== Vedic Insight: {now_in.strftime('%d-%b-%Y')} ==="]
    lines.append(f"• Tithi: {tithi}")
    lines.append(f"• Nakshatra: {nakshatra}")
    
    # Bhadra (Vishti Karana)
    if "Vishti" in str(karana):
        lines.append("• ALERT: Bhadra Kaal is ACTIVE (High Friction)")
    
    # Phases and Special Days
    tithi_str = str(tithi)
    if "Amavasya" in tithi_str:
        lines.append("• Today is AMAVASYA (New Moon Peak)")
    elif "Purnima" in tithi_str:
        lines.append("• Today is PURNIMA (Full Moon Peak)")
    elif "Ekadashi" in tithi_str:
        lines.append("• Today is EKADASHI (Holy Fasting Day)")

    return "\n".join(lines)

def send_notification():
    try:
        message = get_panchang_data()
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode('utf-8'),
            headers={"Title": "Daily Vedic Insight", "Priority": "high"}
        )
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_notification()
