import requests
from datetime import datetime, timedelta
from skyfield.api import load
from skyfield import almanac
import pytz

# Connected directly to your phone's topic channel
NTFY_TOPIC = "mumama"

def check_amavasya_mumbai_to_nl():
    mumbai_tz = pytz.timezone('Asia/Kolkata')
    nl_tz = pytz.timezone('Europe/Amsterdam')
    
    eph = load('de421.bsp')
    ts = load.timescale()
    
    # Scanning window: From 7 PM tonight up to 2 full days forward
    now_nl = datetime.now(nl_tz)
    t0 = ts.from_datetime(now_nl)
    t1 = ts.from_datetime(now_nl + timedelta(days=2))
    
    times, phases = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))
    
    amavasya_found = False
    timing_details = ""
    
    for t, phase in zip(times, phases):
        if phase == 0:  # 0 indicates the astronomical center point of Amavasya
            amavasya_found = True
            
            utc_time = t.astimezone(pytz.utc)
            mumbai_peak = utc_time.astimezone(mumbai_tz)
            
            # Calculate traditional Tithi span (12 hours before and after the astronomical peak)
            mumbai_start = mumbai_peak - timedelta(hours=12)
            mumbai_end = mumbai_peak + timedelta(hours=12)
            
            # Convert the calculated times directly into your Netherlands local clocks
            nl_start = mumbai_start.astimezone(nl_tz)
            nl_end = mumbai_end.astimezone(nl_tz)
            
            timing_details = (
                f"🇮🇳 **Mumbai (Local Clock):**\n"
                f"• Starts: {mumbai_start.strftime('%A, %d-%b at %I:%M %p')}\n"
                f"• Ends: {mumbai_end.strftime('%A, %d-%b at %I:%M %p')}\n\n"
                f"🇳🇱 **Netherlands (Your Clock):**\n"
                f"• Starts: {nl_start.strftime('%A, %d-%b at %I:%M %p')}\n"
                f"• Ends: {nl_end.strftime('%A, %d-%b at %I:%M %p')}\n\n"
                f"⏳ **Total Span:** 24 Hours"
            )
            break

    if amavasya_found:
        message_body = (
            f"🌑 **Upcoming Amavasya Detected!**\n"
            f"An Amavasya phase crosses Mumbai coordinates within your 2-day monitoring window.\n\n"
            f"{timing_details}\n\n"
            f"🔗 Live Drik Panchang: https://www.drikpanchang.com/panchang/day-panchang.html?geoname-id=1275339"
        )
        
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}", 
            data=message_body.encode('utf-8'),
            headers={
                "Title": "Amavasya Lookahead Alert",
                "Priority": "high",
                "Tags": "moon,calendar,alarm_clock"
            }
        )
        print("Amavasya detected! Notification pushed directly to phone.")
    else:
        print("No Amavasya coming up within the next 2 days. Keeping silent.")

if __name__ == "__main__":
    check_amavasya_mumbai_to_nl()
