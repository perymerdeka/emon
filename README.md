# Personal Finance Management API

This project provides a robust backend API designed to empower users with comprehensive control over their personal finances. It offers a suite of features for meticulous tracking of income and expenses, intelligent categorization of transactions, proactive budget setting, automated recurring transaction management, and insightful financial reporting. Built upon the solid foundation of FastAPI and SQLModel, the API ensures high performance and maintainability. User authentication is implemented using JWT, providing secure access to personalized financial data. The application is engineered to support both synchronous and asynchronous database operations, adapting to different deployment environments and scaling requirements. This API is ideal for individuals seeking a powerful tool to gain a deeper understanding of their financial habits and make informed decisions to achieve their financial goals.

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
    *   **`SECRET_KEY`:** Generate a strong secret key (e.g., `openssl rand -hex 32`) and replace the placeholder. This key is used for JWT token generation and should be kept secret. You can generate a key using `openssl rand -hex 32`.
    *   **`DATABASE_URL`:** Specify the database connection string. Examples are provided in `.env.example` for SQLite, PostgreSQL, and MySQL.
        *   **SQLite:** `sqlite:///./database.db` (for synchronous) or `sqlite+aiosqlite:///./database.db` (for asynchronous).
        *   **PostgreSQL:** `postgresql+asyncpg://user:password@host:port/database` (asynchronous) or `postgresql+psycopg2://user:password@host:port/database` (synchronous).
        *   **MySQL:** `mysql+asyncmy://user:password@host:port/database` (asynchronous) or `mysql+pymysql://user:password@host:port/database` (synchronous).
    *   **`USE_ASYNC_DB` (Optional):** Set to `True` to use asynchronous database operations or `False` for synchronous operations. If not set, the application will attempt to infer this from the `DATABASE_URL` prefix (e.g., `asyncpg` in the URL implies asynchronous). Explicitly setting this is recommended for clarity.
    *   **AI API Keys:** Configure API keys for the AI providers you wish to use.
        *   **`OPENAI_API_KEY`:** API key for OpenAI.
        *   **`GEMINI_API_KEY`:** API key for Google Gemini.
        *   ... (Add other AI provider keys as needed)
    *   **Database Service (If not SQLite):** If using PostgreSQL or MySQL, ensure the corresponding service (`db_postgres` or `db_mysql`) is uncommented and properly configured in `docker-compose.yml`. Update the database credentials in the `environment` section of the chosen service in `docker-compose.yml` to match your `DATABASE_URL`. The database host should be set to the service name (e.g., `db_postgres` or `db_mysql`).
4.  **Install Drivers (If not SQLite):** Ensure the necessary database drivers (synchronous and/or asynchronous) are installed. If using Docker, these are already included in the image. If developing locally, install them using pip. Also, ensure AI libraries (`openai`, `google-generativeai`, etc.) are installed if you intend to use the AI consultation feature.
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

## API Endpoints

Below is a detailed list of available API endpoints.

**Authentication (`/auth`)**

*   **`POST /register`**
    *   **Description:** Register a new user.
    *   **Auth:** None
    *   **Rate Limit:** Yes (e.g., 10/minute)
    *   **Request Body:** `UserCreate` (email, password)
        ```json
        {
          "email": "user@example.com",
          "password": "yoursecurepassword"
        }
        ```
    *   **Response:** `UserRead` (id, email, is_active)
        ```json
        {
          "id": 1,
          "email": "user@example.com",
          "is_active": true
        }
        ```

*   **`POST /token`**
    *   **Description:** Authenticate user and return JWT tokens.
    *   **Auth:** None
    *   **Rate Limit:** Yes (e.g., 5/minute)
    *   **Request Body:** Form data (`username`=email, `password`)
    *   **Response:** `Token` (access_token, refresh_token, token_type)
        ```json
        {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "token_type": "bearer"
        }
        ```

*   **`POST /refresh`**
    *   **Description:** Exchange a refresh token for a new access token.
    *   **Auth:** Requires valid Refresh Token in `Authorization: Bearer <refresh_token>` header.
    *   **Response:** `Token` (new access_token, original refresh_token, token_type)
        ```json
        {
          "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
          "token_type": "bearer"
        }
        ```

*   **`GET /users/me`**
    *   **Description:** Fetch the current logged-in user's profile.
    *   **Auth:** Requires valid Access Token.
    *   **Response:** `UserRead` (id, email, is_active)
        ```json
        {
          "id": 1,
          "email": "user@example.com",
          "is_active": true
        }
        ```

