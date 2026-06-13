"""
Shared pytest configuration.

Sets stub environment variables so that api.config.Settings can initialise
without a real .env file. This must run before any api.* imports.
"""
import os

# Set required env vars before any api.* module is imported.
# These are stubs — real values only matter for production.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("RAZORPAY_KEY_ID", "test-rzp-id")
os.environ.setdefault("RAZORPAY_KEY_SECRET", "test-rzp-secret")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
