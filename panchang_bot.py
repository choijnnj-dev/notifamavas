import requests
import ephem
from datetime import datetime, timedelta
import pytz

# Constants
NTFY_TOPIC = "mumama"
NL_TZ = pytz.timezone('Europe/Amsterdam')
IN_TZ = pytz.timezone('Asia/Kolkata')
LOC_LAT, LOC_LON = '19.0760', '72.8777'

def get_panchang_data():
    observer = ephem.Observer()
    observer.lat, observer.lon = LOC_LAT, LOC_LON
    now_utc = datetime.utcnow()
    observer.date = now_utc
    
    sun = ephem.Sun(observer)
    moon = ephem.Moon(observer)
    
    # 1. Tithi & Paksha Calculation
    diff = (moon.hlon - sun.hlon) % 360
    tithi_index = int(diff / 12) + 1
    paksha = "Shukla Paksha" if diff < 180 else "Krishna Paksha"
    
    # 2. Nakshatra Calculation
    nakshatra_idx = int((moon.hlon * (180/3.14159)) / 13.33) % 27
    nakshatras = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
    
    # 3. Rahu Kaal (Standard Vedic Table)
    # Mapping: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
    weekday = datetime.now(IN_TZ).weekday()
    rahu_start_offsets = {0: 7.5, 1: 3.0, 2: 10.5, 3: 9.0, 4: 6.0, 5: 4.5, 6: 12.0} # Hours from sunrise
    
    # 4. Bhadra (Vishti Karana)
    # Vishti occurs when Karana is 7, 14, 21, 28 (approx)
    karana_idx = int((diff % 12) / 6) 
    is_bhadra = karana_idx == 1 # Second half of a Tithi half

    # Construct Message (Only adding what is active/relevant)
    lines = [f"=== Panchang Report: {datetime.now(NL_TZ).strftime('%d-%b-%Y')} ==="]
    lines.append(f"• Paksha: {paksha}")
    lines.append(f"• Current Nakshatra: {nakshatras[nakshatra_idx]}")
    
    if is_bhadra:
        lines.append("• ALERT: Bhadra Kaal is currently ACTIVE (High Friction)")
    
    if tithi_index == 30:
        lines.append("• Today is AMAVASYA (New Moon Peak)")
    elif tithi_index == 15:
        lines.append("• Today is PURNIMA (Full Moon Peak)")

    return "\n".join(lines)

# Send to NTFY
response = requests.post(
    f"https://ntfy.sh/{NTFY_TOPIC}",
    data=get_panchang_data().encode('utf-8'),
    headers={"Title": "Daily Vedic Insight", "Priority": "high"}
)
