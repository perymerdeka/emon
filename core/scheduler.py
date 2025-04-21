import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from datetime import date

# Import the service function to be scheduled
# Ensure the service function itself is async if using AsyncIOScheduler directly
from services.recurring_transaction_service import generate_due_transactions

# Configure job stores and executors
jobstores = {
    'default': MemoryJobStore()
}
executors = {
    'default': AsyncIOExecutor()
}
job_defaults = {
    'coalesce': False, # Run missed jobs if scheduler was down (be careful with this)
    'max_instances': 1 # Only allow one instance of the job to run at a time
}

# Initialize the scheduler
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='UTC' # Or your preferred timezone
)

def schedule_recurring_transaction_job():
    """Adds the recurring transaction generation job to the scheduler."""
    job_id = 'generate_recurring_transactions'
    # Check if job already exists to prevent duplicates during hot reload
    if not scheduler.get_job(job_id):
        scheduler.add_job(
            generate_due_transactions, # Pass the async function directly
            trigger='cron', # Use cron trigger for daily execution
            hour=1,        # Run at 1 AM UTC (adjust as needed)
            minute=0,
            id=job_id,
            name='Generate Due Recurring Transactions',
            replace_existing=True # Replace if job with same ID exists (useful for updates)
        )
        print(f"Scheduled job '{job_id}' to run daily at 01:00 UTC.")
    else:
        print(f"Job '{job_id}' already scheduled.")

async def start_scheduler():
    """Starts the scheduler if it's not already running."""
    if not scheduler.running:
        scheduler.start()
        print("Scheduler started.")
        # Add the job after starting
        schedule_recurring_transaction_job()

async def shutdown_scheduler():
    """Shuts down the scheduler gracefully."""
    if scheduler.running:
        # Wait for running jobs to complete? (timeout optional)
        scheduler.shutdown(wait=False) # Set wait=True if needed
        print("Scheduler shut down.")
