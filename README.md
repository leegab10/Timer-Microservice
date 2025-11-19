ReadMe for Timer Microservice
RestAPI architecture
Python

timer microservice will run at: http://localhost:8000


main is in app folder, 'test.py' is in 'test_timer' folder

necessary timer status imports from 'app.main':
from app.main import app, STATUS_ENDED, STATUS_PENDING, STATUS_PAUSED, STATUS_CANCELED


----------------------Creating a timer (POST)-------------
# Example call:
# short timer (20 seconds)
r = client.post("/timers", params={"duration_ms": 20000})
t = r.json()

# t is the timer JSON as a dict:
# {
#   "timer_id": "...",
#   "status": "pending",
#   "created_at": "...",
#   "expires_at": "...",
#   "remaining_ms": 200
# }


------------- gettin gcurrent timer status ----------------

r = client.get(f"/timers/{timer_id}")
s = r.json()

# s is the timer's JSON, with updated status / remaining_ms
# ex/ "pending" with remaining_ms > 0 or "ended" with remaining_ms = 0






# FULL EXAMPLE:
# (starting a 5 sec timer and chekcing timer status)

import requests

# Start a 5-second timer
r = requests.post("http://localhost:8000/timers", params={"duration_ms": 5000})
timer = r.json()
print("Created:", timer)

# get status
status = requests.get(f"http://localhost:8000/timers/{timer['timer_id']}").json()
print("Status:", status)






