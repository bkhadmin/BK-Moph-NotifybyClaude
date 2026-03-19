import asyncio
from datetime import datetime
from app.db.session import SessionLocal
from app.repositories.schedule_jobs import get_due_jobs, mark_ran
from app.repositories.send_logs import get_failed_or_pending
from app.services.job_runner import run_job
from app.services.send_pipeline import retry_failed_log

async def loop():
    while True:
        db = SessionLocal()
        try:
            due = get_due_jobs(db, datetime.now())
            for job in due:
                result = await run_job(db, job)
                if result:
                    mark_ran(db, job, result["next_run_at"], result["last_run_at"])

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
