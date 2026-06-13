"""
FastAPI Application Factory

Creates and configures the FastAPI application for the REST API.
Includes security features: rate limiting, API key auth, CORS, security headers.
"""

import logging
import os
import time
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Security, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.security import APIKeyHeader
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from ..config import (
    CORS_ORIGINS,
    ENABLE_CORS,
    ENABLE_METRICS,
    RATE_LIMIT_PER_IP,
    RATE_LIMIT_WINDOW_SECONDS,
)
from .routes import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
API_KEY_HEADER_NAME = os.getenv("API_KEY_HEADER", "X-API-Key")
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
PLACEHOLDER_API_KEYS = {"dev-key-12345", "your-production-key-here", "changeme", "change-me"}
PUBLIC_PATHS = {"/", "/health", "/api/v1/health"}
MAX_RATE_LIMIT_KEYS = int(os.getenv("RATE_LIMIT_MAX_KEYS", "10000"))

# Bounded in-process rate limiting storage. For multi-worker deployments, configure
# only trusted proxy headers and keep this as a per-process backstop; production
# platforms should still enforce shared edge/app-level limits where available.
_rate_limit_storage: Dict[str, List[float]] = OrderedDict()
_redis_rate_limit_client = None


def is_dev_mode() -> bool:
    """Return whether local development mode is enabled."""
    return os.getenv("DEV_MODE", "false").lower() == "true"


def get_valid_api_keys() -> List[str]:
    """Load API keys from the environment without falling back to defaults."""
    return [
        key.strip()
        for key in os.getenv("VALID_API_KEYS", "").split(",")
        if key.strip()
    ]


def validate_auth_configuration() -> None:
    """Fail fast if a non-development deployment lacks real API keys."""
    if is_dev_mode():
        logger.warning("DEV_MODE=true: API key authentication is optional")
        return

    keys = get_valid_api_keys()
    invalid_keys = [key for key in keys if key in PLACEHOLDER_API_KEYS]
    if not keys or invalid_keys:
        raise RuntimeError(
            "VALID_API_KEYS must contain at least one non-placeholder key when "
            "DEV_MODE is not true"
        )


def get_rate_limit_redis_url() -> str:
    """Return the configured shared rate-limit store URL, if any."""
    return os.getenv("RATE_LIMIT_REDIS_URL") or os.getenv("REDIS_URL", "")


def validate_rate_limit_configuration() -> None:
    """Require shared rate limiting for non-development deployments unless explicitly waived."""
    if is_dev_mode():
        return

    if get_rate_limit_redis_url():
        try:
            client = get_redis_rate_limit_client()
            if client is not None:
                client.ping()
        except Exception as exc:
            raise RuntimeError(
                "Configured Redis rate-limit store is unavailable"
            ) from exc
        return

    if os.getenv("ALLOW_IN_MEMORY_RATE_LIMIT", "false").lower() == "true":
        logger.warning(
            "ALLOW_IN_MEMORY_RATE_LIMIT=true: using per-process rate limits; "
            "configure RATE_LIMIT_REDIS_URL/REDIS_URL before production traffic"
        )
        return

    raise RuntimeError(
        "RATE_LIMIT_REDIS_URL or REDIS_URL is required when DEV_MODE is not true; "
        "set ALLOW_IN_MEMORY_RATE_LIMIT=true only for non-production smoke tests"
    )


def get_redis_rate_limit_client():
    """Create a Redis client lazily when a shared rate-limit store is configured."""
    global _redis_rate_limit_client

    redis_url = get_rate_limit_redis_url()
    if not redis_url:
        return None

    if _redis_rate_limit_client is None:
        import redis

        _redis_rate_limit_client = redis.Redis.from_url(
            redis_url, socket_connect_timeout=1, socket_timeout=1
        )

    return _redis_rate_limit_client


def get_client_ip(request: Request) -> str:
    """Resolve the rate-limit key, optionally honoring trusted proxy headers."""
    if os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true":
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For is a comma-separated chain; the first value is the
            # original client according to trusted reverse proxies.
            return forwarded_for.split(",", 1)[0].strip() or "unknown"

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip() or "unknown"

    return request.client.host if request.client else "unknown"