*   **`PUT /users/me/password`**
    *   **Description:** Update the current logged-in user's password.
    *   **Auth:** Requires valid Access Token.
    *   **Request Body:** `UserPasswordUpdate` (current_password, new_password)
        ```json
        {
          "current_password": "yourcurrentpassword",
          "new_password": "yournewsecurepassword"
        }
        ```
    *   **Response:** `204 No Content`
        *(No content is returned on success)*

**Categories (`/categories`)**

*All endpoints require authentication (Access Token).*

*   **`POST /`**
    *   **Description:** Create a new category.
    *   **Request Body:** `CategoryBase` (name, description, type: "INCOME" | "EXPENSE")
        ```json
        {
          "name": "Salary",
          "description": "Monthly income",
          "type": "INCOME"
        }
        ```
    *   **Response:** `CategoryRead` (id, name, description, type, owner_id)
        ```json
        {
          "id": 1,
          "name": "Salary",
          "description": "Monthly income",
          "type": "INCOME",
          "owner_id": 1
        }
        ```

*   **`GET /`**
    *   **Description:** Retrieve categories for the current user.
    *   **Query Params:** `skip` (int, default 0), `limit` (int, default 100)
    *   **Response:** `List[CategoryRead]`
        ```json
        [
          {
            "id": 1,
            "name": "Salary",
            "description": "Monthly income",
            "type": "INCOME",
            "owner_id": 1
          },
          {
            "id": 2,
            "name": "Groceries",
            "description": "Weekly expenses",
            "type": "EXPENSE",
            "owner_id": 1
          }
        ]
        ```

*   **`GET /{category_id}`**
    *   **Description:** Retrieve a specific category by ID.
    *   **Path Param:** `category_id` (int)
    *   **Response:** `CategoryRead`
        ```json
        {
          "id": 1,
          "name": "Salary",
          "description": "Monthly income",
          "type": "INCOME",
          "owner_id": 1
        }
        ```

*   **`PUT /{category_id}`**
    *   **Description:** Update an existing category.
    *   **Path Param:** `category_id` (int)
    *   **Request Body:** `CategoryBase`
        ```json
        {
          "name": "Main Salary",
          "description": "Main monthly income",
          "type": "INCOME"
        }
        ```
    *   **Response:** `CategoryRead`
        ```json
        {
          "id": 1,
          "name": "Main Salary",
          "description": "Main monthly income",
          "type": "INCOME",
          "owner_id": 1
        }
        ```

*   **`DELETE /{category_id}`**
    *   **Description:** Delete a category.
    *   **Path Param:** `category_id` (int)
    *   **Response:** `204 No Content`
        *(No content is returned on success)*

**Transactions (`/transactions`)**

*All endpoints require authentication (Access Token).*

*   **`POST /`**
    *   **Description:** Create a new transaction.
    *   **Request Body:** `TransactionBase` (date, amount, description, category_id)
        ```json
        {
          "date": "2024-04-24",
          "amount": 55.75,
          "description": "Weekly groceries",
          "category_id": 1
        }
        ```
    *   **Response:** `TransactionRead` (id, date, amount, description, type, category_id, owner_id)
        ```json
        {
          "id": 1,
          "date": "2024-04-24",
          "amount": 55.75,
          "description": "Weekly groceries",
          "type": "EXPENSE",
          "category_id": 1,
          "owner_id": 1
        }
        ```

*   **`GET /`**
    *   **Description:** Retrieve transactions for the current user.
    *   **Query Params:** `skip` (int, default 0), `limit` (int, default 100), `start_date` (date, optional), `end_date` (date, optional), `category_id` (int, optional)
    *   **Response:** `List[TransactionReadWithCategory]` (includes category details)
        ```json
        [
          {
            "id": 1,
            "date": "2024-04-24",
            "amount": 55.75,
            "description": "Weekly groceries",
            "type": "EXPENSE",
            "category_id": 1,
            "owner_id": 1,
            "category": {
              "id": 1,
              "name": "Groceries",
              "description": "Weekly expenses",
              "type": "EXPENSE",
              "owner_id": 1
            }
          },
          {
            "id": 2,
            "date": "2024-04-23",
            "amount": 2000.00,
            "description": "Monthly salary",
            "type": "INCOME",
            "category_id": 2,
            "owner_id": 1,
            "category": {
              "id": 2,
              "name": "Salary",
              "description": "Monthly income",
              "type": "INCOME",
              "owner_id": 1
            }
          }
        ]
        ```

