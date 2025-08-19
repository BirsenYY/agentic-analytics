# logger.py
import csv, os, time
from datetime import datetime, timezone

LOG_PATH = "query_log.csv"

def log_event(*, user_q: str, sql: str, rows: int, ms: int, ok: bool, error: str | None = None):
    new = not os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["ts_iso", "epoch_s", "ok", "rows", "latency_ms", "question", "sql", "error"])
        now = datetime.now(timezone.utc)
        w.writerow([now.isoformat(), int(time.time()), int(ok), rows, ms, user_q, sql, (error or "")])
