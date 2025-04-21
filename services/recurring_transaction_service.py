from datetime import date, timedelta
from datetime import date, timedelta
from sqlmodel import Session, select # Keep sync Session for type hint if needed
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from dateutil.relativedelta import relativedelta
from typing import Optional, List, Union, Any # Added Union, Any

from models import RecurringTransaction, Transaction, RecurrenceFrequency, Category, User
# Import both session scopes and settings
from core.db import sync_session_scope, async_session_scope
from core.config import settings

def get_next_due_date(start_date: date, last_created: Optional[date], frequency: RecurrenceFrequency) -> date:
    """Calculates the next due date based on frequency."""
    current_check_date = last_created if last_created else start_date

    if frequency == RecurrenceFrequency.DAILY:
        # If no transaction created yet, next due is start_date, otherwise day after last created
        return start_date if not last_created else current_check_date + timedelta(days=1)
    elif frequency == RecurrenceFrequency.WEEKLY:
        return start_date if not last_created else current_check_date + timedelta(weeks=1)
    elif frequency == RecurrenceFrequency.MONTHLY:
        # relativedelta handles month ends correctly
        return start_date if not last_created else current_check_date + relativedelta(months=1)
    elif frequency == RecurrenceFrequency.YEARLY:
        return start_date if not last_created else current_check_date + relativedelta(years=1)
    else:
        # Should not happen with Enum validation, but good practice
        raise ValueError(f"Unknown frequency: {frequency}")

# This function needs to handle both sync and async execution internally
# It cannot be async itself if called directly from sync code,
# but the internal DB operations need to be conditional.
# If run via FastAPI background task, it can be async. Let's make it async.
async def generate_due_transactions(run_date: date = date.today()):
    """
    Checks for active recurring transactions that are due to be created
    on or before the run_date and generates the corresponding Transaction records.
    Handles both sync and async database sessions based on settings.
    """
    created_count = 0
    print(f"Running recurring transaction generation for date: {run_date}")

    # Choose the correct session scope based on settings
    session_context = async_session_scope() if settings.USE_ASYNC_DB else sync_session_scope()

    async with session_context as session: # Use async with for async scope
        # Find active recurring rules where start_date is on or before run_date
        statement = (
            select(RecurringTransaction)
            .where(RecurringTransaction.is_active == True)
            .where(RecurringTransaction.start_date <= run_date)
        )
        if settings.USE_ASYNC_DB:
            results = await session.exec(statement) # type: ignore [union-attr]
            active_rules = results.all()
        else:
            active_rules = session.exec(statement).all() # type: ignore [union-attr]


        for rule in active_rules:
            # Determine the next date a transaction should be created
            next_due = get_next_due_date(rule.start_date, rule.last_created_date, rule.frequency)

            # Loop to create transactions if multiple are due (e.g., if job hasn't run)
            while next_due <= run_date:
                # Check if the rule has an end date and if we've passed it
                if rule.end_date and next_due > rule.end_date:
                    print(f"Recurring rule ID {rule.id} ended ({rule.end_date}). Stopping generation for this rule on {next_due}.")
                    break # Stop generating for this rule

                # Get category details (needed for transaction type)
                if settings.USE_ASYNC_DB:
                    category = await session.get(Category, rule.category_id) # type: ignore [union-attr]
                else:
                    category = session.get(Category, rule.category_id) # type: ignore [union-attr]

                if not category or category.owner_id != rule.owner_id:
                    print(f"Warning: Category ID {rule.category_id} not found or invalid for recurring rule ID {rule.id}. Skipping generation for {next_due}.")
                    break # Stop generating for this rule for this cycle

                # Create the actual transaction record
                new_transaction = Transaction(
                    amount=rule.amount,
                    type=category.type,
                    date=next_due,
                    description=rule.description,
                    category_id=rule.category_id,
                    owner_id=rule.owner_id
                )
                session.add(new_transaction)
                created_count += 1
                print(f"Created transaction for rule ID {rule.id} on date {next_due}")

                # Update the rule's last created date
                rule.last_created_date = next_due
                session.add(rule)

                # Flush changes within the loop if needed (especially for async)
                if settings.USE_ASYNC_DB:
                    await session.flush() # type: ignore [union-attr]
                else:
                    session.flush() # type: ignore [union-attr]

                # Calculate the *next* potential due date for the loop
                next_due = get_next_due_date(rule.start_date, rule.last_created_date, rule.frequency)

        # Commit happens automatically when exiting the session_scope context manager

    print(f"Recurring transaction generation complete. Created {created_count} transactions.")
    return created_count

# Note: Need to install python-dateutil: pip install python-dateutil
# Add 'python-dateutil' to requirements.txt
