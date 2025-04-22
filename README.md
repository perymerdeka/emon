# Personal Finance Management API

This project provides a backend API for managing personal finances, allowing users to track income and expenses, categorize transactions, set budgets, define recurring transactions, and view reports. It is built using FastAPI, SQLModel, and includes user authentication with JWT. The application supports both synchronous and asynchronous database operations based on configuration.

## Features Implemented

*   **User Management:**
    *   User registration (`/auth/register`) with rate limiting.
    *   User login with JWT (`/auth/token`) - Returns access and refresh tokens, with rate limiting.
    *   Token refresh (`/auth/refresh`).
    *   Get current user profile (`/auth/users/me`).
    *   Change user password (`/auth/users/me/password`).
*   **Category Management:** (Requires Authentication)
    *   CRUD operations for income/expense categories (`/categories/`).
    *   Data scoped per user.
*   **Transaction Management:** (Requires Authentication)
    *   CRUD operations for income/expense transactions (`/transactions/`).
    *   Filtering by date range and category.
    *   Transaction type automatically derived from category.
    *   Data scoped per user.
*   **Budget Management:** (Requires Authentication)
    *   CRUD operations for monthly budgets (`/budgets/`).
    *   Budgets can be overall or category-specific.
    *   Data scoped per user.
*   **Recurring Transaction Rules:** (Requires Authentication)
    *   CRUD operations for defining recurring transaction rules (`/recurring-transactions/`).
    *   Supports daily, weekly, monthly, yearly frequencies.
    *   Rules are scoped per user.
*   **Recurring Transaction Generation:**
    *   Background service (`services/recurring_transaction_service.py`) to generate actual `Transaction` records based on due `RecurringTransaction` rules.
    *   Scheduled execution using `APScheduler` (runs daily by default).
    *   Manual trigger endpoint (`POST /recurring-transactions/generate-due`).
*   **Reporting:** (Requires Authentication)
    *   Generate monthly financial summary (`GET /reports/monthly`).
    *   Generate yearly financial summary (`GET /reports/yearly`).
    *   Generate custom date range summary (`GET /reports/custom`).
    *   Reports include totals and category breakdowns, scoped per user.
*   **Notifications:** (Requires Authentication)
    *   API endpoints (`/notifications/`) to retrieve notifications and mark them as read.
    *   Notifications generated for events like recurring transaction creation (more triggers can be added).
*   **AI Consultation:** (Requires Authentication)
    *   Endpoint (`POST /ai-consultation/`) to ask financial questions to supported AI providers (OpenAI, Gemini, etc.).
    *   *Note: Requires API keys to be configured via environment variables. Service logic is currently placeholder.*
*   **Authentication & Authorization:** JWT-based authentication (Access & Refresh Tokens). Endpoints protected using dependencies. Data access strictly scoped per user.
*   **Database:**
    *   Uses SQLModel for ORM.
    *   Supports SQLite, PostgreSQL, MySQL via `DATABASE_URL` configuration.
    *   Supports **conditional sync/async operation** based on `USE_ASYNC_DB` setting / `DATABASE_URL` prefix.
*   **Migrations:** Alembic configured for database schema management.
*   **Containerization:** Dockerfile and Docker Compose setup. Includes optional PostgreSQL/MySQL services.
*   **Testing:** Expanded test suite using `pytest` and `pytest-asyncio`, covering core features, authentication, and data ownership. Test database setup using fixtures.
*   **Error Handling:** Centralized exception handlers for consistent API error responses.
*   **Rate Limiting:** Basic rate limiting on login/registration endpoints using `slowapi`.

## Technology Stack

*   **Framework:** FastAPI
*   **Database ORM:** SQLModel (combines Pydantic and SQLAlchemy)
*   **Database:** SQLite, PostgreSQL, MySQL (configurable via `DATABASE_URL`)
*   **Migrations:** Alembic
*   **Authentication:** JWT (PyJWT), Password Hashing (Passlib)
*   **Scheduling:** APScheduler
*   **Rate Limiting:** SlowAPI
*   **AI Libraries:** OpenAI, Google GenerativeAI (placeholders for DeepSeek/Mistral)
*   **Testing:** Pytest, Pytest-Asyncio, Pytest-Cov, HTTPX
*   **Containerization:** Docker, Docker Compose
*   **Language:** Python 3.10+
*   **Other:** python-dateutil, pydantic-settings

