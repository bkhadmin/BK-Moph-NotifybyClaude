import asyncio
from app.db.session import SessionLocal
from app.repositories.send_logs import get_failed_or_pending
from app.services.send_pipeline import retry_failed_log

# NOTE: Scheduled job execution is handled exclusively by worker_scheduler.py
# This worker only retries failed/pending send_logs to avoid double-sending.

async def loop():
    while True:
        db = SessionLocal()
        try:
            retry_rows = get_failed_or_pending(db)
            for row in retry_rows[:20]:
                if row.retry_count < 5 and row.status in ("failed", "retrying", "pending"):
                    await retry_failed_log(db, row)
        except Exception as exc:
            print("worker error:", exc)
        finally:
            db.close()
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(loop())
