"""
Sentry integration for error tracking.

Configure SENTRY_DSN environment variable to enable.
"""

import os
from typing import Optional


def init_sentry(dsn: Optional[str] = None, environment: str = "production"):
    """
    Initialize Sentry SDK for error tracking.

    Args:
        dsn: Sentry DSN (defaults to SENTRY_DSN env var)
        environment: Deployment environment (production, staging, development)

    Returns:
        True if Sentry was initialized, False otherwise
    """
    dsn = dsn or os.getenv("SENTRY_DSN")

    if not dsn:
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[
                FastApiIntegration(),
            ],
            # Set traces_sample_rate to 1.0 to capture 100% of transactions
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            # Set profiles_sample_rate to profile 10% of transactions
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            # Enable performance monitoring
            enable_tracing=True,
            # Add release information
            release=os.getenv("SENTRY_RELEASE", "world-cup-betting-cli@0.1.0"),
        )

        return True

    except ImportError:
        print("⚠️  Sentry SDK not installed. Run: pip install sentry-sdk[fastapi]")
        return False
    except Exception as e:
        print(f"⚠️  Failed to initialize Sentry: {e}")
        return False
