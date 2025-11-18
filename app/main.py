from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta, timezone
from typing import Dict
import uuid

app = FastAPI(title="Timer Microservice")

# in memory we store timer_id -> dict
timers: Dict[str, dict] = {}

# status strings
STATUS_PENDING = "pending"
STATUS_PAUSED = "paused"
STATUS_ENDED = "ended"
STATUS_CANCELED = "canceled"

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def compute_remaining_or_end(t: dict) -> None:
    """For pending timer, update remaining_ms based on expires_at.
    If time is up, set status='ended' and remaining_ms=0.
    For others states, we do nothing."""

    # pending return status
    if t["status"] != STATUS_PENDING:
        return
    
    expires_at = t["expires_at"]
    if expires_at is None:
        # fail safe case
        t["remaining_ms"] = 0
        t["status"] = STATUS_ENDED
        return
    
    diff_ms = int((expires_at - now_utc()).total_seconds() * 1000)
    if diff_ms <= 0:
        t["remaining_ms"] = 0
        t["status"] = STATUS_ENDED
    else:
        t["remaining_ms"] = diff_ms
# end func

def format_timer(t: dict) -> dict:
    # convert datetypes to strings for JSON
    return {
        "timer_id": t["timer_id"],
        "status": t["status"],
        "created_at": t["created_at"].isoformat(),
        "expires_at": t["expires_at"].isoformat() if t["expires_at"] is not None else None,
        "remaining_ms": t["remaining_ms"],
    }
# end func


# timer creation func
@app.post("/timers")
def create_timer(duration_ms: int):
    '''
    create a new timer:
      duration_ms is passed as a query parameter: /timers?duration_ms=200
      starts in 'pending'
    '''
    # duration check
    if duration_ms < 1:
        raise HTTPException(status_code=400, detail="duration_ms must be >= 1")

    timer_id = str(uuid.uuid4())
    created_at = now_utc()
    expires_at = created_at + timedelta(milliseconds=duration_ms)


    t = {
        "timer_id": timer_id,
        "status": STATUS_PENDING,
        "created_at": created_at,
        "expires_at": expires_at,
        "remaining_ms": duration_ms,
    }
    timers[timer_id] = t
    return format_timer(t)
# end func

@app.get("/timers/{timer_id}")
def get_timer(timer_id: str):
    '''
    get current status of timer
    for pending, recalculate remaining_ms, possible switch to 'ended' if time is up
    '''
    t = timers.get(timer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Timer not found")
    
    # get remaining time w func:
    compute_remaining_or_end(t)
    # return with json formatting func:
    return format_timer(t)

@app.patch("/timers/{timer_id}")
def pause_or_resume_timer(timer_id: str, op: str):
    '''
    pause or resume timer
      op is query param - for: ?op=pause or ?op=resume
      pause: only from 'pending' status
      resume: also only from ''pending' status
    '''

    t = timers.get(timer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Timer not found")
    
    if op == "pause":
        compute_remaining_or_end(t)
        if t["status"] != STATUS_PENDING:
            raise HTTPException(status_code=409, detail="Can only pause timers that are pending")
        
# freeze/pause 'remaining_ms' and clear out 'expires_at' while paused
        t["expires_at"] = None
        t["status"] = STATUS_PAUSED
        return format_timer(t)

    elif op == "resume":
        if t["status"] != STATUS_PAUSED:
            raise HTTPException(status_code=409, detail="Can only resume a paused timer")

        # Resume countdown from remaining_ms
        remaining = t["remaining_ms"]
        new_expires_at = now_utc() + timedelta(milliseconds=remaining)
        t["expires_at"] = new_expires_at
        t["status"] = STATUS_PENDING
        return format_timer(t)

    else:
        raise HTTPException(status_code=400, detail="operation must be 'pause' or 'resume'")


@app.delete("/timers/{timer_id}")
def cancel_timer(timer_id: str):
    """
    cancel a timer
    ff already canceled: return the same state
    if ended: return 409 (cannot cancel an ended timer)
    otherwise: set status='canceled', remaining_ms=0, expires_at=None
    """
    t = timers.get(timer_id)
    if not t:
        raise HTTPException(status_code=404, detail="Timer not found")

    # If it was still pending, see if it should end first
    compute_remaining_or_end(t)

    if t["status"] == STATUS_ENDED:
        raise HTTPException(status_code=409, detail="Cannot cancel an ended timer")

    if t["status"] == STATUS_CANCELED:
        return format_timer(t)

    t["status"] = STATUS_CANCELED
    t["remaining_ms"] = 0
    t["expires_at"] = None

    return format_timer(t)