*   **`GET /{transaction_id}`**
    *   **Description:** Retrieve a specific transaction by ID.
    *   **Path Param:** `transaction_id` (int)
    *   **Response:** `TransactionReadWithCategory`
        ```json
        {
          "id": 1,
          "date": "2024-04-24",
          "amount": 55.75,
          "description": "Weekly groceries",
          "type": "EXPENSE",
          "category_id": 1,
          "owner_id": 1,
          "category": {
            "id": 1,
            "name": "Groceries",
            "description": "Weekly expenses",
            "type": "EXPENSE",
            "owner_id": 1
          }
        }
        ```

*   **`PUT /{transaction_id}`**
    *   **Description:** Update an existing transaction.
    *   **Path Param:** `transaction_id` (int)
    *   **Request Body:** `TransactionBase`
        ```json
        {
          "date": "2024-04-25",
          "amount": 60.00,
          "description": "Weekly groceries",
          "category_id": 1
        }
        ```
    *   **Response:** `TransactionRead`
        ```json
        {
          "id": 1,
          "date": "2024-04-25",
          "amount": 60.00,
          "description": "Weekly groceries",
          "type": "EXPENSE",
          "category_id": 1,
          "owner_id": 1
        }
        ```

*   **`DELETE /{transaction_id}`**
    *   **Description:** Delete a transaction.
    *   **Path Param:** `transaction_id` (int)
    *   **Response:** `204 No Content`
        *(No content is returned on success)*

**Reports (`/reports`)**

*All endpoints require authentication (Access Token).*

*   **`GET /monthly`**
    *   **Description:** Generates a financial report for a specific month and year.
    *   **Query Params:** `year` (int, required), `month` (int, required, 1-12)
        *   Example: `?year=2024&month=4`
    *   **Response:** `MonthlyReport` (totals, net balance, category breakdowns)
        ```json
        {
          "totals": {
            "income": 2000.00,
            "expenses": 1000.00,
            "net_balance": 1000.00
          },
          "category_breakdowns": [
            {
              "category_name": "Salary",
              "income": 2000.00,
              "expenses": 0.00
            },
            {
              "category_name": "Groceries",
              "income": 0.00,
              "expenses": 500.00
            },
            {
              "category_name": "Rent",
              "income": 0.00,
              "expenses": 500.00
            }
          ]
        }
        ```

*   **`GET /yearly`**
    *   **Description:** Generates a financial report for a specific year.
    *   **Query Params:** `year` (int, required)
        *   Example: `?year=2024`
    *   **Response:** `YearlyReport` (totals, net balance, category breakdowns)
        ```json
        {
          "totals": {
            "income": 24000.00,
            "expenses": 12000.00,
            "net_balance": 12000.00
          },
          "category_breakdowns": [
            {
              "category_name": "Salary",
              "income": 24000.00,
              "expenses": 0.00
            },
            {
              "category_name": "Groceries",
              "income": 0.00,
              "expenses": 6000.00
            },
            {
              "category_name": "Rent",
              "income": 0.00,
              "expenses": 6000.00
            }
          ]
        }
        ```

*   **`GET /custom`**
    *   **Description:** Generates a financial report for a custom date range.
    *   **Query Params:** `start_date` (date, required), `end_date` (date, required)
        *   Example: `?start_date=2024-01-01&end_date=2024-03-31`
    *   **Response:** `DateRangeReport` (totals, net balance, category breakdowns)
        ```json
        {
          "totals": {
            "income": 6000.00,
            "expenses": 3000.00,
            "net_balance": 3000.00
          },
          "category_breakdowns": [
            {
              "category_name": "Salary",
              "income": 6000.00,
              "expenses": 0.00
            },
            {
              "category_name": "Groceries",
              "income": 0.00,
              "expenses": 1500.00
            },
            {
              "category_name": "Rent",
              "income": 0.00,
              "expenses": 1500.00
            }
          ]
        }
        ```

**Budgets (`/budgets`)**

*All endpoints require authentication (Access Token).*

*   **`POST /`**
    *   **Description:** Create a new budget for a specific month (and optionally category).
    *   **Request Body:** `BudgetCreate` (year, month, amount, category_id: optional)
        ```json
        {
          "year": 2024,
          "month": 4,
          "amount": 500.00,
          "category_id": 1
        }
        ```
    *   **Response:** `BudgetRead` (id, year, month, amount, category_id, owner_id)
        ```json
        {
          "id": 1,
          "year": 2024,
          "month": 4,
          "amount": 500.00,
          "category_id": 1,
          "owner_id": 1
        }
        ```

