import uvicorn
from core import create_app
from core.config import settings

# Create the FastAPI app instance using the factory function
app = create_app()

if __name__ == "__main__":
    # This block allows running the app directly using `python main.py`
    # Uvicorn is the ASGI server that runs FastAPI
    print(f"Starting Uvicorn server on http://0.0.0.0:8000 (Debug: {settings.DEBUG})")
    uvicorn.run(
        "manage:app",             # Points to the 'app' instance in this 'main.py' file
        host="0.0.0.0",         # Listen on all available network interfaces
        port=8000,              # Standard port for development
        reload=settings.DEBUG,  # Enable auto-reload only when DEBUG is True (for development)
        workers=1               # Use 1 worker for development; adjust for production
    )