def _prune_rate_limit_storage(current_time: float, window: int) -> None:
    """Drop expired and excess client entries to bound memory use."""
    stale_keys = []
    for client_ip, timestamps in _rate_limit_storage.items():
        fresh = [timestamp for timestamp in timestamps if current_time - timestamp < window]
        if fresh:
            _rate_limit_storage[client_ip] = fresh
        else:
            stale_keys.append(client_ip)

    for client_ip in stale_keys:
        _rate_limit_storage.pop(client_ip, None)

    while len(_rate_limit_storage) > MAX_RATE_LIMIT_KEYS:
        _rate_limit_storage.pop(next(iter(_rate_limit_storage)))


def check_rate_limit(client_ip: str) -> bool:
    """
    Check if client IP has exceeded rate limit.

    Args:
        client_ip: Client IP address

    Returns:
        True if request is allowed, False if rate limited
    """
    current_time = time.time()
    window = RATE_LIMIT_WINDOW_SECONDS
    max_requests = RATE_LIMIT_PER_IP

    redis_client = get_redis_rate_limit_client()
    if redis_client is not None:
        try:
            key = f"rate-limit:{client_ip}"
            window_start = current_time - window
            request_member = f"{current_time}:{uuid.uuid4().hex}"
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {request_member: current_time})
            pipe.zcard(key)
            pipe.expire(key, window)
            _, _, request_count, _ = pipe.execute()
            return request_count <= max_requests
        except Exception as exc:
            logger.exception("Redis rate-limit check failed")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate-limit service unavailable",
            ) from exc

    _prune_rate_limit_storage(current_time, window)
    timestamps = _rate_limit_storage.setdefault(client_ip, [])

    # Check limit
    if len(timestamps) >= max_requests:
        return False

    # Record this request
    timestamps.append(current_time)
    if isinstance(_rate_limit_storage, OrderedDict):
        _rate_limit_storage.move_to_end(client_ip)
    return True


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> str:
    """
    Verify API key for authentication.

    In development mode (DEV_MODE=true), API key is optional.
    In production, valid API key is required for all endpoints.
    """
    dev_mode = is_dev_mode()

    if dev_mode and not api_key:
        return "dev-mode"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key not in get_valid_api_keys():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    logger.info("🚀 World Cup Betting Insights API starting...")

    # Log security configuration
    logger.info(
        f"🔒 Rate limiting: {RATE_LIMIT_PER_IP} req/{RATE_LIMIT_WINDOW_SECONDS}s"
    )
    logger.info(f"🔒 CORS enabled: {ENABLE_CORS}")
    validate_auth_configuration()
    validate_rate_limit_configuration()
    logger.info(
        f"🔒 API Key auth: {'optional in dev mode' if is_dev_mode() else 'enabled'}"
    )
    logger.info(f"📊 Metrics enabled: {ENABLE_METRICS}")

    try:
        try:
            from predictors.data_loader import DataLoader
        except ImportError:
            from src.predictors.data_loader import DataLoader

        DataLoader()  # Initialize cache
        logger.info("✅ Database cache initialized")
    except Exception as e:
        logger.warning(f"⚠️  Database initialization skipped: {e}")

    yield

    logger.info("👋 World Cup Betting Insights API shutting down...")