*   **`GET /`**
    *   **Description:** Retrieve budgets for the current user.
    *   **Query Params:** `skip` (int, default 0), `limit` (int, default 100), `year` (int, optional), `month` (int, optional), `category_id` (int, optional)
    *   **Response:** `List[BudgetRead]`
        ```json
        [
          {
            "id": 1,
            "year": 2024,
            "month": 4,
            "amount": 500.00,
            "category_id": 1,
            "owner_id": 1
          },
          {
            "id": 2,
            "year": 2024,
            "month": 5,
            "amount": 1000.00,
            "category_id": null,
            "owner_id": 1
          }
        ]
        ```

*   **`GET /{budget_id}`**
    *   **Description:** Retrieve a specific budget by ID.
    *   **Path Param:** `budget_id` (int)
    *   **Response:** `BudgetRead`
        ```json
        {
          "id": 1,
          "year": 2024,
          "month": 4,
          "amount": 500.00,
          "category_id": 1,
          "owner_id": 1
        }
        ```

*   **`PUT /{budget_id}`**
    *   **Description:** Update an existing budget.
    *   **Path Param:** `budget_id` (int)
    *   **Request Body:** `BudgetCreate`
        ```json
        {
          "year": 2024,
          "month": 4,
          "amount": 600.00,
          "category_id": 1
        }
        ```
    *   **Response:** `BudgetRead`
        ```json
        {
          "id": 1,
          "year": 2024,
          "month": 4,
          "amount": 600.00,
          "category_id": 1,
          "owner_id": 1
        }
        ```

*   **`DELETE /{budget_id}`**
    *   **Description:** Delete a budget.
    *   **Path Param:** `budget_id` (int)
    *   **Response:** `204 No Content`
        *(No content is returned on success)*

**Recurring Transactions (`/recurring-transactions`)**

*All endpoints require authentication (Access Token).*

*   **`POST /`**
    *   **Description:** Create a new recurring transaction rule.
    *   **Request Body:** `RecurringTransactionCreate` (description, amount, category_id, frequency, interval, start_date, end_date: optional, day_of_month: optional, day_of_week: optional, is_active: optional)
        ```json
        {
          "description": "Monthly Subscription",
          "amount": 15.00,
          "category_id": 10,
          "frequency": "MONTHLY",
          "interval": 1,
          "start_date": "2024-05-15",
          "day_of_month": 15,
          "is_active": true
        }
        ```
    *   **Response:** `RecurringTransactionRead` (includes id, owner_id, last_created_date)
        ```json
        {
          "id": 1,
          "owner_id": 1,
          "description": "Monthly Subscription",
          "amount": 15.00,
          "category_id": 10,
          "frequency": "MONTHLY",
          "interval": 1,
          "start_date": "2024-05-15",
          "end_date": null,
          "day_of_month": 15,
          "day_of_week": null,
          "is_active": true,
          "last_created_date": null
        }
        ```

*   **`GET /`**
    *   **Description:** Retrieve recurring transaction rules for the current user.
    *   **Query Params:** `skip` (int, default 0), `limit` (int, default 100), `is_active` (bool, optional)
    *   **Response:** `List[RecurringTransactionRead]`
        ```json
        [
          {
            "id": 1,
            "owner_id": 1,
            "description": "Monthly Subscription",
            "amount": 15.00,
            "category_id": 10,
            "frequency": "MONTHLY",
            "interval": 1,
            "start_date": "2024-05-15",
            "end_date": null,
            "day_of_month": 15,
            "day_of_week": null,
            "is_active": true,
            "last_created_date": null
          },
          {
            "id": 2,
            "owner_id": 1,
            "description": "Weekly Groceries",
            "amount": 50.00,
            "category_id": 1,
            "frequency": "WEEKLY",
            "interval": 1,
            "start_date": "2024-05-01",
            "end_date": null,
            "day_of_month": null,
            "day_of_week": "MONDAY",
            "is_active": true,
            "last_created_date": "2024-04-29"
          }
        ]
        ```