## Project Structure

```
.
├── .env.example            # Example environment variables
├── .gitignore
├── Dockerfile              # Instructions to build the Docker image
├── docker-compose.yml      # Docker Compose configuration
├── main.py                 # FastAPI application entrypoint
├── manage.py               # (Currently unused)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── alembic.ini             # Alembic configuration
├── alembic/                # Alembic migration environment
│   ├── env.py              # Alembic environment setup
│   ├── script.py.mako      # Migration script template
│   └── versions/           # Migration scripts
│       ├── ...
├── core/                   # Core application logic
│   ├── __init__.py         # App factory (create_app), lifespan, exception handlers
│   ├── config.py           # Application settings (Pydantic Settings)
│   ├── db.py               # Sync/Async DB engines, session management
│   ├── limiter.py          # Rate limiter configuration
│   ├── scheduler.py        # APScheduler setup
│   └── security.py         # Password hashing, JWT handling
├── dto/                    # Data Transfer Objects (Pydantic models for API I/O)
│   ├── __init__.py
│   ├── budget_dto.py
│   ├── category_dto.py
│   ├── recurring_transaction_dto.py
│   ├── report_dto.py
│   ├── token_dto.py
│   ├── transaction_dto.py
│   ├── user_dto.py
│   ├── ai_consultation_dto.py
│   └── notification_dto.py # Added
├── middlewares/            # Custom middleware
│   ├── __init__.py
│   └── auth.py             # Authentication middleware & dependency
├── models/                 # SQLModel database models
│   ├── __init__.py
│   ├── budget_model.py
│   ├── category_model.py
│   ├── recurring_transaction_model.py
│   ├── transaction_model.py
│   ├── user_model.py
│   └── notification_model.py # Added
├── routers/                # API endpoint routers
│   ├── __init__.py
│   ├── auth.py
│   ├── budgets.py
│   ├── categories.py
│   ├── recurring_transactions.py
│   ├── reports.py
│   ├── transactions.py
│   ├── ai_consultation.py
│   └── notifications.py # Added
├── services/               # Business logic services
│   ├── __init__.py
│   ├── recurring_transaction_service.py
│   └── ai_consultation_service.py # Added
└── tests/                  # Unit and integration tests
    ├── __init__.py
    ├── conftest.py         # Pytest fixtures (test client, db session)
    └── routers/
        ├── __init__.py
        ├── test_auth.py
        ├── test_budgets.py
        ├── test_categories.py
        ├── test_recurring_transactions.py
        ├── test_reports.py
        └── test_transactions.py
```

## Setup and Running

### Using Docker (Recommended)

1.  **Prerequisites:** Docker and Docker Compose installed.
2.  **Create `.env` file:** Copy `.env.example` to `.env` (`cp .env.example .env`).
3.  **Configure `.env`:**
    *   **`SECRET_KEY`:** Generate a strong secret key (e.g., `openssl rand -hex 32`) and replace the placeholder.
    *   **`DATABASE_URL`:** Choose your desired database URL (see examples in `.env.example`). Ensure the URL prefix matches sync/async drivers if you also set `USE_ASYNC_DB`.
    *   **`USE_ASYNC_DB` (Optional):** Set to `True` or `False` to explicitly control mode, overriding inference from `DATABASE_URL`.
    *   **AI API Keys:** Set `OPENAI_API_KEY`, `GEMINI_API_KEY`, etc., for the AI providers you intend to use.
    *   **Database Service (If not SQLite):** If using PostgreSQL or MySQL, uncomment the corresponding service (`db_postgres` or `db_mysql`) and `volumes` section in `docker-compose.yml`. Update the database credentials in the `environment` section of the chosen service in `docker-compose.yml` to match your `DATABASE_URL`.