def create_app(
    title: str = "World Cup Betting Insights API",
    description: str = """
## 🏆 World Cup Betting Insights API

Find value bets for World Cup matches by comparing AI predictions against odds from Portuguese licensed betting sites.

### Features

- **Match Predictions**: AI-powered win/draw/loss probabilities
- **Value Bet Detection**: Identify bets with positive expected value (EV)
- **Multi-Bookmaker Analysis**: Compare odds across Betano, Betclic, Solverde, and more
- **REST API**: Full RESTful API for integration
- **Python Library**: Import and use programmatically in your projects

### Portuguese Licensed Operators

All integrated bookmakers are licensed by SRIJ (Portuguese Gambling Authority):
- Betano.pt
- Betclic.pt
- Esc Online
- Solverde.pt
- Placard.pt

### ⚠️ Responsible Gambling

This API provides insights only. No guaranteed wins.
You must be 18+ to gamble in Portugal.

**Help**: https://www.srij.turismodeportugal.pt/

### 🔒 Security

- API Key authentication required (X-API-Key header)
- Rate limiting: 100 requests per minute per IP
- CORS configured for allowed origins only
- Security headers enabled
    """,
    version: str = "0.1.0",
    debug: bool = False,
    docs_url: str = "/docs",
    redoc_url: str = "/redoc",
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        title: API title
        description: API description (supports Markdown)
        version: API version
        debug: Enable debug mode
        docs_url: URL for Swagger UI docs
        redoc_url: URL for ReDoc docs

    Returns:
        Configured FastAPI application
    """

    app = FastAPI(
        title=title,
        description=description,
        version=version,
        debug=debug,
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,
        openapi_tags=[
            {
                "name": "Health",
                "description": "Health check and system status",
            },
            {
                "name": "Predictions",
                "description": "Match prediction and analysis endpoints",
            },
            {
                "name": "Scanning",
                "description": "Scan multiple matches for value bets",
            },
            {
                "name": "Configuration",
                "description": "API and bookmaker configuration",
            },
        ],
    )

    # Add CORS middleware (configurable)
    if ENABLE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", API_KEY_HEADER_NAME],
            expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
            max_age=600,
        )

    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Rate limit headers
        client_ip = get_client_ip(request)
        remaining = max(
            0, RATE_LIMIT_PER_IP - len(_rate_limit_storage.get(client_ip, []))
        )
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_PER_IP)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    # Add API authentication middleware
    @app.middleware("http")
    async def api_auth_middleware(request: Request, call_next):
        """Require API-key authentication for protected API endpoints."""
        path = request.url.path
        protected_path = path.startswith("/api/v1/") or path == "/metrics"

        if protected_path and path not in PUBLIC_PATHS:
            api_key = request.headers.get(API_KEY_HEADER_NAME)
            try:
                await verify_api_key(api_key)
            except HTTPException as exc:
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail},
                    headers=exc.headers,
                )

        return await call_next(request)

    # Add rate limiting middleware
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """Apply rate limiting to all requests."""
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/api/v1/health", "/", "/metrics"]:
            return await call_next(request)

        client_ip = get_client_ip(request)

        try:
            rate_limit_allowed = check_rate_limit(client_ip)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=exc.headers,
            )

        if not rate_limit_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RateLimitExceeded",
                    "message": f"Rate limit exceeded. Max {RATE_LIMIT_PER_IP}/{RATE_LIMIT_WINDOW_SECONDS}s.",
                    "code": "RATE_LIMIT_EXCEEDED",
                },
                headers={
                    "Retry-After": str(RATE_LIMIT_WINDOW_SECONDS),
                },
            )

        return await call_next(request)

    # Register routes
    app.include_router(api_router)

    # Add exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle validation errors with detailed response"""
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": "ValidationError",
                "message": "Request validation failed",
                "code": "VALIDATION_ERROR",
                "details": {
                    "errors": exc.errors(),
                    "body": exc.body if hasattr(exc, "body") else None,
                },
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors"""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "code": "INTERNAL_ERROR",
            },
        )

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """
        Root endpoint - API information

        Returns basic information about the API and links to documentation.
        """
        return {
            "name": "World Cup Betting Insights API",
            "version": version,
            "documentation": "/docs",
            "redoc": "/redoc",
            "health": "/api/v1/health",
            "metrics": "/metrics" if ENABLE_METRICS else None,
            "disclaimer": "This API provides betting insights only. No guaranteed wins. 18+",
            "security": {
                "authentication": f"API Key via {API_KEY_HEADER_NAME} header",
                "rate_limit": f"{RATE_LIMIT_PER_IP} requests per {RATE_LIMIT_WINDOW_SECONDS}s",
            },
        }

    # Health check endpoint (public, no auth required)
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        Public health check endpoint.

        Returns basic health status without requiring authentication.
        """
        return {
            "status": "healthy",
            "version": version,
            "timestamp": time.time(),
        }

    # Prometheus metrics endpoint (if enabled)
    if ENABLE_METRICS:

        @app.get("/metrics", tags=["Monitoring"])
        async def metrics():
            """
            Prometheus metrics endpoint.

            Returns metrics in Prometheus text exposition format.
            Should be scraped by Prometheus server.
            """
            return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


# Create default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
