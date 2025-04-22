from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware # Optional: Add CORS if needed
from contextlib import asynccontextmanager # Import for lifespan

# Import individual routers directly
from routers import auth, categories, reports, transactions, budgets, recurring_transactions, ai_consultation, notifications # Add notifications
from middlewares.auth import AuthMiddleware # Import the auth middleware
from core.config import settings # Import settings
# from core.db import init_db # No longer needed if handled by Alembic
from core.limiter import limiter, RateLimitExceeded, _rate_limit_exceeded_handler
# Import scheduler functions
from core.scheduler import start_scheduler, shutdown_scheduler

# --- Lifespan Context Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Application startup...")
    # Start the scheduler
    await start_scheduler()
    yield
    # Shutdown logic
    print("Application shutdown...")
    # Shutdown the scheduler
    await shutdown_scheduler()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Personal Finance Manager API",
        description="API for managing personal finances, including categories and transactions.",
        version="0.1.0", # Add a version
            debug=settings.DEBUG,
            lifespan=lifespan # Add lifespan context manager
        )

    # --- Add Middleware ---
    # AuthMiddleware should be added before routes that need protection
    app.add_middleware(AuthMiddleware)

    # Optional: Add CORS middleware if your frontend is on a different origin
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=["*"], # Allow all origins (adjust for production)
    #     allow_credentials=True,
    #     allow_methods=["*"], # Allow all methods
    #     allow_headers=["*"], # Allow all headers
    # )


    # Optional: Add startup event to initialize DB
    # REMOVED: Database creation is now handled by Alembic migrations
    # @app.on_event("startup")
    # def on_startup():
    #     print("Running startup event: Initializing database...")
    #     init_db() # init_db function in core/db.py likely calls create_all
    #     print("Database initialization complete.")

    # Include individual routers with prefixes
    # No longer using the /api/v1 prefix as per user feedback
    app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    app.include_router(categories.router, prefix="/categories", tags=["Categories"])
    app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
    app.include_router(reports.router, prefix="/reports", tags=["Reports"])
    app.include_router(budgets.router, prefix="/budgets", tags=["Budgets"])
    app.include_router(recurring_transactions.router, prefix="/recurring-transactions", tags=["Recurring Transactions"])
    app.include_router(ai_consultation.router, prefix="/ai-consultation", tags=["AI Consultation"])
    app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"]) # Add Notifications router

    # Add a simple root endpoint for health check or welcome message
    @app.get("/", tags=["Root"])
    def read_root():
        return {"message": "Welcome to the Personal Finance API"}

    # Add limiter state to the app
    app.state.limiter = limiter
    # Add the default rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


     # --- Custom Exception Handlers ---

    # Handler for FastAPI/Starlette HTTPExceptions
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    # Handler for Pydantic Validation Errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # You can customize the error response format here
        errors = []
        for error in exc.errors():
            errors.append({"loc": error["loc"], "msg": error["msg"], "type": error["type"]})
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation Error", "errors": errors},
        )

# Optional: Handler for generic Python Exceptions (use with caution)
# @app.exception_handler(Exception)
# async def generic_exception_handler(request: Request, exc: Exception):
#     # Log the exception for debugging
#     print(f"Unhandled exception: {exc}") # Replace with proper logging
#     return JSONResponse(
#         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         content={"detail": "An internal server error occurred."},
#     )


    return app