4.  **Install Drivers (If not SQLite):** Uncomment the required database driver(s) (sync and/or async) in `requirements.txt`. Ensure AI libraries (`openai`, `google-generativeai`, etc.) are also installed or uncommented.
5.  **Build and Run:**
    ```bash
    docker-compose up --build -d
    ```
6.  **Apply Migrations (First time or after model changes):**
    ```bash
    docker-compose exec app alembic upgrade head
    ```
7.  **Access API:** `http://localhost:8000`
8.  **API Docs:** `http://localhost:8000/docs`
9.  **Stop:** `docker-compose down`

### Local Development (Optional)

1.  **Prerequisites:** Python 3.10+ and pip installed.
2.  **Create Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    # Ensure necessary DB drivers (sync/async) and bcrypt support are installed
    # e.g., pip install psycopg2-binary asyncpg bcrypt openai google-generativeai
    ```
4.  **Create `.env` file:** Copy `.env.example` to `.env`.
5.  **Configure `.env`:** Set `SECRET_KEY`, `DATABASE_URL`, AI API Keys (e.g., `OPENAI_API_KEY`), and optionally `USE_ASYNC_DB`.
6.  **(Important)** If using SQLite and a `database.db` file exists from previous runs without Alembic, delete it.
7.  **Apply Migrations:**
    ```bash
    alembic upgrade head
    ```
8.  **Run Server:**
    ```bash
    uvicorn main:app --reload --port 8000
    ```
9.  **Access API:** `http://localhost:8000`
10. **API Docs:** `http://localhost:8000/docs`

## API Usage

1.  **Register:** `POST /auth/register`
2.  **Login:** `POST /auth/token` (form data: `username`=email, `password`) -> returns access/refresh tokens.
3.  **Authorize:** Use the `access_token` as a Bearer token in the `Authorization` header for protected endpoints.
4.  **Manage Data:** Use `/categories`, `/transactions`, `/budgets`, `/recurring-transactions` endpoints.
5.  **View Reports:** Use `/reports/monthly`, `/reports/yearly`, `/reports/custom`.
6.  **Refresh Token:** `POST /auth/refresh` (send `refresh_token` as Bearer token) -> returns new access/refresh tokens.
7.  **View Profile:** `GET /auth/users/me`
8.  **Change Password:** `PUT /auth/users/me/password`

## Testing

1.  **Prerequisites:** Install test dependencies (`pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` - included in `requirements.txt`).
2.  **Run Tests:** From the project root directory:
    ```bash
    # Ensure USE_ASYNC_DB is set appropriately in your environment or .env
    # if you want to test a specific mode. Tests adapt automatically.
    pytest -v
    ```
3.  **Run Tests with Coverage:**
    ```bash
    pytest --cov=core --cov=routers --cov=services --cov=middlewares --cov-report=term-missing -v
    ```

## Future Development Plan

*   **Deployment:** Add configurations/scripts for deploying to cloud platforms (e.g., Docker Swarm, Kubernetes, Serverless). Add production-ready Uvicorn/Gunicorn settings.
*   **Async Test Refinement:** Improve async test fixtures and potentially parameterize tests to explicitly run against both sync/async modes if needed.
*   **Recurring Transaction Generation Robustness:**
    *   Implement locking or idempotency checks in `generate_due_transactions` if multiple instances could run concurrently.
    *   Add more sophisticated error handling and potentially deactivate rules that consistently fail (e.g., due to deleted categories).
*   **Notifications:**
    *   Implement more notification triggers (budget warnings/exceeded, bill reminders).
    *   Add delivery mechanisms (email, push notifications via services like Firebase Cloud Messaging).
*   **Budget vs. Actual Reporting:** Enhance reports to show budget amounts alongside actual income/expenses for the period.
*   **User Profile:** Add endpoint to update user details (e.g., email - requires verification flow).
*   **Security Hardening:** Implement refresh token rotation, review input validation, consider security headers.
*   **Comprehensive Testing:** Add more edge case tests, unit tests for complex logic (like date calculations in recurring service).
