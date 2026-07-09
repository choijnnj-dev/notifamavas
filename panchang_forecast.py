import json
from datetime import date
import requests

URL = "https://vedicpanchanga.com/api/get-panchang"

params = {
    "latitude": 19.0760,
    "longitude": 72.8777,
    "date": date.today().isoformat(),
    "timezone": "Europe/Amsterdam",
}

print("Requesting Panchang...")
print(params)

response = requests.get(URL, params=params, timeout=60)

print("Status Code:", response.status_code)

response.raise_for_status()

data = response.json()

print("\n========== JSON ==========\n")
print(json.dumps(data, indent=2, ensure_ascii=False))

with open("panchang_output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\nSaved as panchang_output.json")
