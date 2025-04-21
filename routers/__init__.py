# Makes 'routers' a Python package
# Import individual routers to make them easily accessible
from . import auth, categories, reports, transactions, budgets, recurring_transactions, ai_consultation # Add budgets, recurring_tx, ai

# You could optionally define an aggregated router here if needed,
# but including them individually in main app setup is also common.
