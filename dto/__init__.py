# Makes 'dto' a package
# Import DTOs for easier access elsewhere if needed
# Using absolute imports consistent with user's preference in models/__init__.py
from dto.category_dto import CategoryBase, CategoryRead, CategoryReadWithTransactions
from dto.transaction_dto import TransactionBase, TransactionRead, TransactionReadWithCategory
from dto.report_dto import MonthlyReport, CategorySummary
from dto.user_dto import UserCreate, UserRead, UserPasswordUpdate # Add UserPasswordUpdate
from dto.token_dto import Token, TokenPayload
from dto.budget_dto import BudgetBase, BudgetCreate, BudgetRead
from dto.recurring_transaction_dto import RecurringTransactionBase, RecurringTransactionCreate, RecurringTransactionRead
from dto.ai_consultation_dto import AIConsultationRequest, AIConsultationResponse, AIModelProvider
from dto.notification_dto import NotificationRead, NotificationUpdate # Add Notification DTOs
# Add new report DTOs
from dto.report_dto import MonthlyReport, YearlyReport, DateRangeReport, CategorySummary

# Call model_rebuild here after all DTOs that might use forward references
# have been imported. This resolves the circular dependencies.
CategoryReadWithTransactions.model_rebuild()
TransactionReadWithCategory.model_rebuild()
# Add other models needing rebuild if necessary
