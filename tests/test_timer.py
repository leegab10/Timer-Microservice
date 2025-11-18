import os
import sys
import time

# 1) Add project root (the folder that contains "app") to sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi.testclient import TestClient
from app.main import app, STATUS_ENDED, STATUS_PENDING, STATUS_PAUSED, STATUS_CANCELED

client = TestClient(app)


def test_full_flow_pause_resume_ended():
    # create a short timer (200 ms)
    r = client.post("/timers", params={"duration_ms": 200})
    assert r.status_code == 200
    t = r.json()
    timer_id = t["timer_id"]
    assert t["status"] == STATUS_PENDING
    assert t["remaining_ms"] > 0

    # get status (still pending)
    r = client.get(f"/timers/{timer_id}")
    assert r.status_code == 200
    s1 = r.json()
    assert s1["status"] == STATUS_PENDING
    rem1 = s1["remaining_ms"]

    # pause quickly - remaining_ms should freeze (and probably be less than rem1)
    r = client.patch(f"/timers/{timer_id}", params={"op": "pause"})
    assert r.status_code == 200
    paused = r.json()
    assert paused["status"] == STATUS_PAUSED
    paused_remaining = paused["remaining_ms"]
    assert paused_remaining <= rem1

    # wait a bit - it should not count down while paused
    time.sleep(0.15)
    r = client.get(f"/timers/{timer_id}")
    assert r.status_code == 200
    s2 = r.json()
    assert s2["status"] == STATUS_PAUSED
    assert s2["remaining_ms"] == paused_remaining

    # resume - timer should go back to pending
    r = client.patch(f"/timers/{timer_id}", params={"op": "resume"})
    assert r.status_code == 200
    resumed = r.json()
    assert resumed["status"] == STATUS_PENDING

    # wait again until it ends
    for _ in range(20):
        r = client.get(f"/timers/{timer_id}")
        s = r.json()
        if s["status"] == STATUS_ENDED:
            break
        time.sleep(0.05)

    assert s["status"] == STATUS_ENDED
    assert s["remaining_ms"] == 0


def test_cancel_timer():
    # create a timer with a bit more time
    r = client.post("/timers", params={"duration_ms": 500})
    assert r.status_code == 200
    timer_id = r.json()["timer_id"]

    # cancel it
    r = client.delete(f"/timers/{timer_id}")
    assert r.status_code == 200
    canceled = r.json()
    assert canceled["status"] == STATUS_CANCELED
    assert canceled["remaining_ms"] == 0

    # status stays canceled on later reads
    r = client.get(f"/timers/{timer_id}")
    assert r.status_code == 200
    again = r.json()
    assert again["status"] == STATUS_CANCELED
    assert again["remaining_ms"] == 0