*   **`GET /{recurring_tx_id}`**
    *   **Description:** Retrieve a specific recurring transaction rule by ID.
    *   **Path Param:** `recurring_tx_id` (int)
    *   **Response:** `RecurringTransactionRead`
        ```json
        {
          "id": 1,
          "owner_id": 1,
          "description": "Monthly Subscription",
          "amount": 15.00,
          "category_id": 10,
          "frequency": "MONTHLY",
          "interval": 1,
          "start_date": "2024-05-15",
          "end_date": null,
          "day_of_month": 15,
          "day_of_week": null,
          "is_active": true,
          "last_created_date": null
        }
        ```

*   **`PUT /{recurring_tx_id}`**
    *   **Description:** Update an existing recurring transaction rule.
    *   **Path Param:** `recurring_tx_id` (int)
    *   **Request Body:** `RecurringTransactionCreate`
        ```json
        {
          "description": "Monthly Subscription",
          "amount": 16.00,
          "category_id": 10,
          "frequency": "MONTHLY",
          "interval": 1,
          "start_date": "2024-05-15",
          "day_of_month": 15,
          "is_active": true
        }
        ```
    *   **Response:** `RecurringTransactionRead`
        ```json
        {
          "id": 1,
          "owner_id": 1,
          "description": "Monthly Subscription",
          "amount": 16.00,
          "category_id": 10,
          "frequency": "MONTHLY",
          "interval": 1,
          "start_date": "2024-05-15",
          "end_date": null,
          "day_of_month": 15,
          "day_of_week": null,
          "is_active": true,
          "last_created_date": null
        }
        ```

*   **`DELETE /{recurring_tx_id}`**
    *   **Description:** Delete a recurring transaction rule.
    *   **Path Param:** `recurring_tx_id` (int)
    *   **Response:** `204 No Content`
        *(No content is returned on success)*

*   **`POST /generate-due`**
    *   **Description:** Manually triggers the generation of due recurring transactions (runs in background).
    *   **Query Params:** `run_date_str` (str, optional, YYYY-MM-DD)
    *   **Response:** `202 Accepted` with `{"message": "Recurring transaction generation task accepted."}`
        ```json
        {
          "message": "Recurring transaction generation task accepted."
        }
        ```

**AI Consultation (`/ai-consultation`)**

*Requires authentication (Access Token).*

*   **`POST /`**
    *   **Description:** Ask financial questions to a selected AI provider.
    *   **Request Body:** `AIConsultationRequest` (provider: "openai" | "gemini" | ..., query, financial_context: optional)
        ```json
        {
          "provider": "openai",
          "query": "What are some strategies to save more money?",
          "financial_context": "Optional summary"
        }
        ```
    *   **Response:** `AIConsultationResponse` (provider, query, response)
        ```json
        {
          "provider": "openai",
          "query": "What are some strategies to save more money?",
          "response": "Some strategies to save more money include creating a budget, tracking your expenses, and setting financial goals."
        }
        ```

**Notifications (`/notifications`)**

*All endpoints require authentication (Access Token).*

*   **`GET /`**
    *   **Description:** Retrieve notifications for the current user.
    *   **Query Params:** `skip` (int, default 0), `limit` (int, default 100, max 200), `is_read` (bool, optional)
    *   **Response:** `List[NotificationRead]` (id, user_id, message, is_read, created_at)
        ```json
        [
          {
            "id": 1,
            "user_id": 1,
            "message": "Recurring transaction 'Monthly Subscription' created.",
            "is_read": false,
            "created_at": "2024-04-30T08:00:00"
          },
          {
            "id": 2,
            "user_id": 1,
            "message": "Budget 'Groceries' exceeded.",
            "is_read": false,
            "created_at": "2024-04-30T09:00:00"
          }
        ]
        ```

*   **`PATCH /{notification_id}`**
    *   **Description:** Mark a specific notification as read or unread.
    *   **Path Param:** `notification_id` (int)
    *   **Request Body:** `NotificationUpdate` (is_read: bool)
        ```json
        {
          "is_read": true
        }
        ```
    *   **Response:** `NotificationRead`
        ```json
        {
          "id": 1,
          "user_id": 1,
          "message": "Recurring transaction 'Monthly Subscription' created.",
          "is_read": true,
          "created_at": "2024-04-30T08:00:00"
        }
        ```

*   **`POST /mark-all-read`**
    *   **Description:** Mark all unread notifications for the current user as read.
    *   **Response:** `204 No Content`
        *(No content is returned on success)*

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

## Database Schema

The application uses SQLModel to define the database schema. The following tables are defined:

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
