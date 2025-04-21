from sqlmodel import SQLModel
from typing import Dict, List
from datetime import date  as dt_date # Import date

# Optional: DTO for breakdown by category
class CategorySummary(SQLModel):
    category_id: int
    category_name: str
    total_amount: float

# Main DTO for the monthly report response
class MonthlyReport(SQLModel):
    year: int
    month: int
    total_income: float = 0.0
    total_expense: float = 0.0
    net_balance: float = 0.0
    income_by_category: List[CategorySummary] = []
    expense_by_category: List[CategorySummary] = []

# DTO for Yearly report response
class YearlyReport(SQLModel):
    year: int
    total_income: float = 0.0
    total_expense: float = 0.0
    net_balance: float = 0.0
    income_by_category: List[CategorySummary] = []
    expense_by_category: List[CategorySummary] = []

# DTO for Custom Date Range report response
class DateRangeReport(SQLModel):
    start_date: dt_date
    end_date: dt_date
    total_income: float = 0.0
    total_expense: float = 0.0
    net_balance: float = 0.0
    income_by_category: List[CategorySummary] = []
    expense_by_category: List[CategorySummary] = []
