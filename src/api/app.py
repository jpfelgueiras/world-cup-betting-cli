"""
FastAPI Application Factory

Creates and configures the FastAPI application for the REST API.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(api_router)

    # Add exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle validation errors with detailed response"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize application on startup"""
        logger.info("🚀 World Cup Betting Insights API starting...")

        # Initialize database/cache
        try:
            from predictors.data_loader import DataLoader

            DataLoader()  # Initialize cache
            logger.info("✅ Database cache initialized")
        except Exception as e:
            logger.warning(f"⚠️  Database initialization skipped: {e}")

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        logger.info("👋 World Cup Betting Insights API shutting down...")

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
            "disclaimer": "This API provides betting insights only. No guaranteed wins. 18+",
        }

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
