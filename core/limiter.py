from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize the rate limiter
# Uses in-memory storage by default
# get_remote_address identifies clients by IP
limiter = Limiter(key_func=get_remote_address)

# You can define default limits or named limits here if needed
# e.g., default_limits=["100 per minute"]
# named_limits={"login_limit": "5 per minute"}
