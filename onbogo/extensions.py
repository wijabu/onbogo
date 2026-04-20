"""Flask extensions initialized once and imported by blueprints."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# In-memory storage is fine for single-worker gunicorn. If we ever scale to
# multiple workers, swap storage_uri to redis:// (each worker counts its own
# requests otherwise, which would multiply the effective rate limit).
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
)
