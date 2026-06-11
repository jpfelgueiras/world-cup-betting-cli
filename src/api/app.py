"""
FastAPI Application Factory

Creates and configures the FastAPI application for the REST API.
Includes security features: rate limiting, API key auth, CORS, security headers.
"""

import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, Request, Security, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.security import APIKeyHeader

from ..config import (
    API_KEY_HEADER,
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

# Valid API keys (in production, load from environment/secret manager)
VALID_API_KEYS: List[str] = [
    key.strip()
    for key in os.getenv("VALID_API_KEYS", "dev-key-12345").split(",")
    if key.strip()
]

# Rate limiting storage (in production, use Redis)
_rate_limit_storage: Dict[str, List[float]] = defaultdict(list)


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
    
    # Clean old entries
    _rate_limit_storage[client_ip] = [
        timestamp
        for timestamp in _rate_limit_storage[client_ip]
        if current_time - timestamp < window
    ]
    
    # Check limit
    if len(_rate_limit_storage[client_ip]) >= max_requests:
        return False
    
    # Record this request
    _rate_limit_storage[client_ip].append(current_time)
    return True


async def verify_api_key(
    api_key: str = Security(api_key_header),
) -> str:
    """
    Verify API key for authentication.
    
    In development mode (DEV_MODE=true), API key is optional.
    In production, valid API key is required for all endpoints.
    """
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
    
    if dev_mode and not api_key:
        return "dev-mode"
    
    if not api_key:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key not in VALID_API_KEYS:
        from fastapi import HTTPException
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
    logger.info(f"🔒 Rate limiting: {RATE_LIMIT_PER_IP} req/{RATE_LIMIT_WINDOW_SECONDS}s")
    logger.info(f"🔒 CORS enabled: {ENABLE_CORS}")
    logger.info(f"🔒 API Key auth: {'enabled' if VALID_API_KEYS else 'disabled'}")
    logger.info(f"📊 Metrics enabled: {ENABLE_METRICS}")

    try:
        from predictors.data_loader import DataLoader

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
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Rate limit headers
        client_ip = request.client.host if request.client else "unknown"
        remaining = max(0, RATE_LIMIT_PER_IP - len(_rate_limit_storage.get(client_ip, [])))
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_PER_IP)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response

    # Add rate limiting middleware
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """Apply rate limiting to all requests."""
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/api/v1/health", "/", "/metrics"]:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        
        if not check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RateLimitExceeded",
                    "message": f"Rate limit exceeded. Max {RATE_LIMIT_PER_IP} requests per {RATE_LIMIT_WINDOW_SECONDS} seconds.",
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


# Import JSONResponse here to avoid undefined name in middleware
from fastapi.responses import JSONResponse

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
