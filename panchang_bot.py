import requests
from datetime import datetime, timedelta
from skyfield.api import load, Topos
from skyfield import almanac
import pytz

# 1. CHANGE THIS to the exact topic name in your mobile ntfy app
NTFY_TOPIC = "mumama"

def check_amavasya_mumbai():
    # Mumbai coordinates and timezone settings
    mumbai_lat = 19.0760
    mumbai_lon = 72.8777
    mumbai_tz = pytz.timezone('Asia/Kolkata')
    
    # Load high-accuracy astronomical planetary data
    eph = load('de421.bsp')
    ts = load.timescale()
    
    # Check a 24-hour window starting from right now
    now = datetime.now(mumbai_tz)
    t0 = ts.from_datetime(now)
    t1 = ts.from_datetime(now + timedelta(days=1))
    
    # Find moon phases occurring today
    # New Moon (Amavasya) is mathematically phase 0
    times, phases = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))
    
    amavasya_detected = False
    exact_time_str = ""
    
    for t, phase in zip(times, phases):
        #if phase == 0:  # 0 represents the exact instant of the New Moon (Amavasya point)
        if True:
            amavasya_detected = True
            # Convert exact astronomical moment to local Mumbai Time
            local_time = t.astimezone(mumbai_tz)
            
            # Traditional Amavasya tithi spans roughly 12 hours before and after this exact peak point
            tithi_start = local_time - timedelta(hours=12)
            tithi_end = local_time + timedelta(hours=12)
            
            exact_time_str = (
                f"⏰ Starts: {tithi_start.strftime('%d-%b %I:%M %p')}\n"
                f"⏰ Ends: {tithi_end.strftime('%d-%b %I:%M %p')}\n"
                f"⏳ Approx Duration: 24 Hours"
            )
            break

    if amavasya_detected:
        message_body = (
            f"🌑 **Amavasya Alert (Mumbai)**\n\n"
            f"The New Moon tithi is occurring today!\n\n"
            f"{exact_time_str}\n\n"
            f"🔗 Live Dashboard: https://www.drikpanchang.com/panchang/day-panchang.html?geoname-id=1275339"
        )
        
        # Dispatch the live notification straight to your phone dashboard
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}", 
            data=message_body.encode('utf-8'),
            headers={
                "Title": "Mumbai Amavasya Timing",
                "Priority": "high",
                "Tags": "moon,clock8"
            }
        )
        print("Detailed time notification sent to phone!")
    else:
        print("No Amavasya alignment today.")

if __name__ == "__main__":
    check_amavasya_mumbai()
